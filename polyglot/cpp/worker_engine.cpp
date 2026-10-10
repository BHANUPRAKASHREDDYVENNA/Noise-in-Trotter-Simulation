#include "../c/bounded_queue.h"

#include <libpq-fe.h>

#include <atomic>
#include <chrono>
#include <csignal>
#include <cstdint>
#include <cstring>
#include <exception>
#include <iostream>
#include <memory>
#include <shared_mutex>
#include <stdexcept>
#include <string>
#include <thread>
#include <unordered_map>
#include <vector>
#include <optional>

namespace {
std::atomic<bool> g_stop_requested{false};

void signal_handler(int) {
    g_stop_requested.store(true, std::memory_order_relaxed);
}

struct PgConnDeleter {
    void operator()(PGconn *conn) const noexcept { if (conn != nullptr) PQfinish(conn); }
};
struct PgResultDeleter {
    void operator()(PGresult *result) const noexcept { if (result != nullptr) PQclear(result); }
};
using PgConn = std::unique_ptr<PGconn, PgConnDeleter>;
using PgResult = std::unique_ptr<PGresult, PgResultDeleter>;

struct QueueDeleter {
    void operator()(bb_queue_t *queue) const noexcept { bb_queue_destroy(queue); }
};
using JobQueue = std::unique_ptr<bb_queue_t, QueueDeleter>;

struct Job {
    std::uint64_t sequence{};
    std::string job_id;
    std::string task;
    int work_units{};
    int attempt_count{};
};

struct Options {
    std::string dsn;
    std::string worker_id = "polyglot-worker";
    std::size_t threads = 2U;
    std::size_t queue_capacity = 32U;
    std::uint64_t max_jobs = 0U;
    std::uint32_t poll_ms = 100U;
};

std::uint64_t fnv1a_64(const std::string &text) {
    std::uint64_t hash = 1469598103934665603ULL;
    for (unsigned char byte : text) {
        hash ^= static_cast<std::uint64_t>(byte);
        hash *= 1099511628211ULL;
    }
    return hash;
}

std::uint64_t execute_job(const Job &job) {
    if (job.work_units <= 0 || job.work_units > 10000000) {
        throw std::invalid_argument("work_units outside database contract");
    }
    std::uint64_t state = fnv1a_64(job.job_id + ":" + job.task);
    const std::uint64_t units = static_cast<std::uint64_t>(job.work_units);
    for (std::uint64_t i = 0; i < units; ++i) {
        state ^= state >> 12U;
        state ^= state << 25U;
        state ^= state >> 27U;
        state *= 2685821657736338717ULL;
    }
    return state;
}

PgConn connect_db(const std::string &dsn, const std::string &application_name) {
    PgConn connection(PQconnectdb(dsn.c_str()));
    if (!connection || PQstatus(connection.get()) != CONNECTION_OK) {
        const std::string message = connection ? PQerrorMessage(connection.get())
                                               : "unable to allocate PostgreSQL connection";
        throw std::runtime_error("PostgreSQL connection failed: " + message);
    }
    const std::string app_sql = "SET application_name = '" + application_name + "'";
    PgResult app_result(PQexec(connection.get(), app_sql.c_str()));
    if (!app_result || PQresultStatus(app_result.get()) != PGRES_COMMAND_OK) {
        throw std::runtime_error("PostgreSQL SET application_name failed: "
                                 + std::string(PQerrorMessage(connection.get())));
    }
    PgResult timeout_result(PQexec(connection.get(), "SET statement_timeout = '5000ms'"));
    if (!timeout_result || PQresultStatus(timeout_result.get()) != PGRES_COMMAND_OK) {
        throw std::runtime_error("PostgreSQL statement_timeout configuration failed: "
                                 + std::string(PQerrorMessage(connection.get())));
    }
    return connection;
}

void ensure_ok(PGresult *result, ExecStatusType expected, PGconn *connection, const char *operation) {
    if (result == nullptr || PQresultStatus(result) != expected) {
        const std::string detail = connection != nullptr ? PQerrorMessage(connection) : "unknown PostgreSQL error";
        throw std::runtime_error(std::string(operation) + " failed: " + detail);
    }
}

std::optional<Job> claim_next_job(PGconn *connection, const std::string &worker_id, std::uint64_t sequence) {
    const char *values[] = {worker_id.c_str()};
    PgResult result(PQexecParams(connection,
                                 "SELECT job_id::text, task, work_units, attempt_count "
                                 "FROM claim_next_job($1)",
                                 1, nullptr, values, nullptr, nullptr, 0));
    ensure_ok(result.get(), PGRES_TUPLES_OK, connection, "claim_next_job");
    if (PQntuples(result.get()) == 0) return std::nullopt;

    Job job;
    job.sequence = sequence;
    job.job_id = PQgetvalue(result.get(), 0, 0);
    job.task = PQgetvalue(result.get(), 0, 1);
    job.work_units = std::stoi(PQgetvalue(result.get(), 0, 2));
    job.attempt_count = std::stoi(PQgetvalue(result.get(), 0, 3));
    return job;
}

void complete_job(PGconn *connection, const Job &job, const std::string &worker_id, std::uint64_t checksum) {
    const std::string checksum_text = std::to_string(checksum);
    const char *values[] = {job.job_id.c_str(), worker_id.c_str(), checksum_text.c_str()};
    PgResult result(PQexecParams(connection,
                                 "SELECT complete_job($1::uuid, $2, $3::bigint)",
                                 3, nullptr, values, nullptr, nullptr, 0));
    ensure_ok(result.get(), PGRES_TUPLES_OK, connection, "complete_job");
    if (PQntuples(result.get()) != 1 || std::strcmp(PQgetvalue(result.get(), 0, 0), "t") != 0) {
        throw std::runtime_error("complete_job returned an unexpected result");
    }
}

void fail_job(PGconn *connection, const Job &job, const std::string &worker_id, const std::string &error) {
    const char *values[] = {job.job_id.c_str(), worker_id.c_str(), error.c_str()};
    PgResult result(PQexecParams(connection,
                                 "SELECT fail_job($1::uuid, $2, $3)",
                                 3, nullptr, values, nullptr, nullptr, 0));
    ensure_ok(result.get(), PGRES_TUPLES_OK, connection, "fail_job");
}

void requeue_stale_jobs(PGconn *connection) {
    const char *values[] = {"60"};
    PgResult result(PQexecParams(connection,
                                 "SELECT requeue_stale_jobs($1::integer)",
                                 1, nullptr, values, nullptr, nullptr, 0));
    ensure_ok(result.get(), PGRES_TUPLES_OK, connection, "requeue_stale_jobs");
}

class WorkerEngine {
public:
    explicit WorkerEngine(Options options)
        : options_(std::move(options)),
          queue_(bb_queue_create(options_.queue_capacity)) {
        if (options_.dsn.empty()) throw std::invalid_argument("--dsn is required");
        if (options_.threads == 0U || options_.threads > 64U) {
            throw std::invalid_argument("--threads must be between 1 and 64");
        }
        if (options_.queue_capacity == 0U || options_.queue_capacity > 100000U) {
            throw std::invalid_argument("--queue-capacity must be between 1 and 100000");
        }
        if (options_.poll_ms == 0U || options_.poll_ms > 60000U) {
            throw std::invalid_argument("--poll-ms must be between 1 and 60000");
        }
        if (!queue_) throw std::runtime_error("failed to allocate C bounded queue");
    }

