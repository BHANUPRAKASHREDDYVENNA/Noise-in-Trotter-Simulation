BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'job_status') THEN
        CREATE TYPE job_status AS ENUM ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED');
    END IF;
END
$$;

CREATE TABLE IF NOT EXISTS jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idempotency_key VARCHAR(128) NOT NULL,
    task VARCHAR(64) NOT NULL,
    work_units INTEGER NOT NULL,
    max_attempts SMALLINT NOT NULL DEFAULT 3,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    status job_status NOT NULL DEFAULT 'PENDING',
    available_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    locked_by VARCHAR(128),
    locked_at TIMESTAMPTZ,
    result_checksum BIGINT,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT jobs_idempotency_key_uk UNIQUE (idempotency_key),
    CONSTRAINT jobs_task_format_ck CHECK (task ~ '^[A-Za-z0-9._-]{1,64}$'),
    CONSTRAINT jobs_work_units_ck CHECK (work_units BETWEEN 1 AND 10000000),
    CONSTRAINT jobs_max_attempts_ck CHECK (max_attempts BETWEEN 1 AND 10),
    CONSTRAINT jobs_attempt_count_ck CHECK (attempt_count BETWEEN 0 AND 10000000),
    CONSTRAINT jobs_running_lock_ck CHECK (
        (status = 'RUNNING' AND locked_by IS NOT NULL AND locked_at IS NOT NULL)
        OR
        (status <> 'RUNNING' AND locked_by IS NULL AND locked_at IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS jobs_pending_idx
    ON jobs (available_at, created_at, job_id)
    WHERE status = 'PENDING';

CREATE INDEX IF NOT EXISTS jobs_status_updated_idx
    ON jobs (status, updated_at DESC);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := clock_timestamp();
    RETURN NEW;
END
$$;

DROP TRIGGER IF EXISTS jobs_set_updated_at ON jobs;
CREATE TRIGGER jobs_set_updated_at
BEFORE UPDATE ON jobs
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP FUNCTION IF EXISTS create_job(TEXT, TEXT, INTEGER, SMALLINT);

CREATE OR REPLACE FUNCTION create_job(
    p_idempotency_key TEXT,
    p_task TEXT,
    p_work_units INTEGER,
    p_max_attempts INTEGER DEFAULT 3
)
RETURNS TABLE (
    job_id UUID,
    idempotency_key VARCHAR(128),
    task VARCHAR(64),
    work_units INTEGER,
    max_attempts SMALLINT,
    attempt_count INTEGER,
    status job_status,
    available_at TIMESTAMPTZ,
    locked_by VARCHAR(128),
    locked_at TIMESTAMPTZ,
    result_checksum BIGINT,
    last_error TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
DECLARE
    existing jobs%ROWTYPE;
BEGIN
    IF p_idempotency_key IS NULL OR length(trim(p_idempotency_key)) = 0 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'idempotency key must not be empty';
    END IF;
    IF length(p_idempotency_key) > 128 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'idempotency key exceeds 128 characters';
    END IF;
    IF p_task IS NULL OR p_task !~ '^[A-Za-z0-9._-]{1,64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'task contains invalid characters';
    END IF;
    IF p_work_units IS NULL OR p_work_units NOT BETWEEN 1 AND 10000000 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'work_units must be between 1 and 10000000';
    END IF;
    IF p_max_attempts IS NULL OR p_max_attempts NOT BETWEEN 1 AND 10 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'max_attempts must be between 1 and 10';
    END IF;

    INSERT INTO jobs (idempotency_key, task, work_units, max_attempts)
    VALUES (p_idempotency_key, p_task, p_work_units, p_max_attempts)
    ON CONFLICT ON CONSTRAINT jobs_idempotency_key_uk DO NOTHING;

    SELECT * INTO existing
    FROM jobs
    WHERE jobs.idempotency_key = p_idempotency_key
    FOR UPDATE;

    IF existing.task <> p_task
       OR existing.work_units <> p_work_units
       OR existing.max_attempts <> p_max_attempts THEN
        RAISE EXCEPTION USING
            ERRCODE = '23505',
            MESSAGE = 'idempotency key already exists with different job parameters';
    END IF;

    RETURN QUERY
    SELECT existing.job_id, existing.idempotency_key, existing.task, existing.work_units,
           existing.max_attempts, existing.attempt_count, existing.status, existing.available_at,
           existing.locked_by, existing.locked_at, existing.result_checksum, existing.last_error,
           existing.created_at, existing.updated_at;
END
$$;

CREATE OR REPLACE FUNCTION claim_next_job(p_worker_id TEXT)
RETURNS TABLE (
    job_id UUID,
    idempotency_key VARCHAR(128),
    task VARCHAR(64),
    work_units INTEGER,
    max_attempts SMALLINT,
    attempt_count INTEGER,
    status job_status,
    available_at TIMESTAMPTZ,
    locked_by VARCHAR(128),
    locked_at TIMESTAMPTZ,
    result_checksum BIGINT,
    last_error TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
DECLARE
    candidate UUID;
BEGIN
    IF p_worker_id IS NULL OR length(trim(p_worker_id)) = 0 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'worker id must not be empty';
    END IF;
    IF length(p_worker_id) > 128 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'worker id exceeds 128 characters';
    END IF;

    SELECT j.job_id INTO candidate
    FROM jobs AS j
    WHERE j.status = 'PENDING'
      AND j.available_at <= clock_timestamp()
    ORDER BY j.available_at, j.created_at, j.job_id
    FOR UPDATE SKIP LOCKED
    LIMIT 1;

    IF candidate IS NULL THEN
        RETURN;
    END IF;

    UPDATE jobs AS j
    SET status = 'RUNNING',
        locked_by = p_worker_id,
        locked_at = clock_timestamp(),
        attempt_count = j.attempt_count + 1,
        last_error = NULL
    WHERE j.job_id = candidate;

    RETURN QUERY
    SELECT j.job_id, j.idempotency_key, j.task, j.work_units, j.max_attempts,
           j.attempt_count, j.status, j.available_at, j.locked_by, j.locked_at,
           j.result_checksum, j.last_error, j.created_at, j.updated_at
    FROM jobs AS j
    WHERE j.job_id = candidate;
END
$$;

CREATE OR REPLACE FUNCTION complete_job(
    p_job_id UUID,
    p_worker_id TEXT,
    p_result_checksum BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    changed INTEGER;
BEGIN
    IF p_job_id IS NULL OR p_worker_id IS NULL OR length(trim(p_worker_id)) = 0 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'job id and worker id are required';
    END IF;

    UPDATE jobs
    SET status = 'COMPLETED',
        locked_by = NULL,
        locked_at = NULL,
        result_checksum = p_result_checksum,
        last_error = NULL
    WHERE job_id = p_job_id
      AND status = 'RUNNING'
      AND locked_by = p_worker_id;

    GET DIAGNOSTICS changed = ROW_COUNT;
    IF changed <> 1 THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'job is not owned by worker or is not RUNNING';
    END IF;
    RETURN TRUE;
END
$$;

CREATE OR REPLACE FUNCTION fail_job(
    p_job_id UUID,
    p_worker_id TEXT,
    p_error TEXT
)
RETURNS job_status
LANGUAGE plpgsql
AS $$
DECLARE
    current_row jobs%ROWTYPE;
    next_status job_status;
    delay_seconds INTEGER;
BEGIN
    SELECT * INTO current_row
    FROM jobs
    WHERE job_id = p_job_id
      AND status = 'RUNNING'
      AND locked_by = p_worker_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'job is not owned by worker or is not RUNNING';
    END IF;

    IF current_row.attempt_count < current_row.max_attempts THEN
        next_status := 'PENDING';
        delay_seconds := LEAST(300, GREATEST(1, power(2, current_row.attempt_count)::INTEGER));
    ELSE
        next_status := 'FAILED';
        delay_seconds := 0;
    END IF;

    UPDATE jobs
    SET status = next_status,
        available_at = clock_timestamp() + make_interval(secs => delay_seconds),
        locked_by = NULL,
        locked_at = NULL,
        last_error = LEFT(COALESCE(p_error, 'unspecified worker error'), 2000)
    WHERE job_id = p_job_id;

    RETURN next_status;
END
$$;

CREATE OR REPLACE FUNCTION requeue_stale_jobs(p_stale_after_seconds INTEGER DEFAULT 60)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    changed INTEGER;
BEGIN
    IF p_stale_after_seconds < 1 OR p_stale_after_seconds > 86400 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'stale timeout must be between 1 and 86400 seconds';
    END IF;

    UPDATE jobs
    SET status = 'PENDING',
        available_at = clock_timestamp(),
        locked_by = NULL,
        locked_at = NULL,
        last_error = LEFT(COALESCE(last_error, 'stale worker lock recovered'), 2000)
    WHERE status = 'RUNNING'
      AND locked_at < clock_timestamp() - make_interval(secs => p_stale_after_seconds);

    GET DIAGNOSTICS changed = ROW_COUNT;
    RETURN changed;
END
$$;

COMMIT;
