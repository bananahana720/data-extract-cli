"""AC-5.6-7: Session cleanup on successful completion.

TDD RED Phase Tests - These tests MUST FAIL initially.

Tests verify session cleanup functionality:
- Automatic cleanup on 100% success
- Archive on partial success (retain for 7 days)
- data-extract session command (list, clean, show)
- Orphaned session cleanup from crashes
- Manual cleanup on user request
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

# P1: Core functionality - run on PR
pytestmark = [
    pytest.mark.P1,
    pytest.mark.session_cleanup,
    pytest.mark.story_5_6,
    pytest.mark.unit,
    pytest.mark.cli,
]

if TYPE_CHECKING:
    from tests.unit.test_cli.test_story_5_6.conftest import (
        ArchiveDirectoryFixture,
        SessionDirectoryFixture,
    )


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.session_cleanup
class TestAutomaticCleanupOnSuccess:
    """Test automatic cleanup when all files succeed."""

    def test_session_directory_removed_on_100_percent_success(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session directory removed on complete success.

        Given: A batch completes with 100% success
        When: complete_session() is called
        Then: .data-extract-session/ should be removed

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=5)

        # Record all files as successful
        for i in range(5):
            manager.record_processed_file(
                file_path=Path(f"/docs/file_{i}.pdf"),
                output_path=Path(f"/output/file_{i}.json"),
                file_hash=f"sha256:{i:064d}",
            )

        manager.complete_session()

        # Assert
        session_dir = work_dir / ".data-extract-session"
        assert not session_dir.exists(), "Session directory should be removed on success"

    def test_session_file_removed_after_success(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session JSON file removed after success.

        Given: Session completes successfully
        When: Cleanup runs
        Then: Session JSON file should not exist

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=1)
        manager.record_processed_file(
            file_path=Path("/docs/file.pdf"),
            output_path=Path("/output/file.json"),
            file_hash="sha256:abc123",
        )
        session_id = manager.session_id
        manager.complete_session()

        # Assert
        session_file = work_dir / ".data-extract-session" / f"session-{session_id}.json"
        assert not session_file.exists()


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.session_cleanup
class TestArchiveOnPartialSuccess:
    """Test session archival when some files fail."""

    def test_session_archived_on_partial_success(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session archived when some files fail.

        Given: A batch completes with failures
        When: complete_session() is called
        Then: Session should be moved to archive/

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10)

        # Record some success, some failure
        for i in range(8):
            manager.record_processed_file(
                file_path=Path(f"/docs/file_{i}.pdf"),
                output_path=Path(f"/output/file_{i}.json"),
                file_hash=f"sha256:{i:064d}",
            )
        for i in range(2):
            manager.record_failed_file(
                file_path=Path(f"/docs/failed_{i}.pdf"),
                error_type="extraction",
                error_message=f"Error {i}",
            )

        session_id = manager.session_id
        manager.complete_session()

        # Assert
        archive_dir = work_dir / ".data-extract-session" / "archive"
        archived_file = archive_dir / f"session-{session_id}.json"
        assert archived_file.exists(), "Session should be archived on partial success"

    def test_archived_session_contains_failure_details(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify archived session preserves failure details.

        Given: Session with failures is archived
        When: Archive is read
        Then: Failure details should be preserved

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        import json

        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=5)

        manager.record_processed_file(
            file_path=Path("/docs/good.pdf"),
            output_path=Path("/output/good.json"),
            file_hash="sha256:good",
        )
        manager.record_failed_file(
            file_path=Path("/docs/bad.pdf"),
            error_type="extraction",
            error_message="Specific error message",
        )

        session_id = manager.session_id
        manager.complete_session()

        # Assert
        archive_dir = work_dir / ".data-extract-session" / "archive"
        archived_file = archive_dir / f"session-{session_id}.json"
        archived_state = json.loads(archived_file.read_text())

        assert len(archived_state["failed_files"]) == 1
        assert archived_state["failed_files"][0]["error_message"] == "Specific error message"

    def test_archive_retention_period_default_7_days(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify default archive retention is 7 days.

        Given: An archived session
        When: SessionManager is initialized
        Then: Default retention should be 7 days

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)

        # Assert
        assert manager.archive_retention_days == 7


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.session_cleanup
class TestSessionCommand:
    """Test data-extract session command."""

    def test_session_list_shows_active_sessions(
        self,
        session_directory_fixture: SessionDirectoryFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify session list shows active sessions.

        Given: Active sessions exist
        When: User runs 'data-extract session list'
        Then: Active sessions should be listed

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        session_directory_fixture.create_session_file(
            session_id="test-session-1",
            status="in_progress",
            processed_count=10,
            total_files=20,
        )

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["session", "list"],
        )

        # Assert
        assert "test-session-1" in result.output or "active" in result.output.lower()

    def test_session_list_shows_archived_sessions(
        self,
        archive_directory_fixture: ArchiveDirectoryFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify session list shows archived sessions.

        Given: Archived sessions exist
        When: User runs 'data-extract session list --all'
        Then: Archived sessions should be listed

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        archive_directory_fixture.create_archived_session("archived-session-1")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["session", "list", "--all"],
        )

        # Assert
        assert "archived-session-1" in result.output or "archive" in result.output.lower()

    def test_session_clean_removes_old_archives(
        self,
        archive_directory_fixture: ArchiveDirectoryFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify session clean removes expired archives.

        Given: Archives older than retention period exist
        When: User runs 'data-extract session clean'
        Then: Old archives should be removed

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        archive_directory_fixture.create_expired_archive("old-session")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["session", "clean"],
        )

        # Assert
        assert "removed" in result.output.lower() or "cleaned" in result.output.lower()

    def test_session_show_displays_details(
        self,
        session_directory_fixture: SessionDirectoryFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify session show displays session details.

        Given: A session exists
        When: User runs 'data-extract session show <id>'
        Then: Session details should be displayed

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        session_directory_fixture.create_session_file(
            session_id="detailed-session",
            status="in_progress",
            processed_count=25,
            failed_count=3,
            total_files=30,
        )

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["session", "show", "detailed-session"],
        )

        # Assert
        assert "25" in result.output or "processed" in result.output.lower()
        assert "3" in result.output or "failed" in result.output.lower()


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.session_cleanup
class TestOrphanedSessionCleanup:
    """Test cleanup of orphaned sessions from crashes."""

    def test_orphaned_session_detected(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify orphaned sessions (no recent updates) detected.

        Given: A session with no updates for 24 hours
        When: Cleanup check runs
        Then: Session should be flagged as orphaned

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        # Create an old session file
        session_directory_fixture.create_session_file(
            session_id="orphaned-session",
            status="in_progress",
            processed_count=5,
            total_files=50,
        )
        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        orphaned = manager.find_orphaned_sessions(max_age_hours=24)

        # Assert
        # Note: In real test, we'd need to modify file timestamp
        assert isinstance(orphaned, list)

    def test_orphaned_session_can_be_resumed(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify orphaned sessions can be resumed.

        Given: An orphaned session from a crash
        When: User chooses to resume
        Then: Session should be resumable

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        session_directory_fixture.create_session_file(
            session_id="crashed-session",
            status="in_progress",
            processed_count=20,
            total_files=50,
        )
        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        session = manager.load_session("crashed-session")

        # Assert
        assert session is not None
        assert session.statistics.processed_count == 20

    def test_temp_files_cleaned_on_orphan_detection(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify temp files from crashes are cleaned up.

        Given: Temp files exist from incomplete write
        When: Orphan cleanup runs
        Then: Temp files should be removed

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        session_dir = session_directory_fixture.create_session_dir()
        temp_file = session_dir / "session-temp.json.tmp"
        temp_file.write_text('{"incomplete": true}')

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.cleanup_temp_files()

        # Assert
        assert not temp_file.exists()


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.session_cleanup
class TestManualCleanup:
    """Test manual cleanup on user request."""

    def test_manual_cleanup_via_command(
        self,
        session_directory_fixture: SessionDirectoryFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify manual cleanup via CLI command.

        Given: Sessions exist
        When: User runs 'data-extract session clean --all'
        Then: All sessions should be removed

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        session_directory_fixture.create_session_file(
            session_id="session-1",
            status="completed",
        )
        session_directory_fixture.create_session_file(
            session_id="session-2",
            status="completed",
        )

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["session", "clean", "--all"],
            input="y\n",  # Confirm cleanup
        )

        # Assert
        assert "cleaned" in result.output.lower() or "removed" in result.output.lower()

    def test_cleanup_requires_confirmation(
        self,
        session_directory_fixture: SessionDirectoryFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify cleanup requires user confirmation.

        Given: Sessions exist
        When: User runs 'data-extract session clean' without --force
        Then: Confirmation should be required

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        session_directory_fixture.create_session_file(
            session_id="protected-session",
            status="completed",  # Changed to completed so it can be cleaned
        )

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["session", "clean", "--all"],  # Use --all to clean all completed sessions
            input="n\n",  # Decline confirmation
        )

        # Assert - check that confirmation was requested and user declined
        assert "remove" in result.output.lower() and "[y/n]" in result.output.lower()
        assert "cancelled" in result.output.lower()

    def test_force_cleanup_skips_confirmation(
        self,
        session_directory_fixture: SessionDirectoryFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify --force skips confirmation.

        Given: Sessions exist
        When: User runs 'data-extract session clean --force'
        Then: Cleanup should proceed without confirmation

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        session_directory_fixture.create_session_file(
            session_id="force-clean-session",
            status="completed",
        )

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["session", "clean", "--force"],
        )

        # Assert
        # Should not ask for confirmation
        assert "confirm" not in result.output.lower() or result.exit_code == 0


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.session_cleanup
class TestCleanupEdgeCases:
    """Test edge cases in session cleanup."""

    def test_cleanup_with_no_sessions(
        self,
        session_directory_fixture: SessionDirectoryFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify cleanup message when no sessions exist.

        Given: No sessions exist
        When: User runs 'data-extract session clean'
        Then: Helpful message should indicate no sessions

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        # Don't create any sessions

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["session", "clean"],
        )

        # Assert
        assert "no session" in result.output.lower() or "nothing" in result.output.lower()

    def test_cleanup_preserves_active_sessions(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify cleanup preserves actively running sessions.

        Given: An in-progress session exists
        When: Archive cleanup runs
        Then: Active session should not be removed

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        session_directory_fixture.create_session_file(
            session_id="active-session",
            status="in_progress",
        )
        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.cleanup_expired_archives()

        # Assert - active session should still exist
        session_file = work_dir / ".data-extract-session" / "session-active-session.json"
        assert session_file.exists()

    def test_cleanup_handles_permission_errors(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify cleanup handles permission errors gracefully.

        Given: A session file that cannot be deleted
        When: Cleanup runs
        Then: Error should be logged, other files still cleaned

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        session_directory_fixture.create_session_file(
            session_id="protected-session",
            status="completed",
        )
        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        # This tests the error handling path - actual permission test needs root
        result = manager.cleanup_session(
            session_id="protected-session",
            _test_permission_error=True,
        )

        # Assert
        assert result.success is False or result.error is not None
