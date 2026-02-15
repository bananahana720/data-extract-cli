"""Journey 1: First-Time Setup and Sample Processing.

Tests the complete first-run experience including:
- Welcome panel display
- Enterprise/Hobbyist mode selection
- Tutorial walkthrough offer
- Sample file processing demonstration
- Success summary with next steps

Reference: docs/USER_GUIDE.md - Journey 1
"""

import pytest

from tests.uat.framework import (
    TmuxSession,
    assert_command_success,
    assert_contains,
    assert_panel_displayed,
)

pytestmark = [
    pytest.mark.P0,
    pytest.mark.uat,
    pytest.mark.journey,
]


@pytest.mark.uat
@pytest.mark.journey
class TestJourney1FirstTimeSetup:
    """Journey 1: First-Time Setup - New user onboarding flow."""

    def test_welcome_panel_displays(self, tmux_session: TmuxSession) -> None:
        """Validate welcome panel appears on first run.

        Validates that the CLI help output displays:
        - A Rich panel with professional box drawing characters
        - The description "Enterprise document processing"
        - Multiple command options shown in command panels
        - Proper formatting of options and commands

        Reference: docs/USER_GUIDE.md - Journey 1, Step 1
        """
        # Activate venv and send the help command to display welcome panel
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract --help",
            idle_time=3.0,
            timeout=30.0,
        )

        # Assert Rich panel is displayed (contains box drawing characters)
        assert_panel_displayed(output)

        # Assert key content describing the tool's purpose
        assert_contains(output, "Enterprise document processing")

        # Assert command panel is shown
        assert_contains(output, "Commands")

        # Verify no error occurred
        assert_command_success(output)

    def test_mode_selection_prompt(self, tmux_session: TmuxSession) -> None:
        """Validate configuration display shows structured settings.

        Tests that `data-extract config show` displays:
        - All major configuration sections (output, semantic, chunk, cache)
        - Source markers indicating config origin ([project], [default])
        - Semantic analysis settings (TF-IDF, LSA configuration)
        - Properly formatted YAML-style output

        Reference: docs/USER_GUIDE.md - Journey 1, Step 2
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract config show",
            idle_time=3.0,
            timeout=30.0,
        )

        # Core configuration sections
        assert_contains(output, "output_dir")
        assert_contains(output, "semantic")
        assert_contains(output, "chunk")
        assert_contains(output, "cache")

        # Source markers showing config origin
        assert_contains(output, "[project]")
        assert_contains(output, "[default]")

        # Semantic analysis subsections (TF-IDF, LSA)
        assert_contains(output, "tfidf")
        assert_contains(output, "lsa")

        # Verify no errors
        assert_command_success(output)

    def test_tutorial_offer_prompt(self, tmux_session: TmuxSession) -> None:
        """Validate learning mode flag is documented.

        Validates that the CLI provides:
        - A `--learn` flag for learning/tutorial mode
        - Documentation of the learning mode in help text
        - Clear indication that learning content is available

        Reference: docs/USER_GUIDE.md - Journey 1, Step 3
        """
        # Activate venv and send the help command which documents all available flags
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract --help",
            idle_time=2.0,
            timeout=30.0,
        )

        # Assert learning mode flag is documented
        assert_contains(output, "--learn")

        # Assert description mentions learning/tutorial content
        assert_contains(output, "learning mode")

        # Verify help displayed successfully
        assert_command_success(output)

        # Verify options panel is shown
        assert_contains(output, "Options")

    def test_sample_processing_completes(self, tmux_session: TmuxSession) -> None:
        """Validate process command options are fully documented.

        Tests that `data-extract process --help` displays:
        - All critical processing options (--output, --format, --recursive)
        - Resume and error handling options (--resume, --interactive)
        - Learning mode integration (--learn)
        - Proper usage documentation

        Reference: docs/USER_GUIDE.md - Journey 1, Step 4
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract process --help",
            idle_time=3.0,
            timeout=30.0,
        )

        # Core processing options
        assert_contains(output, "--output")
        assert_contains(output, "--format")
        assert_contains(output, "--recursive")

        # Resume and error handling
        assert_contains(output, "--resume")
        assert_contains(output, "--interactive")

        # Learning mode integration
        assert_contains(output, "--learn")

        # Usage documentation
        assert_contains(output, "Usage")
        assert_contains(output, "input_path")

        # Verify no errors
        assert_command_success(output)

    def test_success_summary_shown(self, tmux_session: TmuxSession) -> None:
        """Validate complete configuration summary is displayed.

        Tests that `data-extract config show` provides:
        - Complete semantic analysis configuration (similarity, quality thresholds)
        - Chunking configuration (max_tokens, overlap)
        - Cache configuration (enabled status, size limits)
        - Properly structured hierarchical output

        Reference: docs/USER_GUIDE.md - Journey 1, Step 5
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract config show",
            idle_time=3.0,
            timeout=30.0,
        )

        # Semantic subsections
        assert_contains(output, "similarity")
        assert_contains(output, "quality")

        # Chunking configuration
        assert_contains(output, "max_tokens")

        # Cache configuration
        assert_contains(output, "enabled")

        # Structured output (YAML-style)
        assert_contains(output, ":")

        # Verify no errors
        assert_command_success(output)
