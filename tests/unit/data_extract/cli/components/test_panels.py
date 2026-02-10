"""Unit tests for CLI panel components."""

from pathlib import Path

import pytest
from rich.panel import Panel

from data_extract.cli.components.panels import (
    LARGE_FILE_THRESHOLD,
    PreflightPanel,
    PreflightResult,
    QualityDashboard,
    QualityMetrics,
)

pytestmark = [pytest.mark.P1, pytest.mark.unit]


class TestPreflightResult:
    """Tests for PreflightResult dataclass."""

    def test_initialization_defaults(self):
        """Test PreflightResult initialization with defaults."""
        result = PreflightResult()
        assert result.file_count == 0
        assert result.type_distribution == {}
        assert result.total_size_bytes == 0
        assert result.issues == []
        assert result.estimated_time_seconds == 0.0

    def test_initialization_with_values(self):
        """Test PreflightResult initialization with values."""
        result = PreflightResult(
            file_count=5,
            type_distribution={".pdf": 3, ".docx": 2},
            total_size_bytes=1024000,
            issues=["Warning: Large file"],
            estimated_time_seconds=10.5,
        )
        assert result.file_count == 5
        assert result.type_distribution == {".pdf": 3, ".docx": 2}
        assert result.total_size_bytes == 1024000
        assert len(result.issues) == 1
        assert result.estimated_time_seconds == 10.5

    def test_warnings_alias(self):
        """Test that warnings property aliases issues."""
        result = PreflightResult(issues=["Issue 1", "Issue 2"])
        assert result.warnings == result.issues
        assert len(result.warnings) == 2

    def test_contains_operator(self):
        """Test __contains__ for dict-like access."""
        result = PreflightResult()
        assert "file_count" in result
        assert "type_distribution" in result
        assert "nonexistent_field" not in result


