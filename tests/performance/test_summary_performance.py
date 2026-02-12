"""Performance tests for summary report generation (Story 5-4)."""

from __future__ import annotations

import json
import time
import tracemalloc
from pathlib import Path

import pytest
from rich.console import Console

from data_extract.cli.summary import (
    ExportFormat,
    QualityMetrics,
    SummaryReport,
    export_summary,
    export_summary_parallel,
    iter_summary_sections,
    render_quality_dashboard,
    render_summary_panel,
    render_timing_breakdown,
)

pytestmark = [
    pytest.mark.P2,
    pytest.mark.performance,
    pytest.mark.story_5_4,
    pytest.mark.slow,
]


def _measure_total_ms(fn, iterations: int = 1) -> float:
    start = time.perf_counter()
    for _ in range(iterations):
        fn()
    return (time.perf_counter() - start) * 1000


@pytest.fixture
def medium_summary_report() -> SummaryReport:
    """Create medium-scale summary report."""
    return SummaryReport(
        files_processed=10,
        files_failed=1,
        chunks_created=1000,
        errors=("Error processing file.pdf: OCR timeout",),
        quality_metrics=QualityMetrics(
            avg_quality=0.78,
            excellent_count=500,
            good_count=350,
            review_count=100,
            flagged_count=50,
            entity_count=5000,
            readability_score=68.5,
            duplicate_percentage=3.2,
        ),
        timing={
            "extract": 500.5,
            "normalize": 200.2,
            "chunk": 300.8,
            "semantic": 800.1,
            "output": 150.4,
        },
        config={
            "max_features": 5000,
            "similarity_threshold": 0.95,
            "n_components": 100,
            "quality_min_score": 0.3,
        },
        next_steps=("Review 50 flagged items", "Analyze cluster quality"),
    )


@pytest.fixture
def large_summary_report() -> SummaryReport:
    """Create large summary report for performance testing."""
    return SummaryReport(
        files_processed=100,
        files_failed=3,
        chunks_created=10000,
        errors=tuple(f"Error processing file{i}.pdf: OCR timeout" for i in range(250)),
        quality_metrics=QualityMetrics(
            avg_quality=0.75,
            excellent_count=5000,
            good_count=3500,
            review_count=1200,
            flagged_count=300,
            entity_count=50000,
            readability_score=65.5,
            duplicate_percentage=8.7,
        ),
        timing={
            "extract": 5000.5,
            "normalize": 2000.2,
            "chunk": 3000.8,
            "semantic": 8000.1,
            "output": 1500.4,
        },
        config={
            "max_features": 5000,
            "similarity_threshold": 0.95,
            "n_components": 100,
            "quality_min_score": 0.3,
            "chunk_size": 512,
            "overlap": 128,
        },
        next_steps=tuple(f"Review {i} flagged items" for i in [300, 250, 200, 150, 100]),
    )


class TestSummaryGenerationPerformance:
    """Test performance of real summary rendering primitives."""

    def test_summary_panel_render_under_100ms(self, medium_summary_report: SummaryReport) -> None:
        console = Console(width=120, record=False)

        # Warm-up for Rich internals.
        console.print(render_summary_panel(medium_summary_report))

        elapsed_ms = _measure_total_ms(
            lambda: console.print(render_summary_panel(medium_summary_report)),
            iterations=10,
        )
        assert elapsed_ms < 100.0, f"Panel render took {elapsed_ms:.2f}ms for 10 iterations"

    def test_summary_generation_large_scale_under_500ms(
        self, large_summary_report: SummaryReport
    ) -> None:
        console = Console(width=120, record=False)
        console.print(render_summary_panel(large_summary_report))

        elapsed_ms = _measure_total_ms(
            lambda: console.print(render_summary_panel(large_summary_report)),
            iterations=20,
        )
        assert elapsed_ms < 500.0, f"Large panel render took {elapsed_ms:.2f}ms for 20 iterations"

    def test_summary_rendering_under_50ms(self, medium_summary_report: SummaryReport) -> None:
        elapsed_ms = _measure_total_ms(
            lambda: (
                render_quality_dashboard(medium_summary_report.quality_metrics),
                render_timing_breakdown(medium_summary_report.timing),
            ),
            iterations=20,
        )
        assert elapsed_ms < 50.0, f"Dashboard render took {elapsed_ms:.2f}ms for 20 iterations"


