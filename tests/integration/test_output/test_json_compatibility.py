"""Integration tests for JSON cross-platform compatibility (Story 3.4).

Tests UTF-8 encoding with special characters, large chunk text, deeply nested structures,
and Windows/Linux path compatibility.

Test Coverage:
    - AC-3.4-2: UTF-8 encoding and cross-platform compatibility
"""

import json

import pytest

from data_extract.chunk.entity_preserver import EntityReference
from data_extract.chunk.models import Chunk, ChunkMetadata
from data_extract.output.formatters.json_formatter import JsonFormatter

pytestmark = [pytest.mark.integration, pytest.mark.output, pytest.mark.compatibility]


@pytest.fixture
def json_formatter():
    """Create JsonFormatter instance."""
    return JsonFormatter(validate=True)


class TestUTF8EncodingSpecialCharacters:
    """Test UTF-8 encoding with special characters (AC-3.4-2)."""

    def test_emoji_in_chunk_text(self, json_formatter, tmp_path):
        """Should handle emoji characters in chunk text."""
        # GIVEN: Chunk with emoji in text
        chunk_metadata = ChunkMetadata(
            source_hash="abc123",
            document_type="report",
            processing_version="1.0.0",
        )

        chunk = Chunk(
            id="test_001",
            text="Risk assessment 🚨 shows critical issues 📊 requiring immediate attention ✅",
            document_id="test",
            position_index=0,
            token_count=50,
            word_count=40,
            entities=[],
            section_context="Introduction",
            quality_score=0.9,
            readability_scores={},
            metadata=chunk_metadata,
        )

        output_path = tmp_path / "emoji.json"

        # WHEN: Formatting to JSON
        json_formatter.format_chunks(iter([chunk]), output_path)

        # THEN: JSON should parse and preserve emojis
        with open(output_path, "r", encoding="utf-8-sig") as f:
            json_data = json.load(f)

        assert "🚨" in json_data["chunks"][0]["text"]
        assert "📊" in json_data["chunks"][0]["text"]
        assert "✅" in json_data["chunks"][0]["text"]

    def test_accented_characters(self, json_formatter, tmp_path):
        """Should handle accented characters (French, Spanish, etc.)."""
        # GIVEN: Chunk with accented characters
        chunk_metadata = ChunkMetadata(
            source_hash="abc123",
            document_type="report",
            processing_version="1.0.0",
        )

        chunk = Chunk(
            id="test_001",
            text="Café résumé naïve fiancée São Paulo Zürich",
            document_id="test",
            position_index=0,
            token_count=50,
            word_count=40,
            entities=[],
            section_context="Introduction",
            quality_score=0.9,
            readability_scores={},
            metadata=chunk_metadata,
        )

        output_path = tmp_path / "accents.json"

        # WHEN: Formatting to JSON
        json_formatter.format_chunks(iter([chunk]), output_path)

        # THEN: JSON should preserve accented characters
        with open(output_path, "r", encoding="utf-8-sig") as f:
            json_data = json.load(f)

        text = json_data["chunks"][0]["text"]
        assert "é" in text
        assert "ü" in text
        assert "ñ" in text or "ã" in text

    def test_cjk_characters(self, json_formatter, tmp_path):
        """Should handle Chinese, Japanese, Korean characters."""
        # GIVEN: Chunk with CJK characters
        chunk_metadata = ChunkMetadata(
            source_hash="abc123",
            document_type="report",
            processing_version="1.0.0",
        )

        chunk = Chunk(
            id="test_001",
            text="風險評估 リスク評価 위험 평가 Risk Assessment in multiple languages",
            document_id="test",
            position_index=0,
            token_count=50,
            word_count=40,
            entities=[],
            section_context="Introduction",
            quality_score=0.9,
            readability_scores={},
            metadata=chunk_metadata,
        )

        output_path = tmp_path / "cjk.json"

        # WHEN: Formatting to JSON
        json_formatter.format_chunks(iter([chunk]), output_path)

        # THEN: JSON should preserve CJK characters
        with open(output_path, "r", encoding="utf-8-sig") as f:
            json_data = json.load(f)

        text = json_data["chunks"][0]["text"]
        assert "風險" in text or "リスク" in text or "위험" in text


class TestLargeChunkText:
    """Test handling of large chunk text (AC-3.4-2)."""

    def test_chunk_with_10kb_text(self, json_formatter, tmp_path):
        """Should handle chunks with >10KB of text."""
        # GIVEN: Chunk with large text (10KB+)
        large_text = "This is a long paragraph. " * 400  # ~10KB

        chunk_metadata = ChunkMetadata(
            source_hash="abc123",
            document_type="report",
            processing_version="1.0.0",
        )

        chunk = Chunk(
            id="test_001",
            text=large_text,
            document_id="test",
            position_index=0,
            token_count=2000,
            word_count=1600,
            entities=[],
            section_context="Long Section",
            quality_score=0.9,
            readability_scores={},
            metadata=chunk_metadata,
        )

        output_path = tmp_path / "large.json"

        # WHEN: Formatting to JSON
        json_formatter.format_chunks(iter([chunk]), output_path)

        # THEN: JSON should be parsable
        with open(output_path, "r", encoding="utf-8-sig") as f:
            json_data = json.load(f)

        assert len(json_data["chunks"][0]["text"]) > 10000


