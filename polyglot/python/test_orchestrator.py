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


if __name__ == "__main__":
    unittest.main()
