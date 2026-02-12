"""In-process background queue for local single-user job execution."""

from __future__ import annotations

from dataclasses import dataclass
from queue import Empty, Queue
from threading import Event, Thread
from typing import Any, Callable


@dataclass
class QueuedJob:
    """Queued job payload."""

    job_id: str
    payload: dict[str, Any]


class LocalJobQueue:
    """Simple in-process queue with configurable worker threads."""

    def __init__(
        self, handler: Callable[[str, dict[str, Any]], None], worker_count: int = 1
    ) -> None:
        self._handler = handler
        self._queue: Queue[QueuedJob] = Queue()
        self._stop = Event()
        self._worker_count = max(1, int(worker_count))
        self._threads: list[Thread] = []

    def start(self) -> None:
        """Start worker threads if not already running."""
        if self._threads and all(thread.is_alive() for thread in self._threads):
            return
        self._stop.clear()
        self._threads = []
        for index in range(self._worker_count):
            thread = Thread(
                target=self._run,
                name=f"data-extract-job-worker-{index + 1}",
                daemon=True,
            )
            thread.start()
            self._threads.append(thread)

    def stop(self) -> None:
        """Request worker shutdown and wait briefly for join."""
        self._stop.set()
        for thread in self._threads:
            if thread.is_alive():
                thread.join(timeout=2)
        self._threads = []

    def submit(self, job_id: str, payload: dict[str, Any]) -> None:
        """Queue a job for background execution."""
        self._queue.put(QueuedJob(job_id=job_id, payload=payload))

    @property
    def worker_count(self) -> int:
        """Configured number of queue workers."""
        return self._worker_count

    @property
    def backlog(self) -> int:
        """Approximate number of queued jobs."""
        return self._queue.qsize()

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                queued = self._queue.get(timeout=0.2)
            except Empty:
                continue

            try:
                self._handler(queued.job_id, queued.payload)
            finally:
                self._queue.task_done()
