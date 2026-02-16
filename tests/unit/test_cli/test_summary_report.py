"""Unit tests for CLI summary reporting utilities."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from data_extract.cli.summary import (
    ExportFormat,
    QualityMetrics,
    StageName,
    StageTimer,
    SummaryReport,
    export_summary,
    export_summary_parallel,
    iter_summary_sections,
    render_next_steps,
    render_quality_dashboard,
    render_summary_panel,
    render_timing_breakdown,
)

pytestmark = [
    pytest.mark.P1,
    pytest.mark.story_5_4,
    pytest.mark.unit,
    pytest.mark.cli,
]


@pytest.fixture
def quality_metrics() -> QualityMetrics:
    return QualityMetrics(
        avg_quality=0.81,
        excellent_count=5,
        good_count=3,
        review_count=2,
        flagged_count=1,
        entity_count=17,
        readability_score=64.2,
        duplicate_percentage=12.5,
    )


@pytest.fixture
def summary_report(quality_metrics: QualityMetrics) -> SummaryReport:
    return SummaryReport(
        files_processed=8,
        files_failed=2,
        chunks_created=42,
        errors=("failure-a", "failure-b"),
        quality_metrics=quality_metrics,
        timing={
            "extract": 180.0,
            "normalize": 60.0,
            "chunk": 220.0,
            "semantic": 140.0,
            "output": 30.0,
        },
        config={"chunk_size": 512},
        next_steps=("retry failed files", "review quality dashboard"),
        processing_duration_ms=630.0,
    )


def _render_text(renderable: object) -> str:
    console = Console(record=True, width=120, force_terminal=False, color_system=None)
    console.print(renderable)
    return console.export_text()


class TestDataModels:
    def test_quality_metrics_distribution_and_total(self, quality_metrics: QualityMetrics) -> None:
        assert quality_metrics.total_count == 10
        distribution = quality_metrics.get_distribution()
        assert distribution["excellent"] == pytest.approx(50.0)
        assert distribution["good"] == pytest.approx(30.0)
        assert distribution["review"] == pytest.approx(20.0)

    def test_quality_metrics_distribution_zero_total(self) -> None:
        metrics = QualityMetrics(
            avg_quality=0.0,
            excellent_count=0,
            good_count=0,
            review_count=0,
            flagged_count=0,
            entity_count=0,
            readability_score=0.0,
        )
        assert metrics.get_distribution() == {"excellent": 0.0, "good": 0.0, "review": 0.0}

    def test_summary_report_is_frozen(self, summary_report: SummaryReport) -> None:
        with pytest.raises(FrozenInstanceError):
            summary_report.files_processed = 99  # type: ignore[misc]

    def test_stage_name_and_export_format_values(self) -> None:
        assert [stage.value for stage in StageName] == [
            "extract",
            "normalize",
            "chunk",
            "semantic",
            "output",
        ]
        assert [fmt.value for fmt in ExportFormat] == ["txt", "json", "html"]


class TestStageTimer:
    def test_stop_without_start_returns_zero(self) -> None:
        timer = StageTimer(StageName.EXTRACT)
        assert timer.stop() == 0.0
        assert timer.elapsed() == 0.0
        assert timer.format_duration() == "0ms"

    def test_stop_after_start_records_elapsed(self) -> None:
        timer = StageTimer(StageName.CHUNK)
        timer.start()
        elapsed = timer.stop()
        assert elapsed >= 0.0
        assert timer.elapsed() == elapsed

    def test_format_duration_for_seconds_and_milliseconds(self) -> None:
        timer = StageTimer(StageName.SEMANTIC)
        timer._elapsed_ms = 150.0  # noqa: SLF001 - targeted formatting coverage
        assert timer.format_duration().endswith("ms")
        timer._elapsed_ms = 1500.0  # noqa: SLF001 - targeted formatting coverage
        assert timer.format_duration().endswith("s")


class TestRenderFunctions:
    def test_render_summary_panel_contains_core_fields(self, summary_report: SummaryReport) -> None:
        panel = render_summary_panel(summary_report)
        assert isinstance(panel, Panel)
        assert panel.title == "Processing Summary"
        assert panel.border_style == "yellow"
        output = _render_text(panel)
        assert "Files:" in output
        assert "Chunks:" in output
        assert "Processing time:" in output
        assert "Errors:" in output
        assert "Next Steps:" in output

    def test_render_summary_panel_limits_error_lines(self, quality_metrics: QualityMetrics) -> None:
        report = SummaryReport(
            files_processed=0,
            files_failed=7,
            chunks_created=0,
            errors=tuple(f"error-{i}" for i in range(7)),
            quality_metrics=quality_metrics,
            timing={},
            config={},
            next_steps=(),
        )
        output = _render_text(render_summary_panel(report))
        assert "error-0" in output
        assert "error-4" in output
        assert "and 2 more" in output

    def test_render_quality_dashboard_outputs_distribution(
        self, quality_metrics: QualityMetrics
    ) -> None:
        table = render_quality_dashboard(quality_metrics)
        assert isinstance(table, Table)
        output = _render_text(table)
        assert "Quality Distribution" in output
        assert "Excellent" in output
        assert "Good" in output
        assert "Review" in output
        assert "Total" in output
        assert "Avg: 0.81" in output

    def test_render_timing_breakdown_outputs_all_stages(
        self, summary_report: SummaryReport
    ) -> None:
        table = render_timing_breakdown(summary_report.timing)
        assert isinstance(table, Table)
        output = _render_text(table)
        for stage in ("Extract", "Normalize", "Chunk", "Semantic", "Output", "Total"):
            assert stage in output
        assert "100.0%" in output

    def test_render_next_steps_for_empty_and_non_empty(self) -> None:
        empty_output = _render_text(render_next_steps(()))
        assert "No additional steps required." in empty_output
        steps_output = _render_text(render_next_steps(("step one", "step two")))
        assert "step one" in steps_output
        assert "step two" in steps_output

    def test_render_respects_no_color_ascii_box(
        self, summary_report: SummaryReport, monkeypatch
    ) -> None:
        monkeypatch.setenv("NO_COLOR", "1")
        panel = render_summary_panel(summary_report)
        assert panel.box is box.ASCII


class TestExportFunctions:
    def test_iter_summary_sections_contains_expected_sections(
        self, summary_report: SummaryReport
    ) -> None:
        sections = list(iter_summary_sections(summary_report))
        assert len(sections) >= 4
        assert "PROCESSING SUMMARY REPORT" in sections[0]
        assert any("QUALITY METRICS" in section for section in sections)
        assert any("TIMING BREAKDOWN" in section for section in sections)
        assert any("NEXT STEPS" in section for section in sections)

    def test_export_summary_txt_json_html(self, summary_report: SummaryReport, tmp_path) -> None:
        txt_path = export_summary(summary_report, tmp_path / "summary.txt", ExportFormat.TXT)
        json_path = export_summary(summary_report, tmp_path / "summary.json", ExportFormat.JSON)
        html_path = export_summary(summary_report, tmp_path / "summary.html", ExportFormat.HTML)

        assert txt_path.exists()
        assert "PROCESSING SUMMARY REPORT" in txt_path.read_text()

        data = json.loads(json_path.read_text())
        assert data["files_processed"] == 8
        assert data["quality_metrics"]["distribution"]["excellent"] == pytest.approx(50.0)

        html = html_path.read_text()
        assert "<!DOCTYPE html>" in html
        assert "Processing Summary Report" in html

    def test_export_html_escapes_error_content(self, tmp_path) -> None:
        report = SummaryReport(
            files_processed=1,
            files_failed=1,
            chunks_created=1,
            errors=("<script>alert('x')</script>",),
            quality_metrics=None,
            timing={"extract": 10.0},
            config={},
            next_steps=(),
        )
        html_path = export_summary(report, tmp_path / "escaped.html", ExportFormat.HTML)
        html = html_path.read_text()
        assert "<script>alert('x')</script>" not in html
        assert "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;" in html

    def test_export_summary_parallel_deduplicates_formats(
        self, summary_report: SummaryReport, tmp_path
    ) -> None:
        exported = export_summary_parallel(
            summary_report,
            tmp_path / "exports",
            [ExportFormat.JSON, ExportFormat.JSON, ExportFormat.TXT],
            max_workers=5,
        )
        assert set(exported.keys()) == {ExportFormat.JSON, ExportFormat.TXT}
        assert exported[ExportFormat.JSON].exists()
        assert exported[ExportFormat.TXT].exists()
