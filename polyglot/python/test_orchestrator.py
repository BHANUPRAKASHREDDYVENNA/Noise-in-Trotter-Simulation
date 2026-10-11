import unittest

from orchestrator import ClientConfig, PolyglotApiClient


class OrchestratorTests(unittest.TestCase):
    def test_config_rejects_invalid_scheme(self) -> None:
        with self.assertRaises(ValueError):
            PolyglotApiClient(ClientConfig("postgres://127.0.0.1:5432"))

    def test_job_mapping_is_strict(self) -> None:
        payload = {
            "job_id": "00000000-0000-0000-0000-000000000001",
            "task": "task_0001",
            "status": "COMPLETED",
            "attempt_count": 1,
            "result_checksum": 42,
        }
        result = PolyglotApiClient._job_from_json(payload)
        self.assertEqual(result.status, "COMPLETED")
        self.assertEqual(result.result_checksum, 42)

    def test_job_mapping_rejects_negative_attempts(self) -> None:
        payload = {
            "job_id": "00000000-0000-0000-0000-000000000001",
            "task": "task_0001",
            "status": "COMPLETED",
            "attempt_count": -1,
        }
        with self.assertRaises(RuntimeError):
            PolyglotApiClient._job_from_json(payload)

    def test_config_rejects_zero_retries(self) -> None:
        with self.assertRaises(ValueError):
            ClientConfig("http://127.0.0.1:8080", retries=0)

    def test_job_mapping_rejects_unknown_status(self) -> None:
        payload = {
            "job_id": "00000000-0000-0000-0000-000000000001",
            "task": "task_0001",
            "status": "UNKNOWN",
            "attempt_count": 1,
        }
        with self.assertRaises(RuntimeError):
            PolyglotApiClient._job_from_json(payload)

    def test_job_mapping_rejects_invalid_checksum(self) -> None:
        payload = {
            "job_id": "00000000-0000-0000-0000-000000000001",
            "task": "task_0001",
            "status": "COMPLETED",
            "attempt_count": 1,
            "result_checksum": 9_223_372_036_854_775_808,
        }
        with self.assertRaises(RuntimeError):
            PolyglotApiClient._job_from_json(payload)


if __name__ == "__main__":
    unittest.main()
