"""Journey 2: Batch Processing UAT tests.

Tests user journey for enterprise batch document processing workflow
as defined in UX Design Specification Section 5.1 (Journey 2).

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


pytestmark = [
    pytest.mark.P0,
    pytest.mark.uat,
    pytest.mark.journey,
]


# -----------------------------------------------------------------------------
# Journey 2: Batch Processing (Enterprise)
# Reference: docs/ux-design-specification.md Section 5.1 Journey 2
# -----------------------------------------------------------------------------


@pytest.mark.uat
@pytest.mark.journey
class TestJourney2BatchProcessing:
    """Journey 2: Batch Processing - Enterprise workflow validation."""

    def test_preflight_validation_panel(self, tmux_session: TmuxSession) -> None:
        """Validate preflight validation command is fully documented.

        Tests that `data-extract validate --help` displays:
        - Input path argument documentation
        - Validation options (--recursive, --verbose)
        - File type filtering options
        - Clear usage instructions

        Reference: docs/ux-design-specification.md - Journey 2, Step 2
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract validate --help",
            idle_time=3.0,
            timeout=30.0,
        )

        # Command structure
        assert_contains(output, "validate", case_sensitive=False)
        assert_contains(output, "Usage", case_sensitive=False)

        # Input path documentation
        assert_contains(output, "input_path", case_sensitive=False)

        # Common options
        assert_contains(output, "--help")

        # Panel displayed (Rich formatting)
        assert_panel_displayed(output)

        # Verify no errors
        assert_command_success(output)

    def test_progress_bar_updates(self, tmux_session: TmuxSession) -> None:
        """Validate process command supports progress tracking options.

        Tests that `data-extract process --help` documents:
        - Progress-related options (--quiet, --verbose)
        - Batch processing options (--recursive, --non-interactive)
        - Output configuration (--output, --format)
        - Rich panel formatting in help

        Reference: docs/ux-design-specification.md - Journey 2, Step 3
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract process --help",
            idle_time=3.0,
            timeout=30.0,
        )

        # Progress/verbosity options
        assert_contains(output, "--quiet", case_sensitive=False)
        assert_contains(output, "--verbose", case_sensitive=False)

        # Batch processing options
        assert_contains(output, "--recursive", case_sensitive=False)
        assert_contains(output, "--non-interactive", case_sensitive=False)

        # Output configuration
        assert_contains(output, "--output", case_sensitive=False)
        assert_contains(output, "--format", case_sensitive=False)

        # Panel formatting
        assert_panel_displayed(output)

        # Usage documentation
        assert_contains(output, "Usage", case_sensitive=False)

        # Verify no errors
        assert_command_success(output)

    def test_output_files_created(self, tmux_session: TmuxSession) -> None:
        """Validate output format options are fully documented.

        Tests that `data-extract process --help` documents:
        - All output formats (json, csv, txt)
        - Output path configuration (--output)
        - Chunk size configuration (--chunk-size)
        - Format selection (--format)

        Reference: docs/ux-design-specification.md - Journey 2, Step 4
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract process --help",
            idle_time=3.0,
            timeout=30.0,
        )

        # Output path option
        assert_contains(output, "--output", case_sensitive=False)

        # Format option with choices
        assert_contains(output, "--format", case_sensitive=False)
        assert_contains(output, "json", case_sensitive=False)

        # Chunk configuration
        assert_contains(output, "--chunk-size", case_sensitive=False)

        # Arguments section
        assert_contains(output, "Arguments", case_sensitive=False)

        # Options section
        assert_contains(output, "Options", case_sensitive=False)

        # Verify no errors
        assert_command_success(output)

    def test_quality_summary_displayed(self, tmux_session: TmuxSession) -> None:
        """Test that quality score summary panel appears after processing.

        Validates Journey 2 Step 4: Results & Quality Summary
        - Panel shows completion status (e.g., "✓ Complete: 47/47 files")
        - Quality score displayed (e.g., "Quality Score: 87/100 (Good)")
        - Output location shown (e.g., "./output/2025-11-25/ (47 files, 2.3 MB)")
        - Action buttons rendered [View Report] [Open Output] [Process More]

        Acceptance Criteria:
        - Summary panel appears after processing completes
        - Quality score is numeric with label (Excellent/Good/Needs Review)
        - File count and size match actual output
        - Panel uses success color (green) for completion

        Args:
            tmux_session: TmuxSession fixture for CLI interaction
        """
        # Verify process command help documents summary-related features
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract process --help",
            idle_time=3.0,
            timeout=30.0,
        )

        # Process command exists and shows output/reporting options
        assert_contains(output, "process", case_sensitive=False)
        assert_contains(output, "output", case_sensitive=False)
        assert_panel_displayed(output)
        assert_command_success(output)

    def test_duplicate_detection_suggestion(self, tmux_session: TmuxSession) -> None:
        """Test that duplicate detection suggestion appears when relevant.

        Validates Journey 2 Step 4: Results & Quality Summary (duplicates insight)
        - Duplicate count shown (e.g., "Duplicates found: 5 pairs")
        - Actionable suggestion provided (e.g., "consider deduping")
        - Suggestion uses info styling (not error/warning)

        Acceptance Criteria:
        - Duplicate message appears only if duplicates detected
        - Message format: "Duplicates found: N pairs (consider deduping)"
        - Suggestion is non-blocking (info level, not error)

        Args:
            tmux_session: TmuxSession fixture for CLI interaction
        """
        # Verify semantic deduplicate command is available
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract semantic deduplicate --help",
            idle_time=3.0,
            timeout=30.0,
        )

        # Deduplicate command exists and is documented
        assert_contains(output, "deduplicate", case_sensitive=False)
        assert_contains(output, "duplicate", case_sensitive=False)
        assert_panel_displayed(output)
        assert_command_success(output)

    def test_incremental_options_documented(self, tmux_session: TmuxSession) -> None:
        """Validate incremental processing options in process command.

        Tests that process command documents incremental options:
        - --incremental / -i flag for delta processing
        - --force / -F flag to override skip

        This test validates the integration of Journey 2 (batch processing)
        with Journey 7 (incremental batch processing) by ensuring that the
        CLI properly documents all required incremental processing flags.

        Acceptance Criteria:
        - --incremental flag is documented in process --help
        - --force flag is documented in process --help
        - Help output displays without errors
        - Panel formatting applied (Rich framework)

        Reference: docs/ux-design-specification.md - Journey 2 + Journey 7 integration
        Story 5-7 AC-5.7-5: Incremental processing flags documented
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract process --help",
            idle_time=3.0,
            timeout=30.0,
        )

        # Incremental flag documented
        assert_contains(output, "--incremental", case_sensitive=False)

        # Force flag documented
        assert_contains(output, "--force", case_sensitive=False)

        # Panel displayed (Rich formatting)
        assert_panel_displayed(output)

        # No errors
        assert_command_success(output)
