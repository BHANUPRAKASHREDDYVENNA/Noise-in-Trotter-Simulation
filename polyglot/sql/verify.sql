\set ON_ERROR_STOP on
BEGIN;

DO $$
DECLARE
    j RECORD;
    claimed RECORD;
BEGIN
    SELECT * INTO j
    FROM create_job('sql-verify-001', 'verify_task', 10, 2);

    IF j.status <> 'PENDING' THEN
        RAISE EXCEPTION 'new job status is not PENDING';
    END IF;

    SELECT * INTO claimed
    FROM claim_next_job('sql-verifier');

    IF claimed.job_id <> j.job_id OR claimed.status <> 'RUNNING' OR claimed.attempt_count <> 1 THEN
        RAISE EXCEPTION 'claim_next_job did not atomically claim the expected row';
    END IF;

    IF NOT complete_job(j.job_id, 'sql-verifier', 42) THEN
        RAISE EXCEPTION 'complete_job returned false';
    END IF;

    SELECT * INTO j FROM jobs WHERE job_id = j.job_id;
    IF j.status <> 'COMPLETED' OR j.result_checksum <> 42 THEN
        RAISE EXCEPTION 'completed job state is incorrect';
    END IF;
END
$$;

DO $$
BEGIN
    BEGIN
        PERFORM create_job('sql-verify-invalid', 'bad task!', 1, 1);
        RAISE EXCEPTION 'invalid task unexpectedly succeeded';
    EXCEPTION WHEN SQLSTATE '22023' THEN
        NULL;
    END;
END
$$;

ROLLBACK;

SELECT 'SQL verification passed.' AS result;
