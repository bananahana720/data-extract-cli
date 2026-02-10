"""TDD Red Phase Tests for Rich Panels - Story 5-3.

Tests for:
- AC-5.3-2: Quality dashboard (Rich Panel) after processing
- AC-5.3-3: Pre-flight validation panel before batch operations

Expected RED failure: ModuleNotFoundError - panel components don't exist yet.
"""

import pytest

# P1: Core functionality - run on PR
pytestmark = [
    pytest.mark.P1,
    pytest.mark.panels,
    pytest.mark.unit,
    pytest.mark.story_5_3,
    pytest.mark.cli,
]

# ==============================================================================
# AC-5.3-2: Quality dashboard (Rich Panel) shows metrics with visual bars
# ==============================================================================


class TestQualityDashboard:
    """Test Quality Dashboard panel after processing."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_quality_dashboard_class_exists(self):
        """
        RED: AC-5.3-2 - QualityDashboard class should exist.

        Given: The panels module
        When: Importing QualityDashboard
        Then: Class should be importable

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import QualityDashboard

        assert QualityDashboard is not None

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_quality_dashboard_render_returns_panel(self, quality_metrics_sample):
        """
        RED: AC-5.3-2 - QualityDashboard.render() returns Rich Panel.

        Given: Quality metrics from processing
        When: Calling render()
        Then: Should return a Rich Panel object

        Expected RED failure: ModuleNotFoundError
        """
        from rich.panel import Panel

        from data_extract.cli.components.panels import QualityDashboard

        dashboard = QualityDashboard(metrics=quality_metrics_sample)
        result = dashboard.render()

        assert isinstance(result, Panel)

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_quality_dashboard_has_title(self, quality_metrics_sample, mock_console):
        """
        RED: AC-5.3-2 - Quality dashboard has proper title.

        Given: Quality metrics from processing
        When: Rendering to console
        Then: Panel should have "Quality Insights" or similar title

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import QualityDashboard

        dashboard = QualityDashboard(metrics=quality_metrics_sample)
        panel = dashboard.render()

        mock_console.console.print(panel)
        output = mock_console.exported_text

        assert "Quality" in output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_quality_dashboard_shows_success_count(self, quality_metrics_sample, mock_console):
        """
        RED: AC-5.3-2 - Dashboard shows files processed successfully.

        Given: 44/47 files processed successfully
        When: Rendering dashboard
        Then: Should show "44/47 files processed successfully"

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import QualityDashboard

        dashboard = QualityDashboard(metrics=quality_metrics_sample)
        panel = dashboard.render()

        mock_console.console.print(panel)
        output = mock_console.exported_text

        assert "44" in output
        assert "47" in output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_quality_dashboard_shows_distribution_bars(self, quality_metrics_sample, mock_console):
        """
        RED: AC-5.3-2 - Dashboard shows quality distribution with visual bars.

        Given: Quality distribution (excellent: 34, good: 7, needs review: 3)
        When: Rendering dashboard
        Then: Should show visual bars for each category

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import QualityDashboard

        dashboard = QualityDashboard(metrics=quality_metrics_sample)
        panel = dashboard.render()

        mock_console.console.print(panel)
        output = mock_console.exported_text

        # Should show distribution categories
        assert "Excellent" in output or ">90" in output
        assert "Good" in output or "70-90" in output
        assert "Needs Review" in output or "<70" in output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_quality_dashboard_shows_excellent_bar_with_count(
        self, quality_metrics_sample, mock_console
    ):
        """
        RED: AC-5.3-2 - Excellent category shows count (34 files).

        Given: 34 files with excellent quality
        When: Rendering dashboard
        Then: Should show "34" associated with excellent category

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import QualityDashboard

        dashboard = QualityDashboard(metrics=quality_metrics_sample)
        panel = dashboard.render()

        mock_console.console.print(panel)
        output = mock_console.exported_text

        assert "34" in output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_quality_dashboard_shows_suggestions(self, quality_metrics_sample, mock_console):
        """
        RED: AC-5.3-2 - Dashboard shows actionable suggestions.

        Given: Suggestions from analysis
        When: Rendering dashboard
        Then: Should show suggestion text

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import QualityDashboard

        dashboard = QualityDashboard(metrics=quality_metrics_sample)
        panel = dashboard.render()

        mock_console.console.print(panel)
        output = mock_console.exported_text

        # Should show suggestion
        assert "Suggestion" in output or "dedupe" in output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_quality_dashboard_shows_learning_tip(self, quality_metrics_sample, mock_console):
        """
        RED: AC-5.3-2 - Dashboard includes learning tip.

        Given: Quality metrics with learning tip
        When: Rendering dashboard
        Then: Should show "Learn more" or expandable tip

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import QualityDashboard

        dashboard = QualityDashboard(metrics=quality_metrics_sample)
        panel = dashboard.render()

        mock_console.console.print(panel)
        output = mock_console.exported_text

        assert "Learn" in output or "tip" in output.lower()

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_quality_dashboard_displays_after_process_command(
        self, typer_cli_runner, progress_test_corpus
    ):
        """
        RED: AC-5.3-2 - Dashboard displays after process command.

        Given: A batch of documents
        When: Running process command to completion
        Then: Quality dashboard should appear in output

        Expected RED failure: Process command doesn't exist
        """
        _files = progress_test_corpus.create_small_batch(10)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(progress_test_corpus.tmp_path)])

        # Dashboard should appear after processing
        assert "Quality" in result.output


