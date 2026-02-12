"""Greenfield extractor performance benchmarks and baseline regression checks."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from data_extract.extract import get_extractor
from tests.performance.conftest import (
    BaselineManager,
    BenchmarkResult,
    PerformanceMeasurement,
    assert_memory_limit,
    assert_performance_target,
)

pytestmark = [
    pytest.mark.P1,
    pytest.mark.performance,
]

BASELINE_FILE = Path(__file__).parent / "baselines.json"
REGRESSION_THRESHOLD = 1.0
MEMORY_BASELINE_FLOOR_MB = 50.0
DURATION_BASELINE_FLOOR_MS = 1000.0


def _benchmark_extraction(operation: str, file_path: Path) -> BenchmarkResult:
    adapter = get_extractor(file_path)

    with PerformanceMeasurement() as perf:
        document = adapter.process(file_path)

    assert document.text is not None

    size_kb = file_path.stat().st_size / 1024
    throughput = size_kb / perf.duration_seconds if perf.duration_seconds > 0 else 0.0
    return BenchmarkResult(
        operation=operation,
        duration_ms=perf.duration_ms,
        memory_mb=perf.peak_memory_mb,
        file_size_kb=size_kb,
        throughput=throughput,
        timestamp=datetime.now().isoformat(),
        metadata={"file_name": file_path.name, "chars": len(document.text)},
    )


def _assert_no_regression(operation: str, benchmark: BenchmarkResult) -> None:
    manager = BaselineManager(BASELINE_FILE)
    comparison = manager.compare(operation, benchmark, threshold=REGRESSION_THRESHOLD)
    if not comparison["has_baseline"]:
        return

    baseline_duration = comparison["baseline_duration_ms"]
    if baseline_duration >= DURATION_BASELINE_FLOOR_MS and comparison["duration_change_pct"] > (
        REGRESSION_THRESHOLD * 100
    ):
        raise AssertionError(
            f"{operation} regression detected: "
            f"duration_change={comparison['duration_change_pct']:.2f}% "
            f"(baseline={baseline_duration:.2f}ms)"
        )

    baseline_memory = comparison["baseline_memory_mb"]
    if baseline_memory >= MEMORY_BASELINE_FLOOR_MB and comparison["memory_change_pct"] > (
        REGRESSION_THRESHOLD * 100
    ):
        raise AssertionError(
            f"{operation} memory regression detected: "
            f"memory_change={comparison['memory_change_pct']:.2f}% "
            f"(baseline={baseline_memory:.2f}MB)"
        )


class TestExtractorBenchmarks:
    """Performance checks for current greenfield extractors."""

    def test_txt_small_file_performance(self, fixture_dir: Path) -> None:
        txt_file = fixture_dir / "sample.txt"
        benchmark = _benchmark_extraction("txt_extract_small", txt_file)

        assert_performance_target(
            benchmark.duration_ms, 100.0, "TXT small extraction", tolerance=1.0
        )
        assert_memory_limit(benchmark.memory_mb, 128.0, "TXT small extraction")
        _assert_no_regression("txt_extract_small", benchmark)

    def test_excel_small_file_performance(self, fixture_dir: Path) -> None:
        excel_file = fixture_dir / "excel" / "simple_single_sheet.xlsx"
        benchmark = _benchmark_extraction("excel_extract_small", excel_file)

        assert_performance_target(
            benchmark.duration_ms,
            2000.0,
            "Excel small extraction",
            tolerance=1.0,
        )
        assert_memory_limit(benchmark.memory_mb, 512.0, "Excel small extraction")
        _assert_no_regression("excel_extract_small", benchmark)

    @pytest.mark.slow
    def test_pdf_small_file_performance(self, fixture_dir: Path) -> None:
        pdf_file = fixture_dir / "pdfs" / "sample.pdf"
        benchmark = _benchmark_extraction("pdf_small", pdf_file)

        assert_performance_target(
            benchmark.duration_ms,
            60000.0,
            "PDF small extraction",
            tolerance=1.0,
        )
        assert_memory_limit(benchmark.memory_mb, 1500.0, "PDF small extraction", tolerance=0.2)
        _assert_no_regression("pdf_small", benchmark)

    def test_docx_small_file_performance(self, fixture_dir: Path) -> None:
        docx_file = fixture_dir / "docx" / "sample.docx"
        benchmark = _benchmark_extraction("docx_extract_small", docx_file)

        assert_performance_target(
            benchmark.duration_ms,
            5000.0,
            "DOCX small extraction",
            tolerance=1.0,
        )
        assert_memory_limit(benchmark.memory_mb, 256.0, "DOCX small extraction")

    def test_pptx_small_file_performance(self, fixture_dir: Path) -> None:
        pptx_file = fixture_dir / "test_with_images.pptx"
        benchmark = _benchmark_extraction("pptx_extract_small", pptx_file)

        assert_performance_target(
            benchmark.duration_ms,
            10000.0,
            "PPTX small extraction",
            tolerance=1.0,
        )
        assert_memory_limit(benchmark.memory_mb, 512.0, "PPTX small extraction")
