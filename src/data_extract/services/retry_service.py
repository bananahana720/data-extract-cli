"""Retry orchestration service."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from data_extract.cli.session import ErrorCategory, SessionManager, SessionState, SessionStatistics
from data_extract.contracts import ProcessJobRequest, ProcessJobResult, RetryRequest
from data_extract.services.job_service import JobService


class RetryService:
    """Retry failed files from previous sessions."""

    def __init__(self, job_service: Optional[JobService] = None) -> None:
        self.job_service = job_service or JobService()

    def run_retry(self, request: RetryRequest, work_dir: Optional[Path] = None) -> ProcessJobResult:
        """Retry failed files based on request scope."""
        manager = SessionManager(work_dir=work_dir or Path.cwd())
        session_state = self._resolve_session(manager, request)

        if session_state is None:
            raise FileNotFoundError("No previous session found to retry")

        retryable = self._retryable_failures(session_state, max_retries=manager.max_retries)

        if request.file:
            target = Path(request.file)
            retryable = [
                failed
                for failed in retryable
                if Path(failed.get("path", "")).resolve() == target.resolve()
                or Path(failed.get("path", "")).name == target.name
            ]

        source_files = [failed["path"] for failed in retryable if failed.get("path")]
        if not source_files:
            raise FileNotFoundError("No retryable failed files found")

        process_request = ProcessJobRequest(
            input_path=str(session_state.source_directory),
            output_path=session_state.configuration.get("output_path"),
            output_format=request.output_format,
            chunk_size=request.chunk_size,
            source_files=source_files,
            continue_on_error=True,
            non_interactive=request.non_interactive,
        )

        return self.job_service.run_process(process_request, work_dir=manager.work_dir)

    def _resolve_session(self, manager: SessionManager, request: RetryRequest) -> Optional[SessionState]:
        """Resolve target session from request parameters."""
        if request.session:
            return self._load_session_anywhere(manager, request.session)

        if request.last or request.file:
            return self._latest_session(manager)

        return None

    def _latest_session(self, manager: SessionManager) -> Optional[SessionState]:
        """Return most recently updated session from disk."""
        session_files = self._all_session_files(manager)
        if not session_files:
            return None

        sessions = []
        for session_file in session_files:
            state = self._load_session_file(session_file)
            if state:
                sessions.append(state)

        if not sessions:
            return None

        return max(sessions, key=lambda s: s.updated_at)

    @staticmethod
    def _retryable_failures(session_state: SessionState, max_retries: int) -> list[dict]:
        retryable: list[dict] = []
        for failed_file in session_state.failed_files:
            if failed_file.get("category") == ErrorCategory.PERMANENT.value:
                continue
            if int(failed_file.get("retry_count", 0)) >= max_retries:
                continue
            retryable.append(failed_file)
        return retryable

    def _load_session_anywhere(self, manager: SessionManager, session_id: str) -> Optional[SessionState]:
        """Load session from active or archived location."""
        state = manager.load_session(session_id)
        if state:
            return state

        archived = manager.session_dir / "archive" / f"session-{session_id}.json"
        if archived.exists():
            return self._load_session_file(archived)
        return None

    @staticmethod
    def _all_session_files(manager: SessionManager) -> list[Path]:
        """Return active and archived session files."""
        active = list(manager.session_dir.glob("session-*.json"))
        archive_dir = manager.session_dir / "archive"
        archived = list(archive_dir.glob("session-*.json")) if archive_dir.exists() else []
        return [path for path in active + archived if path.suffix == ".json"]

    @staticmethod
    def _load_session_file(session_file: Path) -> Optional[SessionState]:
        """Deserialize session state directly from a JSON file."""
        try:
            state_dict = json.loads(session_file.read_text())
            statistics_dict = state_dict.get("statistics", {})
            return SessionState(
                session_id=state_dict["session_id"],
                status=state_dict.get("status", "in_progress"),
                source_directory=Path(state_dict["source_directory"]),
                output_directory=(
                    Path(state_dict["output_directory"])
                    if state_dict.get("output_directory")
                    else None
                ),
                total_files=statistics_dict.get("total_files", state_dict.get("total_files", 0)),
                processed_files=state_dict.get("processed_files", []),
                failed_files=state_dict.get("failed_files", []),
                started_at=datetime.fromisoformat(state_dict["started_at"]),
                updated_at=datetime.fromisoformat(state_dict["updated_at"]),
                configuration=state_dict.get("configuration", {}),
                schema_version=state_dict.get("schema_version", "1.0"),
                statistics=SessionStatistics(
                    total_files=statistics_dict.get("total_files", 0),
                    processed_count=statistics_dict.get("processed_count", 0),
                    failed_count=statistics_dict.get("failed_count", 0),
                    skipped_count=statistics_dict.get("skipped_count", 0),
                ),
            )
        except Exception:
            return None
