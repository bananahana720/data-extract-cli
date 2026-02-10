"""Performance benchmarks for JsonFormatter (Story 3.4)."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import pytest

pytestmark = [
    pytest.mark.P2,
    pytest.mark.performance,
]

from data_extract.chunk.engine import ChunkingConfig, ChunkingEngine  # noqa: E402
from data_extract.core.models import Chunk  # noqa: E402
from data_extract.output.formatters.json_formatter import JsonFormatter  # noqa: E402
from tests.performance.conftest import PerformanceMeasurement  # noqa: E402


@pytest.fixture(scope="session")
def chunking_engine() -> ChunkingEngine:
    """Provide a shared ChunkingEngine instance for performance tests."""
    return ChunkingEngine(ChunkingConfig(chunk_size=512, overlap_pct=0.15))


@pytest.fixture
def base_chunks(chunking_engine: ChunkingEngine, sample_processing_result) -> List[Chunk]:
    """Generate a base set of chunks from the sample processing result."""
    chunk_list = list(chunking_engine.chunk(sample_processing_result))
    assert chunk_list, "Fixture should produce at least one chunk"
    return chunk_list


def _materialize(chunks: Iterable[Chunk]) -> List[Chunk]:
    """Helper to copy chunk iterables so multiple tests can reuse the source."""
    return list(chunks)


@pytest.mark.performance
def test_json_generation_performance_100_chunks(base_chunks: List[Chunk], tmp_path: Path):
    """Benchmark JSON generation for ~100 chunks (<1 second target)."""
    formatter = JsonFormatter(validate=True)
    output_path = tmp_path / "json_100.json"
    chunk_batch = _materialize(base_chunks * 100)

    with PerformanceMeasurement() as perf:
        formatter.format_chunks(iter(chunk_batch), output_path)

    assert (
        perf.duration_seconds < 1.0
    ), f"100-chunk JSON generation took {perf.duration_seconds:.2f}s"
    assert (
        perf.peak_memory_mb < 200
    ), f"Materialization should stay well below 200MB (observed {perf.peak_memory_mb:.2f}MB)"


@pytest.mark.performance
def test_json_generation_performance_1000_chunks(base_chunks: List[Chunk], tmp_path: Path):
    """Benchmark JSON generation for ~1000 chunks (<5 seconds target)."""
    formatter = JsonFormatter(validate=True)
    output_path = tmp_path / "json_1000.json"
    chunk_batch = _materialize(base_chunks * 1000)

    with PerformanceMeasurement() as perf:
        formatter.format_chunks(iter(chunk_batch), output_path)

    assert (
        perf.duration_seconds < 5.0
    ), f"1000-chunk JSON generation took {perf.duration_seconds:.2f}s"
    assert (
        perf.peak_memory_mb < 400
    ), f"Peak memory should remain under 400MB even for large batches (observed {perf.peak_memory_mb:.2f}MB)"


@pytest.mark.performance
def test_json_validation_toggle_performance(base_chunks: List[Chunk], tmp_path: Path):
    """Compare validation on/off to ensure optional path is faster."""
    chunk_batch = _materialize(base_chunks * 250)

    validate_output = tmp_path / "json_validate.json"
    noval_output = tmp_path / "json_novalidate.json"

    with PerformanceMeasurement() as perf_validate:
        JsonFormatter(validate=True).format_chunks(iter(chunk_batch), validate_output)

    with PerformanceMeasurement() as perf_no_validate:
        JsonFormatter(validate=False).format_chunks(iter(chunk_batch), noval_output)

    assert perf_validate.duration_seconds < 2.5, "Validation-enabled path should remain performant"
    assert (
        perf_no_validate.duration_seconds <= perf_validate.duration_seconds * 0.85
    ), "Disabling validation should provide a measurable speedup (~15%)"
