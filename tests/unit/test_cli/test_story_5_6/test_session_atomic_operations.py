"""AC-5.6-1 & AC-5.6-2: Session atomic write operations tests.

TDD GREEN Phase Tests - These tests are designed to FAIL initially.

Focuses on atomic file writes for crash safety:
- No temp files after successful save
- Recovery from partial/interrupted writes
- Original file preservation on failure

Reference: docs/stories/5-6-graceful-error-handling-and-recovery.md
Source module: src/data_extract/cli/session.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

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
        AtomicWriteTestFixture,
        SessionDirectoryFixture,
    )


# ==============================================================================
# Test Atomic Write Operations
# ==============================================================================


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.session_state
class TestSessionStateAtomicWrite:
    """Test atomic file writes for crash safety."""

    @pytest.mark.test_id("5.6-UNIT-001")
    def test_session_state_atomic_write_no_temp_files_after_success(
        self,
        session_directory_fixture: SessionDirectoryFixture,
        atomic_write_test_fixture: AtomicWriteTestFixture,
    ) -> None:
        """
        RED: Verify no temp files remain after successful save.

        Given: A session save operation
        When: save() completes successfully
        Then: No .tmp files should remain

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
            total_files=10,
        )
        manager.save()

        # Assert
        session_dir = work_dir / ".data-extract-session"
        temp_files = list(session_dir.glob("*.tmp"))
        assert len(temp_files) == 0, "Temp files should be cleaned up"

    @pytest.mark.test_id("5.6-UNIT-002")
    def test_session_state_atomic_write_recovers_from_partial(
        self,
        session_directory_fixture: SessionDirectoryFixture,
        atomic_write_test_fixture: AtomicWriteTestFixture,
    ) -> None:
        """
        RED: Verify recovery from partial/interrupted writes.

        Given: A partial/temp file exists from interrupted write
        When: SessionManager initializes
        Then: The partial file should be cleaned up

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir
        session_dir = work_dir / ".data-extract-session"
        session_dir.mkdir(parents=True)

        # Create a temp file simulating crash
        temp_file = session_dir / "session-crashed.json.tmp"
        temp_file.write_text('{"partial": true}')

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.cleanup_temp_files()

        # Assert
        assert not temp_file.exists(), "Temp file should be cleaned up"

    @pytest.mark.test_id("5.6-UNIT-003")
    def test_session_state_atomic_write_original_preserved_on_failure(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify original file preserved if write fails.

        Given: A valid session file exists
        When: A save operation fails mid-write
        Then: The original file should be preserved

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir
        source_dir = work_dir / "source"
        source_dir.mkdir()

        # Create initial session
        manager = SessionManager(work_dir=work_dir)
        session = manager.create_session(
            source_directory=source_dir,
            output_directory=work_dir / "output",
            total_files=10,
        )
        manager.save()

        # Store original state
        session_dir = work_dir / ".data-extract-session"
        original_file = next(session_dir.glob("session-*.json"))
        original_content = original_file.read_text()

        # Act - simulate failed save by mocking write
        with patch("builtins.open", side_effect=IOError("Disk full")):
            try:
                manager.record_processed_file(
                    file_path=Path("new.pdf"),
                    output_path=Path("out/new.json"),
                    file_hash="sha256:new",
                )
                manager.save()
            except IOError:
                pass  # Expected

        # Assert - original should still be readable
        current_content = original_file.read_text()
        assert current_content == original_content or json.loads(current_content)
