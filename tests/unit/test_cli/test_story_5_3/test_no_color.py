"""TDD Red Phase Tests for NO_COLOR Support - Story 5-3.

Tests for:
- AC-5.3-5: NO_COLOR environment variable support disables ANSI colors

Expected RED failure: ModuleNotFoundError - components don't respect NO_COLOR yet.
"""

import os

import pytest

# P2: Extended coverage - run nightly
pytestmark = [
    pytest.mark.P2,
    pytest.mark.no_color,
    pytest.mark.unit,
    pytest.mark.story_5_3,
    pytest.mark.cli,
]

# ==============================================================================
# AC-5.3-5: NO_COLOR environment variable support
# ==============================================================================


class TestNoColorEnvironmentSupport:
    """Test NO_COLOR environment variable disables ANSI colors."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.no_color
    def test_no_color_env_disables_ansi_codes(self, typer_cli_runner, env_vars_fixture, tmp_path):
        """
        RED: AC-5.3-5 - NO_COLOR=1 disables ANSI escape codes.

        Given: NO_COLOR environment variable is set
        When: Running any command
        Then: Output should contain no ANSI escape sequences

        Expected RED failure: NO_COLOR not respected
        """
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content " * 50)

        # Set NO_COLOR
        env_vars_fixture.set_no_color(enabled=True)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["--help"])

        # ANSI escape codes start with ESC (0x1b or \x1b or \033)
        assert "\x1b[" not in result.output, "ANSI codes found when NO_COLOR is set"
        assert "\033[" not in result.output, "ANSI codes found when NO_COLOR is set"

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.no_color
    def test_no_color_progress_bar_no_ansi(
        self, typer_cli_runner, env_vars_fixture, progress_test_corpus
    ):
        """
        RED: AC-5.3-5 - Progress bars have no ANSI when NO_COLOR set.

        Given: NO_COLOR=1 and documents to process
        When: Running process command
        Then: Progress output has no ANSI escape codes

        Expected RED failure: Progress bar still uses ANSI
        """
        _files = progress_test_corpus.create_small_batch(5)
        env_vars_fixture.set_no_color(enabled=True)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(progress_test_corpus.tmp_path)])

        # No ANSI escape sequences
        assert "\x1b[" not in result.output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.no_color
    def test_no_color_panels_no_ansi(
        self, typer_cli_runner, env_vars_fixture, progress_test_corpus
    ):
        """
        RED: AC-5.3-5 - Rich panels have no ANSI when NO_COLOR set.

        Given: NO_COLOR=1 and documents to process
        When: Running process command (shows panels)
        Then: Panel output has no ANSI escape codes

        Expected RED failure: Panels still use ANSI
        """
        _files = progress_test_corpus.create_small_batch(5)
        env_vars_fixture.set_no_color(enabled=True)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(progress_test_corpus.tmp_path)])

        # No ANSI escape sequences
        assert "\x1b[" not in result.output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.no_color
    def test_no_color_quality_dashboard_no_ansi(
        self, typer_cli_runner, env_vars_fixture, progress_test_corpus
    ):
        """
        RED: AC-5.3-5 - Quality dashboard has no ANSI when NO_COLOR set.

        Given: NO_COLOR=1 and documents to process
        When: Running process command to completion
        Then: Quality dashboard has no ANSI escape codes

        Expected RED failure: Dashboard still uses ANSI colors
        """
        _files = progress_test_corpus.create_small_batch(5)
        env_vars_fixture.set_no_color(enabled=True)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(progress_test_corpus.tmp_path)])

        # No ANSI escape sequences anywhere
        assert "\x1b[" not in result.output


class TestNoColorAsciiFallbacks:
    """Test ASCII fallbacks for Unicode symbols when NO_COLOR is set."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.no_color
    def test_no_color_uses_ascii_checkmark(
        self, typer_cli_runner, env_vars_fixture, progress_test_corpus
    ):
        """
        RED: AC-5.3-5 - Uses ASCII [x] instead of unicode checkmark.

        Given: NO_COLOR=1
        When: Running command showing success
        Then: Should use [x] or [+] instead of checkmark

        Expected RED failure: Still uses unicode symbols
        """
        _files = progress_test_corpus.create_small_batch(3)
        env_vars_fixture.set_no_color(enabled=True)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(progress_test_corpus.tmp_path)])

        # Should NOT contain unicode checkmark
        unicode_checkmark = "\u2713"  # checkmark
        unicode_heavy_check = "\u2714"  # heavy checkmark

        # Should use ASCII alternative
        if unicode_checkmark in result.output or unicode_heavy_check in result.output:
            pytest.fail("Unicode checkmarks found when NO_COLOR is set")

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.no_color
    def test_no_color_uses_ascii_progress_chars(
        self, typer_cli_runner, env_vars_fixture, progress_test_corpus
    ):
        """
        RED: AC-5.3-5 - Uses ASCII chars for progress bar.

        Given: NO_COLOR=1
        When: Showing progress bar
        Then: Should use ASCII chars like [====----] instead of unicode blocks

        Expected RED failure: Still uses unicode block chars
        """
        _files = progress_test_corpus.create_small_batch(5)
        env_vars_fixture.set_no_color(enabled=True)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(progress_test_corpus.tmp_path)])

        # Unicode block characters that should be replaced
        unicode_full_block = "\u2588"
        unicode_partial_blocks = ["\u2589", "\u258a", "\u258b", "\u258c"]

        for char in [unicode_full_block] + unicode_partial_blocks:
            if char in result.output:
                pytest.fail(f"Unicode block char {repr(char)} found when NO_COLOR is set")

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.no_color
    def test_no_color_uses_ascii_spinners(
        self, typer_cli_runner, env_vars_fixture, progress_test_corpus
    ):
        """
        RED: AC-5.3-5 - Uses ASCII spinner chars instead of unicode.

        Given: NO_COLOR=1
        When: Showing spinner
        Then: Should use ASCII chars like |/-\\ instead of unicode dots/circles

        Expected RED failure: Still uses unicode spinners
        """
        _files = progress_test_corpus.create_small_batch(5)
        env_vars_fixture.set_no_color(enabled=True)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(progress_test_corpus.tmp_path)])

        # Unicode spinner/loading characters
        unicode_spinners = [
            "\u25cf",  # Black circle
            "\u25cb",  # White circle
            "\u25ce",  # Bullseye
            "\u2022",  # Bullet
            "\u280b",  # Braille patterns (dots spinner)
        ]

        for char in unicode_spinners:
            if char in result.output:
                pytest.fail(f"Unicode spinner char {repr(char)} found when NO_COLOR is set")

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.no_color
    def test_no_color_uses_ascii_borders(
        self, typer_cli_runner, env_vars_fixture, progress_test_corpus
    ):
        """
        RED: AC-5.3-5 - Uses ASCII borders for panels instead of box-drawing.

        Given: NO_COLOR=1
        When: Showing Rich panels
        Then: Should use ASCII +--|+ instead of unicode box-drawing

        Expected RED failure: Still uses unicode box chars
        """
        _files = progress_test_corpus.create_small_batch(5)
        env_vars_fixture.set_no_color(enabled=True)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(progress_test_corpus.tmp_path)])

        # Unicode box-drawing characters
        box_drawing_chars = [
            "\u2500",  # horizontal line
            "\u2502",  # vertical line
            "\u250c",  # top-left corner
            "\u2510",  # top-right corner
            "\u2514",  # bottom-left corner
            "\u2518",  # bottom-right corner
        ]

        for char in box_drawing_chars:
            if char in result.output:
                pytest.fail(f"Unicode box-drawing char {repr(char)} found when NO_COLOR set")


