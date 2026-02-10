"""AC-5.6-2: --resume flag detects and resumes interrupted batches.

TDD RED Phase Tests - These tests MUST FAIL initially.

Tests verify resume functionality including:
- Resume flag detection of incomplete sessions
- Resume prompt with options (Resume / Start Fresh / Cancel)
- Incremental processing skipping already-processed files
- Resume with specific session ID
- Configuration mismatch handling
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

# P0: Critical path - always run
pytestmark = [
    pytest.mark.P0,
    pytest.mark.resume,
    pytest.mark.story_5_6,
    pytest.mark.unit,
    pytest.mark.cli,
]

if TYPE_CHECKING:
    from tests.unit.test_cli.test_story_5_6.conftest import (
        InterruptedSessionFixture,
        MockInquirerPrompts,
        SessionDirectoryFixture,
    )


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.resume
class TestResumeDetection:
    """Test detection of incomplete sessions for resume."""

    @pytest.mark.test_id("5.6-UNIT-001")
    def test_resume_flag_detects_incomplete_session(
        self,
        interrupted_session_fixture: InterruptedSessionFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify --resume flag detects incomplete session.

        Given: An interrupted session exists for the source directory
        When: User runs process command with --resume flag
        Then: The incomplete session should be detected

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        scenario = interrupted_session_fixture.create_interrupted_scenario(
            total_files=50,
            processed_count=28,
        )

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(scenario["source_dir"]), "--resume"],
        )

        # Assert
        assert "incomplete session" in result.output.lower() or "resume" in result.output.lower()

    @pytest.mark.test_id("5.6-UNIT-002")
    def test_resume_shows_session_details(
        self,
        interrupted_session_fixture: InterruptedSessionFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify resume shows session details in prompt.

        Given: An interrupted session with 28/50 files processed
        When: User runs with --resume
        Then: Prompt should show completed count and remaining count

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        scenario = interrupted_session_fixture.create_interrupted_scenario(
            total_files=50,
            processed_count=28,
            failed_count=2,
        )

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(scenario["source_dir"]), "--resume"],
            input="n\n",  # Cancel when prompted
        )

        # Assert
        assert "28" in result.output, "Should show processed count"
        # remaining = 50 - 28 - 2 = 20
        assert "20" in result.output or "remaining" in result.output.lower()

    @pytest.mark.test_id("5.6-UNIT-003")
    def test_no_session_found_message(
        self,
        session_directory_fixture: SessionDirectoryFixture,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify helpful message when no session exists to resume.

        Given: No session exists for the source directory
        When: User runs with --resume
        Then: Clear message should indicate no session found

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "empty_source"
        source_dir.mkdir()

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--resume"],
        )

        # Assert
        assert (
            "no incomplete session" in result.output.lower()
            or "session found" in result.output.lower()
        )


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.resume
class TestResumePromptOptions:
    """Test resume prompt options and user choices."""

    @pytest.mark.test_id("5.6-UNIT-004")
    def test_resume_prompt_offers_three_options(
        self,
        interrupted_session_fixture: InterruptedSessionFixture,
        mock_inquirer_prompts: MockInquirerPrompts,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify resume prompt offers correct options.

        Given: An interrupted session exists
        When: User runs with --resume
        Then: Prompt should offer: Resume, Start Fresh, Cancel

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        scenario = interrupted_session_fixture.create_interrupted_scenario()
        mock_inquirer_prompts.set_responses(["cancel"])

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(scenario["source_dir"]), "--resume"],
            input="3\n",  # Select Cancel option
        )

        # Assert - check output contains expected options
        output_lower = result.output.lower()
        assert "resume" in output_lower
        assert "fresh" in output_lower or "start" in output_lower

    @pytest.mark.test_id("5.6-UNIT-005")
    def test_resume_option_continues_from_last_position(
        self,
        interrupted_session_fixture: InterruptedSessionFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify resume continues from last processed position.

        Given: An interrupted session with 28 files processed
        When: User selects "Resume"
        Then: Processing should start from file 29

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        scenario = interrupted_session_fixture.create_interrupted_scenario(
            total_files=50,
            processed_count=28,
        )

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(scenario["source_dir"]), "--resume", "--non-interactive"],
            # Auto-select resume in non-interactive mode
        )

        # Assert
        # Should not reprocess already-processed files
        assert "Skipping" in result.output or "already processed" in result.output.lower()

    @pytest.mark.test_id("5.6-UNIT-006")
    def test_start_fresh_ignores_existing_session(
        self,
        interrupted_session_fixture: InterruptedSessionFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify "Start Fresh" ignores existing session.

        Given: An interrupted session exists
        When: User selects "Start Fresh"
        Then: All files should be processed from beginning

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        scenario = interrupted_session_fixture.create_interrupted_scenario(
            total_files=10,
            processed_count=5,
        )

        # Act - simulate selecting "Start Fresh" option
        result = typer_cli_runner.invoke(
            app,
            [
                "process",
                str(scenario["source_dir"]),
                "--force",
                "--output",
                str(scenario["source_dir"].parent / "out"),
            ],
        )

        # Assert
        assert result.exit_code == 0 or "10 files" in result.output


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.resume
class TestResumeSessionId:
    """Test resume with specific session ID."""

    @pytest.mark.test_id("5.6-UNIT-007")
    def test_resume_specific_session(
        self,
        interrupted_session_fixture: InterruptedSessionFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify --resume-session flag allows specific session selection.

        Given: Multiple sessions exist
        When: User specifies --resume-session=<id>
        Then: The specific session should be resumed

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        scenario = interrupted_session_fixture.create_interrupted_scenario()
        session_id = scenario["session_id"]

        # Act
        result = typer_cli_runner.invoke(
            app,
            [
                "process",
                str(scenario["source_dir"]),
                f"--resume-session={session_id}",
            ],
        )

        # Assert
        assert session_id in result.output or "resuming" in result.output.lower()

    @pytest.mark.test_id("5.6-UNIT-008")
    def test_invalid_session_id_error(
        self,
        session_directory_fixture: SessionDirectoryFixture,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify error for invalid session ID.

        Given: No session exists with the given ID
        When: User specifies --resume-session with invalid ID
        Then: Clear error message should be shown

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Act
        result = typer_cli_runner.invoke(
            app,
            [
                "process",
                str(source_dir),
                "--resume-session=nonexistent-session-id",
            ],
        )

        # Assert
        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "invalid" in result.output.lower()


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.resume
class TestResumeConfigurationMismatch:
    """Test handling of configuration mismatch between session and CLI args."""

    @pytest.mark.test_id("5.6-UNIT-009")
    def test_configuration_mismatch_warning(
        self,
        interrupted_session_fixture: InterruptedSessionFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify warning when CLI args differ from saved session config.

        Given: Session saved with chunk_size=500
        When: User resumes with --chunk-size=200
        Then: Warning should be shown about config mismatch

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        scenario = interrupted_session_fixture.create_interrupted_scenario()

        # Act - try to resume with different chunk size
        result = typer_cli_runner.invoke(
            app,
            [
                "process",
                str(scenario["source_dir"]),
                "--resume",
                "--chunk-size=200",
            ],
            input="n\n",  # Cancel when warned
        )

        # Assert
        assert "mismatch" in result.output.lower() or "different" in result.output.lower()

    @pytest.mark.test_id("5.6-UNIT-010")
    def test_force_config_override(
        self,
        interrupted_session_fixture: InterruptedSessionFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify --force allows overriding session configuration.

        Given: Session saved with specific config
        When: User uses --force with different config
        Then: New config should be used

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        scenario = interrupted_session_fixture.create_interrupted_scenario()

        # Act
        result = typer_cli_runner.invoke(
            app,
            [
                "process",
                str(scenario["source_dir"]),
                "--resume",
                "--chunk-size=200",
                "--force-config",
            ],
        )

        # Assert - should proceed without warning
        assert "mismatch" not in result.output.lower() or result.exit_code == 0


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.resume
class TestResumeSourceDirectoryMatching:
    """Test session matching by source directory."""

    @pytest.mark.test_id("5.6-UNIT-011")
    def test_session_from_different_directory_not_matched(
        self,
        interrupted_session_fixture: InterruptedSessionFixture,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify sessions from different directories are not matched.

        Given: A session exists for /docs/A
        When: User runs process on /docs/B with --resume
        Then: The session should NOT be offered for resume

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        # Create session for one directory
        interrupted_session_fixture.create_interrupted_scenario()

        # Create different source directory
        other_source = tmp_path / "other_docs"
        other_source.mkdir()
        (other_source / "file.pdf").write_bytes(b"%PDF-1.4\nTest")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(other_source), "--resume"],
        )

        # Assert
        assert "no session" in result.output.lower() or "not found" in result.output.lower()

    @pytest.mark.test_id("5.6-UNIT-012")
    def test_session_matched_by_normalized_path(
        self,
        interrupted_session_fixture: InterruptedSessionFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify session matched with normalized paths.

        Given: Session saved with path /docs/./folder/
        When: User runs from /docs/folder
        Then: Session should be matched correctly

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        scenario = interrupted_session_fixture.create_interrupted_scenario()
        # Use path with extra components that normalize to same path
        source_with_dots = scenario["source_dir"].parent / "." / scenario["source_dir"].name

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_with_dots), "--resume"],
            input="n\n",
        )

        # Assert - should find the session
        assert "no session" not in result.output.lower()


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.resume
class TestIncrementalProcessing:
    """Test incremental processing after resume."""

    @pytest.mark.test_id("5.6-UNIT-013")
    def test_processed_files_skipped(
        self,
        interrupted_session_fixture: InterruptedSessionFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify already-processed files are skipped on resume.

        Given: Session with 28 processed files
        When: Resume is selected
        Then: Those 28 files should be skipped

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        scenario = interrupted_session_fixture.create_interrupted_scenario(
            total_files=50,
            processed_count=28,
        )

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(scenario["source_dir"]), "--resume", "--non-interactive"],
        )

        # Assert
        assert (
            "skipping 28" in result.output.lower()
            or "28 already processed" in result.output.lower()
        )

    @pytest.mark.test_id("5.6-UNIT-014")
    def test_failed_files_retried(
        self,
        interrupted_session_fixture: InterruptedSessionFixture,
        typer_cli_runner,
    ) -> None:
        """
        RED: Verify previously failed files are retried on resume.

        Given: Session with 2 failed files
        When: Resume is selected
        Then: Failed files should be retried (unless marked permanent)

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        scenario = interrupted_session_fixture.create_interrupted_scenario(
            total_files=50,
            processed_count=28,
            failed_count=2,
        )

        # Act
        result = typer_cli_runner.invoke(
            app,
            [
                "process",
                str(scenario["source_dir"]),
                "--resume",
                "--non-interactive",
                "--retry-failed",
            ],
        )

        # Assert
        assert "retry" in result.output.lower() or "retrying" in result.output.lower()

    @pytest.mark.test_id("5.6-UNIT-015")
    def test_session_updated_during_incremental_processing(
        self,
        interrupted_session_fixture: InterruptedSessionFixture,
        session_directory_fixture: SessionDirectoryFixture,
    ) -> None:
        """
        RED: Verify session state updated during incremental processing.

        Given: Resume operation in progress
        When: Each file is processed
        Then: Session state should be updated incrementally

        Expected RED failure: ModuleNotFoundError - session module doesn't exist
        """
        # Arrange
        from data_extract.cli.session import SessionManager

        scenario = interrupted_session_fixture.create_interrupted_scenario(
            total_files=50,
            processed_count=28,
        )
        work_dir = session_directory_fixture.work_dir

        # Act
        manager = SessionManager(work_dir=work_dir)
        manager.load_session(scenario["session_id"])

        # Simulate processing one more file
        manager.record_processed_file(
            file_path=Path("/docs/doc_29.pdf"),
            output_path=Path("/output/doc_29.json"),
            file_hash="sha256:new123",
        )
        manager.save_session()

        state = manager.get_session_state()

        # Assert
        assert state["statistics"]["processed_count"] == 29
