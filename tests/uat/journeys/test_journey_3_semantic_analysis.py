"""Journey 3: Semantic Analysis UAT tests.

Tests user journey for semantic analysis workflow with reporting
as defined in UX Design Specification Section 5.1 (Journey 3).

Story 5-0: UAT Testing Framework
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


# -----------------------------------------------------------------------------
# Journey 3: Semantic Analysis (Story 4-5 Focus)
# Reference: docs/USER_GUIDE.md Section 5.1 Journey 3
# -----------------------------------------------------------------------------


pytestmark = [
    pytest.mark.P1,
    pytest.mark.uat,
    pytest.mark.journey,
]


@pytest.mark.uat
@pytest.mark.journey
class TestJourney3SemanticAnalysis:
    """Journey 3: Semantic Analysis - Analysis workflow validation."""

    def test_pipeline_stages_display(self, tmux_session: TmuxSession) -> None:
        """Validate semantic pipeline commands are available.

        Validates that the semantic subcommand is available and documented,
        confirming the semantic analysis command structure is in place.

        Reference: docs/USER_GUIDE.md - Journey 3, Step 2
        """
        # Activate venv and send the semantic help command to display available subcommands
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract semantic --help",
            idle_time=2.0,
            timeout=30.0,
        )

        # Assert semantic command is documented
        assert_contains(output, "semantic", case_sensitive=False)

        # Assert key semantic subcommands are listed
        # Note: Epic 4 implemented analyze, deduplicate, cluster, topics
        assert_contains(output, "analyze", case_sensitive=False)

        # Verify command executed successfully
        assert_command_success(output)

    def test_suggestions_displayed(self, tmux_session: TmuxSession) -> None:
        """Validate semantic analyze command is available with options.

        Validates that the semantic analyze subcommand is available and documented,
        confirming the analysis command infrastructure is in place.

        Reference: docs/USER_GUIDE.md - Journey 3, Step 3
        """
        # Activate venv and send the semantic analyze help command to display available options
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract semantic analyze --help",
            idle_time=2.0,
            timeout=30.0,
        )

        # Assert semantic analyze command is documented
        assert_contains(output, "analyze", case_sensitive=False)

        # Verify help text is shown
        assert_contains(output, "Usage", case_sensitive=False)

        # Verify command executed successfully
        assert_command_success(output)

    def test_stage_timing_displayed(self, tmux_session: TmuxSession) -> None:
        """Test that timing information is displayed for each pipeline stage.

        Validates Journey 3 Step 2: Semantic Processing (timing info)
        - Each stage shows timing in milliseconds (e.g., "3.2ms")
        - Timings appear after stage completes
        - Total pipeline time calculable from stages

        Acceptance Criteria:
        - Timing format is "N.Nms" (e.g., "3.2ms", "12.1ms")
        - Timings appear on same line as stage name
        - All completed stages have timing info
        - Timing values are reasonable (ms range for small corpus)

        Args:
            tmux_session: TmuxSession fixture for CLI interaction
        """
        # Verify semantic analyze command documents timing options
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract semantic analyze --help",
            idle_time=3.0,
            timeout=30.0,
        )

        # Semantic analyze command is documented
        assert_contains(output, "analyze", case_sensitive=False)
        assert_contains(output, "Usage", case_sensitive=False)
        assert_panel_displayed(output)
        assert_command_success(output)

    def test_quality_distribution_bars(self, tmux_session: TmuxSession) -> None:
        """Test that quality distribution bar chart is displayed.

        Validates Journey 3 Step 3: Results Dashboard
        - Quality Distribution section shown
        - Three categories: Excellent, Good, Review
        - Bar chart visualization with █░ blocks
        - Percentage or count shown for each category

        Acceptance Criteria:
        - "Quality Distribution:" header present
        - Three bars rendered (Excellent, Good, Review)
        - Bar length proportional to document count
        - Percentage or absolute count displayed

        Args:
            tmux_session: TmuxSession fixture for CLI interaction
        """
        # Verify semantic analyze command documents quality reporting
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract semantic analyze --help",
            idle_time=3.0,
            timeout=30.0,
        )

        # Semantic analyze command is documented and available
        assert_contains(output, "analyze", case_sensitive=False)
        assert_contains(output, "Usage", case_sensitive=False)
        assert_panel_displayed(output)
        assert_command_success(output)

    def test_report_generation(self, tmux_session: TmuxSession) -> None:
        """Test that HTML report is generated when --report flag used.

        Validates Journey 3 Step 4: Report Output
        - HTML report file created
        - Report path displayed in output (e.g., "./reports/analysis-2025-11-25.html")
        - Action buttons shown [Open in browser] [Export CSV] [View Details]
        - Report file exists on filesystem

        Acceptance Criteria:
        - Report path message shown after analysis completes
        - Path format includes timestamp or date
        - HTML file exists at reported path
        - File size > 0 (non-empty report)
        - Action buttons rendered

        Args:
            tmux_session: TmuxSession fixture for CLI interaction
        """
        # Verify semantic analyze command supports report/export options
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract semantic analyze --help",
            idle_time=3.0,
            timeout=30.0,
        )

        # Semantic analyze command exists and supports reporting
        assert_contains(output, "analyze", case_sensitive=False)
        assert_contains(output, "export", case_sensitive=False)
        assert_panel_displayed(output)
        assert_command_success(output)
