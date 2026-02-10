"""AC-5.6-1 & AC-5.6-2: Session lifecycle completion tests.

TDD GREEN Phase Tests - These tests are designed to FAIL initially.

Focuses on session lifecycle completion:
- Session cleanup on 100% success
- Session archival on partial success
- Failure details preservation
- Completed status setting

Reference: docs/stories/5-6-graceful-error-handling-and-recovery.md
Source module: src/data_extract/cli/session.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

# P0: Critical path - always run
pytestmark = [
    pytest.mark.P0,
    pytest.mark.session_state,
    pytest.mark.story_5_6,
    pytest.mark.unit,
    pytest.mark.cli,
]

if TYPE_CHECKING:
    from tests.unit.test_cli.test_story_5_6.conftest import (
        SessionDirectoryFixture,
    )


# ==============================================================================
# Test Session Cleanup on Success
# ==============================================================================


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.session_state
class TestSessionCleanupOnSuccess:
    """Test session cleanup when processing completes successfully."""

    @pytest.mark.test_id("5.6-UNIT-001")
    def test_session_cleanup_on_success_removes_directory(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session directory removed on 100% success.

        Given: A session completes with all files successful
        When: complete_session() is called
        Then: .data-extract-session/ should be removed

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir
        source_dir = work_dir / "source"
        source_dir.mkdir()

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.create_session(
            source_directory=source_dir,
            output_directory=work_dir / "output",
            total_files=3,
        )
        # Record all files as successful
        for i in range(3):
            manager.record_processed_file(
                file_path=Path(f"doc{i}.pdf"),
                output_path=Path(f"out/doc{i}.json"),
                file_hash=f"sha256:{i}",
            )
        manager.complete_session()

        # Assert
        session_dir = work_dir / ".data-extract-session"
        assert not session_dir.exists(), "Session directory should be removed"

    @pytest.mark.test_id("5.6-UNIT-002")
    def test_session_cleanup_on_success_preserves_archive_on_partial(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session archived when some files fail.

        Given: A session completes with some failures
        When: complete_session() is called
        Then: Session should be moved to archive/

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir
        source_dir = work_dir / "source"
        source_dir.mkdir()

        # Act
        manager = SessionManager(work_dir=work_dir)
        session = manager.create_session(
            source_directory=source_dir,
            output_directory=work_dir / "output",
            total_files=10,
        )

        # Record some success, some failure
        for i in range(8):
            manager.record_processed_file(
                file_path=Path(f"doc{i}.pdf"),
                output_path=Path(f"out/doc{i}.json"),
                file_hash=f"sha256:{i}",
            )
        manager.record_failed_file(
            file_path=Path("bad1.pdf"),
            error_type="extraction",
            error_message="Corrupted",
        )
        manager.record_failed_file(
            file_path=Path("bad2.pdf"),
            error_type="extraction",
            error_message="Corrupted",
        )

        session_id = session.session_id
        manager.complete_session()

        # Assert
        archive_dir = work_dir / ".data-extract-session" / "archive"
        archived_file = archive_dir / f"session-{session_id}.json"
        assert archived_file.exists(), "Session should be archived on partial success"


# ==============================================================================
# Test Session Archive Operations
# ==============================================================================


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.session_state
class TestSessionArchiveOnPartial:
    """Test session archival when some files fail."""

    @pytest.mark.test_id("5.6-UNIT-003")
    def test_session_archive_on_partial_preserves_failure_details(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify archived session preserves failure information.

        Given: Session with failures is archived
        When: Archive is loaded
        Then: All failure details should be present

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir
        source_dir = work_dir / "source"
        source_dir.mkdir()

        # Act
        manager = SessionManager(work_dir=work_dir)
        session = manager.create_session(
            source_directory=source_dir,
            output_directory=work_dir / "output",
            total_files=5,
        )

        manager.record_processed_file(
            file_path=Path("good.pdf"),
            output_path=Path("out/good.json"),
            file_hash="sha256:good",
        )
        manager.record_failed_file(
            file_path=Path("bad.pdf"),
            error_type="extraction",
            error_message="Specific error for testing",
        )

        session_id = session.session_id
        manager.complete_session()

        # Load from archive
        archive_dir = work_dir / ".data-extract-session" / "archive"
        archived_file = archive_dir / f"session-{session_id}.json"
        archived_state = json.loads(archived_file.read_text())

        # Assert
        assert len(archived_state["failed_files"]) == 1
        assert archived_state["failed_files"][0]["error_message"] == "Specific error for testing"

    @pytest.mark.test_id("5.6-UNIT-004")
    def test_session_archive_on_partial_sets_completed_status(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify archived session has completed status.

        Given: Session is archived
        When: Archive is read
        Then: Status should be 'completed' (not 'in_progress')

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir
        source_dir = work_dir / "source"
        source_dir.mkdir()

        # Act
        manager = SessionManager(work_dir=work_dir)
        session = manager.create_session(
            source_directory=source_dir,
            output_directory=work_dir / "output",
            total_files=2,
        )

        manager.record_processed_file(
            file_path=Path("good.pdf"),
            output_path=Path("out/good.json"),
            file_hash="sha256:good",
        )
        manager.record_failed_file(
            file_path=Path("bad.pdf"),
            error_type="extraction",
            error_message="Error",
        )

        session_id = session.session_id
        manager.complete_session()

        # Load from archive
        archive_dir = work_dir / ".data-extract-session" / "archive"
        archived_file = archive_dir / f"session-{session_id}.json"
        archived_state = json.loads(archived_file.read_text())

        # Assert
        assert archived_state["status"] == "completed"
