"""
Tests for CsvFormatter.

Tests organized by requirement:
- Header row correctness (10 columns)
- Column order verification
- Text truncation at max_text_length
- Truncation flag when text is truncated
- Entity tags joined with semicolons
- Quality score from metadata
- UTF-8-sig encoding for Excel compatibility
- Empty chunks edge case
- Single row CSV
- Special characters properly escaped/quoted
- Parent directory creation
- FormattingResult return value
"""

import csv
from pathlib import Path

import pytest

from src.data_extract.chunk.entity_preserver import EntityReference
from src.data_extract.chunk.models import ChunkMetadata
from src.data_extract.chunk.quality import QualityScore
from src.data_extract.core.models import Chunk, Metadata
from src.data_extract.output.formatters.base import FormattingResult
from src.data_extract.output.formatters.csv_formatter import CsvFormatter

pytestmark = [pytest.mark.P0, pytest.mark.unit]


@pytest.fixture
def sample_chunks_for_csv():
    """Create sample chunks for CSV formatter testing."""
    from datetime import datetime

    metadata1 = Metadata(
        source_file=Path("test_doc.pdf"),
        file_hash="abc123",
        processing_timestamp=datetime.now(),
        file_format="pdf",
        file_size_bytes=1024,
        page_count=1,
        word_count=50,
        tool_version="1.0.0",
        config_version="1.0.0",
    )

    chunk1 = Chunk(
        id="chunk_001",
        text="This is the first chunk with sample content.",
        document_id="doc_001",
        position_index=0,
        token_count=10,
        word_count=8,
        quality_score=0.95,
        section_context="Introduction",
        metadata=metadata1,
    )

    chunk2 = Chunk(
        id="chunk_002",
        text="This is the second chunk with more content.",
        document_id="doc_001",
        position_index=1,
        token_count=10,
        word_count=8,
        quality_score=0.92,
        section_context="Analysis",
        metadata=metadata1,
    )

    return [chunk1, chunk2]


@pytest.fixture
def sample_chunk_with_rich_metadata():
    """Create chunk with rich metadata for comprehensive testing."""
    quality = QualityScore(
        readability_flesch_kincaid=8.5,
        readability_gunning_fog=10.2,
        ocr_confidence=0.99,
        completeness=0.95,
        coherence=0.88,
        overall=0.93,
        flags=[],
    )

    entity_tags = [
        EntityReference(
            entity_type="RISK",
            entity_id="RISK-001",
            start_pos=0,
            end_pos=10,
            is_partial=False,
            context_snippet="Test risk",
        ),
        EntityReference(
            entity_type="CONTROL",
            entity_id="CTRL-042",
            start_pos=20,
            end_pos=30,
            is_partial=False,
            context_snippet="Test control",
        ),
        EntityReference(
            entity_type="POLICY",
            entity_id="POL-123",
            start_pos=40,
            end_pos=50,
            is_partial=False,
            context_snippet="Test policy",
        ),
    ]

    chunk_metadata = ChunkMetadata(
        entity_tags=entity_tags,
        section_context="Risk Assessment > Controls",
        quality=quality,
        source_file=Path("test_doc.pdf"),
        word_count=25,
        token_count=30,
        processing_version="1.0.0",
    )

    chunk = Chunk(
        id="chunk_rich_001",
        text="This chunk has rich metadata including entities and quality scores.",
        document_id="doc_001",
        position_index=0,
        token_count=30,
        word_count=25,
        quality_score=0.93,
        section_context="Risk Assessment > Controls",
        metadata=chunk_metadata,
    )

    return chunk


