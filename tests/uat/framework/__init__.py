"""UAT framework components.

Provides TmuxSession wrapper, UX assertions, and journey orchestration
for automated CLI validation testing.
"""

from tests.uat.framework.journey_runner import JourneyRunner, JourneyStep, StepResult
from tests.uat.framework.tmux_wrapper import TmuxError, TmuxSession
from tests.uat.framework.ux_assertions import (
    UXAssertionError,
    assert_checkmark,
    assert_color_present,
    assert_command_success,
    assert_contains,
    assert_error_color,
    assert_error_guide_shown,
    assert_learning_tip,
    assert_not_contains,
    assert_panel_displayed,
    assert_panel_has_content,
    assert_progress_bar_shown,
    assert_progress_percentage,
    assert_quality_distribution,
    assert_step_indicator,
    assert_success_color,
    assert_table_rendered,
    assert_table_row_count,
    strip_ansi,
)

__all__ = [
    # Core classes
    "TmuxSession",
    "TmuxError",
    "JourneyRunner",
    "JourneyStep",
    "StepResult",
    "UXAssertionError",
    # Panel assertions
    "assert_panel_displayed",
    "assert_panel_has_content",
    # Progress assertions
    "assert_progress_bar_shown",
    "assert_progress_percentage",
    # Table assertions
    "assert_table_rendered",
    "assert_table_row_count",
    # Color assertions
    "assert_color_present",
    "assert_success_color",
    "assert_error_color",
    # Quality assertions
    "assert_quality_distribution",
    # Error assertions
    "assert_error_guide_shown",
    # Learning assertions
    "assert_learning_tip",
    "assert_step_indicator",
    # General assertions
    "assert_contains",
    "assert_not_contains",
    "assert_command_success",
    "assert_checkmark",
    # Utilities
    "strip_ansi",
]