class TestPreflightPanel:
    """Tests for PreflightPanel class."""

    def test_initialization(self, mock_console):
        """Test PreflightPanel initialization."""
        output_dir = Path("/tmp/output")
        panel = PreflightPanel(output_dir=output_dir, console=mock_console)
        assert panel._output_dir == output_dir
        assert panel._console is mock_console

    def test_initialization_no_output_dir(self, mock_console):
        """Test PreflightPanel initialization without output directory."""
        panel = PreflightPanel(console=mock_console)
        assert panel._output_dir is None

    def test_analyze_empty_files(self, mock_console):
        """Test analyze with empty file list."""
        panel = PreflightPanel(console=mock_console)
        result = panel.analyze([])

        assert result.file_count == 0
        assert result.type_distribution == {}
        assert result.total_size_bytes == 0
        assert result.issues == []

    def test_analyze_files(self, tmp_path, mock_console):
        """Test analyze with actual files."""
        # Create test files
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"PDF content" * 100)

        docx_file = tmp_path / "test.docx"
        docx_file.write_bytes(b"DOCX content" * 50)

        panel = PreflightPanel(console=mock_console)
        result = panel.analyze([pdf_file, docx_file])

        assert result.file_count == 2
        assert ".pdf" in result.type_distribution
        assert ".docx" in result.type_distribution
        assert result.total_size_bytes > 0

    def test_analyze_type_distribution(self, tmp_path, mock_console):
        """Test that analyze correctly counts file types."""
        files = []
        for i in range(3):
            pdf = tmp_path / f"file{i}.pdf"
            pdf.touch()
            files.append(pdf)

        for i in range(2):
            docx = tmp_path / f"doc{i}.docx"
            docx.touch()
            files.append(docx)

        panel = PreflightPanel(console=mock_console)
        result = panel.analyze(files)

        assert result.type_distribution[".pdf"] == 3
        assert result.type_distribution[".docx"] == 2

    def test_analyze_large_file_warning(self, tmp_path, mock_console):
        """Test that large files generate warnings."""
        large_file = tmp_path / "large.pdf"
        large_file.write_bytes(b"X" * (LARGE_FILE_THRESHOLD + 1000))

        panel = PreflightPanel(console=mock_console)
        result = panel.analyze([large_file])

        assert len(result.issues) > 0
        assert any("Large file warning" in issue for issue in result.issues)

    def test_analyze_empty_file_warning(self, tmp_path, mock_console):
        """Test that empty files generate warnings."""
        empty_file = tmp_path / "empty.pdf"
        empty_file.touch()

        panel = PreflightPanel(console=mock_console)
        result = panel.analyze([empty_file])

        assert len(result.issues) > 0
        assert any("Empty file warning" in issue for issue in result.issues)

    def test_analyze_time_estimation(self, tmp_path, mock_console):
        """Test time estimation for different file types."""
        pdf = tmp_path / "test.pdf"
        pdf.touch()
        txt = tmp_path / "test.txt"
        txt.touch()

        panel = PreflightPanel(console=mock_console)
        result = panel.analyze([pdf, txt])

        # PDF (2s) + TXT (0.2s) = 2.2s
        assert result.estimated_time_seconds > 0

    def test_analyze_unknown_extension(self, tmp_path, mock_console):
        """Test handling files with no extension."""
        no_ext = tmp_path / "noextension"
        no_ext.touch()

        panel = PreflightPanel(console=mock_console)
        result = panel.analyze([no_ext])

        assert ".unknown" in result.type_distribution

    def test_analyze_string_paths(self, tmp_path, mock_console):
        """Test analyze with string paths instead of Path objects."""
        pdf = tmp_path / "test.pdf"
        pdf.touch()

        panel = PreflightPanel(console=mock_console)
        result = panel.analyze([str(pdf)])

        assert result.file_count == 1

    def test_render_returns_panel(self, mock_console):
        """Test that render returns a Rich Panel."""
        panel = PreflightPanel(console=mock_console)
        result = PreflightResult(file_count=5, type_distribution={".pdf": 5})

        rendered = panel.render(result)
        assert isinstance(rendered, Panel)

    def test_render_with_stored_result(self, mock_console):
        """Test render uses stored result if none provided."""
        panel = PreflightPanel(console=mock_console)
        panel.analyze([])  # Store a result

        rendered = panel.render()
        assert isinstance(rendered, Panel)

    def test_render_content_includes_file_count(self, string_console):
        """Test that rendered panel includes file count."""
        panel = PreflightPanel(console=string_console)
        result = PreflightResult(file_count=10)

        rendered = panel.render(result)
        # Convert panel to string for inspection
        string_console.print(rendered)
        output = string_console._test_buffer.getvalue()

        assert "10 documents" in output or "Files:" in output

    def test_render_content_includes_type_distribution(self, string_console):
        """Test that rendered panel includes type distribution."""
        panel = PreflightPanel(console=string_console)
        result = PreflightResult(
            file_count=5,
            type_distribution={".pdf": 3, ".docx": 2},
        )

        rendered = panel.render(result)
        string_console.print(rendered)
        output = string_console._test_buffer.getvalue()

        assert "PDF" in output
        assert "DOCX" in output

    def test_render_content_includes_warnings(self, string_console):
        """Test that rendered panel includes warnings."""
        panel = PreflightPanel(console=string_console)
        result = PreflightResult(
            file_count=1,
            issues=["Warning: Large file detected"],
        )

        rendered = panel.render(result)
        string_console.print(rendered)
        output = string_console._test_buffer.getvalue()

        assert "Warnings" in output
        assert "Large file" in output

    def test_render_content_includes_output_dir(self, string_console):
        """Test that rendered panel includes output directory."""
        output_dir = Path("/tmp/output")
        panel = PreflightPanel(output_dir=output_dir, console=string_console)
        result = PreflightResult(file_count=1)

        rendered = panel.render(result)
        string_console.print(rendered)
        output = string_console._test_buffer.getvalue()

        assert "output" in output.lower()


class TestQualityMetrics:
    """Tests for QualityMetrics dataclass."""

    def test_initialization_defaults(self):
        """Test QualityMetrics initialization with defaults."""
        metrics = QualityMetrics()
        assert metrics.total_files == 0
        assert metrics.successful_files == 0
        assert metrics.failed_files == 0
        assert metrics.excellent_count == 0
        assert metrics.good_count == 0
        assert metrics.needs_review_count == 0
        assert metrics.suggestions == []
        assert metrics.learning_tip == ""

    def test_initialization_with_values(self):
        """Test QualityMetrics initialization with values."""
        metrics = QualityMetrics(
            total_files=10,
            successful_files=9,
            failed_files=1,
            excellent_count=5,
            good_count=3,
            needs_review_count=1,
            suggestions=["Suggestion 1"],
            learning_tip="Tip",
        )
        assert metrics.total_files == 10
        assert metrics.successful_files == 9
        assert metrics.failed_files == 1
        assert metrics.excellent_count == 5


