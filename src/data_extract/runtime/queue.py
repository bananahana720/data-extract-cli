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
    """Simple single-worker queue for local background jobs."""

    def __init__(self, handler: Callable[[str, dict[str, Any]], None]) -> None:
        self._handler = handler
        self._queue: Queue[QueuedJob] = Queue()
        self._stop = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        """Start worker thread if not already running."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = Thread(target=self._run, name="data-extract-job-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Request worker shutdown and wait briefly for join."""
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def submit(self, job_id: str, payload: dict[str, Any]) -> None:
        """Queue a job for background execution."""
        self._queue.put(QueuedJob(job_id=job_id, payload=payload))

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
