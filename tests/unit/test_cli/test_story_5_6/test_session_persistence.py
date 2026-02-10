"""AC-5.6-1 & AC-5.6-2: Session state persistence tests.

TDD GREEN Phase Tests - These tests are designed to FAIL initially.

Focuses on session state save/load operations:
- JSON file creation
- Valid JSON structure
- Load from disk
- Update on progress
- Schema version compatibility

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
# Test Session State Persistence
# ==============================================================================


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.session_state
class TestSessionStatePersistence:
    """Test session state persistence to disk."""

    @pytest.mark.test_id("5.6-UNIT-001")
    def test_session_state_persistence_creates_json_file(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session state is persisted to JSON file.

        Given: A session is created
        When: save() is called
        Then: A JSON file should exist in .data-extract-session/

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
        manager.save()

        # Assert
        session_dir = work_dir / ".data-extract-session"
        session_files = list(session_dir.glob("session-*.json"))
        assert len(session_files) >= 1

    @pytest.mark.test_id("5.6-UNIT-002")
    def test_session_state_persistence_writes_valid_json(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify persisted file contains valid JSON.

        Given: A session is saved
        When: The session file is read
        Then: Content should be parseable as JSON

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
        manager.save()

        # Assert
        session_dir = work_dir / ".data-extract-session"
        session_file = next(session_dir.glob("session-*.json"))
        content = session_file.read_text()
        parsed = json.loads(content)  # Should not raise
        assert isinstance(parsed, dict)
        assert "session_id" in parsed

    @pytest.mark.test_id("5.6-UNIT-003")
    def test_session_state_persistence_loads_correctly(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session can be loaded from disk.

        Given: A session is saved to disk
        When: load_session() is called with the session_id
        Then: Session should be restored with all fields

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir
        source_dir = work_dir / "source"
        source_dir.mkdir()

        # Create and save a session
        manager = SessionManager(work_dir=work_dir)
        session = manager.create_session(
            source_directory=source_dir,
            output_directory=work_dir / "output",
            total_files=50,
            configuration={"format": "json"},
        )
        session_id = session.session_id
        manager.save()

        # Act - create new manager and load
        new_manager = SessionManager(work_dir=work_dir)
        loaded_session = new_manager.load_session(session_id)

        # Assert
        assert loaded_session is not None
        assert loaded_session.session_id == session_id
        assert loaded_session.total_files == 50
        assert loaded_session.configuration["format"] == "json"

    @pytest.mark.test_id("5.6-UNIT-004")
    def test_session_state_persistence_updates_on_progress(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session file updates when progress is recorded.

        Given: A session with some processed files
        When: A new file is processed and saved
        Then: The session file should reflect the update

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
        manager.save()

        # Record progress
        manager.record_processed_file(
            file_path=Path("doc1.pdf"),
            output_path=Path("out/doc1.json"),
            file_hash="sha256:abc123",
        )
        manager.save()

        # Reload and verify
        session_id = session.session_id
        new_manager = SessionManager(work_dir=work_dir)
        loaded = new_manager.load_session(session_id)

        # Assert
        assert len(loaded.processed_files) == 1
        assert loaded.processed_files[0]["path"] == "doc1.pdf"

    @pytest.mark.test_id("5.6-UNIT-005")
    def test_session_state_persistence_includes_schema_version(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session file includes schema_version for compatibility.

        Given: A session is saved
        When: The JSON is read
        Then: schema_version field should be present

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
        session_file = next(session_dir.glob("session-*.json"))
        parsed = json.loads(session_file.read_text())
        assert "schema_version" in parsed
        assert parsed["schema_version"] == "1.0"