class TestCsvFormatterHeaderAndColumns:
    """Tests for CSV header row and column structure."""

    def test_header_row_has_ten_columns(self, sample_chunks_for_csv, tmp_path):
        """CSV header should have exactly 10 columns."""
        formatter = CsvFormatter()
        output_path = tmp_path / "output.csv"

        result = formatter.format_chunks(sample_chunks_for_csv, output_path)

        with open(output_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)

        assert len(header) == 10

    def test_column_order_verification(self, sample_chunks_for_csv, tmp_path):
        """Columns should be in correct order per specification."""
        formatter = CsvFormatter()
        output_path = tmp_path / "output.csv"

        result = formatter.format_chunks(sample_chunks_for_csv, output_path)

        with open(output_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)

        # Verify exact column order
        expected_columns = [
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

        assert header == expected_columns


class TestCsvFormatterTextTruncation:
    """Tests for text truncation functionality."""

    def test_text_truncation_at_max_length(self, sample_chunks_for_csv, tmp_path):
        """Text should be truncated at max_text_length."""
        formatter = CsvFormatter(max_text_length=20)
        output_path = tmp_path / "output.csv"

        result = formatter.format_chunks(sample_chunks_for_csv, output_path)

        with open(output_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            row1 = next(reader)

        chunk_text = row1[3]  # chunk_text column
        # Should be truncated to 20 chars + ellipsis
        assert len(chunk_text) == 21
        assert chunk_text.endswith("…")
        assert chunk_text == "This is the first ch…"

    def test_truncation_flag_added_when_truncated(self, sample_chunks_for_csv, tmp_path):
        """Warnings column should show 'TRUNCATED' when text is truncated."""
        formatter = CsvFormatter(max_text_length=20)
        output_path = tmp_path / "output.csv"

        result = formatter.format_chunks(sample_chunks_for_csv, output_path)

        with open(output_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            row1 = next(reader)

        warnings = row1[9]  # warnings column
        assert warnings == "TRUNCATED"

    def test_no_truncation_flag_when_not_truncated(self, sample_chunks_for_csv, tmp_path):
        """Warnings column should be empty when text is not truncated."""
        formatter = CsvFormatter(max_text_length=1000)
        output_path = tmp_path / "output.csv"

        result = formatter.format_chunks(sample_chunks_for_csv, output_path)

        with open(output_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            row1 = next(reader)

        warnings = row1[9]  # warnings column
        assert warnings == ""


class TestCsvFormatterMetadata:
    """Tests for metadata extraction and formatting."""

    def test_entity_tags_joined_with_semicolons(self, sample_chunk_with_rich_metadata, tmp_path):
        """Entity tags should be semicolon-separated."""
        formatter = CsvFormatter()
        output_path = tmp_path / "output.csv"

        result = formatter.format_chunks([sample_chunk_with_rich_metadata], output_path)

        with open(output_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            row = next(reader)

        entity_tags = row[4]  # entity_tags column
        assert entity_tags == "RISK-001; CTRL-042; POL-123"
        assert "; " in entity_tags

    def test_quality_score_from_metadata(self, sample_chunk_with_rich_metadata, tmp_path):
        """Quality score should be extracted from metadata."""
        formatter = CsvFormatter()
        output_path = tmp_path / "output.csv"

        result = formatter.format_chunks([sample_chunk_with_rich_metadata], output_path)

        with open(output_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            row = next(reader)

        quality_score = row[5]  # quality_score column
        assert quality_score == "0.93"

    def test_word_count_and_token_count(self, sample_chunk_with_rich_metadata, tmp_path):
        """Word count and token count should be extracted."""
        formatter = CsvFormatter()
        output_path = tmp_path / "output.csv"

        result = formatter.format_chunks([sample_chunk_with_rich_metadata], output_path)

        with open(output_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            row = next(reader)

        word_count = row[6]  # word_count column
        token_count = row[7]  # token_count column
        assert word_count == "25"
        assert token_count == "30"


class TestCsvFormatterFileHandling:
    """Tests for file handling and encoding."""

    def test_utf8_sig_encoding_present(self, sample_chunks_for_csv, tmp_path):
        """Output file should use UTF-8-sig encoding for Excel compatibility."""
        formatter = CsvFormatter()
        output_path = tmp_path / "output.csv"

        result = formatter.format_chunks(sample_chunks_for_csv, output_path)

        # Read raw bytes to check BOM
        raw_bytes = output_path.read_bytes()
        # UTF-8-sig BOM is EF BB BF
        assert raw_bytes[:3] == b"\xef\xbb\xbf"

    def test_creates_parent_directories(self, sample_chunks_for_csv, tmp_path):
        """Formatter should create parent directories if they don't exist."""
        formatter = CsvFormatter()
        output_path = tmp_path / "nested" / "dirs" / "output.csv"

        assert not output_path.parent.exists()

        result = formatter.format_chunks(sample_chunks_for_csv, output_path)

        assert output_path.parent.exists()
        assert output_path.exists()

    def test_returns_formatting_result(self, sample_chunks_for_csv, tmp_path):
        """Format should return FormattingResult with correct metadata."""
        formatter = CsvFormatter()
        output_path = tmp_path / "output.csv"

        result = formatter.format_chunks(sample_chunks_for_csv, output_path)

        # Verify FormattingResult structure
        assert isinstance(result, FormattingResult)
        assert result.output_path == output_path
        assert result.chunk_count == 2
        assert result.total_size > 0
        assert result.format_type == "csv"
        assert result.duration_seconds >= 0
        assert result.errors == []


class TestCsvFormatterEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_chunks_produces_header_only_csv(self, tmp_path):
        """Empty chunk list should produce CSV with header row only."""
        formatter = CsvFormatter()
        output_path = tmp_path / "output.csv"

        result = formatter.format_chunks([], output_path)

        assert output_path.exists()

        with open(output_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Should have header row only
        assert len(rows) == 1
        assert len(rows[0]) == 10

    def test_single_row_csv(self, sample_chunks_for_csv, tmp_path):
        """Single chunk should produce CSV with header + 1 data row."""
        formatter = CsvFormatter()
        output_path = tmp_path / "output.csv"

        result = formatter.format_chunks([sample_chunks_for_csv[0]], output_path)

        with open(output_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Header + 1 data row
        assert len(rows) == 2
        assert rows[1][0] == "chunk_001"  # chunk_id

    def test_special_characters_properly_escaped(self, tmp_path):
        """Special characters (quotes, commas, newlines) should be properly escaped."""
        from datetime import datetime

        metadata = Metadata(
            source_file=Path("test_doc.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            file_format="pdf",
            file_size_bytes=1024,
            page_count=1,
            word_count=50,
            tool_version="1.0.0",
            config_version="1.0.0",
        )

        chunk = Chunk(
            id="chunk_special",
            text='Text with "quotes", commas, and\nnewlines.',
            document_id="doc_001",
            position_index=0,
            token_count=10,
            word_count=8,
            quality_score=0.95,
            section_context="Section, with, commas",
            metadata=metadata,
        )

        formatter = CsvFormatter()
        output_path = tmp_path / "output.csv"

        result = formatter.format_chunks([chunk], output_path)

        # Read CSV to verify proper parsing
        with open(output_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            row = next(reader)

        chunk_text = row[3]  # chunk_text column
        section_context = row[2]  # section_context column

        # CSV reader should properly unescape values
        assert '"quotes"' in chunk_text
        assert "commas" in chunk_text
        assert "\n" in chunk_text
        assert section_context == "Section, with, commas"
