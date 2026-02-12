"""In-process background queue for local single-user job execution."""

from __future__ import annotations

from dataclasses import dataclass
from queue import Empty, Full, Queue
from threading import Event, Thread
from time import monotonic, sleep
from typing import Any, Callable


@dataclass
class QueuedJob:
    """Queued job payload."""

    job_id: str
    payload: dict[str, Any]


class QueueFullError(RuntimeError):
    """Raised when a submit is rejected because queue capacity is exhausted."""


class LocalJobQueue:
    """Simple in-process queue with configurable worker threads."""

    def __init__(
        self,
        handler: Callable[[str, dict[str, Any]], None],
        worker_count: int = 1,
        max_backlog: int = 1000,
        error_handler: Callable[[str, dict[str, Any], Exception], None] | None = None,
    ) -> None:
        self._handler = handler
        self._error_handler = error_handler
        self._queue: Queue[QueuedJob] = Queue(maxsize=max(1, int(max_backlog)))
        self._stop = Event()
        self._worker_count = max(1, int(worker_count))
        self._max_backlog = max(1, int(max_backlog))
        self._threads: list[Thread] = []
        self._watchdog: Thread | None = None
        self._heartbeats: dict[int, float] = {}
        self._worker_restarts = 0

    def start(self) -> None:
        """Start worker threads if not already running."""
        if self._threads and all(thread.is_alive() for thread in self._threads):
            return
        self._stop.clear()
        self._threads = []
        self._heartbeats = {}
        for index in range(self._worker_count):
            self._spawn_worker(index)
        self._watchdog = Thread(
            target=self._watchdog_loop,
            name="data-extract-job-worker-watchdog",
            daemon=True,
        )
        self._watchdog.start()

    def stop(self) -> None:
        """Request worker shutdown and wait briefly for join."""
        self._stop.set()
        for thread in self._threads:
            if thread.is_alive():
                thread.join(timeout=2)
        if self._watchdog is not None and self._watchdog.is_alive():
            self._watchdog.join(timeout=2)
        self._watchdog = None
        self._threads = []

    def submit(self, job_id: str, payload: dict[str, Any]) -> None:
        """Queue a job for background execution."""
        try:
            self._queue.put_nowait(QueuedJob(job_id=job_id, payload=payload))
        except Full as exc:
            raise QueueFullError(
                f"Queue backlog is at capacity ({self._max_backlog}); try again later."
            ) from exc

    @property
    def worker_count(self) -> int:
        """Configured number of queue workers."""
        return self._worker_count

    @property
    def backlog(self) -> int:
        """Approximate number of queued jobs."""
        return self._queue.qsize()

    @property
    def capacity(self) -> int:
        """Configured maximum in-memory backlog."""
        return self._max_backlog

    @property
    def utilization(self) -> float:
        """Queue utilization ratio in [0.0, 1.0]."""
        if self.capacity <= 0:
            return 0.0
        return min(1.0, self.backlog / float(self.capacity))

    @property
    def alive_workers(self) -> int:
        """Number of currently alive worker threads."""
        return sum(1 for thread in self._threads if thread.is_alive())

    @property
    def dead_workers(self) -> int:
        """Number of workers currently not alive."""
        return max(0, self._worker_count - self.alive_workers)

    @property
    def worker_restarts(self) -> int:
        """Number of worker restarts performed by watchdog."""
        return self._worker_restarts

    @property
    def heartbeat_ages(self) -> dict[int, float]:
        """Seconds since each worker's last heartbeat."""
        now = monotonic()
        return {index: max(0.0, now - heartbeat) for index, heartbeat in self._heartbeats.items()}

    def _spawn_worker(self, index: int) -> None:
        thread = Thread(
            target=self._run,
            args=(index,),
            name=f"data-extract-job-worker-{index + 1}",
            daemon=True,
        )
        self._heartbeats[index] = monotonic()
        thread.start()
        if index < len(self._threads):
            self._threads[index] = thread
        else:
            self._threads.append(thread)

    def _watchdog_loop(self) -> None:
        while not self._stop.is_set():
            for index in range(self._worker_count):
                if self._stop.is_set():
                    return
                if index >= len(self._threads):
                    continue
                thread = self._threads[index]
                if thread.is_alive():
                    continue
                self._worker_restarts += 1
                self._spawn_worker(index)
            sleep(0.5)

    def _run(self, worker_index: int) -> None:
        while not self._stop.is_set():
            self._heartbeats[worker_index] = monotonic()
            try:
                queued = self._queue.get(timeout=0.2)
            except Empty:
                continue

            try:
                self._heartbeats[worker_index] = monotonic()
                try:
                    self._handler(queued.job_id, queued.payload)
                except Exception as exc:
                    if self._error_handler is not None:
                        try:
                            self._error_handler(queued.job_id, queued.payload, exc)
                        except Exception:
                            pass
            finally:
                self._queue.task_done()
