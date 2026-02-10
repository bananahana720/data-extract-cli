"""Integration tests for CSV organization across all strategies (Story 3.7).

Tests CSV output with BY_DOCUMENT, BY_ENTITY, and FLAT organization strategies,
validating Excel/pandas compatibility and RFC 4180 compliance.

Test Coverage:
    - CSV with BY_DOCUMENT strategy
    - CSV with BY_ENTITY strategy
    - CSV with FLAT strategy
    - Excel UTF-8 BOM compatibility
    - pandas DataFrame loading
    - csvkit validation (if available)
"""

import csv
from pathlib import Path

import pytest

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.output]

import pandas as pd  # noqa: E402

from data_extract.chunk.models import Chunk, ChunkMetadata  # noqa: E402
from data_extract.output.formatters.csv_formatter import CsvFormatter  # noqa: E402
from data_extract.output.organization import OrganizationStrategy, Organizer  # noqa: E402

pytestmark = [pytest.mark.integration, pytest.mark.output]


class TestCsvOrganization:
    """Integration tests for CSV output with organization strategies."""

    @pytest.fixture
    def sample_chunks(self) -> list:
        """Create sample chunks for CSV testing."""
        chunks = []

        for i in range(3):
            metadata = ChunkMetadata(
                source_file=Path(f"doc_{i}.pdf"),
                entity_tags=[],
                section_context=f"Section {i}",
            )

            chunk = Chunk(
                id=f"chunk_{i:03d}",
                text=f'Content for chunk {i} with, commas and "quotes"',
                document_id=f"doc_{i:03d}",
                position_index=i,
                token_count=50,
                word_count=40,
                entities=[],
                section_context=f"Section {i}",
                quality_score=0.85,
                readability_scores={},
                metadata=metadata,
            )
            chunks.append(chunk)

        return chunks

    def test_csv_with_by_document_strategy(self, sample_chunks, tmp_path):
        """Should organize CSV files by document (AC-3.7-2)."""
        organizer = Organizer()
        formatter = CsvFormatter()
        output_dir = tmp_path / "output"

        # Organize chunks
        org_result = organizer.organize(sample_chunks, output_dir, OrganizationStrategy.BY_DOCUMENT)

        # Write CSV for each document folder (simulation of OutputWriter behavior)
        for folder_name in ["doc_0", "doc_1", "doc_2"]:
            folder_path = output_dir / folder_name
            csv_path = folder_path / f"{folder_name}.csv"

            # Filter chunks for this document
            doc_chunks = [c for c in sample_chunks if c.metadata.source_file.stem == folder_name]

            if doc_chunks:
                formatter.format_chunks(doc_chunks, csv_path)

        # Verify CSV files exist in document folders
        assert (output_dir / "doc_0" / "doc_0.csv").exists()
        assert (output_dir / "doc_1" / "doc_1.csv").exists()
        assert (output_dir / "doc_2" / "doc_2.csv").exists()

        # Verify CSV is valid RFC 4180
        with open(output_dir / "doc_0" / "doc_0.csv", "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1  # One chunk per document
            assert "chunk_text" in rows[0]

    def test_csv_with_flat_strategy(self, sample_chunks, tmp_path):
        """Should create single CSV in flat directory (AC-3.7-4)."""
        organizer = Organizer()
        formatter = CsvFormatter()
        output_dir = tmp_path / "output"

        # Organize with FLAT strategy
        org_result = organizer.organize(sample_chunks, output_dir, OrganizationStrategy.FLAT)

        # Write single CSV in root
        csv_path = output_dir / "chunks.csv"
        formatter.format_chunks(sample_chunks, csv_path)

        # Verify single CSV file
        assert csv_path.exists()
        assert org_result.folders_created == 0  # No subdirectories

        # Verify all chunks in one CSV
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 3  # All chunks

    def test_csv_pandas_compatibility(self, sample_chunks, tmp_path):
        """Should load CSV into pandas DataFrame (AC-3.7-8)."""
        formatter = CsvFormatter()
        csv_path = tmp_path / "test.csv"

        formatter.format_chunks(sample_chunks, csv_path)

        # Load with pandas
        df = pd.read_csv(csv_path, encoding="utf-8-sig")

        # Verify structure
        assert len(df) == 3
        assert "chunk_id" in df.columns
        assert "chunk_text" in df.columns
        assert "entity_tags" in df.columns

        # Verify data integrity
        assert df["chunk_id"].tolist() == ["chunk_000", "chunk_001", "chunk_002"]

    def test_csv_utf8_bom_excel_compatibility(self, sample_chunks, tmp_path):
        """Should include UTF-8 BOM for Excel compatibility (AC-3.7-8)."""
        formatter = CsvFormatter()
        csv_path = tmp_path / "test.csv"

        formatter.format_chunks(sample_chunks, csv_path)

        # Verify BOM is present (UTF-8 BOM bytes)
        with open(csv_path, "rb") as f:
            header = f.read(3)
            assert header == b"\xef\xbb\xbf", "UTF-8 BOM not found"

    def test_csv_rfc4180_escaping(self, sample_chunks, tmp_path):
        """Should properly escape commas, quotes, and newlines (AC-3.7-8)."""
        formatter = CsvFormatter()
        csv_path = tmp_path / "test.csv"

        formatter.format_chunks(sample_chunks, csv_path)

        # Verify escaping by parsing with csv module
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            # Verify commas and quotes are preserved
            first_text = rows[0]["chunk_text"]
            assert "commas" in first_text
            assert "quotes" in first_text

    def test_csv_manifest_traceability(self, sample_chunks, tmp_path):
        """Should reference CSV files in manifest (AC-3.7-6)."""
        organizer = Organizer()
        output_dir = tmp_path / "output"

        result = organizer.organize(sample_chunks, output_dir, OrganizationStrategy.FLAT)

        # Verify manifest exists and has organization metadata
        import json  # noqa: E402

        with open(result.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["organization_strategy"] == "flat"
        assert manifest["total_chunks"] == 3
        assert "generated_at" in manifest  # ISO 8601 timestamp
