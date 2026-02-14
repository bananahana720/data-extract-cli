"""
Tests for TxtFormatter.

Tests organized by requirement:
- Basic formatting with default delimiter
- Custom delimiter support
- Chunk numbering format (3-digit padded)
- Metadata header inclusion
- Empty chunks edge case
- Single chunk delimiter behavior
- Multiple chunks delimiter placement
- UTF-8-sig encoding
- Parent directory creation
- FormattingResult return value
"""

from pathlib import Path

import pytest

from src.data_extract.chunk.entity_preserver import EntityReference
from src.data_extract.chunk.models import ChunkMetadata
from src.data_extract.chunk.quality import QualityScore
from src.data_extract.core.models import Chunk, Metadata
from src.data_extract.output.formatters.base import FormattingResult
from src.data_extract.output.formatters.txt_formatter import TxtFormatter

pytestmark = [pytest.mark.P0, pytest.mark.unit]


@pytest.fixture
def sample_chunks_for_txt():
    """Create sample chunks for TXT formatter testing."""
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
    metadata2 = Metadata(
        source_file=Path("test_doc.pdf"),
        file_hash="abc123",
        processing_timestamp=datetime.now(),
        file_format="pdf",
        file_size_bytes=1024,
        page_count=1,
        word_count=60,
        tool_version="1.0.0",
        config_version="1.0.0",
    )

    chunk1 = Chunk(
        id="test_001",
        text="This is the first chunk with sample content.",
        document_id="doc_001",
        position_index=0,
        token_count=10,
        word_count=8,
        quality_score=0.95,
        metadata=metadata1,
    )

    chunk2 = Chunk(
        id="test_002",
        text="This is the second chunk with more content.",
        document_id="doc_001",
        position_index=1,
        token_count=10,
        word_count=8,
        quality_score=0.92,
        metadata=metadata2,
    )

    return [chunk1, chunk2]


@pytest.fixture
def sample_chunk_with_metadata():
    """Create chunk with rich metadata for metadata inclusion tests."""
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
    ]

    chunk_metadata = ChunkMetadata(
        entity_tags=entity_tags,
        section_context="Risk Assessment > Controls",
        quality=quality,
        source_file=Path("test_doc.pdf"),
        word_count=25,
        token_count=30,
    )

    from datetime import datetime

    metadata = Metadata(
        source_file=Path("test_doc.pdf"),
        file_hash="abc123",
        processing_timestamp=datetime.now(),
        file_format="pdf",
        file_size_bytes=1024,
        page_count=1,
        word_count=25,
        tool_version="1.0.0",
        config_version="1.0.0",
    )

    chunk = Chunk(
        id="test_001",
        text="This chunk has rich metadata including entities and quality scores.",
        document_id="doc_001",
        position_index=0,
        token_count=30,
        word_count=25,
        quality_score=0.93,
        metadata=chunk_metadata,
    )

    return chunk


class TestTxtFormatterBasicFormatting:
    """Tests for basic TXT formatting functionality."""

    def test_format_chunks_with_default_delimiter(self, sample_chunks_for_txt, tmp_path):
        """Format should use default delimiter '━━━ CHUNK {{n}} ━━━'."""
        formatter = TxtFormatter()
        output_path = tmp_path / "output.txt"

        result = formatter.format_chunks(sample_chunks_for_txt, output_path)

        assert result.output_path == output_path
        assert output_path.exists()

        content = output_path.read_text(encoding="utf-8-sig")
        # BOM removal for assertion
        content = content.lstrip("\ufeff")

        assert "━━━ CHUNK 001 ━━━" in content
        assert "━━━ CHUNK 002 ━━━" in content
        assert "This is the first chunk" in content
        assert "This is the second chunk" in content

    def test_format_chunks_with_custom_delimiter(self, sample_chunks_for_txt, tmp_path):
        """Format should support custom delimiter strings."""
        formatter = TxtFormatter(delimiter="--- CHUNK {{n}} ---")
        output_path = tmp_path / "output.txt"

        result = formatter.format_chunks(sample_chunks_for_txt, output_path)

        content = output_path.read_text(encoding="utf-8-sig")
        content = content.lstrip("\ufeff")

        assert "--- CHUNK 001 ---" in content
        assert "--- CHUNK 002 ---" in content

    def test_chunk_numbering_format_three_digit_padded(self, sample_chunks_for_txt, tmp_path):
        """Chunk numbers should be zero-padded to 3 digits."""
        formatter = TxtFormatter()
        output_path = tmp_path / "output.txt"

        result = formatter.format_chunks(sample_chunks_for_txt, output_path)

        content = output_path.read_text(encoding="utf-8-sig")
        content = content.lstrip("\ufeff")

        # Verify 3-digit padding
        assert "001" in content
        assert "002" in content
        assert "CHUNK 001" in content
        assert "CHUNK 002" in content


