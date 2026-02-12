from __future__ import annotations

import time
from threading import Lock

from data_extract.runtime.queue import LocalJobQueue, QueueFullError


def test_local_job_queue_processes_jobs_with_multiple_workers() -> None:
    handled: list[str] = []
    lock = Lock()

    def handler(job_id: str, _payload: dict[str, object]) -> None:
        with lock:
            handled.append(job_id)

    queue = LocalJobQueue(handler, worker_count=2)
    queue.start()
    try:
        queue.submit("job-1", {"kind": "process"})
        queue.submit("job-2", {"kind": "process"})
        queue.submit("job-3", {"kind": "process"})

        deadline = time.time() + 2.0
        while len(handled) < 3 and time.time() < deadline:
            time.sleep(0.05)
    finally:
        queue.stop()

    assert sorted(handled) == ["job-1", "job-2", "job-3"]
    assert queue.worker_count == 2


def test_local_job_queue_enforces_backlog_capacity() -> None:
    queue = LocalJobQueue(lambda _job_id, _payload: None, worker_count=1, max_backlog=1)
    queue.submit("job-1", {"kind": "process"})
    try:
        queue.submit("job-2", {"kind": "process"})
        raise AssertionError("Expected QueueFullError")
    except QueueFullError:
        pass


def test_local_job_queue_traps_handler_errors_and_continues() -> None:
    handled: list[str] = []
    captured_errors: list[str] = []

    def handler(job_id: str, _payload: dict[str, object]) -> None:
        if job_id == "job-bad":
            raise RuntimeError("boom")
        handled.append(job_id)

    def error_handler(job_id: str, _payload: dict[str, object], exc: Exception) -> None:
        captured_errors.append(f"{job_id}:{exc}")

    queue = LocalJobQueue(handler, worker_count=1, error_handler=error_handler)
    queue.start()
    try:
        queue.submit("job-bad", {"kind": "process"})
        queue.submit("job-good", {"kind": "process"})
        deadline = time.time() + 2.0
        while "job-good" not in handled and time.time() < deadline:
            time.sleep(0.05)
    finally:
        queue.stop()

    assert "job-good" in handled
    assert captured_errors == ["job-bad:boom"]
    assert queue.alive_workers <= queue.worker_count
