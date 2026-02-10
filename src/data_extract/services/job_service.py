"""Processing job orchestration service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from data_extract.cli.batch import IncrementalProcessor
from data_extract.cli.exit_codes import determine_exit_code
from data_extract.cli.session import SessionManager, SessionState
from data_extract.contracts import (
    FileFailure,
    JobStatus,
    ProcessedFileOutcome,
    ProcessJobRequest,
    ProcessJobResult,
)
from data_extract.services.file_discovery_service import FileDiscoveryService
from data_extract.services.pipeline_service import PipelineService


class JobService:
    """Orchestrate discovery, session state, and pipeline execution."""

    def __init__(
        self,
        discovery_service: Optional[FileDiscoveryService] = None,
        pipeline_service: Optional[PipelineService] = None,
    ) -> None:
        self.discovery = discovery_service or FileDiscoveryService()
        self.pipeline = pipeline_service or PipelineService()

    def run_process(
        self,
        request: ProcessJobRequest,
        work_dir: Optional[Path] = None,
        job_id: Optional[str] = None,
    ) -> ProcessJobResult:
        """Execute a processing job and return structured outcome."""
        started_at = datetime.now(timezone.utc)
        resolved_files, source_dir = self._resolve_files(request)
        output_dir = self._resolve_output_dir(request, source_dir)

        manager = SessionManager(work_dir=work_dir or source_dir)
        session_state = self._resolve_session(request, manager, source_dir)

        skipped_files: List[Path] = []

        # Apply incremental filtering before resume-based skips.
        if request.incremental and not request.source_files:
            incremental = IncrementalProcessor(source_dir=source_dir, output_dir=output_dir)
            changes = incremental.analyze()
            if not request.force:
                changed = set(changes.new_files + changes.modified_files)
                skipped_files.extend(changes.unchanged_files)
                resolved_files = [f for f in resolved_files if f in changed]

        if session_state is None:
            manager.start_session(
                source_dir=source_dir,
                total_files=len(resolved_files),
                configuration={
                    "format": request.output_format,
                    "chunk_size": request.chunk_size,
                    "recursive": request.recursive,
                    "output_path": str(output_dir),
                },
            )
            session_state = manager._current_session
        else:
            already_processed_names = {entry.get("path") for entry in session_state.processed_files}
            remaining = []
            for file_path in resolved_files:
                if file_path.name in already_processed_names:
                    skipped_files.append(file_path)
                else:
                    remaining.append(file_path)
            resolved_files = remaining

        run = self.pipeline.process_files(
            files=resolved_files,
            output_dir=output_dir,
            output_format=request.output_format,
            chunk_size=request.chunk_size,
            include_semantic=request.include_semantic,
            continue_on_error=request.continue_on_error,
        )

        processed_outcomes: List[ProcessedFileOutcome] = []
        failure_outcomes: List[FileFailure] = []

        if session_state:
            for processed in run.processed:
                manager.record_processed_file(
                    file_path=processed.source_path,
                    output_path=processed.output_path,
                    file_hash="",
                )
                processed_outcomes.append(
                    ProcessedFileOutcome(
                        path=str(processed.source_path),
                        output_path=str(processed.output_path),
                        chunk_count=processed.chunk_count,
                        stage_timings_ms=processed.stage_timings_ms,
                    )
                )

            for failed in run.failed:
                manager.record_failed_file(
                    file_path=failed.source_path,
                    error_type=failed.error_type,
                    error_message=failed.error_message,
                )
                failure_outcomes.append(
                    FileFailure(
                        path=str(failed.source_path),
                        error_type=failed.error_type,
                        error_message=failed.error_message,
                    )
                )

            manager.save_session()
            manager.complete_session()

        processed_count = len(run.processed)
        failed_count = len(run.failed)
        total_files = len(resolved_files) + len(skipped_files)

        if processed_count == 0 and failed_count == 0:
            exit_code = 0
        else:
            exit_code = determine_exit_code(
                total_files=total_files,
                processed_count=processed_count,
                failed_count=failed_count,
                config_error=False,
            )

        if failed_count > 0 and processed_count > 0:
            status = JobStatus.PARTIAL
        elif failed_count > 0:
            status = JobStatus.FAILED
        elif processed_count == 0 and len(skipped_files) > 0:
            status = JobStatus.COMPLETED
        else:
            status = JobStatus.COMPLETED

        finished_at = datetime.now(timezone.utc)
        return ProcessJobResult(
            job_id=job_id or (session_state.session_id if session_state else str(uuid.uuid4())[:8]),
            status=status,
            total_files=total_files,
            processed_count=processed_count,
            failed_count=failed_count,
            skipped_count=len(skipped_files),
            output_dir=str(output_dir),
            session_id=session_state.session_id if session_state else None,
            processed_files=processed_outcomes,
            failed_files=failure_outcomes,
            stage_totals_ms=run.stage_totals_ms,
            started_at=started_at,
            finished_at=finished_at,
            exit_code=exit_code,
        )

    def _resolve_files(self, request: ProcessJobRequest) -> tuple[List[Path], Path]:
        """Resolve files to process from explicit list or path discovery."""
        if request.source_files:
            files = [Path(p).resolve() for p in request.source_files]
            for file_path in files:
                if not file_path.exists():
                    raise FileNotFoundError(f"Retry source file not found: {file_path}")
            source_dir = files[0].parent if files else Path(request.input_path).resolve()
            return files, source_dir

        files, source_dir = self.discovery.discover(request.input_path, recursive=request.recursive)
        return files, source_dir

    @staticmethod
    def _resolve_output_dir(request: ProcessJobRequest, source_dir: Path) -> Path:
        """Resolve output dir honoring explicit output or default workspace output."""
        output_dir = Path(request.output_path).resolve() if request.output_path else source_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def _resolve_session(
        self,
        request: ProcessJobRequest,
        manager: SessionManager,
        source_dir: Path,
    ) -> Optional[SessionState]:
        """Resolve resume target from explicit session id or source dir."""
        if request.resume_session:
            state = manager.load_session(request.resume_session)
            if not state:
                raise FileNotFoundError(f"Session not found: {request.resume_session}")
            return state
        if request.resume:
            return manager.find_incomplete_session(source_dir)
        return None