class TestTxtFormatterMetadata:
    """Tests for metadata header inclusion."""

    def test_metadata_header_inclusion(self, sample_chunk_with_metadata, tmp_path):
        """With include_metadata=True, metadata headers should be included."""
        formatter = TxtFormatter(include_metadata=True)
        output_path = tmp_path / "output.txt"

        result = formatter.format_chunks([sample_chunk_with_metadata], output_path)

        content = output_path.read_text(encoding="utf-8-sig")
        content = content.lstrip("\ufeff")

        # Check metadata headers
        assert "Source: test_doc.pdf" in content
        assert "Entities: RISK-001; CTRL-042" in content
        assert "Quality: 0.93" in content

    def test_no_metadata_header_by_default(self, sample_chunk_with_metadata, tmp_path):
        """Without include_metadata, no metadata headers should appear."""
        formatter = TxtFormatter(include_metadata=False)
        output_path = tmp_path / "output.txt"

        result = formatter.format_chunks([sample_chunk_with_metadata], output_path)

        content = output_path.read_text(encoding="utf-8-sig")
        content = content.lstrip("\ufeff")

        # No metadata headers
        assert "Source:" not in content
        assert "Entities:" not in content
        assert "Quality:" not in content


class TestTxtFormatterEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_chunks_produces_empty_file(self, tmp_path):
        """Empty chunk list should produce empty file."""
        formatter = TxtFormatter()
        output_path = tmp_path / "output.txt"

        result = formatter.format_chunks([], output_path)

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8-sig")
        content = content.lstrip("\ufeff")
        assert content == ""

    def test_single_chunk_has_delimiter(self, sample_chunks_for_txt, tmp_path):
        """Single chunk should have delimiter at start."""
        formatter = TxtFormatter()
        output_path = tmp_path / "output.txt"

        result = formatter.format_chunks([sample_chunks_for_txt[0]], output_path)

        content = output_path.read_text(encoding="utf-8-sig")
        content = content.lstrip("\ufeff")

        # First chunk gets delimiter at start
        assert "━━━ CHUNK 001 ━━━" in content
        assert content.startswith("━━━ CHUNK 001 ━━━")

    def test_multiple_chunks_have_delimiters_between(self, sample_chunks_for_txt, tmp_path):
        """Multiple chunks should have delimiters with spacing."""
        formatter = TxtFormatter()
        output_path = tmp_path / "output.txt"

        result = formatter.format_chunks(sample_chunks_for_txt, output_path)

        content = output_path.read_text(encoding="utf-8-sig")
        content = content.lstrip("\ufeff")

        # Both delimiters present with proper spacing
        lines = content.split("\n")
        delimiter_indices = [i for i, line in enumerate(lines) if "━━━ CHUNK" in line]

        assert len(delimiter_indices) == 2
        # Verify spacing between chunks
        assert delimiter_indices[0] == 0  # First delimiter at start
        # Second delimiter should have spacing before it


class TestTxtFormatterFileHandling:
    """Tests for file handling and encoding."""

    def test_utf8_sig_encoding_present(self, sample_chunks_for_txt, tmp_path):
        """Output file should use UTF-8-sig encoding (with BOM)."""
        formatter = TxtFormatter()
        output_path = tmp_path / "output.txt"

        result = formatter.format_chunks(sample_chunks_for_txt, output_path)

        # Read raw bytes to check BOM
        raw_bytes = output_path.read_bytes()
        # UTF-8-sig BOM is EF BB BF
        assert raw_bytes[:3] == b"\xef\xbb\xbf"

    def test_creates_parent_directories(self, sample_chunks_for_txt, tmp_path):
        """Formatter should create parent directories if they don't exist."""
        formatter = TxtFormatter()
        output_path = tmp_path / "nested" / "dirs" / "output.txt"

        assert not output_path.parent.exists()

        result = formatter.format_chunks(sample_chunks_for_txt, output_path)

        assert output_path.parent.exists()
        assert output_path.exists()

    def test_returns_formatting_result(self, sample_chunks_for_txt, tmp_path):
        """Format should return FormattingResult with correct metadata."""
        formatter = TxtFormatter()
        output_path = tmp_path / "output.txt"

        result = formatter.format_chunks(sample_chunks_for_txt, output_path)

        # Verify FormattingResult structure
        assert isinstance(result, FormattingResult)
        assert result.output_path == output_path
        assert result.chunk_count == 2
        assert result.total_size > 0
        assert result.format_type == "txt"
        assert result.duration_seconds >= 0
        assert result.errors == []
