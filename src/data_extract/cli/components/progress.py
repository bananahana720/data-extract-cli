"""Progress tracking components for CLI pipeline visualization.

This module provides:
- PipelineProgress: Tracks progress across the 5-stage pipeline
- FileProgress: Tracks individual file processing progress
- PipelineStage: Enum for the 5 pipeline stages

AC-5.3-1: Progress bars in ALL long-running commands
AC-5.3-4: Per-stage progress tracking across pipeline
AC-5.3-7: Progress updates show required info (%, count, file, elapsed, ETA)
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from types import TracebackType
from typing import Any, Optional

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from .feedback import get_console


class PipelineStage(str, Enum):
    """The 5 stages of the document processing pipeline."""

    EXTRACT = "extract"
    NORMALIZE = "normalize"
    CHUNK = "chunk"
    SEMANTIC = "semantic"
    OUTPUT = "output"


@dataclass
class StageProgress:
    """Progress tracking for a single pipeline stage."""

    name: str
    total: int = 0
    completed: int = 0
    started: bool = False


class PipelineProgress:
    """Tracks progress across the 5-stage document processing pipeline.

    Provides Rich Progress integration with all required information:
    - Percentage complete
    - File count (X/Y)
    - Current filename
    - Elapsed time
    - ETA (estimated time remaining)

    Usage:
        with PipelineProgress(total_files=10) as progress:
            for file in files:
                for stage in progress.STAGES:
                    progress.update_stage(stage, files.index(file) + 1)
    """

    STAGES = ["extract", "normalize", "chunk", "semantic", "output"]

    def __init__(
        self,
        total_files: int,
        console: Optional[Console] = None,
    ) -> None:
        """Initialize PipelineProgress.

        Args:
            total_files: Total number of files to process
            console: Rich Console for output. Uses get_console() if None.
        """
        self._total_files = total_files
        self._console = console or get_console()
        self._completed = 0
        self._current_file: Optional[str] = None
        self._start_time: Optional[float] = None
        self._is_started = False
        self._is_stopped = False

        # Initialize stage tracking
        self._stages: dict[str, StageProgress] = {}
        for stage in self.STAGES:
            self._stages[stage] = StageProgress(name=stage, total=total_files)

        # Rich Progress instance
        self._progress: Optional[Progress] = None
        self._task_id: Optional[TaskID] = None

    @property
    def total_files(self) -> int:
        """Total number of files to process."""
        return self._total_files

    @property
    def completed(self) -> int:
        """Number of files fully completed (all stages)."""
        return self._completed

    @property
    def current_file(self) -> Optional[str]:
        """Currently processing filename."""
        return self._current_file

    @property
    def is_started(self) -> bool:
        """True if progress tracking has started."""
        return self._is_started

    @property
    def is_stopped(self) -> bool:
        """True if progress tracking has stopped."""
        return self._is_stopped

    @property
    def stages(self) -> dict[str, StageProgress]:
        """Dictionary of stage progress trackers."""
        return self._stages

    @property
    def percentage(self) -> float:
        """Overall completion percentage."""
        if self._total_files == 0:
            return 100.0
        return (self._completed / self._total_files) * 100

    @property
    def file_count(self) -> str:
        """File count string (e.g., "5/10")."""
        return f"{self._completed}/{self._total_files}"

    @property
    def elapsed(self) -> float:
        """Elapsed time in seconds since start."""
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time

    @property
    def eta(self) -> Optional[float]:
        """Estimated time remaining in seconds."""
        return self.get_eta()

    def start(self) -> None:
        """Start progress tracking."""
        self._start_time = time.time()
        self._is_started = True
        self._is_stopped = False

        # Create Rich Progress with required columns
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self._console,
            transient=False,
        )
        self._progress.start()
        self._task_id = self._progress.add_task(
            "Processing",
            total=self._total_files,
        )

    def stop(self) -> None:
        """Stop progress tracking."""
        self._is_stopped = True
        self._is_started = False
        if self._progress:
            self._progress.stop()

    def __enter__(self) -> "PipelineProgress":
        """Context manager entry - starts progress tracking."""
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit - stops progress tracking."""
        self.stop()

    def start_stage(self, stage: str) -> None:
        """Mark a stage as started.

        Args:
            stage: Stage name (extract, normalize, chunk, semantic, output)
        """
        if stage in self._stages:
            self._stages[stage].started = True

    def complete_stage(self, stage: str) -> None:
        """Mark a stage as complete for one file.

        Args:
            stage: Stage name
        """
        if stage in self._stages:
            self._stages[stage].completed += 1

    def update_stage(self, stage: str, completed: int) -> None:
        """Update progress for a specific stage.

        Args:
            stage: Stage name (extract, normalize, chunk, semantic, output)
            completed: Number of files completed for this stage
        """
        if stage not in self._stages:
            return

        self._stages[stage].completed = completed
        self._stages[stage].started = True

        # If all stages complete for a file, increment overall progress
        # Check if this is the last stage (output) to count completed files
        if stage == "output" or stage == self.STAGES[-1]:
            self._completed = completed
            if self._progress and self._task_id is not None:
                self._progress.update(self._task_id, completed=completed)

    def update_file(self, filename: str, stage: str) -> None:
        """Update current file being processed.

        Args:
            filename: Name of file being processed
            stage: Current stage
        """
        self._current_file = filename
        if self._progress and self._task_id is not None:
            self._progress.update(
                self._task_id,
                description=f"[{stage}] {filename}",
            )

    def advance(self) -> None:
        """Advance progress by one file."""
        self._completed += 1
        if self._progress and self._task_id is not None:
            self._progress.advance(self._task_id)

    def get_eta(self) -> Optional[float]:
        """Calculate estimated time remaining.

        Returns:
            ETA in seconds, or None if cannot be calculated
        """
        if self._start_time is None or self._completed == 0:
            return None

        elapsed = time.time() - self._start_time
        rate = self._completed / elapsed
        remaining = self._total_files - self._completed

        if rate > 0:
            return remaining / rate
        return None

    def get_status(self) -> dict[str, Any]:
        """Get current progress status as dictionary.

        Returns:
            Dict with percentage, completed, filename, elapsed, eta
        """
        return {
            "percentage": self.percentage,
            "completed": self._completed,
            "total": self._total_files,
            "filename": self._current_file,
            "current_file": self._current_file,
            "elapsed": self.elapsed,
            "eta": self.get_eta(),
            "remaining": self.get_eta(),
        }

    def is_complete(self) -> bool:
        """Check if all files have completed all stages.

        Returns:
            True if all files completed
        """
        return self._completed >= self._total_files

    def reset(self, total_files: int) -> None:
        """Reset progress for a new batch.

        Args:
            total_files: New total file count
        """
        self._total_files = total_files
        self._completed = 0
        self._current_file = None
        self._start_time = None
        self._is_started = False
        self._is_stopped = False

        # Reset stage tracking
        for stage in self.STAGES:
            self._stages[stage] = StageProgress(name=stage, total=total_files)

        # Reset Rich Progress
        if self._progress:
            self._progress.stop()
        self._progress = None
        self._task_id = None