    int run() {
        std::cout << "C++ worker starting with " << options_.threads << " threads\n";
        producer_thread_ = std::thread(&WorkerEngine::producer_loop, this);
        for (std::size_t i = 0U; i < options_.threads; ++i) {
            worker_threads_.emplace_back(&WorkerEngine::worker_loop, this, i);
        }
        producer_thread_.join();
        for (std::thread &thread : worker_threads_) thread.join();
        std::cout << "C++ worker completed " << completed_.load() << " job(s), claimed "
                  << claimed_.load() << " job(s).\n";
        return failed_jobs_.load() == 0U ? 0 : 1;
    }

    static int self_test() {
        Job job{1U, "00000000-0000-0000-0000-000000000001", "self_test", 3, 1};
        const std::uint64_t a = execute_job(job);
        const std::uint64_t b = execute_job(job);
        if (a != b || a == 0U) {
            std::cerr << "C++ self-test failed: checksum is not deterministic.\n";
            return 1;
        }
        std::cout << "C++ worker self-test passed. checksum=" << a << "\n";
        return 0;
    }

private:
    void producer_loop() {
        PgConn connection;
        try {
            connection = connect_db(options_.dsn, options_.worker_id + "-producer");
            requeue_stale_jobs(connection.get());
            while (!should_stop()) {
                if (options_.max_jobs > 0U && claimed_.load() >= options_.max_jobs) break;

                const std::uint64_t sequence = claimed_.load() + 1U;
                const auto claimed_job = claim_next_job(connection.get(), options_.worker_id, sequence);
                if (!claimed_job.has_value()) {
                    std::this_thread::sleep_for(std::chrono::milliseconds(options_.poll_ms));
                    continue;
                }

                auto shared_job = std::make_shared<Job>(*claimed_job);
                {
                    std::unique_lock<std::shared_mutex> lock(jobs_mutex_);
                    jobs_.emplace(shared_job->sequence, shared_job);
                }
                claimed_.fetch_add(1U);

                for (;;) {
                    if (should_stop()) break;
                    const bb_status_t status = bb_queue_push(queue_.get(), shared_job->sequence, 100U);
                    if (status == BB_OK) break;
                    if (status == BB_CLOSED) {
                        stop_requested_.store(true);
                        return;
                    }
                    if (status != BB_TIMEOUT) throw std::runtime_error("C bounded queue push failed");
                }
            }
        } catch (const std::exception &error) {
            std::cerr << "Producer error: " << error.what() << '\n';
            failed_jobs_.fetch_add(1U);
            stop_requested_.store(true);
        }
        bb_queue_close(queue_.get());
    }