class TestQualityDashboard:
    """Tests for QualityDashboard class."""

    def test_initialization_no_metrics(self, mock_console):
        """Test QualityDashboard initialization without metrics."""
        dashboard = QualityDashboard(console=mock_console)
        assert dashboard._console is mock_console

    def test_initialization_with_dict(self, mock_console):
        """Test QualityDashboard initialization with metrics dict."""
        metrics_dict = {
            "total_files": 10,
            "successful_files": 9,
            "failed_files": 1,
        }
        dashboard = QualityDashboard(metrics=metrics_dict, console=mock_console)
        assert dashboard._metrics.total_files == 10

    def test_initialization_with_quality_metrics(self, mock_console):
        """Test QualityDashboard initialization with QualityMetrics object."""
        metrics = QualityMetrics(total_files=5, successful_files=5)
        dashboard = QualityDashboard(metrics=metrics, console=mock_console)
        assert dashboard._metrics.total_files == 5

    def test_parse_metrics_dict(self, mock_console):
        """Test _parse_metrics with dictionary."""
        dashboard = QualityDashboard(console=mock_console)
        metrics_dict = {
            "total_files": 20,
            "successful_files": 18,
            "excellent_count": 10,
        }
        parsed = dashboard._parse_metrics(metrics_dict)
        assert parsed.total_files == 20
        assert parsed.successful_files == 18
        assert parsed.excellent_count == 10

    def test_parse_metrics_none(self, mock_console):
        """Test _parse_metrics with None."""
        dashboard = QualityDashboard(console=mock_console)
        parsed = dashboard._parse_metrics(None)
        assert isinstance(parsed, QualityMetrics)
        assert parsed.total_files == 0

    def test_parse_metrics_quality_metrics(self, mock_console):
        """Test _parse_metrics with QualityMetrics object."""
        dashboard = QualityDashboard(console=mock_console)
        metrics = QualityMetrics(total_files=15)
        parsed = dashboard._parse_metrics(metrics)
        assert parsed is metrics

    def test_parse_metrics_dataclass_like(self, mock_console):
        """Test _parse_metrics with dataclass-like object."""

        class FakeMetrics:
            total_files = 10
            successful_files = 8
            failed_files = 2
            excellent_count = 5
            good_count = 3
            needs_review_count = 0
            suggestions = []
            learning_tip = "Test tip"

        dashboard = QualityDashboard(console=mock_console)
        fake = FakeMetrics()
        parsed = dashboard._parse_metrics(fake)
        assert parsed.total_files == 10

    def test_render_returns_panel(self, mock_console):
        """Test that render returns a Rich Panel."""
        dashboard = QualityDashboard(console=mock_console)
        rendered = dashboard.render()
        assert isinstance(rendered, Panel)

    def test_render_with_new_metrics(self, mock_console):
        """Test render with new metrics dict."""
        dashboard = QualityDashboard(console=mock_console)
        metrics_dict = {"total_files": 5, "successful_files": 5}

        rendered = dashboard.render(metrics=metrics_dict)
        assert isinstance(rendered, Panel)

    def test_render_no_files_processed(self, string_console):
        """Test rendering with no files processed."""
        dashboard = QualityDashboard(console=string_console)
        rendered = dashboard.render()

        string_console.print(rendered)
        output = string_console._test_buffer.getvalue()

        assert "No files processed" in output

    def test_render_success_summary(self, string_console):
        """Test rendering success summary."""
        metrics = QualityMetrics(total_files=10, successful_files=10, failed_files=0)
        dashboard = QualityDashboard(metrics=metrics, console=string_console)
        rendered = dashboard.render()

        string_console.print(rendered)
        output = string_console._test_buffer.getvalue()

        assert "10/10" in output
        assert "successfully" in output.lower()

    def test_render_with_failures(self, string_console):
        """Test rendering with failed files."""
        metrics = QualityMetrics(total_files=10, successful_files=8, failed_files=2)
        dashboard = QualityDashboard(metrics=metrics, console=string_console)
        rendered = dashboard.render()

        string_console.print(rendered)
        output = string_console._test_buffer.getvalue()

        assert "8/10" in output
        assert "2 failed" in output

    def test_render_quality_distribution(self, string_console):
        """Test rendering quality distribution bars."""
        metrics = QualityMetrics(
            total_files=10,
            successful_files=10,
            excellent_count=5,
            good_count=3,
            needs_review_count=2,
        )
        dashboard = QualityDashboard(metrics=metrics, console=string_console)
        rendered = dashboard.render()

        string_console.print(rendered)
        output = string_console._test_buffer.getvalue()

        assert "Quality Distribution" in output
        assert "Excellent" in output
        assert "Good" in output
        assert "Needs Review" in output

    def test_render_suggestions(self, string_console):
        """Test rendering suggestions."""
        metrics = QualityMetrics(
            total_files=5,
            successful_files=5,
            suggestions=["Suggestion 1", "Suggestion 2"],
        )
        dashboard = QualityDashboard(metrics=metrics, console=string_console)
        rendered = dashboard.render()

        string_console.print(rendered)
        output = string_console._test_buffer.getvalue()

        assert "Suggestions" in output
        assert "Suggestion 1" in output
        assert "Suggestion 2" in output

    def test_render_learning_tip(self, string_console):
        """Test rendering learning tip."""
        metrics = QualityMetrics(
            total_files=5,
            successful_files=5,
            learning_tip="This is a helpful tip",
        )
        dashboard = QualityDashboard(metrics=metrics, console=string_console)
        rendered = dashboard.render()

        string_console.print(rendered)
        output = string_console._test_buffer.getvalue()

        assert "Learn more" in output
        assert "helpful tip" in output

    def test_make_bar(self, mock_console):
        """Test _make_bar creates text-based progress bar."""
        dashboard = QualityDashboard(console=mock_console)

        # 50% bar
        bar = dashboard._make_bar(50.0, width=10)
        bar_str = str(bar)
        assert "50.0%" in bar_str
        assert "=====" in bar_str  # 5 filled characters
        assert "-----" in bar_str  # 5 empty characters

        # 0% bar
        bar_zero = dashboard._make_bar(0.0, width=10)
        bar_zero_str = str(bar_zero)
        assert "0.0%" in bar_zero_str

        # 100% bar
        bar_full = dashboard._make_bar(100.0, width=10)
        bar_full_str = str(bar_full)
        assert "100.0%" in bar_full_str
        assert "==========" in bar_full_str  # All filled

    def test_render_dedupe_suggestion_highlighted(self, string_console):
        """Test that dedupe suggestions are highlighted."""
        metrics = QualityMetrics(
            total_files=5,
            successful_files=5,
            suggestions=["Run dedupe command to remove duplicates"],
        )
        dashboard = QualityDashboard(metrics=metrics, console=string_console)
        rendered = dashboard.render()

        string_console.print(rendered)
        output = string_console._test_buffer.getvalue()

        assert "dedupe" in output.lower()


