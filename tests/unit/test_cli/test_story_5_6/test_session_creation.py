"""AC-5.6-1 & AC-5.6-2: Session state creation and initialization tests.

TDD GREEN Phase Tests - These tests are designed to FAIL initially.

Focuses on SessionState dataclass creation:
- Session state creation and initialization
- Unique session ID generation
- Timestamp capture
- Empty list initialization
- Status initialization
- Configuration storage

Reference: docs/tech-spec-epic-5.md
Source module: src/data_extract/cli/session.py
"""

from __future__ import annotations

from datetime import datetime
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
# Test Session State Creation
# ==============================================================================


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.session_state
class TestSessionStateCreation:
    """Test SessionState dataclass creation and initialization."""

    @pytest.mark.test_id("5.6-UNIT-001")
    def test_session_state_creation_returns_valid_state(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify SessionManager.create_session returns a valid SessionState.

        Given: A fresh SessionManager instance
        When: create_session() is called with source directory
        Then: A SessionState object with all required fields should be returned

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager, SessionState

        work_dir = session_directory_fixture.work_dir
        source_dir = work_dir / "source"
        source_dir.mkdir()

        # Act
        manager = SessionManager(work_dir=work_dir)
        session = manager.create_session(
            source_directory=source_dir,
            output_directory=work_dir / "output",
            total_files=50,
            configuration={"format": "json", "chunk_size": 500},
        )

        # Assert
        assert isinstance(session, SessionState)
        assert session.session_id is not None
        assert session.source_directory == source_dir
        assert session.total_files == 50

    @pytest.mark.test_id("5.6-UNIT-002")
    def test_session_state_creation_generates_unique_session_id(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify each session gets a unique ID.

        Given: Multiple session creation requests
        When: create_session() is called twice
        Then: Each session should have a unique session_id

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir
        source_dir = work_dir / "source"
        source_dir.mkdir()

        # Act
        manager = SessionManager(work_dir=work_dir)
        session1 = manager.create_session(
            source_directory=source_dir,
            output_directory=work_dir / "output1",
            total_files=10,
        )
        session2 = manager.create_session(
            source_directory=source_dir,
            output_directory=work_dir / "output2",
            total_files=10,
        )

        # Assert
        assert session1.session_id != session2.session_id

    @pytest.mark.test_id("5.6-UNIT-003")
    def test_session_state_creation_sets_started_at_timestamp(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session captures start timestamp.

        Given: A session creation request
        When: create_session() is called
        Then: started_at should be set to current timestamp

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir
        source_dir = work_dir / "source"
        source_dir.mkdir()
        before_time = datetime.now()

        # Act
        manager = SessionManager(work_dir=work_dir)
        session = manager.create_session(
            source_directory=source_dir,
            output_directory=work_dir / "output",
            total_files=10,
        )
        after_time = datetime.now()

        # Assert
        assert session.started_at is not None
        assert before_time <= session.started_at <= after_time

    @pytest.mark.test_id("5.6-UNIT-004")
    def test_session_state_creation_initializes_empty_lists(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session initializes with empty processed/failed lists.

        Given: A new session
        When: create_session() is called
        Then: processed_files and failed_files should be empty lists

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

        # Assert
        assert session.processed_files == []
        assert session.failed_files == []

    @pytest.mark.test_id("5.6-UNIT-005")
    def test_session_state_creation_sets_in_progress_status(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify new session has 'in_progress' status.

        Given: A new session creation
        When: create_session() is called
        Then: status should be 'in_progress'

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

        # Assert
        assert session.status == "in_progress"

    @pytest.mark.test_id("5.6-UNIT-006")
    def test_session_state_creation_stores_configuration(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session stores CLI configuration.

        Given: Configuration dict with processing options
        When: create_session() is called
        Then: configuration should be stored in session

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir
        source_dir = work_dir / "source"
        source_dir.mkdir()
        config = {
            "format": "json",
            "chunk_size": 500,
            "quality_threshold": 0.7,
        }

        # Act
        manager = SessionManager(work_dir=work_dir)
        session = manager.create_session(
            source_directory=source_dir,
            output_directory=work_dir / "output",
            total_files=10,
            configuration=config,
        )

        # Assert
        assert session.configuration == config
        assert session.configuration["format"] == "json"
