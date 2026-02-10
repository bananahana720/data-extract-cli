"""Processing job orchestration service."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

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
from data_extract.services.pathing import normalized_path_text, source_key_for_path
from data_extract.services.pipeline_service import PipelineService
from data_extract.services.persistence_repository import RUNNING_STATUSES, TERMINAL_STATUSES
from data_extract.services.persistence_repository import PersistenceRepository


class JobService:
    """Orchestrate discovery, session state, and pipeline execution."""

    def __init__(
        self,
        discovery_service: Optional[FileDiscoveryService] = None,
        pipeline_service: Optional[PipelineService] = None,
        persistence_repository: Optional[PersistenceRepository] = None,
    ) -> None:
        self.discovery = discovery_service or FileDiscoveryService()
        self.pipeline = pipeline_service or PipelineService()
        self.persistence = persistence_repository or PersistenceRepository()

    def run_process(
        self,
        request: ProcessJobRequest,
        work_dir: Optional[Path] = None,
        job_id: Optional[str] = None,
        prior_retry_counts: Optional[dict[str, int]] = None,
    ) -> ProcessJobResult:
        """Execute a processing job and return structured outcome."""
        started_at = datetime.now(timezone.utc)
        resolved_files, source_dir = self._resolve_files(request)
        request_hash = self._compute_request_hash(request, resolved_files)

        idempotency_hit = self._resolve_idempotency(request, request_hash)
        if idempotency_hit is not None:
            return idempotency_hit

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
                    "idempotency_key": request.idempotency_key,
                    "request_hash": request_hash,
                },
            )
            session_state = manager._current_session
        else:
            already_processed = set()
            for entry in session_state.processed_files:
                source_key = entry.get("source_key")
                source_path = entry.get("source_path")
                path_name = entry.get("path")
                if source_key:
                    already_processed.add(str(source_key))
                if source_path:
                    already_processed.add(str(source_path))
                if path_name:
                    already_processed.add(str(path_name))

            remaining = []
            for file_path in resolved_files:
                normalized_source = normalized_path_text(file_path)
                source_key = source_key_for_path(file_path)
                if (
                    source_key in already_processed
                    or normalized_source in already_processed
                    or file_path.name in already_processed
                ):
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
            source_root=source_dir,
        )

        processed_outcomes: List[ProcessedFileOutcome] = []
        failure_outcomes: List[FileFailure] = []
        retry_counts = prior_retry_counts or {}

        if session_state:
            for processed in run.processed:
                source_key = source_key_for_path(processed.source_path)
                manager.record_processed_file(
                    file_path=processed.source_path,
                    output_path=processed.output_path,
                    file_hash="",
                    source_key=source_key,
                )
                processed_outcomes.append(
                    ProcessedFileOutcome(
                        path=str(processed.source_path),
                        output_path=str(processed.output_path),
                        chunk_count=processed.chunk_count,
                        stage_timings_ms=processed.stage_timings_ms,
                        source_key=source_key,
                    )
                )

            for failed in run.failed:
                source_path_key = normalized_path_text(failed.source_path)
                source_key = source_key_for_path(failed.source_path)
                retry_count = int(retry_counts.get(source_path_key, 0))
                manager.record_failed_file(
                    file_path=failed.source_path,
                    error_type=failed.error_type,
                    error_message=failed.error_message,
                    retry_count=retry_count,
                    source_key=source_key,
                )
                failure_outcomes.append(
                    FileFailure(
                        path=str(failed.source_path),
                        error_type=failed.error_type,
                        error_message=failed.error_message,
                        retry_count=retry_count,
                        source_key=source_key,
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
        effective_job_id = job_id or (session_state.session_id if session_state else str(uuid.uuid4())[:8])
        result = ProcessJobResult(
            job_id=effective_job_id,
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
            artifact_dir=str(output_dir),
            request_hash=request_hash,
            exit_code=exit_code,
        )

        if job_id:
            self.persistence.update_job_metadata(
                job_id=job_id,
                request_hash=request_hash,
                idempotency_key=request.idempotency_key,
                artifact_dir=str(output_dir),
                attempt=1,
            )

        if session_state:
            session_payload = manager.get_session_state()
            if session_payload:
                self.persistence.upsert_session_record(
                    session_payload,
                    artifact_dir=str(output_dir),
                    is_archived=failed_count > 0,
                    archived_at=finished_at if failed_count > 0 else None,
                )

        return result

    def _resolve_files(self, request: ProcessJobRequest) -> tuple[List[Path], Path]:
        """Resolve files to process from explicit list or path discovery."""
        if request.source_files:
            files = sorted({Path(p).resolve() for p in request.source_files}, key=lambda p: str(p))
            for file_path in files:
                if not file_path.exists():
                    raise FileNotFoundError(f"Retry source file not found: {file_path}")
            if files:
                common_root = Path(os.path.commonpath([str(f) for f in files]))
                source_dir = common_root if common_root.is_dir() else common_root.parent
            else:
                source_dir = Path(request.input_path).resolve()
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

    def _resolve_idempotency(
        self,
        request: ProcessJobRequest,
        request_hash: str,
    ) -> ProcessJobResult | None:
        """Return existing result when idempotency key already exists."""
        if not request.idempotency_key:
            return None

        existing = self.persistence.find_idempotent_job(request.idempotency_key, request_hash)
        if existing is None:
            return None

        job_id, status, payload = existing
        if status in TERMINAL_STATUSES and payload:
            try:
                result = ProcessJobResult.model_validate(payload)
                if result.request_hash != request_hash:
                    result = result.model_copy(update={"request_hash": request_hash})
                return result
            except Exception:
                pass

        if status in RUNNING_STATUSES:
            return ProcessJobResult(
                job_id=job_id,
                status=JobStatus(status),
                total_files=0,
                processed_count=0,
                failed_count=0,
                output_dir=request.output_path or "",
                artifact_dir=request.output_path,
                request_hash=request_hash,
                exit_code=0,
            )

        return None

    @staticmethod
    def _compute_request_hash(request: ProcessJobRequest, files: list[Path]) -> str:
        """Compute deterministic request hash from file set + key options."""
        payload: dict[str, Any] = {
            "files": sorted(normalized_path_text(file_path) for file_path in files),
            "options": {
                "output_format": request.output_format,
                "chunk_size": request.chunk_size,
                "recursive": request.recursive,
                "incremental": request.incremental,
                "force": request.force,
                "resume": request.resume,
                "preset": request.preset,
                "include_semantic": request.include_semantic,
                "continue_on_error": request.continue_on_error,
            },
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