class TestExportPerformance:
    """Test performance of summary export to various formats."""

    def test_json_export_under_100ms(
        self, medium_summary_report: SummaryReport, tmp_path: Path
    ) -> None:
        output_path = tmp_path / "summary.json"
        elapsed_ms = _measure_total_ms(
            lambda: export_summary(medium_summary_report, output_path, ExportFormat.JSON),
            iterations=10,
        )

        data = json.loads(output_path.read_text(encoding="utf-8"))
        assert data["files_processed"] == 10
        assert elapsed_ms < 100.0, f"JSON export took {elapsed_ms:.2f}ms for 10 iterations"

    def test_json_export_large_scale_under_300ms(
        self, large_summary_report: SummaryReport, tmp_path: Path
    ) -> None:
        output_path = tmp_path / "large_summary.json"
        elapsed_ms = _measure_total_ms(
            lambda: export_summary(large_summary_report, output_path, ExportFormat.JSON),
            iterations=20,
        )

        assert output_path.exists()
        assert elapsed_ms < 300.0, f"Large JSON export took {elapsed_ms:.2f}ms for 20 iterations"

    def test_html_export_under_500ms(
        self, medium_summary_report: SummaryReport, tmp_path: Path
    ) -> None:
        output_path = tmp_path / "summary.html"
        elapsed_ms = _measure_total_ms(
            lambda: export_summary(medium_summary_report, output_path, ExportFormat.HTML),
            iterations=20,
        )

        content = output_path.read_text(encoding="utf-8")
        assert "Processing Summary Report" in content
        assert elapsed_ms < 500.0, f"HTML export took {elapsed_ms:.2f}ms for 20 iterations"

    def test_txt_export_under_100ms(
        self, medium_summary_report: SummaryReport, tmp_path: Path
    ) -> None:
        output_path = tmp_path / "summary.txt"
        elapsed_ms = _measure_total_ms(
            lambda: export_summary(medium_summary_report, output_path, ExportFormat.TXT),
            iterations=20,
        )

        content = output_path.read_text(encoding="utf-8")
        assert "PROCESSING SUMMARY REPORT" in content
        assert elapsed_ms < 100.0, f"TXT export took {elapsed_ms:.2f}ms for 20 iterations"


class TestMemoryUsage:
    """Test memory usage during summary operations."""

    def test_export_memory_usage_under_50mb(
        self, medium_summary_report: SummaryReport, tmp_path: Path
    ) -> None:
        tracemalloc.start()
        export_summary(medium_summary_report, tmp_path / "summary.json", ExportFormat.JSON)
        export_summary(medium_summary_report, tmp_path / "summary.html", ExportFormat.HTML)
        export_summary(medium_summary_report, tmp_path / "summary.txt", ExportFormat.TXT)
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak_bytes / 1024 / 1024
        assert peak_mb < 50.0, f"Peak export memory {peak_mb:.2f}MB exceeded 50MB"

    def test_large_scale_export_memory_reasonable(
        self, large_summary_report: SummaryReport, tmp_path: Path
    ) -> None:
        tracemalloc.start()
        export_summary(large_summary_report, tmp_path / "large_summary.html", ExportFormat.HTML)
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak_bytes / 1024 / 1024
        assert peak_mb < 64.0, f"Large HTML export peak memory {peak_mb:.2f}MB exceeded 64MB"


class TestConcurrentExport:
    """Test performance with concurrent export operations."""

    def test_multiple_format_exports_under_1s(
        self, medium_summary_report: SummaryReport, tmp_path: Path
    ) -> None:
        start = time.perf_counter()
        output = export_summary_parallel(
            medium_summary_report,
            tmp_path,
            formats=[ExportFormat.JSON, ExportFormat.HTML, ExportFormat.TXT],
            max_workers=3,
        )
        elapsed_s = time.perf_counter() - start

        assert set(output.keys()) == {ExportFormat.JSON, ExportFormat.HTML, ExportFormat.TXT}
        assert all(path.exists() for path in output.values())
        assert elapsed_s < 1.0, f"Parallel export took {elapsed_s:.3f}s"