class FileProgress:
    """Tracks progress for individual file processing.

    Provides a simpler interface for tracking file-by-file progress
    without the full pipeline stage breakdown.

    Usage:
        progress = FileProgress(total_files=10)
        for i, file in enumerate(files):
            progress.update(current=i+1, filename=file.name)
    """

    def __init__(
        self,
        total_files: int = 0,
        filename: str = "",
        total_stages: int = 5,
        console: Optional[Console] = None,
    ) -> None:
        """Initialize FileProgress.

        Args:
            total_files: Total number of files to process
            filename: Optional initial filename
            total_stages: Number of pipeline stages (default 5)
            console: Rich Console for output
        """
        self._total_files = total_files
        self._total_stages = total_stages
        self._current = 0
        self._current_file: Optional[str] = filename or None
        self._console = console or get_console()
        self._start_time: Optional[float] = None
        self._progress: Optional[Progress] = None
        self._task_id: Optional[TaskID] = None

    @property
    def current_file(self) -> Optional[str]:
        """Currently processing filename."""
        return self._current_file

    @property
    def total_files(self) -> int:
        """Total files to process."""
        return self._total_files

    @property
    def current(self) -> int:
        """Current file index (1-based)."""
        return self._current

    def update(self, current: int, filename: str) -> None:
        """Update progress with current file.

        Args:
            current: Current file number (1-based)
            filename: Name of current file
        """
        self._current = current
        self._current_file = filename

        if self._progress and self._task_id is not None:
            self._progress.update(
                self._task_id,
                completed=current,
                description=filename,
            )

    def start(self) -> None:
        """Start progress display."""
        self._start_time = time.time()
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self._console,
        )
        self._progress.start()
        self._task_id = self._progress.add_task(
            "Processing",
            total=self._total_files,
        )

    def stop(self) -> None:
        """Stop progress display."""
        if self._progress:
            self._progress.stop()

    def __enter__(self) -> "FileProgress":
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit - stops progress display."""
        self.stop()


__all__ = [
    "PipelineStage",
    "StageProgress",
    "PipelineProgress",
    "FileProgress",
]
