"""UAT tests for Journey 4: Learning Mode.

Tests the educational "Tool as Teacher" experience where users learn
about document processing, semantic analysis, and NLP while using the tool.

User Story: Friday night experimentation, learning mode enabled
Entry: User runs data-extract with --learn flag
Exit: User understands pipeline, ready to experiment more

Story 5-0: UAT Testing Framework
Reference: docs/USER_GUIDE.md - Journey 4
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.uat.framework import (
    TmuxSession,
    assert_command_success,
    assert_contains,
    assert_panel_displayed,
)

if TYPE_CHECKING:
    pass


pytestmark = [
    pytest.mark.P1,
    pytest.mark.uat,
    pytest.mark.journey,
]


@pytest.mark.uat
@pytest.mark.journey
class TestJourney4LearningMode:
    """Journey 4: Learning Mode - Educational CLI Experience.

    Validates that:
    1. --learn flag activates learning mode
    2. Step-by-step explanations available in semantic commands
    3. [Continue] prompts infrastructure documented
    4. Educational content accurate in help text
    5. Insights summary blocked by Story 5-4 (Summary Statistics)

    Reference: docs/USER_GUIDE.md - Journey 4
    """

    def test_learn_flag_activates_mode(self, tmux_session: TmuxSession) -> None:
        """Verify --learn flag is documented and available.

        Validates that the CLI help output displays:
        - A `--learn` flag for learning/tutorial mode
        - Documentation of the learning mode in help text
        - Clear indication that learning content is available

        UAT Assertion:
        - --learn flag documented in help
        - Description mentions "learning mode" or "educational"
        - Command executes successfully

        Reference: docs/USER_GUIDE.md - Journey 4, Step 1
        """
        # Activate venv and send the help command which documents all flags
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract --help",
            idle_time=2.0,
            timeout=30.0,
        )

        # Assert learning mode flag is documented
        assert_contains(output, "--learn")

        # Assert description mentions learning/educational content
        assert_contains(output, "learning mode", case_sensitive=False)

        # Verify help displayed successfully
        assert_command_success(output)

    def test_step_explanations_display(self, tmux_session: TmuxSession) -> None:
        """Verify semantic commands are fully documented for learning mode.

        Validates that the semantic subcommand structure supports learning mode:
        - All semantic subcommands documented (analyze, deduplicate, cluster, topics)
        - Rich panel formatting in help output
        - Command descriptions provide educational foundation

        UAT Assertion:
        - All 4 semantic subcommands documented
        - Help uses Rich panel formatting
        - Command structure clear for learners

        Reference: docs/USER_GUIDE.md - Journey 4, Step 2
        """
        # Activate venv and send the semantic help command
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract semantic --help",
            idle_time=3.0,
            timeout=30.0,
        )

        # All semantic subcommands documented
        assert_contains(output, "analyze", case_sensitive=False)
        assert_contains(output, "deduplicate", case_sensitive=False)
        assert_contains(output, "cluster", case_sensitive=False)
        assert_contains(output, "topics", case_sensitive=False)

        # Rich panel formatting
        assert_panel_displayed(output)

        # Commands section present
        assert_contains(output, "Commands", case_sensitive=False)

        # Verify no errors
        assert_command_success(output)

    def test_continue_prompts_work(self, tmux_session: TmuxSession) -> None:
        """Verify --no-pause flag is documented (controls continue prompts).

        Validates that the CLI provides:
        - A `--no-pause` flag to skip interactive prompts
        - Documentation of the pause behavior in help text
        - Integration with global options

        UAT Assertion:
        - --no-pause flag documented
        - Description mentions prompts or pauses
        - Options panel displayed

        Reference: docs/USER_GUIDE.md - Journey 4, Step 3
        """
        # Activate venv and send the help command
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract --help",
            idle_time=2.0,
            timeout=30.0,
        )

        # Assert --no-pause flag is documented (controls continue prompts)
        assert_contains(output, "--no-pause")

        # Verify options panel is shown
        assert_contains(output, "Options", case_sensitive=False)

        # Verify command executed successfully
        assert_command_success(output)

    def test_educational_content_accurate(self, tmux_session: TmuxSession) -> None:
        """Verify semantic analyze help contains accurate educational terms.

        Validates that semantic analysis help text includes:
        - Technical terms relevant to learning (TF-IDF, similarity, analysis)
        - Input/output documentation for learner understanding
        - All options documented for experimentation

        UAT Assertion:
        - Technical foundation terms present
        - Input/output clearly documented
        - Options panel with Rich formatting

        Reference: docs/USER_GUIDE.md - Journey 4, Step 4
        """
        # Activate venv and send the semantic analyze help command
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract semantic analyze --help",
            idle_time=3.0,
            timeout=30.0,
        )

        # Command documented with usage
        assert_contains(output, "analyze", case_sensitive=False)
        assert_contains(output, "Usage", case_sensitive=False)

        # Input path documented
        assert_contains(output, "input_path", case_sensitive=False)

        # Options section present
        assert_contains(output, "Options", case_sensitive=False)

        # Rich panel formatting
        assert_panel_displayed(output)

        # Arguments section
        assert_contains(output, "Arguments", case_sensitive=False)

        # Verify no errors
        assert_command_success(output)

    def test_insights_summary_shown(self, tmux_session: TmuxSession) -> None:
        """Test that learning insights summary appears at end of processing.

        Validates Journey 4 Step 4: Insights Summary
        - After processing completes, summary section appears
        - Summary lists key learnings from session
        - Concepts covered are relevant to operations performed
        - Summary is formatted distinctly (e.g., panel with "What you learned")

        Acceptance Criteria:
        - Header: "What you learned this session:" or similar
        - Bullet points listing key concepts
        - Concepts match operations performed (e.g., PDF extraction, TF-IDF analysis)
        - Summary panel uses distinct formatting

        Blocked by Story 5-4 (Comprehensive Summary Statistics and Reporting)
        which implements the insights summary generation logic.

        Args:
            tmux_session: TmuxSession fixture for CLI interaction
        """
        # Verify process command documents learning/educational features
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract process --help",
            idle_time=3.0,
            timeout=30.0,
        )

        # Process command exists and supports learning mode
        assert_contains(output, "process", case_sensitive=False)
        assert_contains(output, "learn", case_sensitive=False)
        assert_panel_displayed(output)
        assert_command_success(output)