class TestPanelIntegration:
    """Integration tests for panel components."""

    def test_preflight_panel_full_workflow(self, tmp_path, string_console):
        """Test complete PreflightPanel workflow."""
        # Create test files
        files = []
        for i in range(3):
            pdf = tmp_path / f"test{i}.pdf"
            pdf.write_bytes(b"Content" * 100)
            files.append(pdf)

        # Analyze and render
        panel = PreflightPanel(output_dir=tmp_path / "output", console=string_console)
        result = panel.analyze(files)
        rendered = panel.render(result)

        string_console.print(rendered)
        output = string_console._test_buffer.getvalue()

        assert result.file_count == 3
        assert "3 documents" in output or "Files:" in output

    def test_quality_dashboard_full_workflow(self, string_console):
        """Test complete QualityDashboard workflow."""
        metrics = QualityMetrics(
            total_files=20,
            successful_files=18,
            failed_files=2,
            excellent_count=12,
            good_count=5,
            needs_review_count=1,
            suggestions=["Review low-quality files"],
            learning_tip="Quality improves with better source documents",
        )

        dashboard = QualityDashboard(metrics=metrics, console=string_console)
        rendered = dashboard.render()

        string_console.print(rendered)
        output = string_console._test_buffer.getvalue()

        assert "18/20" in output
        assert "Quality Distribution" in output
        assert "Review low-quality files" in output
