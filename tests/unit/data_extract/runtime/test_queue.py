from __future__ import annotations

import time
from threading import Lock

from data_extract.runtime.queue import LocalJobQueue


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
