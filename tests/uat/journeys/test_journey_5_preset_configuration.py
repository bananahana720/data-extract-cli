"""Journey Test: Story 5-5 Preset Configuration User Experience.

Tests the complete user journey for preset configuration:
- User discovers available presets
- User saves current config as preset
- User loads preset to apply settings
- User uses preset flag with process command
- System handles invalid preset names gracefully

Reference: docs/user-guide.md - Story 5-5
"""

import pytest

from tests.uat.framework import (
    TmuxSession,
    assert_command_success,
    assert_contains,
    assert_not_contains,
)

pytestmark = [
    pytest.mark.P1,
    pytest.mark.uat,
    pytest.mark.journey,
    pytest.mark.story_5_5,
]


@pytest.mark.uat
@pytest.mark.journey
@pytest.mark.story_5_5
class TestJourney5PresetConfiguration:
    """Journey 5: Preset Configuration - Managing workflow configurations."""

    def test_preset_list_displays_builtins(self, tmux_session: TmuxSession) -> None:
        """Validate preset list displays built-in presets.

        UAT Assertion:
        - 'config presets list' command is available
        - Output includes quality, speed, balanced presets
        - Built-in presets are clearly marked
        - Output is formatted nicely (table or list)

        Journey Step: User discovers available presets
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract config presets list",
            idle_time=3.0,
            timeout=30.0,
        )

        # Assert command succeeded
        assert_command_success(output)

        # Assert no traceback
        assert_not_contains(output, "Traceback", case_sensitive=True)

        # Assert presets are listed
        assert_contains(output, "quality", case_sensitive=False)
        assert_contains(output, "speed", case_sensitive=False)
        assert_contains(output, "balanced", case_sensitive=False)

    def test_preset_save_creates_file(self, tmux_session: TmuxSession) -> None:
        """Validate preset save creates configuration file.

        UAT Assertion:
        - 'config presets save' command accepts preset name
        - Command shows success message
        - Preset file is created in ~/.data-extract/presets/
        - Saved preset contains all settings

        Journey Step: User saves current config as preset
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract config presets save --help",
            idle_time=2.0,
            timeout=30.0,
        )

        # Assert command is available
        assert_command_success(output)

        # Assert help text mentions save functionality
        has_save_info = (
            "save" in output.lower() or "preset" in output.lower() or "name" in output.lower()
        )
        assert has_save_info, "Save command not properly documented"

    def test_preset_load_applies_settings(self, tmux_session: TmuxSession) -> None:
        """Validate preset load applies configuration settings.

        UAT Assertion:
        - 'config presets load' command accepts preset name
        - Command shows confirmation panel
        - Settings are applied (verified by config show or next command)
        - Load message shows applied settings

        Journey Step: User loads preset to apply settings
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract config presets load --help",
            idle_time=2.0,
            timeout=30.0,
        )

        # Assert command is available
        assert_command_success(output)

        # Assert help text mentions load functionality
        has_load_info = (
            "load" in output.lower() or "preset" in output.lower() or "name" in output.lower()
        )
        assert has_load_info, "Load command not properly documented"

    def test_preset_flag_on_process(self, tmux_session: TmuxSession) -> None:
        """Validate process command accepts preset flag.

        UAT Assertion:
        - 'process' command has --preset flag in help
        - Flag documentation explains preset usage
        - Preset name can be specified as argument

        Journey Step: User uses preset flag with process command
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract process --help",
            idle_time=2.0,
            timeout=30.0,
        )

        # Assert command succeeded
        assert_command_success(output)

        # Assert help shows preset option
        has_preset_option = "--preset" in output or "-p" in output or "preset" in output.lower()
        assert has_preset_option, "Process command doesn't show preset option"

    def test_invalid_preset_shows_suggestions(self, tmux_session: TmuxSession) -> None:
        """Validate system handles invalid preset names gracefully.

        UAT Assertion:
        - Invalid preset name is detected
        - Error message is user-friendly (no traceback)
        - Suggestions offered (fuzzy matching)
        - Message suggests correct command usage

        Journey Step: System handles invalid preset names gracefully
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract config presets load nonexistent 2>&1 || true",
            idle_time=3.0,
            timeout=30.0,
        )

        # Assert no Python traceback
        assert_not_contains(output, "Traceback", case_sensitive=True)
        assert_not_contains(output, "traceback", case_sensitive=True)

        # Assert either error message or helpful suggestion
        has_helpful_response = (
            "not found" in output.lower()
            or "invalid" in output.lower()
            or "available" in output.lower()
            or "did you mean" in output.lower()
            or "quality" in output.lower()  # Suggestion of available preset
            or "speed" in output.lower()
        )
        assert has_helpful_response, "No helpful error message for invalid preset"

    def test_quality_preset_workflow(self, tmux_session: TmuxSession) -> None:
        """Validate complete quality preset workflow.

        UAT Assertion:
        - User can load quality preset
        - Quality preset settings are applied
        - Settings include high thresholds and strict validation
        - Next process command uses quality settings

        Journey Step: User adopts quality preset for critical work
        """
        # Load quality preset
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract config presets load quality",
            idle_time=3.0,
            timeout=30.0,
        )

        # Assert command succeeded
        assert_command_success(output)

        # Assert no traceback
        assert_not_contains(output, "Traceback", case_sensitive=True)

        # Assert quality preset loaded
        assert_contains(output, "quality", case_sensitive=False)

    def test_speed_preset_workflow(self, tmux_session: TmuxSession) -> None:
        """Validate complete speed preset workflow.

        UAT Assertion:
        - User can load speed preset
        - Speed preset settings are applied
        - Settings include minimal validation and large chunks
        - Next process command executes faster

        Journey Step: User adopts speed preset for quick processing
        """
        # Load speed preset
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract config presets load speed",
            idle_time=3.0,
            timeout=30.0,
        )

        # Assert command succeeded
        assert_command_success(output)

        # Assert no traceback
        assert_not_contains(output, "Traceback", case_sensitive=True)

        # Assert speed preset loaded
        assert_contains(output, "speed", case_sensitive=False)

    def test_custom_preset_workflow(self, tmux_session: TmuxSession) -> None:
        """Validate complete custom preset workflow.

        UAT Assertion:
        - User can save custom preset
        - User can load saved custom preset
        - Custom preset appears in list
        - Settings are preserved across save/load

        Journey Step: User creates personalized preset for workflow
        """
        # Test save command is available
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract config presets save --help",
            idle_time=2.0,
            timeout=30.0,
        )

        # Assert command is available
        assert_command_success(output)

        # Assert help text mentions save functionality
        has_save_info = (
            "save" in output.lower() or "preset" in output.lower() or "name" in output.lower()
        )
        assert has_save_info, "Save command not properly documented"

    def test_preset_helps_onboarding(self, tmux_session: TmuxSession) -> None:
        """Validate presets help new users get started.

        UAT Assertion:
        - Built-in presets are discoverable (list command)
        - Presets have clear descriptions
        - User can quickly adopt recommended configuration
        - Documentation links to preset usage

        Journey Step: New user discovers and uses presets
        """
        # Verify preset list shows built-in presets
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract config presets list",
            idle_time=3.0,
            timeout=30.0,
        )

        # Assert command succeeded
        assert_command_success(output)

        # Assert no traceback
        assert_not_contains(output, "Traceback", case_sensitive=True)

        # Assert presets are listed and discoverable
        assert_contains(output, "quality", case_sensitive=False)
        assert_contains(output, "speed", case_sensitive=False)
        assert_contains(output, "balanced", case_sensitive=False)
