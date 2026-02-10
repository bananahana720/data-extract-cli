"""Shared DTOs for CLI, API, and UI integration."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Processing job lifecycle state."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class FileFailure(BaseModel):
    """Failure details for a single source file."""

    path: str
    error_type: str
    error_message: str


class ProcessedFileOutcome(BaseModel):
    """Success details for a single processed file."""

    path: str
    output_path: str
    chunk_count: int = 0
    stage_timings_ms: Dict[str, float] = Field(default_factory=dict)


class ProcessJobRequest(BaseModel):
    """Request contract for processing files through the pipeline."""

    input_path: str
    output_path: Optional[str] = None
    output_format: str = "json"
    chunk_size: int = 512
    recursive: bool = False
    incremental: bool = False
    force: bool = False
    resume: bool = False
    resume_session: Optional[str] = None
    preset: Optional[str] = None
    non_interactive: bool = False
    include_semantic: bool = False
    continue_on_error: bool = True
    source_files: List[str] = Field(default_factory=list)


class ProcessJobResult(BaseModel):
    """Result contract for process/retry operations."""

    job_id: str
    status: JobStatus
    total_files: int
    processed_count: int
    failed_count: int
    skipped_count: int = 0
    output_dir: str
    session_id: Optional[str] = None
    processed_files: List[ProcessedFileOutcome] = Field(default_factory=list)
    failed_files: List[FileFailure] = Field(default_factory=list)
    stage_totals_ms: Dict[str, float] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    exit_code: int = 0


class RetryRequest(BaseModel):
    """Request contract for retry operations."""

    last: bool = False
    session: Optional[str] = None
    file: Optional[str] = None
    backoff: bool = False
    non_interactive: bool = False
    output_format: str = "json"
    chunk_size: int = 512


class SessionSummary(BaseModel):
    """Session summary for listing and API responses."""

    session_id: str
    status: str
    source_directory: str
    total_files: int
    processed_count: int
    failed_count: int
    updated_at: datetime
