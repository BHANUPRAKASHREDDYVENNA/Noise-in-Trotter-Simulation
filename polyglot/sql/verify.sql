\set ON_ERROR_STOP on
BEGIN;

DO $polyglot$
DECLARE
    j RECORD;
    claimed RECORD;
BEGIN
    SELECT * INTO j
    FROM create_job('sql-verify-001', 'verify_task', 10, 2);

    IF j.status <> 'PENDING' OR j.lease_token IS NOT NULL THEN
        RAISE EXCEPTION 'new job status is not PENDING';
    END IF;

    SELECT * INTO claimed
    FROM claim_next_job('sql-verifier');

    IF claimed.job_id <> j.job_id OR claimed.status <> 'RUNNING' OR claimed.attempt_count <> 1 OR claimed.lease_token IS NULL THEN
        RAISE EXCEPTION 'claim_next_job did not atomically claim the expected row';
    END IF;

    IF NOT complete_job(j.job_id, 'sql-verifier', claimed.lease_token, 42) THEN
        RAISE EXCEPTION 'complete_job returned false';
    END IF;

    IF NOT complete_job(j.job_id, 'sql-verifier', claimed.lease_token, 42) THEN
        RAISE EXCEPTION 'idempotent completion failed';
    END IF;

    SELECT * INTO j FROM jobs WHERE job_id = j.job_id;
    IF j.status <> 'COMPLETED' OR j.result_checksum <> 42 OR j.lease_token IS NOT NULL THEN
        RAISE EXCEPTION 'completed job state is incorrect';
    END IF;
END
$polyglot$;

DO $polyglot$
DECLARE
    job_row RECORD;
    first_claim RECORD;
    second_claim RECORD;
BEGIN
    SELECT * INTO job_row
    FROM create_job('sql-verify-fencing', 'fencing_task', 5, 3);

    SELECT * INTO first_claim
    FROM claim_next_job('sql-fencer-a');

    UPDATE jobs
    SET locked_at = clock_timestamp() - INTERVAL '120 seconds'
    WHERE job_id = job_row.job_id;

    IF requeue_stale_jobs(60) <> 1 THEN
        RAISE EXCEPTION 'stale lease recovery failed';
    END IF;

    SELECT * INTO second_claim
    FROM claim_next_job('sql-fencer-b');

    IF second_claim.lease_token IS NULL OR second_claim.lease_token = first_claim.lease_token THEN
        RAISE EXCEPTION 'lease token was not replaced';
    END IF;

    BEGIN
        PERFORM complete_job(job_row.job_id, 'sql-fencer-a', first_claim.lease_token, 99);
        RAISE EXCEPTION 'stale lease was accepted';
    EXCEPTION WHEN SQLSTATE '55000' THEN
        NULL;
    END;

    IF NOT complete_job(job_row.job_id, 'sql-fencer-b', second_claim.lease_token, 100) THEN
        RAISE EXCEPTION 'current lease completion failed';
    END IF;
END
$polyglot$;

DO $polyglot$
BEGIN
    BEGIN
        PERFORM create_job('sql-verify-invalid', 'bad task!', 1, 1);
        RAISE EXCEPTION 'invalid task unexpectedly succeeded';
    EXCEPTION WHEN SQLSTATE '22023' THEN
        NULL;
    END;
END
$polyglot$;

ROLLBACK;

SELECT 'SQL verification passed.' AS result;