# ==============================================================================
# AC-5.3-3: Pre-flight validation panel before batch operations
# ==============================================================================


class TestPreflightPanel:
    """Test Pre-flight validation panel before batch operations."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_preflight_panel_class_exists(self):
        """
        RED: AC-5.3-3 - PreflightPanel class should exist.

        Given: The panels module
        When: Importing PreflightPanel
        Then: Class should be importable

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import PreflightPanel

        assert PreflightPanel is not None

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_preflight_panel_analyze_method(self, preflight_test_files):
        """
        RED: AC-5.3-3 - PreflightPanel has analyze() method.

        Given: A list of files to process
        When: Calling analyze()
        Then: Should return analysis results

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import PreflightPanel

        files = preflight_test_files.create_preflight_corpus()

        panel = PreflightPanel()
        analysis = panel.analyze(files)

        assert analysis is not None
        assert "file_count" in analysis or hasattr(analysis, "file_count")

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_preflight_panel_shows_file_count(self, preflight_test_files, mock_console):
        """
        RED: AC-5.3-3 - Pre-flight panel shows total file count.

        Given: 13 files to process
        When: Rendering pre-flight panel
        Then: Should show "Files: 13 documents"

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import PreflightPanel

        files = preflight_test_files.create_preflight_corpus()

        panel = PreflightPanel()
        panel.analyze(files)
        rendered = panel.render()

        mock_console.console.print(rendered)
        output = mock_console.exported_text

        # Should show file count
        assert str(len(files)) in output or "Files:" in output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_preflight_panel_shows_type_breakdown(self, preflight_test_files, mock_console):
        """
        RED: AC-5.3-3 - Pre-flight panel shows file type breakdown.

        Given: Files of various types (TXT, PDF, DOCX)
        When: Rendering pre-flight panel
        Then: Should show type counts (e.g., "PDF: 5, DOCX: 3, TXT: 10")

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import PreflightPanel

        files = preflight_test_files.create_preflight_corpus()

        panel = PreflightPanel()
        panel.analyze(files)
        rendered = panel.render()

        mock_console.console.print(rendered)
        output = mock_console.exported_text

        # Should show at least one type
        type_indicators = ["PDF", "DOCX", "TXT", "XLSX"]
        assert any(t in output for t in type_indicators)

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_preflight_panel_shows_estimated_time(self, preflight_test_files, mock_console):
        """
        RED: AC-5.3-3 - Pre-flight panel shows estimated processing time.

        Given: Files to process
        When: Rendering pre-flight panel
        Then: Should show estimated time (e.g., "Estimated time: ~2 minutes")

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import PreflightPanel

        files = preflight_test_files.create_preflight_corpus()

        panel = PreflightPanel()
        panel.analyze(files)
        rendered = panel.render()

        mock_console.console.print(rendered)
        output = mock_console.exported_text

        # Should show estimated time
        time_indicators = ["Estimated", "time", "minute", "second", "~"]
        assert any(ind in output for ind in time_indicators)

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_preflight_panel_shows_warnings(self, preflight_test_files, mock_console):
        """
        RED: AC-5.3-3 - Pre-flight panel shows warnings for problematic files.

        Given: Files including problematic ones (large, empty, OCR-needed)
        When: Rendering pre-flight panel
        Then: Should show warnings for each issue

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import PreflightPanel

        files = preflight_test_files.create_preflight_corpus()
        _expected_warnings = preflight_test_files.expected_warnings

        panel = PreflightPanel()
        panel.analyze(files)
        rendered = panel.render()

        mock_console.console.print(rendered)
        output = mock_console.exported_text

        # Should show warning indicator
        assert "Warning" in output or "issue" in output.lower()

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_preflight_panel_shows_output_directory(
        self, preflight_test_files, mock_console, tmp_path
    ):
        """
        RED: AC-5.3-3 - Pre-flight panel shows output directory.

        Given: Files and an output directory
        When: Rendering pre-flight panel
        Then: Should show where output will be written

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import PreflightPanel

        files = preflight_test_files.create_preflight_corpus()
        output_dir = tmp_path / "output"

        panel = PreflightPanel(output_dir=output_dir)
        panel.analyze(files)
        rendered = panel.render()

        mock_console.console.print(rendered)
        output = mock_console.exported_text

        assert "Output" in output or "output" in output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_preflight_panel_has_title(self, preflight_test_files, mock_console):
        """
        RED: AC-5.3-3 - Pre-flight panel has "Pre-flight Check" title.

        Given: Files to analyze
        When: Rendering pre-flight panel
        Then: Panel should have appropriate title

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import PreflightPanel

        files = preflight_test_files.create_preflight_corpus()

        panel = PreflightPanel()
        panel.analyze(files)
        rendered = panel.render()

        mock_console.console.print(rendered)
        output = mock_console.exported_text

        assert "Pre-flight" in output or "Preflight" in output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_preflight_panel_displays_before_process_command(
        self, typer_cli_runner, progress_test_corpus
    ):
        """
        RED: AC-5.3-3 - Pre-flight panel displays before processing.

        Given: A batch of documents
        When: Running process command
        Then: Pre-flight panel should appear before progress

        Expected RED failure: Process command doesn't exist
        """
        _files = progress_test_corpus.create_small_batch(10)

        from data_extract.cli.app import app

        result = typer_cli_runner.invoke(app, ["process", str(progress_test_corpus.tmp_path)])

        # Pre-flight should appear
        assert "Pre-flight" in result.output or "Files:" in result.output

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_preflight_panel_action_buttons_shown(self, preflight_test_files, mock_console):
        """
        RED: AC-5.3-3 - Pre-flight panel shows action buttons.

        Given: Files to analyze
        When: Rendering pre-flight panel
        Then: Should show [Continue] [Preview First] [Cancel] options

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import PreflightPanel

        files = preflight_test_files.create_preflight_corpus()

        panel = PreflightPanel()
        panel.analyze(files)
        rendered = panel.render()

        mock_console.console.print(rendered)
        output = mock_console.exported_text

        # Should show at least Continue option
        assert "Continue" in output or "Proceed" in output


