"""Bounded in-memory coordination never substitutes for persisted experiment state."""

import threading

import pytest

from alphamosaic.mcp.server import JobManager


def test_job_quota_and_queued_cancellation() -> None:
    jobs = JobManager(max_jobs=2, max_workers=1)
    started, release = threading.Event(), threading.Event()
    def waiting() -> str:
        started.set()
        if not release.wait(10):
            raise TimeoutError("test release missing")
        return "completed"
    first = jobs.submit(waiting)
    assert started.wait(5)
    second = jobs.submit(lambda: "must not run")
    try:
        with pytest.raises(ValueError, match="quota"):
            jobs.submit(lambda: None)
        assert jobs.cancel(first)["status"] == "RUNNING_USE_DECLARED_WORKER_DEADLINE"
        assert jobs.cancel(second)["status"] == "CANCELLED"
        assert jobs.status(second)["status"] == "CANCELLED"
    finally:
        release.set()
        jobs._executor.shutdown(wait=True, cancel_futures=True)
    assert jobs.status(first)["result"] == "completed"
    assert jobs.cancel("missing")["status"] == "UNKNOWN_OR_EXPIRED"