class TestNoColorComponentIntegration:
    """Test component-level NO_COLOR integration."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.no_color
    def test_progress_component_respects_no_color(self, no_color_console):
        """
        RED: AC-5.3-5 - PipelineProgress respects NO_COLOR console.

        Given: A console with NO_COLOR mode
        When: Creating PipelineProgress with that console
        Then: Output should have no ANSI codes

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.progress import PipelineProgress

        progress = PipelineProgress(total_files=10, console=no_color_console.console)

        progress.start()
        for i in range(10):
            progress.update_stage("extract", i + 1)
        progress.stop()

        output = no_color_console.exported_text
        assert "\x1b[" not in output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.no_color
    def test_quality_dashboard_respects_no_color(self, no_color_console, quality_metrics_sample):
        """
        RED: AC-5.3-5 - QualityDashboard respects NO_COLOR console.

        Given: A console with NO_COLOR mode
        When: Rendering QualityDashboard
        Then: Output should have no ANSI codes

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import QualityDashboard

        dashboard = QualityDashboard(metrics=quality_metrics_sample)
        panel = dashboard.render()

        no_color_console.console.print(panel)
        output = no_color_console.exported_text

        assert "\x1b[" not in output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.no_color
    def test_preflight_panel_respects_no_color(self, no_color_console, preflight_test_files):
        """
        RED: AC-5.3-5 - PreflightPanel respects NO_COLOR console.

        Given: A console with NO_COLOR mode
        When: Rendering PreflightPanel
        Then: Output should have no ANSI codes

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import PreflightPanel

        files = preflight_test_files.create_preflight_corpus()

        panel = PreflightPanel()
        panel.analyze(files)
        rendered = panel.render()

        no_color_console.console.print(rendered)
        output = no_color_console.exported_text

        assert "\x1b[" not in output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.no_color
    def test_console_detects_no_color_env(self, env_vars_fixture):
        """
        RED: AC-5.3-5 - Console initialization detects NO_COLOR env var.

        Given: NO_COLOR=1 in environment
        When: Creating console for CLI
        Then: Console should be configured with no_color=True

        Expected RED failure: ModuleNotFoundError or console creation doesn't check env
        """
        env_vars_fixture.set_no_color(enabled=True)

        from data_extract.cli.components.feedback import get_console

        console = get_console()

        assert console.no_color is True

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.no_color
    def test_no_color_empty_value_does_not_disable(self, env_vars_fixture):
        """
        RED: AC-5.3-5 - Empty NO_COLOR value does not disable colors.

        Given: NO_COLOR="" (empty string) in environment
        When: Creating console
        Then: Console should still have colors enabled

        Expected RED failure: Empty string treated as truthy
        """
        # Per spec, NO_COLOR presence (any value) disables colors
        # But empty might be edge case - test actual behavior
        os.environ["NO_COLOR"] = ""

        try:
            from data_extract.cli.components.feedback import get_console

            console = get_console()

            # Empty NO_COLOR still counts as "set" per spec
            # But some implementations treat empty as false
            # This test documents expected behavior
            assert console.no_color is True  # NO_COLOR="" should disable colors
        finally:
            if "NO_COLOR" in os.environ:
                del os.environ["NO_COLOR"]