# ==============================================================================
# Panel Component Unit Tests
# ==============================================================================


class TestPanelComponentAPI:
    """Unit tests for panel component APIs."""

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_quality_dashboard_accepts_metrics_dict(self):
        """
        RED: QualityDashboard can be initialized with dict.

        Given: Quality metrics as dictionary
        When: Creating QualityDashboard
        Then: Should accept dict input

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import QualityDashboard

        metrics = {
            "total_files": 10,
            "successful_files": 9,
            "failed_files": 1,
            "excellent_count": 5,
            "good_count": 3,
            "needs_review_count": 1,
        }

        dashboard = QualityDashboard(metrics=metrics)
        assert dashboard is not None

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_preflight_panel_accepts_path_list(self, tmp_path):
        """
        RED: PreflightPanel accepts list of paths.

        Given: List of Path objects
        When: Calling analyze()
        Then: Should process all paths

        Expected RED failure: ModuleNotFoundError
        """

        from data_extract.cli.components.panels import PreflightPanel

        files = [
            tmp_path / "doc1.txt",
            tmp_path / "doc2.pdf",
        ]
        for f in files:
            f.write_text("content") if f.suffix == ".txt" else f.write_bytes(b"data")

        panel = PreflightPanel()
        analysis = panel.analyze(files)

        assert analysis.file_count == 2

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_preflight_panel_handles_empty_directory(self, tmp_path):
        """
        RED: PreflightPanel handles empty directory gracefully.

        Given: Empty directory
        When: Analyzing directory
        Then: Should report 0 files without error

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import PreflightPanel

        panel = PreflightPanel()
        analysis = panel.analyze([])

        assert analysis.file_count == 0

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_quality_dashboard_handles_zero_files(self):
        """
        RED: QualityDashboard handles zero processed files.

        Given: No files processed
        When: Rendering dashboard
        Then: Should show appropriate message without error

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import QualityDashboard

        metrics = {
            "total_files": 0,
            "successful_files": 0,
            "failed_files": 0,
        }

        dashboard = QualityDashboard(metrics=metrics)
        panel = dashboard.render()

        assert panel is not None

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_preflight_detects_large_files(self, tmp_path):
        """
        RED: PreflightPanel detects and warns about large files.

        Given: A file over threshold size
        When: Analyzing
        Then: Should include in warnings

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import PreflightPanel

        # Create large file (simulate)
        large_file = tmp_path / "huge_report.xlsx"
        large_file.write_bytes(b"x" * (10 * 1024 * 1024))  # 10MB

        panel = PreflightPanel()
        analysis = panel.analyze([large_file])

        assert len(analysis.warnings) > 0
        assert any("huge_report.xlsx" in w for w in analysis.warnings)

    @pytest.mark.unit
    @pytest.mark.story_5_3
    @pytest.mark.panels
    def test_preflight_detects_empty_files(self, tmp_path):
        """
        RED: PreflightPanel detects and warns about empty files.

        Given: An empty file
        When: Analyzing
        Then: Should include in warnings

        Expected RED failure: ModuleNotFoundError
        """
        from data_extract.cli.components.panels import PreflightPanel

        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        panel = PreflightPanel()
        analysis = panel.analyze([empty_file])

        assert len(analysis.warnings) > 0
        assert any("empty" in w.lower() for w in analysis.warnings)
