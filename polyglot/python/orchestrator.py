#!/usr/bin/env python3
"""Async orchestration client for the polyglot job-processing pipeline."""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ClientConfig:
    base_url: str
    request_timeout_seconds: float = 5.0
    poll_interval_seconds: float = 0.2
    overall_timeout_seconds: float = 60.0
    retries: int = 5

    def __post_init__(self) -> None:
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        if not 0.1 <= self.request_timeout_seconds <= 120.0:
            raise ValueError("request_timeout_seconds must be between 0.1 and 120")
        if not 0.01 <= self.poll_interval_seconds <= 60.0:
            raise ValueError("poll_interval_seconds must be between 0.01 and 60")
        if not 1.0 <= self.overall_timeout_seconds <= 3600.0:
            raise ValueError("overall_timeout_seconds must be between 1 and 3600")
        if not 1 <= self.retries <= 10:
            raise ValueError("retries must be between 1 and 10")


@dataclass(frozen=True)
class JobResult:
    job_id: str
    task: str
    status: str
    attempt_count: int
    result_checksum: int | None


class ApiError(RuntimeError):
    """Raised when the Java service returns an unexpected API response."""


class RetryableApiError(ApiError):
    """Raised for transient HTTP failures that are safe to retry."""


class PolyglotApiClient:
    def __init__(self, config: ClientConfig) -> None:
        self._config = config
        base = config.base_url.rstrip("/")
        if not base.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        self._base_url = base

    async def health(self) -> Mapping[str, Any]:
        return await self._request_json("GET", "/health", None)

    async def create_job(
        self,
        idempotency_key: str,
        task: str,
        work_units: int,
        max_attempts: int,
    ) -> JobResult:
        if not idempotency_key or len(idempotency_key) > 128:
            raise ValueError("idempotency_key must be non-empty and <= 128 characters")
        if not task or len(task) > 64 or not all(ch.isalnum() or ch in "._-" for ch in task):
            raise ValueError("task contains unsupported characters")
        if not 1 <= work_units <= 10_000_000:
            raise ValueError("work_units must be between 1 and 10000000")
        if not 1 <= max_attempts <= 10:
            raise ValueError("max_attempts must be between 1 and 10")

        form = urllib.parse.urlencode(
            {
                "idempotency_key": idempotency_key,
                "task": task,
                "work_units": str(work_units),
                "max_attempts": str(max_attempts),
            }
        ).encode("utf-8")
        payload = await self._request_json(
            "POST", "/v1/jobs", form, "application/x-www-form-urlencoded"
        )
        return self._job_from_json(payload)

    async def get_job(self, job_id: str, deadline: float | None = None) -> JobResult:
        try:
            uuid.UUID(job_id)
        except ValueError as error:
            raise ValueError("job_id must be a UUID") from error
        payload = await self._request_json("GET", f"/v1/jobs/{job_id}", None, deadline=deadline)
        return self._job_from_json(payload)

    async def wait_for_completion(self, job_id: str) -> JobResult:
        deadline = asyncio.get_running_loop().time() + self._config.overall_timeout_seconds
        while True:
            if asyncio.get_running_loop().time() >= deadline:
                raise TimeoutError(f"job {job_id} did not finish before the deadline")
            result = await self.get_job(job_id, deadline=deadline)
            if result.status in {"COMPLETED", "FAILED"}:
                return result
            await asyncio.sleep(
                self._config.poll_interval_seconds + random.uniform(0.0, 0.05)
            )

    async def _request_json(
        self,
        method: str,
        path: str,
        body: bytes | None,
        content_type: str = "application/json",
        deadline: float | None = None,
    ) -> Mapping[str, Any]:
        url = self._base_url + path
        last_error: Exception | None = None
        for attempt in range(self._config.retries):
            timeout_seconds = self._config.request_timeout_seconds
            if deadline is not None:
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    raise TimeoutError("request deadline expired")
                timeout_seconds = min(timeout_seconds, remaining)

            try:
                return await asyncio.to_thread(
                    self._request_json_sync,
                    method,
                    url,
                    body,
                    content_type,
                    timeout_seconds,
                )
            except RetryableApiError as error:
                last_error = error
            except (urllib.error.URLError, TimeoutError, OSError) as error:
                last_error = error
            except ApiError:
                raise

            if attempt + 1 >= self._config.retries:
                break

            delay = min(1.0, 0.1 * (2**attempt))
            if deadline is not None:
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    raise TimeoutError("request deadline expired")
                delay = min(delay, max(0.0, remaining))
            await asyncio.sleep(delay)

        raise ApiError(f"request failed after retries: {last_error}") from last_error

    def _request_json_sync(
        self,
        method: str,
        url: str,
        body: bytes | None,
        content_type: str,
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        request = urllib.request.Request(url=url, data=body, method=method)
        request.add_header("Accept", "application/json")
        request.add_header("Connection", "close")
        if body is not None:
            request.add_header("Content-Type", content_type)
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                content = response.read(1_048_577)
                if len(content) > 1_048_576:
                    raise ApiError("service response exceeds 1 MiB")
                parsed: Any = json.loads(content.decode("utf-8"))
                if not isinstance(parsed, dict):
                    raise ApiError("service returned a non-object JSON response")
                return parsed
        except urllib.error.HTTPError as error:
            raw = error.read(16_384).decode("utf-8", errors="replace")
            try:
                details = json.loads(raw)
            except json.JSONDecodeError:
                details = {"error": raw or error.reason}
            if error.code in {408, 425, 429, 500, 502, 503, 504}:
                raise RetryableApiError(f"HTTP {error.code}: {details}") from error
            raise ApiError(f"HTTP {error.code}: {details}") from error

    @staticmethod
    def _job_from_json(payload: Mapping[str, Any]) -> JobResult:
        required = ("job_id", "task", "status", "attempt_count")
        missing = [key for key in required if key not in payload]
        if missing:
            raise ApiError(f"job response missing fields: {missing}")
        job_id = payload["job_id"]
        task = payload["task"]
        status = payload["status"]
        attempts = payload["attempt_count"]
        checksum = payload.get("result_checksum")
        if not isinstance(job_id, str) or not isinstance(task, str) or not isinstance(status, str):
            raise ApiError("job response contains invalid string fields")
        try:
            uuid.UUID(job_id)
        except ValueError as error:
            raise ApiError("job response contains invalid job_id") from error
        if not task or len(task) > 64 or not all(ch.isalnum() or ch in "._-" for ch in task):
            raise ApiError("job response contains invalid task")
        if status not in {"PENDING", "RUNNING", "COMPLETED", "FAILED"}:
            raise ApiError("job response contains invalid status")
        if not isinstance(attempts, int) or not 0 <= attempts <= 10_000_000:
            raise ApiError("job response contains invalid attempt_count")
        if checksum is not None and (
            not isinstance(checksum, int) or not 0 <= checksum <= 9_223_372_036_854_775_807
        ):
            raise ApiError("job response contains invalid result_checksum")
        return JobResult(job_id, task, status, attempts, checksum)


async def run_pipeline(config: ClientConfig, job_count: int) -> list[JobResult]:
    if not 1 <= job_count <= 1000:
        raise ValueError("job_count must be between 1 and 1000")

    client = PolyglotApiClient(config)
    health = await client.health()
    if health.get("status") != "ok":
        raise ApiError("Java service health check failed")

    submissions = [
        client.create_job(
            str(uuid.uuid4()),
            f"cpu_task_{index + 1:04d}",
            25_000 + index * 1_000,
            3,
        )
        for index in range(job_count)
    ]
    jobs = await asyncio.gather(*submissions)
    print(f"Submitted {len(jobs)} job(s).")

    completed = await asyncio.gather(
        *(client.wait_for_completion(job.job_id) for job in jobs)
    )
    failures = [job for job in completed if job.status != "COMPLETED"]
    if failures:
        raise RuntimeError(f"pipeline returned failed jobs: {failures}")
    return completed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the polyglot end-to-end pipeline.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--request-timeout", type=float, default=5.0)
    parser.add_argument("--poll-ms", type=int, default=200)
    parser.add_argument("--overall-timeout", type=float, default=60.0)
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    if args.poll_ms <= 0 or args.poll_ms > 60_000:
        raise ValueError("--poll-ms must be between 1 and 60000")
    if args.request_timeout <= 0 or args.request_timeout > 120:
        raise ValueError("--request-timeout must be between 0.1 and 120 seconds")
    if args.overall_timeout <= 0 or args.overall_timeout > 3600:
        raise ValueError("--overall-timeout must be between 1 and 3600 seconds")
    config = ClientConfig(
        base_url=args.base_url,
        request_timeout_seconds=args.request_timeout,
        poll_interval_seconds=args.poll_ms / 1000.0,
        overall_timeout_seconds=args.overall_timeout,
    )
    results = await run_pipeline(config, args.jobs)
    print("Python orchestration completed successfully.")
    for result in results:
        print(
            f"{result.job_id} {result.task} {result.status} "
            f"attempts={result.attempt_count} checksum={result.result_checksum}"
        )


if __name__ == "__main__":
    asyncio.run(main())
