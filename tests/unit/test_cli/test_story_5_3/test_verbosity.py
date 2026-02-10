"""TDD Red Phase Tests for Verbosity Levels - Story 5-3.

Tests for:
- AC-5.3-8: Quiet mode (-q) and verbose levels (-v, -vv, -vvv)

Expected RED failure: ModuleNotFoundError - verbosity controller doesn't exist yet.
"""

import pytest

# P1: Core functionality - run on PR
pytestmark = [
    pytest.mark.P1,
    pytest.mark.verbosity,
    pytest.mark.unit,
    pytest.mark.story_5_3,
    pytest.mark.cli,
]

# ==============================================================================
# AC-5.3-8: Quiet mode (-q) and verbose levels (-v, -vv, -vvv)
# ==============================================================================


class TestQuietMode:
    """Test quiet mode (-q/--quiet) suppresses all but errors."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_quiet_flag_suppresses_normal_output(self, typer_cli_runner, progress_test_corpus):
        """
        RED: AC-5.3-8 - Quiet mode suppresses normal output.

        Given: A batch of documents to process
        When: Running with -q flag
        Then: Only errors should be visible (no progress, no summary)

        Expected RED failure: -q flag not implemented
        """
        _files = progress_test_corpus.create_small_batch(5)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(progress_test_corpus.tmp_path), "-q"])

        # Quiet mode should suppress progress and summary
        assert "%" not in result.output
        assert "Processing" not in result.output
        assert "Summary" not in result.output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_quiet_long_flag_works(self, typer_cli_runner, progress_test_corpus):
        """
        RED: AC-5.3-8 - --quiet long flag works same as -q.

        Given: Documents to process
        When: Running with --quiet flag
        Then: Output should be suppressed same as -q

        Expected RED failure: --quiet flag not implemented
        """
        _files = progress_test_corpus.create_small_batch(3)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(
            app, ["process", str(progress_test_corpus.tmp_path), "--quiet"]
        )

        # Same behavior as -q
        assert "%" not in result.output
        assert "Processing" not in result.output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_quiet_mode_shows_errors(self, typer_cli_runner, batch_processing_fixture):
        """
        RED: AC-5.3-8 - Quiet mode still shows errors.

        Given: Documents including ones that will fail
        When: Running with -q flag
        Then: Errors should still be visible

        Expected RED failure: -q flag not implemented
        """
        good_files, error_files = batch_processing_fixture.create_mixed_batch()

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(
            app, ["process", str(batch_processing_fixture.tmp_path), "-q"]
        )

        # Errors should still appear in quiet mode
        assert "Error" in result.output or "error" in result.output or result.exit_code != 0

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_quiet_mode_returns_correct_exit_code(self, typer_cli_runner, progress_test_corpus):
        """
        RED: AC-5.3-8 - Quiet mode returns correct exit code.

        Given: Successful processing
        When: Running with -q flag
        Then: Exit code should indicate success (0)

        Expected RED failure: -q flag not implemented
        """
        _files = progress_test_corpus.create_small_batch(3)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(progress_test_corpus.tmp_path), "-q"])

        assert result.exit_code == 0


class TestVerboseMode:
    """Test verbose mode (-v) shows detailed per-file info."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_verbose_flag_shows_per_file_info(self, typer_cli_runner, progress_test_corpus):
        """
        RED: AC-5.3-8 - Verbose mode shows per-file information.

        Given: Documents to process
        When: Running with -v flag
        Then: Should show detailed info for each file

        Expected RED failure: -v flag not implemented
        """
        _files = progress_test_corpus.create_small_batch(5)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(progress_test_corpus.tmp_path), "-v"])

        # Should show individual file names
        assert any(f"doc_{i:03d}.txt" in result.output for i in range(5))

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_verbose_long_flag_works(self, typer_cli_runner, progress_test_corpus):
        """
        RED: AC-5.3-8 - --verbose long flag works same as -v.

        Given: Documents to process
        When: Running with --verbose flag
        Then: Should show detailed info

        Expected RED failure: --verbose flag not implemented
        """
        _files = progress_test_corpus.create_small_batch(3)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(
            app, ["process", str(progress_test_corpus.tmp_path), "--verbose"]
        )

        # Should show file details
        assert "doc_" in result.output


