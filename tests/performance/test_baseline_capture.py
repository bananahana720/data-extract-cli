"""Greenfield baseline capture tests for extractor performance."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from data_extract.extract import get_extractor
from tests.performance.conftest import BaselineManager, BenchmarkResult, PerformanceMeasurement

pytestmark = [
    pytest.mark.P1,
    pytest.mark.performance,
]


def _capture_extractor_benchmark(operation: str, file_path: Path) -> BenchmarkResult:
    """Capture one benchmark result using the greenfield extractor registry."""
    adapter = get_extractor(file_path)

    with PerformanceMeasurement() as perf:
        document = adapter.process(file_path)

    file_size_kb = file_path.stat().st_size / 1024
    throughput = file_size_kb / perf.duration_seconds if perf.duration_seconds > 0 else 0.0

    metadata = {
        "file_name": file_path.name,
        "char_count": len(document.text),
    }
    page_count = document.structure.get("page_count")
    if isinstance(page_count, int):
        metadata["page_count"] = page_count

    return BenchmarkResult(
        operation=operation,
        duration_ms=perf.duration_ms,
        memory_mb=perf.peak_memory_mb,
        file_size_kb=file_size_kb,
        throughput=throughput,
        timestamp=datetime.now().isoformat(),
        metadata=metadata,
    )


def _assert_persisted_baseline(
    manager: BaselineManager,
    operation: str,
    benchmark: BenchmarkResult,
) -> None:
    manager.update_baseline(operation, benchmark)
    manager.save()

    reloaded = BaselineManager(manager.baseline_file)
    stored = reloaded.get_baseline(operation)

    assert stored is not None
    assert stored.operation == operation
    assert stored.duration_ms >= 0
    assert stored.memory_mb >= 0
    assert stored.file_size_kb > 0
    assert stored.throughput >= 0
    assert stored.timestamp
    assert stored.metadata["file_name"]
    assert "char_count" in stored.metadata


class TestBaselineCapture:
    """Capture and persist real extractor baselines for greenfield fixtures."""

    def test_capture_txt_baseline(
        self,
        fixture_dir: Path,
        production_baseline_manager: BaselineManager,
    ) -> None:
        txt_file = fixture_dir / "sample.txt"
        benchmark = _capture_extractor_benchmark("baseline_txt_sample", txt_file)

        assert benchmark.metadata["file_name"] == "sample.txt"
        _assert_persisted_baseline(production_baseline_manager, benchmark.operation, benchmark)

    def test_capture_excel_baseline(
        self,
        fixture_dir: Path,
        production_baseline_manager: BaselineManager,
    ) -> None:
        excel_file = fixture_dir / "excel" / "simple_single_sheet.xlsx"
        benchmark = _capture_extractor_benchmark("baseline_excel_simple", excel_file)

        assert benchmark.metadata["file_name"] == "simple_single_sheet.xlsx"
        _assert_persisted_baseline(production_baseline_manager, benchmark.operation, benchmark)

    def test_capture_docx_baseline(
        self,
        fixture_dir: Path,
        production_baseline_manager: BaselineManager,
    ) -> None:
        docx_file = fixture_dir / "docx" / "sample.docx"
        benchmark = _capture_extractor_benchmark("baseline_docx_sample", docx_file)

        assert benchmark.metadata["file_name"] == "sample.docx"
        _assert_persisted_baseline(production_baseline_manager, benchmark.operation, benchmark)

    def test_capture_pptx_baseline(
        self,
        fixture_dir: Path,
        production_baseline_manager: BaselineManager,
    ) -> None:
        pptx_file = fixture_dir / "test_with_images.pptx"
        benchmark = _capture_extractor_benchmark("baseline_pptx_images", pptx_file)

        assert benchmark.metadata["file_name"] == "test_with_images.pptx"
        _assert_persisted_baseline(production_baseline_manager, benchmark.operation, benchmark)

    def test_capture_pdf_baseline_roundtrip(
        self,
        fixture_dir: Path,
        production_baseline_manager: BaselineManager,
    ) -> None:
        pdf_file = fixture_dir / "pdfs" / "sample.pdf"
        benchmark = _capture_extractor_benchmark("baseline_pdf_sample", pdf_file)

        _assert_persisted_baseline(production_baseline_manager, benchmark.operation, benchmark)

        persisted = production_baseline_manager.baseline_file.read_text(encoding="utf-8")
        assert "baseline_pdf_sample" in persisted
        assert '"duration_ms"' in persisted
        assert '"memory_mb"' in persisted
        assert '"throughput"' in persisted
        assert '"timestamp"' in persisted
