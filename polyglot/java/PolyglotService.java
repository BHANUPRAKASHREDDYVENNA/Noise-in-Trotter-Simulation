import com.sun.net.httpserver.Headers;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.regex.Pattern;

public final class PolyglotService {
    private static final int MAX_BODY_BYTES = 8192;
    private static final Pattern TOKEN = Pattern.compile("^[A-Za-z0-9._-]{1,128}$");
    private static final Pattern TASK = Pattern.compile("^[A-Za-z0-9._-]{1,64}$");
    private static final int IDEMPOTENCY_CACHE_MAX_ENTRIES = 10000;
    private static final long IDEMPOTENCY_CACHE_TTL_NANOS = TimeUnit.MINUTES.toNanos(10);

    private final JobRepository repository;
    private final ConcurrentHashMap<String, CacheEntry> idempotencyCache = new ConcurrentHashMap<>();

    private PolyglotService(JobRepository repository) {
        this.repository = repository;
    }

    public static void main(String[] args) throws Exception {
        if (args.length == 1 && "--self-test".equals(args[0])) {
            runSelfTest();
            return;
        }

        String host = "127.0.0.1";
        int port = 8080;
        String jdbcUrl = envOrDefault("POLYGLOT_JDBC_URL", "jdbc:postgresql://127.0.0.1:5432/polyglot");
        String dbUser = envOrDefault("POLYGLOT_DB_USER", "polyglot");
        String dbPassword = envOrDefault("POLYGLOT_DB_PASSWORD", "polyglot");
        int poolSize = 8;

        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--host" -> host = requireValue(args, ++i, "--host");
                case "--port" -> port = Integer.parseInt(requireValue(args, ++i, "--port"));
                case "--jdbc-url" -> jdbcUrl = requireValue(args, ++i, "--jdbc-url");
                case "--db-user" -> dbUser = requireValue(args, ++i, "--db-user");
                case "--db-password" -> dbPassword = requireValue(args, ++i, "--db-password");
                case "--pool-size" -> poolSize = Integer.parseInt(requireValue(args, ++i, "--pool-size"));
                default -> throw new IllegalArgumentException("unknown argument: " + args[i]);
            }
        }

        if (port < 1 || port > 65535) {
            throw new IllegalArgumentException("port must be between 1 and 65535");
        }
        if (poolSize < 1 || poolSize > 64) {
            throw new IllegalArgumentException("pool size must be between 1 and 64");
        }

        Class.forName("org.postgresql.Driver");
        ConnectionPool pool = new ConnectionPool(jdbcUrl, dbUser, dbPassword, poolSize);
        PolyglotService service = new PolyglotService(new JobRepository(pool));
        service.start(host, port, pool);
    }

    private void start(String host, int port, ConnectionPool pool) throws IOException, InterruptedException {
        HttpServer server = HttpServer.create(new InetSocketAddress(host, port), 64);
        server.createContext("/health", this::handleHealth);
        server.createContext("/v1/jobs", this::handleJobs);
        server.setExecutor(Executors.newFixedThreadPool(16));
        java.util.concurrent.CountDownLatch shutdown = new java.util.concurrent.CountDownLatch(1);
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            server.stop(0);
            pool.close();
            shutdown.countDown();
        }, "polyglot-shutdown"));
        server.start();
        System.out.printf("Java domain service listening on http://%s:%d%n", host, port);
        shutdown.await();
    }

    private void handleHealth(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendJson(exchange, 405, "{\"error\":\"method not allowed\"}");
            return;
        }
        sendJson(exchange, 200, "{\"status\":\"ok\"}");
    }

    private void handleJobs(HttpExchange exchange) throws IOException {
        try {
            String method = exchange.getRequestMethod().toUpperCase();
            String path = exchange.getRequestURI().getPath();
            if ("POST".equals(method) && "/v1/jobs".equals(path)) {
                handleCreateJob(exchange);
                return;
            }
            if ("GET".equals(method) && path.startsWith("/v1/jobs/")) {
                handleGetJob(exchange, path.substring("/v1/jobs/".length()));
                return;
            }
            sendJson(exchange, 404, "{\"error\":\"not found\"}");
        } catch (ValidationException error) {
            sendJson(exchange, 400, jsonError(error.getMessage()));
        } catch (JobConflictException error) {
            sendJson(exchange, 409, jsonError(error.getMessage()));
        } catch (NotFoundException error) {
            sendJson(exchange, 404, jsonError(error.getMessage()));
        } catch (TimeoutException error) {
            sendJson(exchange, 503, jsonError("database connection pool timeout"));
        } catch (SQLException error) {
            System.err.println("Database failure: " + error.getMessage());
            sendJson(exchange, 503, jsonError("database unavailable"));
        } catch (Exception error) {
            error.printStackTrace(System.err);
            sendJson(exchange, 500, jsonError("internal server error"));
        } finally {
            exchange.close();
        }
    }

    private void handleCreateJob(HttpExchange exchange) throws Exception {
        Map<String, String> form = parseForm(readBody(exchange));
        String idempotencyKey = required(form, "idempotency_key");
        String task = required(form, "task");
        int workUnits = parseInt(form, "work_units", 1, 10_000_000);
        int maxAttempts = parseInt(form, "max_attempts", 1, 10);

        validateToken(idempotencyKey, 128, "idempotency_key");
        if (!TASK.matcher(task).matches()) {
            throw new ValidationException("task must match [A-Za-z0-9._-]{1,64}");
        }

        CacheEntry cached = idempotencyCache.get(idempotencyKey);
        long now = System.nanoTime();
        if (cached != null) {
            if (cached.expiresAtNanos() > now) {
                JobView existing = repository.findJob(cached.jobId());
                if (existing != null) {
                    sendJson(exchange, 200, existing.toJson());
                    return;
                }
            }
            idempotencyCache.remove(idempotencyKey, cached);
        }

        JobView job = repository.createJob(idempotencyKey, task, workUnits, maxAttempts);
        idempotencyCache.put(idempotencyKey, new CacheEntry(job.jobId(), now + IDEMPOTENCY_CACHE_TTL_NANOS));
        pruneIdempotencyCache();
        sendJson(exchange, 201, job.toJson());
    }

    private void handleGetJob(HttpExchange exchange, String idText) throws Exception {
        UUID jobId;
        try {
            jobId = UUID.fromString(idText);
        } catch (IllegalArgumentException error) {
            throw new ValidationException("invalid job id");
        }
        JobView job = repository.findJob(jobId);
        if (job == null) {
            throw new NotFoundException("job not found");
        }
        sendJson(exchange, 200, job.toJson());
    }

    private static String readBody(HttpExchange exchange) throws IOException, ValidationException {
        String contentLength = exchange.getRequestHeaders().getFirst("Content-Length");
        long declaredLength;
        if (contentLength == null) {
            declaredLength = -1L;
        } else {
            try {
                declaredLength = Long.parseLong(contentLength);
            } catch (NumberFormatException error) {
                throw new ValidationException("invalid Content-Length header");
            }
        }
        if (declaredLength > MAX_BODY_BYTES) {
            throw new ValidationException("request body exceeds limit");
        }
        try (InputStream input = exchange.getRequestBody()) {
            byte[] buffer = new byte[MAX_BODY_BYTES + 1];
            int offset = 0;
            int read;
            while ((read = input.read(buffer, offset, buffer.length - offset)) > 0) {
                offset += read;
                if (offset > MAX_BODY_BYTES) {
                    throw new ValidationException("request body exceeds limit");
                }
                if (offset == buffer.length) {
                    break;
                }
            }
            return new String(buffer, 0, offset, StandardCharsets.UTF_8);
        }
    }

    private static Map<String, String> parseForm(String body) throws ValidationException {
        if (body == null || body.isBlank()) {
            throw new ValidationException("request body is empty");
        }
        Map<String, String> values = new HashMap<>();
        for (String part : body.split("&", -1)) {
            if (part.isEmpty()) {
                continue;
            }
            String[] pieces = part.split("=", 2);
            if (pieces.length != 2) {
                throw new ValidationException("malformed form field");
            }
            String key = URLDecoder.decode(pieces[0], StandardCharsets.UTF_8);
            String value = URLDecoder.decode(pieces[1], StandardCharsets.UTF_8);
            if (key.isBlank() || values.putIfAbsent(key, value) != null) {
                throw new ValidationException("duplicate or empty form field");
            }
        }
        return values;
    }

    private static String required(Map<String, String> values, String key) throws ValidationException {
        String value = values.get(key);
        if (value == null || value.isBlank()) {
            throw new ValidationException(key + " is required");
        }
        return value;
    }

    private static int parseInt(Map<String, String> values, String key, int min, int max) throws ValidationException {
        String raw = required(values, key);
        try {
            int value = Integer.parseInt(raw);
            if (value < min || value > max) {
                throw new ValidationException(key + " must be between " + min + " and " + max);
            }
            return value;
        } catch (NumberFormatException error) {
            throw new ValidationException(key + " must be an integer");
        }
    }

    private static void validateToken(String value, int maxLength, String field) throws ValidationException {
        if (value.length() > maxLength || !TOKEN.matcher(value).matches()) {
            throw new ValidationException(field + " contains invalid characters");
        }
    }

    private void pruneIdempotencyCache() {
        if (idempotencyCache.size() <= IDEMPOTENCY_CACHE_MAX_ENTRIES) {
            return;
        }
        long now = System.nanoTime();
        for (Map.Entry<String, CacheEntry> entry : idempotencyCache.entrySet()) {
            if (entry.getValue().expiresAtNanos() <= now) {
                idempotencyCache.remove(entry.getKey(), entry.getValue());
            }
        }
        if (idempotencyCache.size() <= IDEMPOTENCY_CACHE_MAX_ENTRIES) {
            return;
        }
        int toRemove = idempotencyCache.size() - IDEMPOTENCY_CACHE_MAX_ENTRIES;
        for (String key : idempotencyCache.keySet()) {
            if (toRemove <= 0) {
                break;
            }
            if (idempotencyCache.remove(key) != null) {
                toRemove--;
            }
        }
    }

    private static String envOrDefault(String key, String defaultValue) {
        String value = System.getenv(key);
        return value == null || value.isBlank() ? defaultValue : value;
    }

    private static String requireValue(String[] args, int index, String flag) {
        if (index >= args.length) {
            throw new IllegalArgumentException("missing value for " + flag);
        }
        return args[index];
    }

    private static void sendJson(HttpExchange exchange, int status, String body) throws IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        Headers headers = exchange.getResponseHeaders();
        headers.set("Content-Type", "application/json; charset=utf-8");
        headers.set("Cache-Control", "no-store");
        exchange.sendResponseHeaders(status, bytes.length);
        try (OutputStream output = exchange.getResponseBody()) {
            output.write(bytes);
        }
    }

    private static String jsonError(String message) {
        return "{"error":"" + escapeJson(message) + ""}";
    }

    static String escapeJson(String value) {
        if (value == null) {
            return "";
        }
        return value.replace("\", "\\").replace(""", "\"").replace("
", "\n").replace("", "\r");
    }

    private static void runSelfTest() throws Exception {
        if (!"a_b-1".equals(URLDecoder.decode("a_b-1", StandardCharsets.UTF_8))) {
            throw new AssertionError("URL decoding failed");
        }
        Map<String, String> values = parseForm("idempotency_key=abc&task=cpu_test&work_units=5&max_attempts=2");
        if (!"abc".equals(values.get("idempotency_key"))) {
            throw new AssertionError("form parsing failed");
        }
        if (parseInt(values, "work_units", 1, 10_000_000) != 5) {
            throw new AssertionError("integer parsing failed");
        }
        if (!"{\"error\":\"x\\\"y\"}".equals(jsonError("x\"y"))) {
            throw new AssertionError("JSON escaping failed");
        }
        System.out.println("Java domain service self-test passed.");
    }

    private record CacheEntry(UUID jobId, long expiresAtNanos) {}

    private record JobView(
        UUID jobId,
        String idempotencyKey,
        String task,
        int workUnits,
        int maxAttempts,
        int attemptCount,
        String status,
        Instant availableAt,
        Instant lockedAt,
        Long resultChecksum,
        String lastError,
        Instant createdAt,
        Instant updatedAt
    ) {
        String toJson() {
            String result = resultChecksum == null ? "null" : resultChecksum.toString();
            String locked = lockedAt == null
                ? "null"
                : "\"" + escapeJson(lockedAt.toString()) + "\"";
            String error = lastError == null
                ? "null"
                : "\"" + escapeJson(lastError) + "\"";
            return "{"
                + "\"job_id\":\"" + jobId + "\","
                + "\"idempotency_key\":\"" + escapeJson(idempotencyKey) + "\","
                + "\"task\":\"" + escapeJson(task) + "\","
                + "\"work_units\":" + workUnits + ","
                + "\"max_attempts\":" + maxAttempts + ","
                + "\"attempt_count\":" + attemptCount + ","
                + "\"status\":\"" + escapeJson(status) + "\","
                + "\"available_at\":\"" + escapeJson(availableAt.toString()) + "\","
                + "\"locked_at\":" + locked + ","
                + "\"result_checksum\":" + result + ","
                + "\"last_error\":" + error + ","
                + "\"created_at\":\"" + escapeJson(createdAt.toString()) + "\","
                + "\"updated_at\":\"" + escapeJson(updatedAt.toString()) + "\""
                + "}";
        }
    }

    private static final class JobRepository {
        private final ConnectionPool pool;

        JobRepository(ConnectionPool pool) {
            this.pool = pool;
        }

        JobView createJob(String idempotencyKey, String task, int workUnits, int maxAttempts)
            throws SQLException, TimeoutException, JobConflictException {
            Connection connection = pool.borrow();
            try (PreparedStatement statement = connection.prepareStatement("SELECT * FROM create_job(?,?,?,?)")) {
                statement.setString(1, idempotencyKey);
                statement.setString(2, task);
                statement.setInt(3, workUnits);
                statement.setInt(4, maxAttempts);
                try (ResultSet result = statement.executeQuery()) {
                    if (!result.next()) {
                        throw new SQLException("create_job returned no row");
                    }
                    return map(result);
                }
            } catch (SQLException error) {
                if ("23505".equals(error.getSQLState())) {
                    throw new JobConflictException(error.getMessage());
                }
                throw error;
            } finally {
                pool.release(connection);
            }
        }

        JobView findJob(UUID jobId) throws SQLException, TimeoutException {
            Connection connection = pool.borrow();
            try (PreparedStatement statement = connection.prepareStatement("SELECT * FROM jobs WHERE job_id = ?")) {
                statement.setObject(1, jobId);
                try (ResultSet result = statement.executeQuery()) {
                    return result.next() ? map(result) : null;
                }
            } finally {
                pool.release(connection);
            }
        }

        private JobView map(ResultSet result) throws SQLException {
            return new JobView(
                result.getObject("job_id", UUID.class),
                result.getString("idempotency_key"),
                result.getString("task"),
                result.getInt("work_units"),
                result.getInt("max_attempts"),
                result.getInt("attempt_count"),
                result.getString("status"),
                result.getTimestamp("available_at").toInstant(),
                timestampOrNull(result, "locked_at"),
                result.getObject("result_checksum", Long.class),
                result.getString("last_error"),
                result.getTimestamp("created_at").toInstant(),
                result.getTimestamp("updated_at").toInstant()
            );
        }

        private static Instant timestampOrNull(ResultSet result, String column) throws SQLException {
            Timestamp timestamp = result.getTimestamp(column);
            return timestamp == null ? null : timestamp.toInstant();
        }
    }

    private static final class ConnectionPool implements AutoCloseable {
        private final ArrayBlockingQueue<Connection> connections;
        private final String url;
        private final String user;
        private final String password;
        private volatile boolean closed;

        ConnectionPool(String url, String user, String password, int size) throws SQLException {
            this.url = url;
            this.user = user;
            this.password = password;
            this.connections = new ArrayBlockingQueue<>(size);
            for (int i = 0; i < size; i++) {
                connections.add(openConnection());
            }
        }

        private Connection openConnection() throws SQLException {
            Connection connection = DriverManager.getConnection(url, user, password);
            connection.setReadOnly(false);
            connection.setAutoCommit(true);
            return connection;
        }

        Connection borrow() throws SQLException, TimeoutException {
            if (closed) {
                throw new SQLException("connection pool is closed");
            }
            try {
                Connection connection = connections.poll(3, TimeUnit.SECONDS);
                if (connection == null) {
                    throw new TimeoutException("connection pool exhausted");
                }
                if (connection.isClosed() || !connection.isValid(2)) {
                    try {
                        connection.close();
                    } catch (SQLException ignored) {
                        // The replacement connection is authoritative.
                    }
                    return openConnection();
                }
                return connection;
            } catch (InterruptedException error) {
                Thread.currentThread().interrupt();
                throw new TimeoutException("interrupted while borrowing database connection");
            }
        }

        void release(Connection connection) throws SQLException {
            if (connection == null) {
                return;
            }
            if (closed || connection.isClosed()) {
                try {
                    connection.close();
                } catch (SQLException ignored) {
                    // Best effort during pool shutdown.
                }
                return;
            }
            if (!connections.offer(connection)) {
                connection.close();
            }
        }

        @Override
        public void close() {
            closed = true;
            List<Connection> snapshot = new ArrayList<>();
            connections.drainTo(snapshot);
            for (Connection connection : snapshot) {
                try {
                    connection.close();
                } catch (SQLException ignored) {
                    // Best effort during shutdown.
                }
            }
        }
    }

    private static final class ValidationException extends Exception {
        private static final long serialVersionUID = 1L;
        ValidationException(String message) { super(message); }
    }

    private static final class NotFoundException extends Exception {
        private static final long serialVersionUID = 1L;
        NotFoundException(String message) { super(message); }
    }

    private static final class JobConflictException extends Exception {
        private static final long serialVersionUID = 1L;
        JobConflictException(String message) { super(message); }
    }
}
