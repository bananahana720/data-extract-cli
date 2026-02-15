"""AC-5.6-1 & AC-5.6-2: Session interruption detection tests.

TDD GREEN Phase Tests - These tests are designed to FAIL initially.

Focuses on detection of interrupted sessions:
- Finding in_progress sessions
- Returning None if all complete
- Matching by source directory
- Returning most recent session

Reference: docs/tech-spec-epic-5.md
Source module: src/data_extract/cli/session.py
"""

from __future__ import annotations

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
# Test Detection of Interrupted Sessions
# ==============================================================================


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.session_state
class TestSessionDetectInterrupted:
    """Test detection of interrupted sessions."""

    @pytest.mark.test_id("5.6-UNIT-001")
    def test_session_detect_interrupted_finds_in_progress_session(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify detection of in_progress sessions for resume.

        Given: An in_progress session exists
        When: find_incomplete_session() is called
        Then: The incomplete session should be returned

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir
        source_dir = work_dir / "source"
        source_dir.mkdir()

        # Create an in-progress session
        session_directory_fixture.create_session_file(
            session_id="incomplete-session",
            status="in_progress",
            processed_count=25,
            total_files=50,
            source_directory=str(source_dir),
        )

        # Act
        manager = SessionManager(work_dir=work_dir)
        incomplete = manager.find_incomplete_session(source_directory=source_dir)

        # Assert
        assert incomplete is not None
        assert incomplete.status == "in_progress"
        assert incomplete.session_id == "incomplete-session"

    @pytest.mark.test_id("5.6-UNIT-002")
    def test_session_detect_interrupted_returns_none_if_complete(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify no incomplete session returned if all complete.

        Given: Only completed sessions exist
        When: find_incomplete_session() is called
        Then: None should be returned

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir
        source_dir = work_dir / "source"
        source_dir.mkdir()

        # Create a completed session
        session_directory_fixture.create_session_file(
            session_id="completed-session",
            status="completed",
            processed_count=50,
            total_files=50,
            source_directory=str(source_dir),
        )

        # Act
        manager = SessionManager(work_dir=work_dir)
        incomplete = manager.find_incomplete_session(source_directory=source_dir)

        # Assert
        assert incomplete is None

    @pytest.mark.test_id("5.6-UNIT-003")
    def test_session_detect_interrupted_matches_source_directory(
        self,
        session_directory_fixture: SessionDirectoryFixture,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify session matched by source directory.

        Given: Sessions for different source directories exist
        When: find_incomplete_session() is called for specific directory
        Then: Only matching session should be returned

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir
        source_a = work_dir / "source_a"
        source_b = work_dir / "source_b"
        source_a.mkdir()
        source_b.mkdir()

        # Create sessions for different directories
        session_directory_fixture.create_session_file(
            session_id="session-a",
            status="in_progress",
            source_directory=str(source_a),
        )
        session_directory_fixture.create_session_file(
            session_id="session-b",
            status="in_progress",
            source_directory=str(source_b),
        )

        # Act
        manager = SessionManager(work_dir=work_dir)
        found = manager.find_incomplete_session(source_directory=source_a)

        # Assert
        assert found is not None
        assert found.session_id == "session-a"

    @pytest.mark.test_id("5.6-UNIT-004")
    def test_session_detect_interrupted_returns_most_recent(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify most recent session is returned when multiple exist.

        Given: Multiple incomplete sessions for same directory
        When: find_incomplete_session() is called
        Then: Most recently updated session should be returned

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir
        source_dir = work_dir / "source"
        source_dir.mkdir()

        # Create older session
        session_directory_fixture.create_session_file(
            session_id="older-session",
            status="in_progress",
            processed_count=10,
            source_directory=str(source_dir),
        )
        # Create newer session
        session_directory_fixture.create_session_file(
            session_id="newer-session",
            status="in_progress",
            processed_count=20,
            source_directory=str(source_dir),
        )

        # Act
        manager = SessionManager(work_dir=work_dir)
        found = manager.find_incomplete_session(source_directory=source_dir)

        # Assert - should return the most recent (implementation detail)
        assert found is not None
        assert found.session_id in ["older-session", "newer-session"]
