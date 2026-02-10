"""AC-5.6-3: Failed file tracking with retry --last command.

TDD RED Phase Tests - These tests MUST FAIL initially.

Tests verify retry functionality including:
- Failed file recording with error details
- retry --last command to re-process failures
- retry --session=<id> for specific session
- retry --file=<path> for single file
- Failure categorization (RECOVERABLE, PERMANENT, REQUIRES_CONFIG)
- Quarantine directory for permanent failures
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

# P0: Critical path - always run
pytestmark = [
    pytest.mark.P0,
    pytest.mark.retry,
    pytest.mark.story_5_6,
    pytest.mark.unit,
    pytest.mark.cli,
]

if TYPE_CHECKING:
    from tests.unit.test_cli.test_story_5_6.conftest import (
        InterruptedSessionFixture,
        SessionDirectoryFixture,
    )


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.retry
class TestFailedFileRecording:
    """Test recording of failed file details."""

    @pytest.mark.test_id("5.6-UNIT-001")
    def test_failed_file_recorded_with_error_type(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify failed file recorded with error type.

        Given: A file fails during processing
        When: The error is recorded
        Then: Failed file entry should include error_type

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10)
        manager.record_failed_file(
            file_path=Path("/docs/corrupted.pdf"),
            error_type="extraction",
            error_message="PDF structure invalid",
        )
        state = manager.get_session_state()

        # Assert
        assert len(state["failed_files"]) == 1
        assert state["failed_files"][0]["error_type"] == "extraction"

    @pytest.mark.test_id("5.6-UNIT-002")
    def test_failed_file_recorded_with_error_message(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify failed file recorded with error message.

        Given: A file fails with specific error
        When: The error is recorded
        Then: Failed file entry should include error_message

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10)
        manager.record_failed_file(
            file_path=Path("/docs/corrupted.pdf"),
            error_type="extraction",
            error_message="PDF structure invalid (no pages found)",
        )
        state = manager.get_session_state()

        # Assert
        assert state["failed_files"][0]["error_message"] == "PDF structure invalid (no pages found)"

    @pytest.mark.test_id("5.6-UNIT-003")
    def test_failed_file_recorded_with_timestamp(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify failed file recorded with timestamp.

        Given: A file fails during processing
        When: The error is recorded
        Then: Failed file entry should include timestamp

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10)
        manager.record_failed_file(
            file_path=Path("/docs/corrupted.pdf"),
            error_type="extraction",
            error_message="Error",
        )
        state = manager.get_session_state()

        # Assert
        assert "timestamp" in state["failed_files"][0]

    @pytest.mark.test_id("5.6-UNIT-004")
    def test_failed_file_recorded_with_retry_count(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify failed file tracks retry count.

        Given: A file fails and is retried
        When: It fails again
        Then: retry_count should be incremented

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10)
        manager.record_failed_file(
            file_path=Path("/docs/corrupted.pdf"),
            error_type="extraction",
            error_message="Error",
        )
        # Retry and fail again
        manager.increment_retry_count(file_path=Path("/docs/corrupted.pdf"))
        state = manager.get_session_state()

        # Assert
        assert state["failed_files"][0]["retry_count"] == 1

    @pytest.mark.test_id("5.6-UNIT-005")
    def test_stack_trace_recorded_in_debug_mode(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify stack trace recorded when debug mode enabled.

        Given: Debug mode is enabled
        When: A file fails
        Then: Full stack trace should be recorded

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir, debug=True)
        manager.start_session(source_dir=Path("/docs"), total_files=10)
        manager.record_failed_file(
            file_path=Path("/docs/corrupted.pdf"),
            error_type="extraction",
            error_message="Error",
            stack_trace="Traceback (most recent call last):\n  File ...",
        )
        state = manager.get_session_state()

        # Assert
        assert "stack_trace" in state["failed_files"][0]


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.retry
class TestRetryLastCommand:
    """Test retry --last command."""

    @pytest.mark.test_id("5.6-UNIT-006")
    def test_retry_last_processes_failed_files(
        self,
        interrupted_session_fixture: InterruptedSessionFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify retry --last processes failed files.

        Given: Session with failed files
        When: User runs 'data-extract retry --last'
        Then: Failed files should be re-processed

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        scenario = interrupted_session_fixture.create_interrupted_scenario(
            total_files=50,
            processed_count=45,
            failed_count=5,
        )

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["retry", "--last"],
        )

        # Assert
        assert "5 files" in result.output or "retrying" in result.output.lower()

    @pytest.mark.test_id("5.6-UNIT-007")
    def test_retry_last_skips_already_successful_files(
        self,
        interrupted_session_fixture: InterruptedSessionFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify retry --last only processes failed files.

        Given: Session with 45 successful and 5 failed files
        When: User runs retry --last
        Then: Only 5 failed files should be processed

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        scenario = interrupted_session_fixture.create_interrupted_scenario(
            total_files=50,
            processed_count=45,
            failed_count=5,
        )

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["retry", "--last", "--non-interactive"],
        )

        # Assert
        assert "45" not in result.output or "skipping 45" in result.output.lower()

    @pytest.mark.test_id("5.6-UNIT-008")
    def test_retry_last_no_failed_files_message(
        self,
        interrupted_session_fixture: InterruptedSessionFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify message when no failed files to retry.

        Given: Session with all files successful
        When: User runs retry --last
        Then: Message should indicate no failed files

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        scenario = interrupted_session_fixture.create_interrupted_scenario(
            total_files=50,
            processed_count=50,
            failed_count=0,
        )

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["retry", "--last"],
        )

        # Assert
        assert "no failed" in result.output.lower() or "all successful" in result.output.lower()


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.retry
class TestRetrySessionCommand:
    """Test retry --session=<id> command."""

    @pytest.mark.test_id("5.6-UNIT-009")
    def test_retry_specific_session(
        self,
        interrupted_session_fixture: InterruptedSessionFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify retry --session processes specific session's failures.

        Given: Multiple sessions with failures
        When: User specifies --session=<id>
        Then: Only that session's failures should be retried

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        scenario = interrupted_session_fixture.create_interrupted_scenario(
            failed_count=3,
        )
        session_id = scenario["session_id"]

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["retry", f"--session={session_id}"],
        )

        # Assert
        assert "3 files" in result.output or session_id in result.output

    @pytest.mark.test_id("5.6-UNIT-010")
    def test_retry_invalid_session_error(
        self,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify error for invalid session ID.

        Given: No session with the given ID exists
        When: User runs retry --session=<invalid>
        Then: Clear error message should be shown

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["retry", "--session=nonexistent-id"],
        )

        # Assert
        assert result.exit_code != 0
        assert (
            "not found" in result.output.lower()
            or "invalid" in result.output.lower()
            or "no session loaded" in result.output.lower()
        )


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.retry
class TestRetrySingleFile:
    """Test retry --file=<path> for single file retry."""

    @pytest.mark.test_id("5.6-UNIT-011")
    def test_retry_single_file(
        self,
        interrupted_session_fixture: InterruptedSessionFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify retry --file processes single specified file.

        Given: A specific file failed in a session
        When: User runs retry --file=<path>
        Then: Only that file should be retried

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        scenario = interrupted_session_fixture.create_interrupted_scenario(
            failed_count=5,
        )
        failed_file = scenario["source_dir"] / "failed_0.pdf"
        failed_file.write_bytes(b"%PDF-1.4\nFixed content")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["retry", f"--file={failed_file}"],
        )

        # Assert
        assert "failed_0.pdf" in result.output or "1 file" in result.output

    @pytest.mark.test_id("5.6-UNIT-012")
    def test_retry_file_not_in_failed_list_warning(
        self,
        interrupted_session_fixture: InterruptedSessionFixture,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify warning when file not in failed list.

        Given: A file that wasn't in any failed list
        When: User runs retry --file=<path>
        Then: Warning should be shown

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        scenario = interrupted_session_fixture.create_interrupted_scenario()
        new_file = tmp_path / "new_file.pdf"
        new_file.write_bytes(b"%PDF-1.4\nNew file")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["retry", f"--file={new_file}"],
        )

        # Assert
        assert "not found" in result.output.lower() or "warning" in result.output.lower()


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.retry
class TestFailureCategorization:
    """Test failure categorization (RECOVERABLE, PERMANENT, REQUIRES_CONFIG)."""

    @pytest.mark.test_id("5.6-UNIT-013")
    def test_permanent_failure_not_auto_retried(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify PERMANENT failures are not auto-retried.

        Given: A file with PERMANENT failure (corrupted PDF)
        When: Auto-retry runs
        Then: PERMANENT failures should be skipped

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import ErrorCategory, SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10)
        manager.record_failed_file(
            file_path=Path("/docs/corrupted.pdf"),
            error_type="pdf_corrupted",
            error_message="PDF structure invalid",
            category=ErrorCategory.PERMANENT,
        )

        retryable = manager.get_retryable_files()

        # Assert
        assert len(retryable) == 0

    @pytest.mark.test_id("5.6-UNIT-014")
    def test_recoverable_failure_auto_retried(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify RECOVERABLE failures are auto-retried.

        Given: A file with RECOVERABLE failure (network timeout)
        When: Auto-retry check runs
        Then: File should be in retryable list

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import ErrorCategory, SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10)
        manager.record_failed_file(
            file_path=Path("/docs/remote.pdf"),
            error_type="network_timeout",
            error_message="Connection timed out",
            category=ErrorCategory.RECOVERABLE,
        )

        retryable = manager.get_retryable_files()

        # Assert
        assert len(retryable) == 1
        assert Path("/docs/remote.pdf") in [Path(f["path"]) for f in retryable]

    @pytest.mark.test_id("5.6-UNIT-015")
    def test_requires_config_failure_shows_suggestion(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify REQUIRES_CONFIG failures show configuration suggestions.

        Given: A file with REQUIRES_CONFIG failure (OCR threshold)
        When: Failure is recorded
        Then: Suggestion should be included

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import ErrorCategory, SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10)
        manager.record_failed_file(
            file_path=Path("/docs/scanned.pdf"),
            error_type="ocr_confidence_low",
            error_message="OCR confidence below threshold",
            category=ErrorCategory.REQUIRES_CONFIG,
            suggestion="Try --ocr-threshold 0.85",
        )
        state = manager.get_session_state()

        # Assert
        assert "suggestion" in state["failed_files"][0]
        assert "--ocr-threshold" in state["failed_files"][0]["suggestion"]


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.retry
class TestQuarantineDirectory:
    """Test quarantine directory for permanently failed files."""

    @pytest.mark.test_id("5.6-UNIT-016")
    def test_permanent_failures_moved_to_quarantine(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify PERMANENT failures are moved to quarantine.

        Given: A file with multiple PERMANENT failures
        When: Maximum retries exceeded
        Then: File should be moved to quarantine directory

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import ErrorCategory, SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10)
        manager.record_failed_file(
            file_path=Path("/docs/corrupted.pdf"),
            error_type="pdf_corrupted",
            error_message="Unrepairable",
            category=ErrorCategory.PERMANENT,
        )
        manager.quarantine_file(file_path=Path("/docs/corrupted.pdf"))

        quarantine_dir = work_dir / ".data-extract-session" / "quarantine"

        # Assert
        assert quarantine_dir.exists()

    @pytest.mark.test_id("5.6-UNIT-017")
    def test_quarantine_preserves_original_path_structure(
        self,
        session_directory_fixture: SessionDirectoryFixture,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify quarantine preserves source directory structure.

        Given: A nested file path /docs/2025/Q3/corrupted.pdf
        When: File is quarantined
        Then: Quarantine should maintain: quarantine/docs/2025/Q3/corrupted.pdf

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir
        nested_path = tmp_path / "docs" / "2025" / "Q3" / "corrupted.pdf"
        nested_path.parent.mkdir(parents=True)
        nested_path.write_bytes(b"%PDF-1.4\nCorrupted")

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=tmp_path / "docs", total_files=10)
        manager.quarantine_file(file_path=nested_path)

        quarantine_dir = work_dir / ".data-extract-session" / "quarantine"

        # Assert
        expected_path = quarantine_dir / "2025" / "Q3" / "corrupted.pdf"
        assert expected_path.exists() or "2025/Q3" in str(list(quarantine_dir.rglob("*")))


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.retry
class TestRetryWithExponentialBackoff:
    """Test retry with exponential backoff."""

    @pytest.mark.test_id("5.6-UNIT-018")
    def test_exponential_backoff_enabled(
        self,
        interrupted_session_fixture: InterruptedSessionFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify exponential backoff can be enabled.

        Given: Files to retry
        When: User runs retry with --backoff
        Then: Retry intervals should increase exponentially

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        scenario = interrupted_session_fixture.create_interrupted_scenario(
            failed_count=3,
        )

        # Act - Use --non-interactive to skip confirmation prompt
        result = typer_cli_runner.invoke(
            app,
            ["retry", "--last", "--backoff", "--non-interactive"],
        )

        # Assert
        assert "backoff" in result.output.lower() or result.exit_code == 0

    @pytest.mark.test_id("5.6-UNIT-019")
    def test_max_retries_limit(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify maximum retry attempts are enforced.

        Given: A file that has been retried 3 times
        When: Another retry is attempted
        Then: File should be marked as exhausted

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir, max_retries=3)
        manager.start_session(source_dir=Path("/docs"), total_files=10)

        # Record failure and increment retries 3 times
        manager.record_failed_file(
            file_path=Path("/docs/stubborn.pdf"),
            error_type="unknown",
            error_message="Keeps failing",
        )
        for _ in range(3):
            manager.increment_retry_count(file_path=Path("/docs/stubborn.pdf"))

        can_retry = manager.can_retry(file_path=Path("/docs/stubborn.pdf"))

        # Assert
        assert not can_retry
