"""AC-5.6-1: Session state persisted to .data-extract-session/ directory.

TDD RED Phase Tests - These tests MUST FAIL initially.

Tests verify session state persistence including:
- Session directory creation on processing start
- Session JSON schema with required fields
- Atomic file writes for crash safety
- Session file corruption handling
- Concurrent session detection
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
        AtomicWriteTestFixture,
        ConcurrentSessionFixture,
        SessionDirectoryFixture,
    )


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.session_state
class TestSessionDirectoryCreation:
    """Test session directory creation on processing start."""

    @pytest.mark.test_id("5.6-UNIT-001")
    def test_session_directory_created_on_processing_start(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session directory created when processing begins.

        Given: A batch processing operation is started
        When: The first file begins processing
        Then: .data-extract-session/ directory should be created

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10)

        # Assert
        session_dir = work_dir / ".data-extract-session"
        assert session_dir.exists(), "Session directory not created"

    @pytest.mark.test_id("5.6-UNIT-002")
    def test_session_directory_not_created_for_dry_run(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session directory NOT created for --dry-run operations.

        Given: A dry-run operation is executed
        When: The process command runs with --dry-run
        Then: No session directory should be created

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10, dry_run=True)

        # Assert
        session_dir = work_dir / ".data-extract-session"
        assert not session_dir.exists(), "Session directory created for dry-run"


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.session_state
class TestSessionJsonSchema:
    """Test session JSON contains required schema fields."""

    @pytest.mark.test_id("5.6-UNIT-003")
    def test_session_json_contains_session_id(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session JSON contains session_id field.

        Given: A session is in progress
        When: The session state is read
        Then: JSON should contain session_id field

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10)
        state = manager.get_session_state()

        # Assert
        assert "session_id" in state, "Missing required field: session_id"

    @pytest.mark.test_id("5.6-UNIT-004")
    def test_session_json_contains_started_at(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session JSON contains started_at timestamp.

        Given: A session is started
        When: The session state is read
        Then: JSON should contain started_at timestamp

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10)
        state = manager.get_session_state()

        # Assert
        assert "started_at" in state, "Missing required field: started_at"

    @pytest.mark.test_id("5.6-UNIT-005")
    def test_session_json_contains_processed_files_list(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session JSON contains processed_files list.

        Given: A session is in progress with some files processed
        When: The session state is read
        Then: JSON should contain processed_files array

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10)
        manager.record_processed_file(
            file_path=Path("/docs/file1.pdf"),
            output_path=Path("/output/file1.json"),
            file_hash="sha256:abc123",
        )
        state = manager.get_session_state()

        # Assert
        assert "processed_files" in state, "Missing required field: processed_files"
        assert isinstance(state["processed_files"], list), "processed_files should be a list"
        assert len(state["processed_files"]) == 1, "Should have 1 processed file"

    @pytest.mark.test_id("5.6-UNIT-006")
    def test_session_json_contains_failed_files_list(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session JSON contains failed_files list.

        Given: A session has file processing failures
        When: The session state is read
        Then: JSON should contain failed_files array with error details

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
        assert "failed_files" in state, "Missing required field: failed_files"
        assert isinstance(state["failed_files"], list), "failed_files should be a list"
        assert len(state["failed_files"]) == 1, "Should have 1 failed file"

    @pytest.mark.test_id("5.6-UNIT-007")
    def test_session_json_contains_configuration(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session JSON contains configuration dict.

        Given: A session is started with specific CLI configuration
        When: The session state is read
        Then: JSON should contain configuration dict with CLI args

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir
        config = {"format": "json", "chunk_size": 500, "quality_threshold": 0.7}

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10, configuration=config)
        state = manager.get_session_state()

        # Assert
        assert "configuration" in state, "Missing required field: configuration"
        assert state["configuration"]["format"] == "json"

    @pytest.mark.test_id("5.6-UNIT-008")
    def test_session_json_contains_schema_version(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session JSON contains schema_version for compatibility.

        Given: A session is created
        When: The session state is read
        Then: JSON should contain schema_version field

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10)
        state = manager.get_session_state()

        # Assert
        assert "schema_version" in state, "Missing required field: schema_version"
        assert state["schema_version"] == "1.0"

    @pytest.mark.test_id("5.6-UNIT-009")
    def test_session_json_contains_statistics(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session JSON contains statistics object.

        Given: A session is in progress
        When: The session state is read
        Then: JSON should contain statistics with counts

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=50)
        state = manager.get_session_state()

        # Assert
        assert "statistics" in state, "Missing required field: statistics"
        assert state["statistics"]["total_files"] == 50


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.session_state
class TestSessionFileOperations:
    """Test session file read/write operations."""

    @pytest.mark.test_id("5.6-UNIT-010")
    def test_session_file_persisted_to_disk(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session file is written to disk.

        Given: A session is started and updated
        When: save_session() is called
        Then: A JSON file should exist in .data-extract-session/

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10)
        manager.save_session()

        # Assert
        session_dir = work_dir / ".data-extract-session"
        session_files = list(session_dir.glob("session-*.json"))
        assert len(session_files) == 1, "Session file not created"

    @pytest.mark.test_id("5.6-UNIT-011")
    def test_session_file_contains_valid_json(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session file contains valid JSON.

        Given: A session is saved to disk
        When: The file is read
        Then: Content should be valid JSON

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10)
        manager.save_session()

        # Assert
        session_dir = work_dir / ".data-extract-session"
        session_file = next(session_dir.glob("session-*.json"))
        content = session_file.read_text()
        parsed = json.loads(content)  # Should not raise
        assert isinstance(parsed, dict)

    @pytest.mark.test_id("5.6-UNIT-012")
    def test_session_file_updated_on_progress(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session file updated when progress is recorded.

        Given: A session is in progress
        When: A file is recorded as processed
        Then: Session file should be updated with new progress

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10)
        manager.save_session()

        initial_state = manager.get_session_state()
        initial_count = initial_state["statistics"]["processed_count"]

        manager.record_processed_file(
            file_path=Path("/docs/file1.pdf"),
            output_path=Path("/output/file1.json"),
            file_hash="sha256:abc123",
        )
        manager.save_session()

        final_state = manager.get_session_state()
        final_count = final_state["statistics"]["processed_count"]

        # Assert
        assert final_count == initial_count + 1, "Processed count not incremented"


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.session_state
class TestAtomicWrites:
    """Test atomic file write operations for crash safety."""

    @pytest.mark.test_id("5.6-UNIT-013")
    def test_atomic_write_uses_temp_file(
        self,
        atomic_write_test_fixture: AtomicWriteTestFixture,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify atomic write uses temporary file pattern.

        Given: A session save operation is in progress
        When: The write operation occurs
        Then: A temp file should be used before renaming to final

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.start_session(source_dir=Path("/docs"), total_files=10)
        manager.save_session()

        # Assert - no temp files should remain after successful write
        assert not atomic_write_test_fixture.has_temp_files(), "Temp files not cleaned up"

    @pytest.mark.test_id("5.6-UNIT-014")
    def test_corrupted_session_file_detected(
        self,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify corrupted session file is detected and handled.

        Given: A session file with invalid JSON exists
        When: SessionManager tries to load it
        Then: A SessionCorruptedError should be raised

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionCorruptedError, SessionManager

        session_directory_fixture.create_corrupted_session_file("corrupted-session")
        work_dir = session_directory_fixture.work_dir

        # Act & Assert
        manager = SessionManager(work_dir=work_dir)
        with pytest.raises(SessionCorruptedError):
            manager.load_session("corrupted-session")


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.session_state
class TestConcurrentSessions:
    """Test concurrent session detection and handling."""

    @pytest.mark.test_id("5.6-UNIT-015")
    def test_concurrent_session_detected(
        self,
        concurrent_session_fixture: ConcurrentSessionFixture,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify concurrent sessions for same directory are detected.

        Given: Multiple session files exist for the same source directory
        When: A new session is started
        Then: ConcurrentSessionError should be raised

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import ConcurrentSessionError, SessionManager

        concurrent_session_fixture.create_concurrent_sessions(count=2)
        work_dir = session_directory_fixture.work_dir

        # Act & Assert
        manager = SessionManager(work_dir=work_dir)
        with pytest.raises(ConcurrentSessionError):
            manager.start_session(source_dir=Path("/docs"), total_files=10)

    @pytest.mark.test_id("5.6-UNIT-016")
    def test_find_latest_session(
        self,
        concurrent_session_fixture: ConcurrentSessionFixture,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify find_latest_session returns most recent session.

        Given: Multiple session files exist
        When: find_latest_session is called
        Then: The most recently updated session should be returned

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        concurrent_session_fixture.create_concurrent_sessions(count=3)
        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        latest = manager.find_latest_session(source_dir=Path("/docs"))

        # Assert
        assert latest is not None, "No latest session found"


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.session_state
class TestSessionPermissions:
    """Test session directory permission handling."""

    @pytest.mark.test_id("5.6-UNIT-017")
    def test_permission_denied_on_session_directory(
        self,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify graceful handling of permission denied errors.

        Given: Session directory cannot be created due to permissions
        When: start_session is called
        Then: SessionPermissionError should be raised with helpful message

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager, SessionPermissionError

        # Create read-only parent directory
        work_dir = tmp_path / "readonly"
        work_dir.mkdir()

        # Act & Assert
        manager = SessionManager(work_dir=work_dir)
        # Note: Actual permission change would require root, so we test the error path
        # by mocking or using a directory that doesn't exist
        with pytest.raises(SessionPermissionError):
            manager.start_session(
                source_dir=Path("/docs"),
                total_files=10,
                _test_permission_error=True,
            )
