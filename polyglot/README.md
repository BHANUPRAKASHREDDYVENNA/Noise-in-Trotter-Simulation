# Polyglot Production Pipeline

This subsystem assigns each language to a distinct production layer and joins them with explicit contracts.

## Architecture

- SQL / PostgreSQL: normalized job persistence, uniqueness, lifecycle constraints, indexes, and atomic functions. `claim_next_job()` uses row-level `FOR UPDATE SKIP LOCKED`.
- C11: fixed-capacity, thread-safe `uint64_t` bounded queue with timed operations, close semantics, and NULL validation.
- C++20: concurrent PostgreSQL-backed worker engine with RAII, smart pointers, `shared_mutex`, atomics, bounded back-pressure, and per-thread database connections.
- Java 17: HTTP domain service with immutable records, checked SQL failures, bounded JDBC pooling, `ConcurrentHashMap` idempotency caching, strict request validation, and bounded request bodies.
- Python 3.11: asyncio orchestration with concurrent submission/polling, retries, deadlines, and strict response validation.

Runtime flow:

```text
Python -> Java HTTP API -> PostgreSQL -> C++ worker -> PostgreSQL -> Java/Python polling
```

## Exact verification commands

PostgreSQL:

```bash
psql "$POLYGLOT_DATABASE_URL" -v ON_ERROR_STOP=1 -f polyglot/sql/schema.sql
psql "$POLYGLOT_DATABASE_URL" -v ON_ERROR_STOP=1 -f polyglot/sql/verify.sql
```

C with sanitizers:

```bash
mkdir -p build/polyglot
cc -std=c11 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror -pthread \
  -fsanitize=address,undefined -fno-omit-frame-pointer \
  -Ipolyglot/c -c polyglot/c/bounded_queue.c -o build/polyglot/bounded_queue_san.o
cc -std=c11 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror -pthread \
  -fsanitize=address,undefined -fno-omit-frame-pointer \
  -Ipolyglot/c polyglot/c/test_bounded_queue.c build/polyglot/bounded_queue_san.o \
  -o build/polyglot/c_queue_test
ASAN_OPTIONS=detect_leaks=1 build/polyglot/c_queue_test
```

C++:

```bash
cc -std=c11 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror -pthread \
  -Ipolyglot/c -c polyglot/c/bounded_queue.c -o build/polyglot/bounded_queue.o
g++ -std=c++20 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror -pthread \
  -I/usr/include/postgresql polyglot/cpp/worker_engine.cpp build/polyglot/bounded_queue.o \
  -lpq -o build/polyglot/polyglot_worker
build/polyglot/polyglot_worker --self-test
```

Java:

```bash
javac --release 17 -Xlint:all -Werror -d build/polyglot/java polyglot/java/PolyglotService.java
java -cp build/polyglot/java PolyglotService --self-test
```

Python:

```bash
python3 -m unittest discover -s polyglot/python -p 'test_*.py'
python3 -m py_compile polyglot/python/orchestrator.py polyglot/python/test_orchestrator.py
```

End-to-end runtime:

```bash
java -cp "build/polyglot/java:/usr/share/java/postgresql.jar" PolyglotService \
  --jdbc-url "jdbc:postgresql://127.0.0.1:5432/polyglot?connectTimeout=3&socketTimeout=5" \
  --db-user polyglot --db-password polyglot --host 127.0.0.1 --port 8080
```

In another terminal:

```bash
build/polyglot/polyglot_worker \
  --dsn "host=127.0.0.1 port=5432 dbname=polyglot user=polyglot password=polyglot connect_timeout=3" \
  --worker-id worker-01 --threads 4 --queue-capacity 32 --jobs 8 --poll-ms 100
```

In a third terminal:

```bash
python3 polyglot/python/orchestrator.py --base-url http://127.0.0.1:8080 --jobs 8
```

Then:

```bash
psql "$POLYGLOT_DATABASE_URL" -c \
  "SELECT task, status, attempt_count, result_checksum FROM jobs WHERE task LIKE 'cpu_task_%' ORDER BY task;"
```

The repository also contains a GitHub Actions integration workflow at `.github/workflows/polyglot-ci.yml` that starts PostgreSQL and verifies the complete cross-language pipeline.