class TestScalability:
    """Test how summary generation scales with data size."""

    def test_summary_generation_scales_linearly(
        self,
        medium_summary_report: SummaryReport,
        large_summary_report: SummaryReport,
    ) -> None:
        time_med_ms = _measure_total_ms(
            lambda: render_summary_panel(medium_summary_report), iterations=500
        )
        time_large_ms = _measure_total_ms(
            lambda: render_summary_panel(large_summary_report), iterations=500
        )

        ratio = time_large_ms / time_med_ms if time_med_ms > 0 else 1.0
        assert 0.5 <= ratio <= 20.0, f"Scaling ratio {ratio:.2f}x out of expected range"

    def test_export_memory_scales_linearly(
        self,
        medium_summary_report: SummaryReport,
        large_summary_report: SummaryReport,
        tmp_path: Path,
    ) -> None:
        medium_path = tmp_path / "medium.json"
        large_path = tmp_path / "large.json"

        export_summary(medium_summary_report, medium_path, ExportFormat.JSON)
        export_summary(large_summary_report, large_path, ExportFormat.JSON)

        medium_size = medium_path.stat().st_size
        large_size = large_path.stat().st_size

        assert large_size > medium_size, "Large summary JSON should be bigger"
        assert large_size / medium_size > 2.0, "Large summary should be at least 2x bigger"


class TestOutputFormatPerformance:
    """Test performance characteristics of different output formats."""

    def test_json_fastest_format(
        self, medium_summary_report: SummaryReport, tmp_path: Path
    ) -> None:
        json_path = tmp_path / "summary.json"
        txt_path = tmp_path / "summary.txt"

        time_json_ms = _measure_total_ms(
            lambda: export_summary(medium_summary_report, json_path, ExportFormat.JSON),
            iterations=25,
        )
        time_txt_ms = _measure_total_ms(
            lambda: export_summary(medium_summary_report, txt_path, ExportFormat.TXT),
            iterations=25,
        )

        assert time_json_ms <= time_txt_ms * 4.0, "JSON should remain in the same order as TXT"

    def test_html_generation_efficiency(
        self,
        medium_summary_report: SummaryReport,
        tmp_path: Path,
    ) -> None:
        html_path = tmp_path / "summary.html"
        elapsed_ms = _measure_total_ms(
            lambda: export_summary(medium_summary_report, html_path, ExportFormat.HTML),
            iterations=25,
        )

        assert html_path.exists()
        assert elapsed_ms < 500.0, f"HTML generation took {elapsed_ms:.2f}ms"


class TestPerformanceOptimizations:
    """Performance optimization checks for summary rendering/export."""

    def test_cached_summary_rendering(self, medium_summary_report: SummaryReport) -> None:
        # Warm-up pass to stabilize imports and Rich internals.
        render_summary_panel(medium_summary_report)
        console = Console(width=120, record=False)
        console.print(render_summary_panel(medium_summary_report))

        elapsed_ms = _measure_total_ms(
            lambda: console.print(render_summary_panel(medium_summary_report)),
            iterations=50,
        )
        average_ms = elapsed_ms / 50

        assert average_ms < 5.0, f"Average render latency {average_ms:.3f}ms exceeded budget"

    def test_streaming_export_for_large_summaries(
        self, large_summary_report: SummaryReport
    ) -> None:
        section_iter = iter_summary_sections(large_summary_report)

        start = time.perf_counter()
        first_section = next(section_iter)
        first_section_latency_ms = (time.perf_counter() - start) * 1000

        assert "PROCESSING SUMMARY REPORT" in first_section
        assert (
            first_section_latency_ms < 10.0
        ), f"First progressive section took {first_section_latency_ms:.2f}ms"

    def test_parallel_export_formats(
        self,
        large_summary_report: SummaryReport,
        tmp_path: Path,
    ) -> None:
        output = export_summary_parallel(
            large_summary_report,
            tmp_path,
            formats=[ExportFormat.JSON, ExportFormat.HTML, ExportFormat.TXT],
            max_workers=3,
        )

        assert output[ExportFormat.JSON].exists()
        assert output[ExportFormat.HTML].exists()
        assert output[ExportFormat.TXT].exists()

    def test_progressive_summary_display(self, medium_summary_report: SummaryReport) -> None:
        sections = list(iter_summary_sections(medium_summary_report))

        assert len(sections) >= 4
        assert sections[0].startswith("=")
        assert any("QUALITY METRICS" in section for section in sections)
        assert any("TIMING BREAKDOWN" in section for section in sections)