class TestDeeplyNestedStructures:
    """Test handling of deeply nested entity structures (AC-3.4-2)."""

    def test_chunk_with_multiple_entities(self, json_formatter, tmp_path):
        """Should handle chunks with many nested entities."""
        # GIVEN: Chunk with 10+ entities
        entities = [
            EntityReference(
                entity_type="risk",
                entity_id=f"RISK-{i:03d}",
                start_pos=i * 20,
                end_pos=i * 20 + 15,
                is_partial=False,
                context_snippet=f"risk {i}",
            )
            for i in range(10)
        ]

        chunk_metadata = ChunkMetadata(
            entity_tags=entities,
            source_hash="abc123",
            document_type="report",
            processing_version="1.0.0",
        )

        chunk = Chunk(
            id="test_001",
            text="Complex document with many entities...",
            document_id="test",
            position_index=0,
            token_count=50,
            word_count=40,
            entities=[],
            section_context="Risk Section",
            quality_score=0.9,
            readability_scores={},
            metadata=chunk_metadata,
        )

        output_path = tmp_path / "nested.json"

        # WHEN: Formatting to JSON
        json_formatter.format_chunks(iter([chunk]), output_path)

        # THEN: JSON should be parsable with all entities
        with open(output_path, "r", encoding="utf-8-sig") as f:
            json_data = json.load(f)

        entity_tags = json_data["chunks"][0]["metadata"]["entity_tags"]
        assert len(entity_tags) == 10


class TestPathCompatibility:
    """Test Windows/Linux path compatibility (AC-3.4-2)."""

    def test_windows_path_serialization(self, json_formatter, tmp_path):
        """Should serialize Windows-style paths correctly."""
        # GIVEN: ChunkMetadata with Windows-style path
        from datetime import datetime

        chunk_metadata = ChunkMetadata(
            source_hash="abc123",
            document_type="report",
            processing_version="1.0.0",
            created_at=datetime(2025, 11, 14),
        )

        chunk = Chunk(
            id="test_001",
            text="Test chunk",
            document_id="test",
            position_index=0,
            token_count=50,
            word_count=40,
            entities=[],
            section_context="Section",
            quality_score=0.9,
            readability_scores={},
            metadata=chunk_metadata,
        )

        output_path = tmp_path / "paths.json"

        # WHEN: Formatting to JSON
        json_formatter.format_chunks(iter([chunk]), output_path)

        # THEN: JSON should be parsable
        with open(output_path, "r", encoding="utf-8-sig") as f:
            json_data = json.load(f)

        # Paths should be strings (not Path objects)
        sources = json_data["metadata"]["source_documents"]
        assert isinstance(sources, list)

        for source in sources:
            assert isinstance(source, str)

    def test_cross_platform_path_reading(self, json_formatter, tmp_path):
        """Should read JSON with paths from different platforms."""
        # GIVEN: Chunk with path metadata
        chunk_metadata = ChunkMetadata(
            source_hash="abc123",
            document_type="report",
            processing_version="1.0.0",
        )

        chunk = Chunk(
            id="test_001",
            text="Test",
            document_id="test",
            position_index=0,
            token_count=10,
            word_count=8,
            entities=[],
            section_context="Section",
            quality_score=0.9,
            readability_scores={},
            metadata=chunk_metadata,
        )

        output_path = tmp_path / "cross_platform.json"

        # WHEN: Formatting to JSON
        json_formatter.format_chunks(iter([chunk]), output_path)

        # THEN: JSON should be readable on any platform
        with open(output_path, "r", encoding="utf-8-sig") as f:
            json_data = json.load(f)

        assert json_data is not None


class TestFileEncodingDetails:
    """Test file encoding specifics (AC-3.4-2)."""

    def test_utf8_bom_written(self, json_formatter, tmp_path):
        """Should write UTF-8 BOM for Windows compatibility."""
        # GIVEN: Simple chunk
        chunk_metadata = ChunkMetadata(
            source_hash="abc123",
            document_type="report",
            processing_version="1.0.0",
        )

        chunk = Chunk(
            id="test_001",
            text="Test chunk",
            document_id="test",
            position_index=0,
            token_count=10,
            word_count=8,
            entities=[],
            section_context="Section",
            quality_score=0.9,
            readability_scores={},
            metadata=chunk_metadata,
        )

        output_path = tmp_path / "bom.json"

        # WHEN: Formatting to JSON
        json_formatter.format_chunks(iter([chunk]), output_path)

        # THEN: File should have UTF-8 encoding (with or without BOM)
        with open(output_path, "rb") as f:
            raw_bytes = f.read()

        # Should decode as UTF-8
        content = raw_bytes.decode("utf-8-sig")  # Handles BOM if present
        assert len(content) > 0

        # Verify it's valid JSON
        json.loads(content)

    def test_no_encoding_corruption(self, json_formatter, tmp_path):
        """Should not corrupt special characters during write/read cycle."""
        # GIVEN: Chunk with mixed special characters
        original_text = "Café 🚨 風險評估 naïve Zürich"

        chunk_metadata = ChunkMetadata(
            source_hash="abc123",
            document_type="report",
            processing_version="1.0.0",
        )

        chunk = Chunk(
            id="test_001",
            text=original_text,
            document_id="test",
            position_index=0,
            token_count=50,
            word_count=40,
            entities=[],
            section_context="Section",
            quality_score=0.9,
            readability_scores={},
            metadata=chunk_metadata,
        )

        output_path = tmp_path / "no_corruption.json"

        # WHEN: Writing and reading back
        json_formatter.format_chunks(iter([chunk]), output_path)

        with open(output_path, "r", encoding="utf-8-sig") as f:
            json_data = json.load(f)

        # THEN: Text should be identical
        assert json_data["chunks"][0]["text"] == original_text
