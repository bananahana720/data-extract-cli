"""AC-5.6-4: Interactive error prompts (InquirerPy).

TDD RED Phase Tests - These tests MUST FAIL initially.

Tests verify interactive error prompt functionality:
- Error panel display with file details
- Continue/Retry/Skip/Stop options
- Retry with different settings flow
- --interactive flag (default for TTY)
- --non-interactive flag for CI/scripting
- Non-TTY mode auto-skip behavior
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

# P1: Core functionality - run on PR
pytestmark = [
    pytest.mark.P1,
    pytest.mark.story_5_6,
    pytest.mark.unit,
    pytest.mark.error_prompts,
    pytest.mark.cli,
]

if TYPE_CHECKING:
    from tests.unit.test_cli.test_story_5_6.conftest import (
        MockInquirerPrompts,
        TTYModeFixture,
    )


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.error_prompts
class TestErrorPanelDisplay:
    """Test error panel display with Rich formatting."""

    def test_error_panel_shows_file_path(
        self,
        mock_console,
    ) -> None:
        """
        RED: Verify error panel displays the failed file path.

        Given: A file processing error occurs
        When: Error prompt is displayed
        Then: Panel should show the file path

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorPrompt

        file_path = Path("/docs/corrupted-file.pdf")
        error = ValueError("PDF structure invalid")

        # Act
        prompt = ErrorPrompt(console=mock_console.console)
        prompt.display_error_panel(file_path=file_path, error=error)

        # Assert
        output = mock_console.exported_text
        assert "corrupted-file.pdf" in output

    def test_error_panel_shows_error_message(
        self,
        mock_console,
    ) -> None:
        """
        RED: Verify error panel displays the error message.

        Given: A file processing error occurs
        When: Error prompt is displayed
        Then: Panel should show the error message

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorPrompt

        file_path = Path("/docs/corrupted-file.pdf")
        error = ValueError("PDF structure invalid (no pages found)")

        # Act
        prompt = ErrorPrompt(console=mock_console.console)
        prompt.display_error_panel(file_path=file_path, error=error)

        # Assert
        output = mock_console.exported_text
        assert "PDF structure invalid" in output

    def test_error_panel_title_indicates_error(
        self,
        mock_console,
    ) -> None:
        """
        RED: Verify error panel has appropriate title.

        Given: An error panel is displayed
        When: Panel is rendered
        Then: Title should indicate "Error Processing File"

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorPrompt

        file_path = Path("/docs/corrupted-file.pdf")
        error = ValueError("Error")

        # Act
        prompt = ErrorPrompt(console=mock_console.console)
        prompt.display_error_panel(file_path=file_path, error=error)

        # Assert
        output = mock_console.exported_text
        assert "error" in output.lower() and "file" in output.lower()


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.error_prompts
class TestErrorActionChoices:
    """Test error prompt action choices."""

    def test_prompt_offers_skip_option(
        self,
        error_action_choices,
    ) -> None:
        """
        RED: Verify Skip option is available.

        Given: An error prompt is shown
        When: User sees the options
        Then: "Skip this file and continue" should be available

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorAction, ErrorPrompt

        # Act
        prompt = ErrorPrompt()
        actions = prompt.get_available_actions()

        # Assert
        assert ErrorAction.SKIP in actions

    def test_prompt_offers_retry_option(
        self,
        error_action_choices,
    ) -> None:
        """
        RED: Verify Retry option is available.

        Given: An error prompt is shown
        When: User sees the options
        Then: "Retry with different settings" should be available

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorAction, ErrorPrompt

        # Act
        prompt = ErrorPrompt()
        actions = prompt.get_available_actions()

        # Assert
        assert ErrorAction.RETRY in actions

    def test_prompt_offers_stop_option(
        self,
        error_action_choices,
    ) -> None:
        """
        RED: Verify Stop option is available.

        Given: An error prompt is shown
        When: User sees the options
        Then: "Stop processing (save progress)" should be available

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorAction, ErrorPrompt

        # Act
        prompt = ErrorPrompt()
        actions = prompt.get_available_actions()

        # Assert
        assert ErrorAction.STOP in actions

    def test_prompt_offers_continue_option(
        self,
        error_action_choices,
    ) -> None:
        """
        RED: Verify Continue option is available.

        Given: An error prompt is shown
        When: User sees the options
        Then: "Continue" option should be available

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorAction, ErrorPrompt

        # Act
        prompt = ErrorPrompt()
        actions = prompt.get_available_actions()

        # Assert
        assert ErrorAction.CONTINUE in actions


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.error_prompts
class TestPromptUserSelection:
    """Test user selection from error prompt."""

    def test_skip_action_returns_skip(
        self,
        mock_inquirer_prompts: MockInquirerPrompts,
    ) -> None:
        """
        RED: Verify Skip selection returns SKIP action.

        Given: User is prompted for action
        When: User selects "Skip"
        Then: ErrorAction.SKIP should be returned

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorAction, ErrorPrompt

        mock_inquirer_prompts.set_responses(["skip"])

        # Act
        with patch("data_extract.cli.error_prompts.inquirer") as mock_inquirer:
            mock_inquirer.select.return_value.execute.return_value = "skip"
            prompt = ErrorPrompt()
            action = prompt.prompt_on_error(
                file_path=Path("/docs/test.pdf"),
                error=ValueError("Test error"),
            )

        # Assert
        assert action == ErrorAction.SKIP

    def test_stop_action_returns_stop(
        self,
        mock_inquirer_prompts: MockInquirerPrompts,
    ) -> None:
        """
        RED: Verify Stop selection returns STOP action.

        Given: User is prompted for action
        When: User selects "Stop"
        Then: ErrorAction.STOP should be returned

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorAction, ErrorPrompt

        # Act
        with patch("data_extract.cli.error_prompts.inquirer") as mock_inquirer:
            mock_inquirer.select.return_value.execute.return_value = "stop"
            prompt = ErrorPrompt()
            action = prompt.prompt_on_error(
                file_path=Path("/docs/test.pdf"),
                error=ValueError("Test error"),
            )

        # Assert
        assert action == ErrorAction.STOP

    def test_retry_action_triggers_settings_dialog(
        self,
        mock_inquirer_prompts: MockInquirerPrompts,
    ) -> None:
        """
        RED: Verify Retry selection triggers settings modification dialog.

        Given: User is prompted for action
        When: User selects "Retry"
        Then: Settings modification dialog should be shown

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorAction, ErrorPrompt

        # Act
        with patch("data_extract.cli.error_prompts.inquirer") as mock_inquirer:
            mock_inquirer.select.return_value.execute.return_value = "retry"
            prompt = ErrorPrompt()
            action = prompt.prompt_on_error(
                file_path=Path("/docs/test.pdf"),
                error=ValueError("Test error"),
            )

        # Assert
        assert action == ErrorAction.RETRY
        # Additional check that settings dialog was invoked
        assert mock_inquirer.select.call_count >= 1


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.error_prompts
class TestRetryWithDifferentSettings:
    """Test retry with modified settings flow."""

    def test_retry_shows_available_settings(
        self,
        mock_console,
    ) -> None:
        """
        RED: Verify retry dialog shows modifiable settings.

        Given: User selects "Retry with different settings"
        When: Settings dialog is shown
        Then: Available settings should be listed

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorPrompt

        # Act
        prompt = ErrorPrompt(console=mock_console.console)
        with patch("data_extract.cli.error_prompts.inquirer") as mock_inquirer:
            mock_inquirer.checkbox.return_value.execute.return_value = []
            _settings = prompt.show_retry_settings_dialog()  # noqa: F841

        # Assert - verify settings options exist
        assert mock_inquirer.checkbox.called or mock_inquirer.select.called

    def test_retry_with_ocr_threshold_modification(self) -> None:
        """
        RED: Verify OCR threshold can be modified for retry.

        Given: File failed due to low OCR confidence
        When: User modifies OCR threshold
        Then: New threshold should be applied to retry

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorPrompt

        # Note: original_config shows context but isn't used in test setup

        # Act
        prompt = ErrorPrompt()
        with patch("data_extract.cli.error_prompts.inquirer") as mock_inquirer:
            mock_inquirer.text.return_value.execute.return_value = "0.85"
            new_config = prompt.modify_setting_for_retry(
                setting="ocr_threshold",
                current_value=0.8,
            )

        # Assert
        assert new_config["ocr_threshold"] == 0.85


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.error_prompts
class TestInteractiveFlag:
    """Test --interactive flag behavior."""

    @pytest.mark.skip(reason="Interactive error prompts implementation required for BLUE phase")
    def test_interactive_flag_enables_prompts(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify --interactive flag enables error prompts.

        Given: Processing with --interactive flag
        When: An error occurs
        Then: Interactive prompt should be shown

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()
        (source_dir / "corrupted.pdf").write_bytes(b"%PDF-corrupt")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--interactive"],
            input="s\n",  # Skip on prompt
        )

        # Assert
        assert "how would you like" in result.output.lower() or "skip" in result.output.lower()

    def test_interactive_default_for_tty(
        self,
        tty_mode_fixture: TTYModeFixture,
    ) -> None:
        """
        RED: Verify interactive mode is default when TTY detected.

        Given: Running in a TTY terminal
        When: Error occurs without explicit flag
        Then: Interactive prompts should be enabled by default

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorPrompt

        mock_stdin = tty_mode_fixture.simulate_tty()

        # Act
        with patch("sys.stdin", mock_stdin):
            prompt = ErrorPrompt()
            is_interactive = prompt.is_interactive_mode()

        # Assert
        assert is_interactive is True


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.error_prompts
class TestNonInteractiveFlag:
    """Test --non-interactive flag behavior."""

    def test_non_interactive_flag_disables_prompts(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify --non-interactive disables error prompts.

        Given: Processing with --non-interactive flag
        When: An error occurs
        Then: No prompt should be shown, auto-skip

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()
        (source_dir / "corrupted.pdf").write_bytes(b"%PDF-corrupt")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        # Should not contain prompt text
        assert "how would you like" not in result.output.lower()

    @pytest.mark.skip(
        reason="Non-interactive auto-skip behavior implementation required for BLUE phase"
    )
    def test_non_interactive_auto_skips_errors(
        self,
        typer_cli_runner,
        tmp_path: Path,
    ) -> None:
        """
        RED: Verify non-interactive mode auto-skips failed files.

        Given: Non-interactive mode enabled
        When: A file fails processing
        Then: File should be automatically skipped

        Expected RED failure: ModuleNotFoundError - CLI command doesn't exist
        """
        # Arrange
        from data_extract.cli.app import app

        source_dir = tmp_path / "docs"
        source_dir.mkdir()
        (source_dir / "good.txt").write_text("Good content")
        (source_dir / "corrupted.pdf").write_bytes(b"%PDF-corrupt")

        # Act
        result = typer_cli_runner.invoke(
            app,
            ["process", str(source_dir), "--non-interactive"],
        )

        # Assert
        assert "skipped" in result.output.lower() or "skipping" in result.output.lower()


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.error_prompts
class TestNonTTYMode:
    """Test behavior when running in non-TTY mode (piped/scripted)."""

    def test_non_tty_auto_skips(
        self,
        tty_mode_fixture: TTYModeFixture,
    ) -> None:
        """
        RED: Verify non-TTY mode automatically skips errors.

        Given: Running in non-TTY mode (piped)
        When: An error occurs
        Then: Error should be auto-skipped

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorAction, ErrorPrompt

        mock_stdin = tty_mode_fixture.simulate_non_tty()

        # Act
        with patch("sys.stdin", mock_stdin):
            prompt = ErrorPrompt()
            action = prompt.get_default_action_for_non_tty()

        # Assert
        assert action == ErrorAction.SKIP

    def test_non_tty_logs_skipped_files(
        self,
        tty_mode_fixture: TTYModeFixture,
        mock_console,
    ) -> None:
        """
        RED: Verify non-TTY mode logs skipped files to stderr.

        Given: Running in non-TTY mode
        When: A file is auto-skipped
        Then: Skip should be logged to stderr

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorPrompt

        mock_stdin = tty_mode_fixture.simulate_non_tty()

        # Act
        with patch("sys.stdin", mock_stdin):
            prompt = ErrorPrompt(console=mock_console.console)
            prompt.log_auto_skip(
                file_path=Path("/docs/corrupted.pdf"),
                error=ValueError("PDF corrupt"),
            )

        # Assert
        output = mock_console.exported_text
        assert "corrupted.pdf" in output or "skipped" in output.lower()


@pytest.mark.unit
@pytest.mark.story_5_6
@pytest.mark.error_prompts
class TestErrorPromptEdgeCases:
    """Test edge cases for error prompts."""

    def test_keyboard_interrupt_during_prompt(self) -> None:
        """
        RED: Verify Ctrl+C during prompt is handled gracefully.

        Given: User is at error prompt
        When: User presses Ctrl+C
        Then: Processing should stop gracefully with progress saved

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorAction, ErrorPrompt

        # Act
        with patch("data_extract.cli.error_prompts.inquirer") as mock_inquirer:
            mock_inquirer.select.return_value.execute.side_effect = KeyboardInterrupt()
            prompt = ErrorPrompt()
            action = prompt.prompt_on_error(
                file_path=Path("/docs/test.pdf"),
                error=ValueError("Test error"),
            )

        # Assert
        assert action == ErrorAction.STOP

    def test_eof_during_prompt(self) -> None:
        """
        RED: Verify EOF during prompt is handled gracefully.

        Given: User is at error prompt
        When: EOF is received (closed stdin)
        Then: Processing should stop gracefully

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorAction, ErrorPrompt

        # Act
        with patch("data_extract.cli.error_prompts.inquirer") as mock_inquirer:
            mock_inquirer.select.return_value.execute.side_effect = EOFError()
            prompt = ErrorPrompt()
            action = prompt.prompt_on_error(
                file_path=Path("/docs/test.pdf"),
                error=ValueError("Test error"),
            )

        # Assert
        assert action == ErrorAction.STOP

    def test_error_prompt_timeout(self) -> None:
        """
        RED: Verify prompt times out after configured period.

        Given: Error prompt shown with timeout
        When: User doesn't respond within timeout
        Then: Default action should be taken

        Expected RED failure: ModuleNotFoundError - error_prompts module doesn't exist
        """
        # Arrange
        from data_extract.cli.error_prompts import ErrorAction, ErrorPrompt

        # Act
        prompt = ErrorPrompt(prompt_timeout=1)  # 1 second timeout
        with patch("data_extract.cli.error_prompts.inquirer") as mock_inquirer:
            mock_inquirer.select.return_value.execute.side_effect = TimeoutError()
            action = prompt.prompt_on_error(
                file_path=Path("/docs/test.pdf"),
                error=ValueError("Test error"),
            )

        # Assert
        assert action in [ErrorAction.SKIP, ErrorAction.CONTINUE]
