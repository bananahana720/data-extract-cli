"""Integration tests for CSV output pipeline (Story 3.6 - ATDD RED PHASE).

Validates ProcessingResult → ChunkingEngine → CsvFormatter → OutputWriter flow,
pandas import compatibility, organization strategies, and parser validation wiring.

Test Coverage:
    - AC-3.6-1: Canonical schema end-to-end
    - AC-3.6-4: Import validation via pandas.read_csv()
    - AC-3.6-5: Truncation indicator and ellipsis propagation
    - AC-3.6-6: Entity serialization within pipeline
    - AC-3.6-7: Parser validation invoked before surfacing artifacts

These tests WILL FAIL until CsvFormatter, OutputWriter, and CsvParserValidator exist.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

import pytest

from data_extract.chunk.models import Chunk, ChunkMetadata
from data_extract.chunk.quality import QualityScore
from data_extract.output.formatters.csv_formatter import CsvFormatter
from data_extract.output.writer import OutputWriter

try:  # Optional dependency for AC-3.6-4
    import pandas as pd
except ImportError:  # pragma: no cover - pandas optional
    pd = None  # type: ignore[assignment]

pytestmark = [pytest.mark.integration, pytest.mark.output]

EXPECTED_COLUMNS = [
    "chunk_id",
    "source_file",
    "section_context",
    "chunk_text",
    "entity_tags",
    "quality_score",
    "word_count",
    "token_count",
    "processing_version",
    "warnings",
]


@pytest.fixture
def csv_formatter():
    """Provide CsvFormatter with validation enabled."""
    return CsvFormatter()


@pytest.fixture
def csv_formatter_with_truncation():
    """Provide CsvFormatter configured to truncate text."""
    return CsvFormatter(max_text_length=64)


@pytest.fixture
def output_writer():
    """Provide OutputWriter instance for format registry validation."""
    return OutputWriter()


@pytest.fixture
def pipeline_chunks(tmp_path: Path) -> Iterable[Chunk]:
    """Create chunk list mirroring chunking output for CSV integration tests."""
    source_file = tmp_path / "pipeline-source.pdf"
    source_file.write_text("dummy", encoding="utf-8")

    metadata = ChunkMetadata(
        entity_tags=[],
        section_context="Risk Assessment > Controls",
        quality=QualityScore(
            readability_flesch_kincaid=8.5,
            readability_gunning_fog=9.2,
            ocr_confidence=0.97,
            completeness=0.9,
            coherence=0.91,
            overall=0.9,
            flags=["OCR_LOW"],
        ),
        source_hash="abc123",
        document_type="audit",
        word_count=80,
        token_count=120,
        created_at=None,
        processing_version="1.0.0-epic3",
        source_file=source_file,
        config_snapshot={"chunk_size": 256},
    )

    base_chunk = Chunk(
        id="chunk_pipeline_001",
        text='Chunk text with comma, "quotes", and newline.\nNext line for RFC 4180 validation.',
        document_id="doc_pipeline",
        position_index=0,
        token_count=120,
        word_count=80,
        entities=[],
        section_context="Risk Assessment > Controls",
        quality_score=0.9,
        readability_scores={"flesch_kincaid": 8.5},
        metadata=metadata,
    )

    return iter([base_chunk])


class TestCsvFormatterPipeline:
    """Validate ChunkingEngine → CsvFormatter pipeline behavior."""

    def test_chunking_pipeline_generates_csv_with_header(
        self,
        csv_formatter: CsvFormatter,
        pipeline_chunks: Iterable[Chunk],
        tmp_path: Path,
    ) -> None:
        """Should produce CSV file with canonical header (AC-3.6-1)."""
        output_path = tmp_path / "pipeline.csv"

        csv_formatter.format_chunks(pipeline_chunks, output_path)

        with output_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader)
        assert header == EXPECTED_COLUMNS

    def test_formatter_truncation_indicator_surfaces_in_pipeline(
        self,
        csv_formatter_with_truncation: CsvFormatter,
        pipeline_chunks: Iterable[Chunk],
        tmp_path: Path,
    ) -> None:
        """Should append ellipsis indicator in warnings column for truncated text (AC-3.6-5)."""
        output_path = tmp_path / "truncate.csv"

        csv_formatter_with_truncation.format_chunks(pipeline_chunks, output_path)

        with output_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            row = next(reader)
        assert row["chunk_text"].endswith("…")
        assert "TRUNCATED" in row["warnings"]


class TestCsvImportValidation:
    """Ensure CSV output is ingestible by pandas (AC-3.6-4)."""

    def test_pandas_can_import_csv_output(
        self, csv_formatter: CsvFormatter, pipeline_chunks: Iterable[Chunk], tmp_path: Path
    ) -> None:
        """Should read CSV into pandas DataFrame without warnings."""
        if pd is None:
            pytest.skip("pandas not installed")

        output_path = tmp_path / "pandas.csv"
        csv_formatter.format_chunks(pipeline_chunks, output_path)

        df = pd.read_csv(output_path)
        assert list(df.columns) == EXPECTED_COLUMNS
        assert len(df.index) == 1


class TestOutputWriterCsvIntegration:
    """Validate OutputWriter registry and organization for CSV format."""

    def test_output_writer_emits_csv_format(
        self, output_writer: OutputWriter, pipeline_chunks: Iterable[Chunk], tmp_path: Path
    ) -> None:
        """Should register csv format_type and return FormatResult."""
        output_path = tmp_path / "writer.csv"

        result = output_writer.write(
            chunks=pipeline_chunks,
            output_path=output_path,
            format_type="csv",
            validate=True,
        )

        assert result.format_type == "csv"
        assert result.output_path == output_path
        assert output_path.exists()

    def test_output_writer_honors_per_chunk_option(
        self, output_writer: OutputWriter, pipeline_chunks: Iterable[Chunk], tmp_path: Path
    ) -> None:
        """Should create per-chunk CSV files when per_chunk=True."""
        output_dir = tmp_path / "per-chunk"

        result = output_writer.write(
            chunks=pipeline_chunks,
            output_path=output_dir,
            format_type="csv",
            per_chunk=True,
            validate=False,
        )

        assert result.output_path == output_dir
        chunk_files = list(output_dir.glob("*.csv"))
        assert len(chunk_files) >= 1