    void worker_loop(std::size_t worker_index) {
        try {
            const std::string worker_name = options_.worker_id + "-worker-" + std::to_string(worker_index);
            PgConn connection = connect_db(options_.dsn, worker_name);
            for (;;) {
                std::uint64_t sequence = 0U;
                const bb_status_t status = bb_queue_pop(queue_.get(), &sequence, 250U);
                if (status == BB_CLOSED) break;
                if (status == BB_TIMEOUT) {
                    if (should_stop() && claimed_.load() == completed_.load()) break;
                    continue;
                }
                if (status != BB_OK) throw std::runtime_error("C bounded queue pop failed");

                std::shared_ptr<Job> job;
                {
                    std::shared_lock<std::shared_mutex> lock(jobs_mutex_);
                    const auto it = jobs_.find(sequence);
                    if (it == jobs_.end()) throw std::runtime_error("job metadata missing from C++ registry");
                    job = it->second;
                }

                try {
                    const std::uint64_t checksum = execute_job(*job);
                    for (int attempt = 0; attempt < 3; ++attempt) {
                        try {
                            complete_job(connection.get(), *job, options_.worker_id, checksum);
                            completed_.fetch_add(1U);
                            break;
                        } catch (const std::exception &) {
                            if (attempt == 2) throw;
                            std::this_thread::sleep_for(
                                std::chrono::milliseconds(100U * static_cast<unsigned int>(attempt + 1)));
                            connection = connect_db(options_.dsn, worker_name);
                        }
                    }
                } catch (const std::exception &error) {
                    try {
                        fail_job(connection.get(), *job, options_.worker_id, error.what());
                    } catch (const std::exception &failure_error) {
                        std::cerr << "Worker " << worker_index << " could not record failure for "
                                  << job->job_id << ": " << failure_error.what() << '\n';
                    }
                    failed_jobs_.fetch_add(1U);
                }

                {
                    std::unique_lock<std::shared_mutex> lock(jobs_mutex_);
                    jobs_.erase(sequence);
                }

                if (options_.max_jobs > 0U &&
                    completed_.load() + failed_jobs_.load() >= options_.max_jobs) {
                    stop_requested_.store(true);
                    bb_queue_close(queue_.get());
                    break;
                }
            }
        } catch (const std::exception &error) {
            std::cerr << "Worker thread error: " << error.what() << '\n';
            failed_jobs_.fetch_add(1U);
            stop_requested_.store(true);
            bb_queue_close(queue_.get());
        }
    }

    bool should_stop() const {
        return stop_requested_.load(std::memory_order_relaxed)
            || g_stop_requested.load(std::memory_order_relaxed);
    }

    Options options_;
    JobQueue queue_;
    std::thread producer_thread_;
    std::vector<std::thread> worker_threads_;
    std::atomic<bool> stop_requested_{false};
    std::atomic<std::uint64_t> claimed_{0U};
    std::atomic<std::uint64_t> completed_{0U};
    std::atomic<std::uint64_t> failed_jobs_{0U};
    mutable std::shared_mutex jobs_mutex_;
    std::unordered_map<std::uint64_t, std::shared_ptr<Job>> jobs_;
};

std::string next_arg(int &index, int argc, char **argv) {
    if (index + 1 >= argc) throw std::invalid_argument("missing value for argument " + std::string(argv[index]));
    ++index;
    return argv[index];
}

Options parse_options(int argc, char **argv) {
    Options options;
    for (int i = 1; i < argc; ++i) {
        const std::string argument = argv[i];
        if (argument == "--dsn") {
            options.dsn = next_arg(i, argc, argv);
        } else if (argument == "--worker-id") {
            options.worker_id = next_arg(i, argc, argv);
        } else if (argument == "--threads") {
            options.threads = static_cast<std::size_t>(std::stoul(next_arg(i, argc, argv)));
        } else if (argument == "--queue-capacity") {
            options.queue_capacity = static_cast<std::size_t>(std::stoul(next_arg(i, argc, argv)));
        } else if (argument == "--jobs") {
            options.max_jobs = std::stoull(next_arg(i, argc, argv));
        } else if (argument == "--poll-ms") {
            options.poll_ms = static_cast<std::uint32_t>(std::stoul(next_arg(i, argc, argv)));
        } else if (argument == "--self-test") {
            return options;
        } else if (argument == "--help") {
            std::cout << "Usage: worker_engine --dsn <postgres-dsn> [--worker-id ID] [--threads N] "
                         "[--queue-capacity N] [--jobs N] [--poll-ms MS] [--self-test]\n";
            std::exit(0);
        } else {
            throw std::invalid_argument("unknown argument: " + argument);
        }
    }
    return options;
}
}

int main(int argc, char **argv) {
    try {
        const bool self_test = argc > 1 && std::string(argv[1]) == "--self-test";
        if (self_test) return WorkerEngine::self_test();
        std::signal(SIGINT, signal_handler);
        std::signal(SIGTERM, signal_handler);
        const Options options = parse_options(argc, argv);
        WorkerEngine engine(options);
        return engine.run();
    } catch (const std::exception &error) {
        std::cerr << "Fatal: " << error.what() << '\n';
        return 2;
    }
}
