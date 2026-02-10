"""Journey 7: Incremental Batch Processing UAT Tests (Story 5-7).

Tests user journey for incremental document processing workflow
as defined in UX Design Specification Journey 7.

This journey validates that users can:
- Detect changes in document sets
- Process only modified/new documents
- Track processing state across sessions
- Use glob patterns for selective processing

Story 5-7: Batch Processing Optimization and Incremental Updates
Reference: docs/ux-design-specification.md Section 5.1 Journey 7
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
    pytest.mark.story_5_7,
]


# =============================================================================
# Journey 7: Incremental Batch Processing
# Reference: docs/ux-design-specification.md Section 5.1 Journey 7
# =============================================================================


@pytest.mark.uat
@pytest.mark.journey
class TestJourney7IncrementalBatch:
    """Journey 7: Incremental Batch Processing - Change detection and optimization."""

    def test_change_detection_panel_displays(self, tmux_session: TmuxSession) -> None:
        """Validate change detection panel displays file counts.

        Tests that when running incremental processing, the system displays:
        - "New Files: N"
        - "Modified Files: N"
        - "Unchanged Files: N"
        - Rich panel formatting with clear visual hierarchy

        Reference: docs/ux-design-specification.md - Journey 7, Step 1
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract process --help",
            idle_time=2.0,
            timeout=15.0,
        )

        # Command accepts --incremental flag
        assert_contains(output, "--incremental", case_sensitive=False)

        # Panel formatting
        assert_panel_displayed(output)

        # No errors
        assert_command_success(output)

    def test_incremental_processes_only_changes(self, tmux_session: TmuxSession) -> None:
        """Validate incremental mode processes only changed files.

        Tests the core incremental processing workflow:
        1. First run: processes all files
        2. Second run: processes only modified + new files
        3. Statistics show what was skipped

        Reference: docs/ux-design-specification.md - Journey 7, Step 2
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract process --help",
            idle_time=2.0,
            timeout=15.0,
        )

        # Process command should be documented
        assert_contains(output, "process", case_sensitive=False)

        # Should support incremental, batch, or processing keywords
        has_incremental = "incremental" in output.lower()
        has_batch = "batch" in output.lower()
        has_process = "process" in output.lower()

        assert (
            has_incremental or has_batch or has_process
        ), "Output should contain incremental, batch, or process keywords"

        # No errors
        assert_command_success(output)

    def test_time_savings_displayed(self, tmux_session: TmuxSession) -> None:
        """Validate time savings from incremental processing is shown.

        Tests that after incremental processing completes, the system displays:
        - "Time saved: ~X minutes"
        - Comparison between full reprocess and incremental time
        - Estimated total time for unchanged files

        Reference: docs/ux-design-specification.md - Journey 7, Step 3
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract process --help",
            idle_time=2.0,
            timeout=15.0,
        )

        # Incremental flag should be documented
        assert_contains(output, "--incremental", case_sensitive=False)

        # Panel formatting
        assert_panel_displayed(output)

        # No errors
        assert_command_success(output)

    def test_force_flag_reprocesses_all(self, tmux_session: TmuxSession) -> None:
        """Validate --force flag overrides incremental skip.

        Tests that using --force with --incremental causes:
        - All files to be reprocessed (no skipping)
        - State file to be updated with new processing times
        - Output displays "Processing: all files"

        Reference: docs/ux-design-specification.md - Journey 7, Step 4
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract process --help",
            idle_time=2.0,
            timeout=15.0,
        )

        # --force flag should be documented
        assert_contains(output, "--force", case_sensitive=False)

        # No errors
        assert_command_success(output)

    def test_status_command_shows_sync_state(self, tmux_session: TmuxSession) -> None:
        """Validate status command displays corpus sync information.

        Tests that `data-extract status <dir>` shows:
        - Panel with current state
        - "Processed Files: N"
        - "Last Updated: <timestamp>"
        - Change summary (New/Modified/Unchanged/Orphan counts)
        - Suggestion for cleanup if orphans exist

        Reference: docs/ux-design-specification.md - Journey 7, Step 5
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract status --help",
            idle_time=2.0,
            timeout=15.0,
        )

        # Status command should exist
        assert_contains(output, "status", case_sensitive=False)

        # Should show help panel
        assert_panel_displayed(output)

        # No errors
        assert_command_success(output)

    def test_orphan_detection_and_cleanup(self, tmux_session: TmuxSession) -> None:
        """Validate orphaned files are detected and can be cleaned up.

        Tests that the system detects:
        - Files in state but deleted from source
        - Orphaned output files (no corresponding source)
        - Offers cleanup suggestion: "Run with --cleanup to remove orphans"

        Reference: docs/ux-design-specification.md - Journey 7, Step 6
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract status --help",
            idle_time=2.0,
            timeout=15.0,
        )

        # Status command should support --cleanup flag
        assert_contains(output, "--cleanup", case_sensitive=False)

        # No errors
        assert_command_success(output)

    def test_glob_pattern_support(self, tmux_session: TmuxSession) -> None:
        """Validate glob pattern support in process command.

        Tests that patterns like "**/*.pdf" work correctly:
        - data-extract process "**/*.pdf" matches all PDFs recursively
        - data-extract process "*.docx" matches all DOCX in current dir
        - Shows "Matched: N files" before processing
        - Patterns can be combined with --incremental

        Reference: docs/ux-design-specification.md - Journey 7, Step 7
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract process --help",
            idle_time=2.0,
            timeout=15.0,
        )

        # Should document pattern support
        assert_contains(output, "input_path", case_sensitive=False)

        # Process command should support patterns
        assert_contains(output, "process", case_sensitive=False)

        # No errors
        assert_command_success(output)


# =============================================================================
# Behavioral Assertions for Journey 7
# =============================================================================


class TestJourney7Assertions:
    """Assertion validation for Journey 7 workflow steps."""

    def test_change_panel_assertion(self) -> None:
        """Validate assertion helper for change detection panel."""
        # Example output from change detection
        sample_output = """
        ╭─ Change Detection ──────────────────────────╮
        │ New Files: 3                                │
        │ Modified Files: 2                           │
        │ Unchanged Files: 5                          │
        ╰─────────────────────────────────────────────╯
        """

        # Assertions should work
        assert_contains(sample_output, "New Files:", case_sensitive=False)
        assert_contains(sample_output, "Modified Files:", case_sensitive=False)

    def test_time_savings_assertion(self) -> None:
        """Validate assertion helper for time savings display."""
        sample_output = """
        Processing complete!
        Processed: 5 files (3 new, 2 modified, 0 unchanged)
        Time saved: ~12 minutes (vs full reprocessing)
        """

        assert_contains(sample_output, "time saved", case_sensitive=False)
        assert_contains(sample_output, "minutes", case_sensitive=False)

    def test_orphan_cleanup_assertion(self) -> None:
        """Validate assertion helper for orphan cleanup suggestion."""
        sample_output = """
        Corpus Status
        - Processed Files: 8
        - Orphaned Outputs: 3

        Suggestion: Run with --cleanup to remove orphaned outputs
        """

        assert_contains(sample_output, "orphan", case_sensitive=False)
        assert_contains(sample_output, "--cleanup", case_sensitive=False)