class TestDebugMode:
    """Test debug mode (-vv) shows full trace and timing."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_debug_flag_shows_timing(self, typer_cli_runner, progress_test_corpus):
        """
        RED: AC-5.3-8 - Debug mode (-vv) shows timing information.

        Given: Documents to process
        When: Running with -vv flag
        Then: Should show timing/performance info

        Expected RED failure: -vv flag not implemented
        """
        _files = progress_test_corpus.create_small_batch(3)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(
            app, ["process", str(progress_test_corpus.tmp_path), "-vv"]
        )

        # Should show timing info
        timing_indicators = ["ms", "timing", "duration", "elapsed", "DEBUG"]
        assert any(ind in result.output for ind in timing_indicators)

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_debug_flag_shows_debug_prefix(self, typer_cli_runner, progress_test_corpus):
        """
        RED: AC-5.3-8 - Debug mode shows DEBUG: prefix.

        Given: Documents to process
        When: Running with -vv flag
        Then: Should show DEBUG: prefixed messages

        Expected RED failure: -vv flag not implemented
        """
        _files = progress_test_corpus.create_small_batch(3)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(
            app, ["process", str(progress_test_corpus.tmp_path), "-vv"]
        )

        assert "DEBUG" in result.output


class TestTraceMode:
    """Test trace mode (-vvv) shows maximum detail."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_trace_flag_shows_maximum_detail(self, typer_cli_runner, progress_test_corpus):
        """
        RED: AC-5.3-8 - Trace mode (-vvv) shows maximum detail.

        Given: Documents to process
        When: Running with -vvv flag
        Then: Should show all available debug info including TRACE

        Expected RED failure: -vvv flag not implemented
        """
        _files = progress_test_corpus.create_small_batch(3)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(
            app, ["process", str(progress_test_corpus.tmp_path), "-vvv"]
        )

        # Should show trace-level info
        assert "TRACE" in result.output or "DEBUG" in result.output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_trace_includes_all_lower_levels(self, typer_cli_runner, progress_test_corpus):
        """
        RED: AC-5.3-8 - Trace mode includes all lower verbosity info.

        Given: Documents to process
        When: Running with -vvv flag
        Then: Should include verbose and debug info too

        Expected RED failure: -vvv flag not implemented
        """
        _files = progress_test_corpus.create_small_batch(3)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(
            app, ["process", str(progress_test_corpus.tmp_path), "-vvv"]
        )

        # Should include verbose-level file info
        assert "doc_" in result.output
        # Should include debug-level timing
        timing_indicators = ["ms", "timing", "duration"]
        assert any(ind in result.output for ind in timing_indicators)