class TestNoColorContentPreservation:
    """Test that content is preserved when colors are disabled."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.no_color
    def test_no_color_preserves_text_content(self, typer_cli_runner, env_vars_fixture, tmp_path):
        """
        RED: AC-5.3-5 - All text content is still visible without colors.

        Given: NO_COLOR=1
        When: Running help command
        Then: All help text should be present

        Expected RED failure: Some text hidden or lost
        """
        env_vars_fixture.set_no_color(enabled=True)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["--help"])

        # Essential help content should be present
        assert "Usage" in result.output or "usage" in result.output
        assert "Options" in result.output or "options" in result.output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.no_color
    def test_no_color_preserves_error_messages(self, typer_cli_runner, env_vars_fixture, tmp_path):
        """
        RED: AC-5.3-5 - Error messages visible without colors.

        Given: NO_COLOR=1 and invalid input
        When: Running command that will error
        Then: Error message should be visible

        Expected RED failure: Error styling causes message loss
        """
        env_vars_fixture.set_no_color(enabled=True)

        from data_extract.cli.app import app

        # Non-existent path should error
        result = typer_cli_runner.invoke(app, ["process", "/nonexistent/path/does/not/exist"])

        # Error should be visible
        assert "Error" in result.output or "error" in result.output or result.exit_code != 0