class TestVerbosityLevelInteraction:
    """Test verbosity level interactions and edge cases."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_quiet_overrides_verbose(self, typer_cli_runner, progress_test_corpus):
        """
        RED: AC-5.3-8 - Quiet flag overrides verbose flags.

        Given: Both -q and -v specified
        When: Running command
        Then: Quiet mode should win (no output)

        Expected RED failure: Flag conflict not handled
        """
        _files = progress_test_corpus.create_small_batch(3)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(
            app, ["process", str(progress_test_corpus.tmp_path), "-q", "-v"]
        )

        # Quiet should override verbose
        assert "%" not in result.output
        assert "Processing" not in result.output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_default_verbosity_is_normal(self, typer_cli_runner, progress_test_corpus):
        """
        RED: AC-5.3-8 - Default (no flags) shows normal summary.

        Given: Documents to process
        When: Running without verbosity flags
        Then: Should show summary but not debug info

        Expected RED failure: Default verbosity not correct
        """
        _files = progress_test_corpus.create_small_batch(5)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(progress_test_corpus.tmp_path)])

        # Should show summary
        assert "files" in result.output.lower() or "processed" in result.output.lower()
        # Should NOT show debug info
        assert "DEBUG" not in result.output
        assert "TRACE" not in result.output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_verbosity_stacks_correctly(self, typer_cli_runner, progress_test_corpus):
        """
        RED: AC-5.3-8 - Stacked -v flags increase verbosity.

        Given: Documents to process
        When: Running with -v -v (two separate flags)
        Then: Should behave same as -vv

        Expected RED failure: Stacking not implemented
        """
        _files = progress_test_corpus.create_small_batch(3)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(
            app, ["process", str(progress_test_corpus.tmp_path), "-v", "-v"]
        )

        # Should show debug-level (same as -vv)
        assert "DEBUG" in result.output or "timing" in result.output.lower()


class TestVerbosityControllerAPI:
    """Test VerbosityController component API."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_verbosity_controller_class_exists(self):
        """
        RED: AC-5.3-8 - VerbosityController class should exist.

        Given: The feedback module
        When: Importing VerbosityController
        Then: Class should be importable

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import VerbosityController

        assert VerbosityController is not None

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_verbosity_controller_levels(self):
        """
        RED: AC-5.3-8 - VerbosityController supports all levels.

        Given: VerbosityController
        When: Creating with different levels
        Then: Should accept levels 0-4 (quiet to trace)

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import VerbosityController

        # Level 0 = quiet
        quiet = VerbosityController(level=0)
        assert quiet.is_quiet

        # Level 1 = normal (default)
        normal = VerbosityController(level=1)
        assert not normal.is_quiet
        assert not normal.is_verbose

        # Level 2 = verbose
        verbose = VerbosityController(level=2)
        assert verbose.is_verbose

        # Level 3 = debug
        debug = VerbosityController(level=3)
        assert debug.is_debug

        # Level 4 = trace
        trace = VerbosityController(level=4)
        assert trace.is_trace

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_verbosity_controller_should_log(self):
        """
        RED: AC-5.3-8 - VerbosityController filters messages by level.

        Given: VerbosityController at level 2 (verbose)
        When: Checking should_log for various message levels
        Then: Should filter appropriately

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import VerbosityController

        controller = VerbosityController(level=2)  # verbose

        # Should log normal and verbose
        assert controller.should_log("normal")
        assert controller.should_log("verbose")

        # Should NOT log debug or trace
        assert not controller.should_log("debug")
        assert not controller.should_log("trace")

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_verbosity_controller_log_method(self, mock_console):
        """
        RED: AC-5.3-8 - VerbosityController.log() respects level.

        Given: VerbosityController at quiet level
        When: Calling log() with normal message
        Then: Message should not appear

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import VerbosityController

        controller = VerbosityController(level=0, console=mock_console.console)

        controller.log("This is a normal message", level="normal")

        # Quiet mode should not output normal messages
        assert "normal message" not in mock_console.output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_verbosity_controller_error_always_shown(self, mock_console):
        """
        RED: AC-5.3-8 - Errors shown even in quiet mode.

        Given: VerbosityController at quiet level
        When: Calling log() with error message
        Then: Error should still appear

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.feedback import VerbosityController

        controller = VerbosityController(level=0, console=mock_console.console)

        controller.log("This is an error", level="error")

        # Error should appear even in quiet mode
        assert "error" in mock_console.output.lower()


class TestVerbosityWithProgress:
    """Test verbosity interaction with progress bars."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_quiet_mode_hides_progress_bar(self, typer_cli_runner, progress_test_corpus):
        """
        RED: AC-5.3-8 - Quiet mode hides progress bar.

        Given: Documents to process
        When: Running with -q flag
        Then: No progress bar should be visible

        Expected RED failure: Progress bar shown in quiet mode
        """
        _files = progress_test_corpus.create_small_batch(10)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(progress_test_corpus.tmp_path), "-q"])

        # No progress indicators
        assert "%" not in result.output
        assert "/" not in result.output or "10" not in result.output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.verbosity
    def test_verbose_mode_shows_enhanced_progress(self, typer_cli_runner, progress_test_corpus):
        """
        RED: AC-5.3-8 - Verbose mode shows enhanced progress info.

        Given: Documents to process
        When: Running with -v flag
        Then: Progress should include file names

        Expected RED failure: Enhanced progress not shown
        """
        _files = progress_test_corpus.create_small_batch(5)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(progress_test_corpus.tmp_path), "-v"])

        # Should show progress with file names
        assert any(f"doc_{i:03d}.txt" in result.output for i in range(5))
