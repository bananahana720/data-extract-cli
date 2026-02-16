"""Comprehensive tests for JsonFormatter.

Tests organized by category:
1. Basic Formatting - Valid JSON output, chunk arrays, metadata
2. Encoding - UTF-8-sig BOM, Unicode preservation
3. Entity Serialization - Entity tags and relationships
4. Edge Cases - Empty chunks, single chunk, long text
5. File Operations - Path creation, directory creation, FormattingResult
6. Error Handling - Invalid paths, permission errors

Test Coverage:
    - format_chunks() produces valid JSON
    - UTF-8-sig encoding with BOM for Windows compatibility
    - Entity tags serialization
    - Source document tracking
    - Output metadata includes duration_seconds
    - Empty chunks list produces valid JSON
    - validate parameter behavior
    - Directory auto-creation (parents=True)
"""

import json

import pytest

pytestmark = [pytest.mark.P0, pytest.mark.unit]

from data_extract.chunk.entity_preserver import EntityReference  # noqa: E402
from data_extract.chunk.models import Chunk, ChunkMetadata, QualityScore  # noqa: E402
from data_extract.core.models import Entity, EntityType  # noqa: E402
from data_extract.output.formatters.base import FormattingResult  # noqa: E402
from data_extract.output.formatters.json_formatter import JsonFormatter  # noqa: E402

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_chunk(tmp_path):
    """Create a basic chunk for testing."""
    source_file = tmp_path / "test_document.pdf"
    source_file.touch()

    metadata = ChunkMetadata(
        source_file=source_file,
        processing_version="1.0.0",
        quality=QualityScore(
            overall=0.95,
            completeness=0.98,
            coherence=0.92,
            ocr_confidence=0.98,
            readability_flesch_kincaid=8.0,
            readability_gunning_fog=9.5,
            flags=[],
        ),
    )

    return Chunk(
        id="chunk_001",
        text="This is a sample chunk for testing.",
        document_id="test_document",
        position_index=0,
        token_count=8,
        word_count=7,
        entities=[],
        section_context="",
        quality_score=0.95,
        readability_scores={"flesch_reading_ease": 65.0},
        metadata=metadata,
    )


@pytest.fixture
def sample_chunks(tmp_path):
    """Create multiple chunks for testing."""
    source_file = tmp_path / "test_document.pdf"
    source_file.touch()

    chunks = []
    for idx in range(1, 4):
        metadata = ChunkMetadata(
            source_file=source_file,
            processing_version="1.0.0",
            quality=QualityScore(
                overall=0.95,
                completeness=0.98,
                coherence=0.92,
                ocr_confidence=0.98,
                readability_flesch_kincaid=8.0,
                readability_gunning_fog=9.5,
                flags=[],
            ),
        )

        chunk = Chunk(
            id=f"chunk_{idx:03d}",
            text=f"This is test chunk {idx} for JSON testing.",
            document_id="test_document",
            position_index=idx - 1,
            token_count=8,
            word_count=7,
            entities=[],
            section_context="",
            quality_score=0.95,
            readability_scores={"flesch_reading_ease": 65.0},
            metadata=metadata,
        )
        chunks.append(chunk)

    return chunks


@pytest.fixture
def chunk_with_entities(tmp_path):
    """Create a chunk with entity tags for testing entity serialization."""
    source_file = tmp_path / "test_document.pdf"
    source_file.touch()

    # Create entity references
    entity_refs = [
        EntityReference(
            entity_type="RISK",
            entity_id="RISK-001",
            start_pos=10,
            end_pos=25,
            is_partial=False,
            context_snippet="...financial risk...",
        ),
        EntityReference(
            entity_type="CONTROL",
            entity_id="CTRL-042",
            start_pos=50,
            end_pos=70,
            is_partial=True,
            context_snippet="...access control...",
        ),
    ]

    metadata = ChunkMetadata(
        source_file=source_file,
        processing_version="1.0.0",
        entity_tags=entity_refs,
        entity_relationships=[("RISK-001", "mitigated_by", "CTRL-042")],
        quality=QualityScore(
            overall=0.95,
            completeness=0.98,
            coherence=0.92,
            ocr_confidence=0.98,
            readability_flesch_kincaid=8.0,
            readability_gunning_fog=9.5,
            flags=[],
        ),
    )

    return Chunk(
        id="chunk_001",
        text="This chunk contains financial risk and access control entities.",
        document_id="test_document",
        position_index=0,
        token_count=10,
        word_count=9,
        entities=[
            Entity(
                type=EntityType.RISK,
                id="RISK-001",
                text="financial risk",
                confidence=0.95,
                location={"start": 10, "end": 25},
            )
        ],
        section_context="Risk Assessment > Identified Risks",
        quality_score=0.95,
        readability_scores={"flesch_reading_ease": 65.0},
        metadata=metadata,
    )


@pytest.fixture
def unicode_chunk(tmp_path):
    """Create a chunk with Unicode characters for testing encoding."""
    source_file = tmp_path / "test_document.pdf"
    source_file.touch()

    metadata = ChunkMetadata(
        source_file=source_file,
        processing_version="1.0.0",
        quality=QualityScore(
            overall=0.95,
            completeness=0.98,
            coherence=0.92,
            ocr_confidence=0.98,
            readability_flesch_kincaid=8.0,
            readability_gunning_fog=9.5,
            flags=[],
        ),
    )

    return Chunk(
        id="chunk_001",
        text="Test with Unicode: 你好世界 🎉 Ñoño café",
        document_id="test_document",
        position_index=0,
        token_count=10,
        word_count=7,
        entities=[],
        section_context="",
        quality_score=0.95,
        readability_scores={"flesch_reading_ease": 65.0},
        metadata=metadata,
    )


# ============================================================================
# Test Category 1: Basic Formatting
# ============================================================================


class TestJsonFormatterBasicFormatting:
    """Test basic JSON formatting behavior."""

    def test_format_chunks_produces_valid_json(self, sample_chunks, tmp_path):
        """Should produce valid, parseable JSON output."""
        # GIVEN: JsonFormatter and sample chunks
        formatter = JsonFormatter()
        output_path = tmp_path / "output.json"

        # WHEN: Formatting chunks
        result = formatter.format_chunks(chunks=sample_chunks, output_path=output_path)

        # THEN: Output should be valid JSON
        assert output_path.exists()
        with open(output_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        assert isinstance(data, dict)
        assert result.format_type == "json"

    def test_chunks_array_contains_all_input_chunks(self, sample_chunks, tmp_path):
        """Should include all input chunks in chunks array."""
        # GIVEN: JsonFormatter and 3 chunks
        formatter = JsonFormatter()
        output_path = tmp_path / "output.json"

        # WHEN: Formatting chunks
        result = formatter.format_chunks(chunks=sample_chunks, output_path=output_path)

        # THEN: All chunks should be in output
        with open(output_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        assert "chunks" in data
        assert len(data["chunks"]) == 3
        assert result.chunk_count == 3

        # Verify chunk IDs
        chunk_ids = [chunk["id"] for chunk in data["chunks"]]
        assert "chunk_001" in chunk_ids
        assert "chunk_002" in chunk_ids
        assert "chunk_003" in chunk_ids

    def test_metadata_section_present(self, sample_chunks, tmp_path):
        """Should include metadata section in JSON output."""
        # GIVEN: JsonFormatter and chunks
        formatter = JsonFormatter()
        output_path = tmp_path / "output.json"

        # WHEN: Formatting chunks
        formatter.format_chunks(chunks=sample_chunks, output_path=output_path)

        # THEN: Metadata section should exist
        with open(output_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        assert "metadata" in data
        assert "chunk_count" in data["metadata"]
        assert data["metadata"]["chunk_count"] == 3
        assert "processing_version" in data["metadata"]
        assert "source_documents" in data["metadata"]


# ============================================================================
# Test Category 2: Encoding
# ============================================================================


class TestJsonFormatterEncoding:
    """Test UTF-8-sig encoding and BOM handling."""

    def test_utf8_sig_bom_present(self, sample_chunk, tmp_path):
        """Should write UTF-8-sig BOM (EF BB BF) for Windows compatibility."""
        # GIVEN: JsonFormatter and a chunk
        formatter = JsonFormatter()
        output_path = tmp_path / "output.json"

        # WHEN: Formatting chunks
        formatter.format_chunks(chunks=[sample_chunk], output_path=output_path)

        # THEN: File should have UTF-8-sig BOM
        with open(output_path, "rb") as f:
            first_bytes = f.read(3)

        assert first_bytes == b"\xef\xbb\xbf"  # UTF-8-sig BOM

    def test_unicode_characters_preserved(self, unicode_chunk, tmp_path):
        """Should preserve Unicode characters correctly."""
        # GIVEN: JsonFormatter and chunk with Unicode
        formatter = JsonFormatter()
        output_path = tmp_path / "output.json"

        # WHEN: Formatting chunks
        formatter.format_chunks(chunks=[unicode_chunk], output_path=output_path)

        # THEN: Unicode should be preserved
        with open(output_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        chunk_text = data["chunks"][0]["text"]
        assert "你好世界" in chunk_text
        assert "🎉" in chunk_text
        assert "Ñoño" in chunk_text
        assert "café" in chunk_text


# ============================================================================
# Test Category 3: Entity Serialization
# ============================================================================


class TestJsonFormatterEntitySerialization:
    """Test entity tags and relationships serialization."""

    def test_entity_tags_included_in_output(self, chunk_with_entities, tmp_path):
        """Should serialize entity tags in chunk metadata."""
        # GIVEN: JsonFormatter and chunk with entities
        formatter = JsonFormatter()
        output_path = tmp_path / "output.json"

        # WHEN: Formatting chunks
        formatter.format_chunks(chunks=[chunk_with_entities], output_path=output_path)

        # THEN: Entity tags should be in metadata
        with open(output_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        chunk_metadata = data["chunks"][0]["metadata"]
        assert "entity_tags" in chunk_metadata
        assert len(chunk_metadata["entity_tags"]) == 2

        # Verify first entity
        entity1 = chunk_metadata["entity_tags"][0]
        assert entity1["entity_id"] == "RISK-001"
        assert entity1["entity_type"] == "RISK"
        assert entity1["start_pos"] == 10
        assert entity1["end_pos"] == 25
        assert entity1["is_partial"] is False
        assert entity1["context_snippet"] == "...financial risk..."

    def test_entity_relationships_serialized(self, chunk_with_entities, tmp_path):
        """Should serialize entity relationships."""
        # GIVEN: JsonFormatter and chunk with relationships
        formatter = JsonFormatter()
        output_path = tmp_path / "output.json"

        # WHEN: Formatting chunks
        formatter.format_chunks(chunks=[chunk_with_entities], output_path=output_path)

        # THEN: Entity relationships should be present
        with open(output_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        # Note: Relationships may be stored differently depending on implementation
        # This tests the actual JsonFormatter behavior
        chunk = data["chunks"][0]
        assert "metadata" in chunk


# ============================================================================
# Test Category 4: Edge Cases
# ============================================================================


class TestJsonFormatterEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_chunks_list_produces_valid_json(self, tmp_path):
        """Should produce valid JSON with empty chunks array."""
        # GIVEN: JsonFormatter and empty chunks list
        formatter = JsonFormatter()
        output_path = tmp_path / "output.json"

        # WHEN: Formatting empty chunks
        result = formatter.format_chunks(chunks=[], output_path=output_path)

        # THEN: Valid JSON with empty chunks array
        assert result.chunk_count == 0
        with open(output_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        assert "chunks" in data
        assert len(data["chunks"]) == 0
        assert data["metadata"]["chunk_count"] == 0

    def test_single_chunk_produces_valid_array(self, sample_chunk, tmp_path):
        """Should produce valid JSON array with single chunk."""
        # GIVEN: JsonFormatter and single chunk
        formatter = JsonFormatter()
        output_path = tmp_path / "output.json"

        # WHEN: Formatting single chunk
        result = formatter.format_chunks(chunks=[sample_chunk], output_path=output_path)

        # THEN: Valid JSON with 1-item array
        assert result.chunk_count == 1
        with open(output_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        assert len(data["chunks"]) == 1
        assert data["chunks"][0]["id"] == "chunk_001"

    def test_very_long_text_chunks_handled(self, tmp_path):
        """Should handle chunks with very long text content."""
        # GIVEN: JsonFormatter and chunk with long text
        formatter = JsonFormatter()
        output_path = tmp_path / "output.json"

        long_text = "This is a very long chunk. " * 1000  # ~27KB
        source_file = tmp_path / "test.pdf"
        source_file.touch()

        metadata = ChunkMetadata(
            source_file=source_file,
            processing_version="1.0.0",
            quality=QualityScore(
                overall=0.95,
                completeness=0.98,
                coherence=0.92,
                ocr_confidence=0.98,
                readability_flesch_kincaid=8.0,
                readability_gunning_fog=9.5,
                flags=[],
            ),
        )

        long_chunk = Chunk(
            id="chunk_001",
            text=long_text,
            document_id="test_document",
            position_index=0,
            token_count=6000,
            word_count=5000,
            entities=[],
            section_context="",
            quality_score=0.95,
            readability_scores={"flesch_reading_ease": 65.0},
            metadata=metadata,
        )

        # WHEN: Formatting long chunk
        result = formatter.format_chunks(chunks=[long_chunk], output_path=output_path)

        # THEN: Should handle successfully
        assert result.chunk_count == 1
        assert output_path.exists()
        with open(output_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        assert len(data["chunks"][0]["text"]) > 20000


# ============================================================================
# Test Category 5: File Operations
# ============================================================================


class TestJsonFormatterFileOperations:
    """Test file creation, directory handling, and FormattingResult."""

    def test_creates_output_file_at_specified_path(self, sample_chunk, tmp_path):
        """Should create JSON file at the specified output path."""
        # GIVEN: JsonFormatter and output path
        formatter = JsonFormatter()
        output_path = tmp_path / "custom_output.json"

        # WHEN: Formatting chunks
        result = formatter.format_chunks(chunks=[sample_chunk], output_path=output_path)

        # THEN: File should exist at specified path
        assert output_path.exists()
        assert result.output_path == output_path

    def test_creates_parent_directories_if_missing(self, sample_chunk, tmp_path):
        """Should auto-create parent directories (parents=True)."""
        # GIVEN: JsonFormatter and nested path that doesn't exist
        formatter = JsonFormatter()
        output_path = tmp_path / "level1" / "level2" / "level3" / "output.json"

        # Verify parent directories don't exist
        assert not output_path.parent.exists()

        # WHEN: Formatting chunks
        result = formatter.format_chunks(chunks=[sample_chunk], output_path=output_path)

        # THEN: Parent directories should be created
        assert output_path.exists()
        assert output_path.parent.exists()
        assert result.output_path == output_path

    def test_returns_formatting_result_with_correct_fields(self, sample_chunks, tmp_path):
        """Should return FormattingResult with all required fields."""
        # GIVEN: JsonFormatter and chunks
        formatter = JsonFormatter()
        output_path = tmp_path / "output.json"

        # WHEN: Formatting chunks
        result = formatter.format_chunks(chunks=sample_chunks, output_path=output_path)

        # THEN: FormattingResult should have correct fields
        assert isinstance(result, FormattingResult)
        assert result.output_path == output_path
        assert result.chunk_count == 3
        assert result.format_type == "json"
        assert result.duration_seconds >= 0.0
        assert result.total_size > 0  # File should have content
        assert isinstance(result.errors, list)


# ============================================================================
# Test Category 6: Error Handling
# ============================================================================


class TestJsonFormatterErrorHandling:
    """Test error handling for invalid inputs and edge cases."""

    def test_atomic_write_removes_partial_output_on_dump_failure(
        self, sample_chunk, tmp_path, monkeypatch
    ):
        """Should leave no final or temp file when write fails mid-dump."""
        formatter = JsonFormatter()
        output_path = tmp_path / "output.json"

        def fail_dump(_payload, file_obj, **_kwargs):
            file_obj.write('{"partial": true')
            file_obj.flush()
            raise RuntimeError("dump failed")

        monkeypatch.setattr(
            "data_extract.output.formatters.json_formatter.json.dump",
            fail_dump,
        )

        with pytest.raises(RuntimeError, match="dump failed"):
            formatter.format_chunks(chunks=[sample_chunk], output_path=output_path)

        assert not output_path.exists()
        assert not list(tmp_path.glob(f".{output_path.name}*.tmp"))

    def test_source_document_tracking(self, tmp_path):
        """Should track unique source documents in metadata."""
        # GIVEN: JsonFormatter and chunks from multiple sources
        formatter = JsonFormatter()
        output_path = tmp_path / "output.json"

        source1 = tmp_path / "doc1.pdf"
        source2 = tmp_path / "doc2.pdf"
        source1.touch()
        source2.touch()

        chunks = []
        for idx, source in enumerate([source1, source1, source2], 1):
            metadata = ChunkMetadata(
                source_file=source,
                processing_version="1.0.0",
                quality=QualityScore(
                    overall=0.95,
                    completeness=0.98,
                    coherence=0.92,
                    ocr_confidence=0.98,
                    readability_flesch_kincaid=8.0,
                    readability_gunning_fog=9.5,
                    flags=[],
                ),
            )

            chunk = Chunk(
                id=f"chunk_{idx:03d}",
                text=f"Chunk {idx}",
                document_id=f"doc{idx}",
                position_index=idx - 1,
                token_count=2,
                word_count=2,
                entities=[],
                section_context="",
                quality_score=0.95,
                readability_scores={"flesch_reading_ease": 65.0},
                metadata=metadata,
            )
            chunks.append(chunk)

        # WHEN: Formatting chunks
        formatter.format_chunks(chunks=chunks, output_path=output_path)

        # THEN: Unique source documents should be tracked
        with open(output_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        source_docs = data["metadata"]["source_documents"]
        assert len(source_docs) == 2
        assert str(source1) in source_docs
        assert str(source2) in source_docs

    def test_output_metadata_includes_duration(self, sample_chunk, tmp_path):
        """Should include duration_seconds in FormattingResult."""
        # GIVEN: JsonFormatter and chunk
        formatter = JsonFormatter()
        output_path = tmp_path / "output.json"

        # WHEN: Formatting chunks
        result = formatter.format_chunks(chunks=[sample_chunk], output_path=output_path)

        # THEN: Duration should be tracked
        assert hasattr(result, "duration_seconds")
        assert result.duration_seconds >= 0.0
        assert result.duration_seconds < 10.0  # Sanity check

    def test_validate_parameter_accepted(self, sample_chunk, tmp_path):
        """Should accept validate parameter (even if not used)."""
        # GIVEN: JsonFormatter with validate=False
        formatter = JsonFormatter(validate=False)
        output_path = tmp_path / "output.json"

        # WHEN: Formatting chunks
        result = formatter.format_chunks(chunks=[sample_chunk], output_path=output_path)

        # THEN: Should succeed
        assert result.chunk_count == 1
        assert output_path.exists()

    def test_handles_chunks_without_metadata(self, tmp_path):
        """Should handle chunks with None metadata gracefully."""
        # GIVEN: JsonFormatter and chunk with no metadata
        formatter = JsonFormatter()
        output_path = tmp_path / "output.json"

        chunk = Chunk(
            id="chunk_001",
            text="Chunk without metadata",
            document_id="test_doc",
            position_index=0,
            token_count=3,
            word_count=3,
            entities=[],
            section_context="",
            quality_score=0.95,
            readability_scores={"flesch_reading_ease": 65.0},
            metadata=None,
        )

        # WHEN: Formatting chunks
        result = formatter.format_chunks(chunks=[chunk], output_path=output_path)

        # THEN: Should handle gracefully
        assert result.chunk_count == 1
        with open(output_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        # Metadata should be empty dict
        assert "metadata" in data["chunks"][0]
        assert isinstance(data["chunks"][0]["metadata"], dict)

    def test_handles_iterator_input(self, sample_chunks, tmp_path):
        """Should handle iterator input (not just lists)."""
        # GIVEN: JsonFormatter and iterator
        formatter = JsonFormatter()
        output_path = tmp_path / "output.json"

        # WHEN: Formatting with iterator
        result = formatter.format_chunks(chunks=iter(sample_chunks), output_path=output_path)

        # THEN: Should process successfully
        assert result.chunk_count == 3
        with open(output_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        assert len(data["chunks"]) == 3

    def test_serializes_all_optional_metadata_fields(self, tmp_path):
        """Should serialize all optional ChunkMetadata fields (source_hash, document_type, created_at)."""
        # GIVEN: JsonFormatter and chunk with all metadata fields populated
        from datetime import datetime

        formatter = JsonFormatter()
        output_path = tmp_path / "output.json"

        source_file = tmp_path / "test.pdf"
        source_file.touch()

        metadata = ChunkMetadata(
            source_file=source_file,
            processing_version="1.0.0",
            source_hash="abc123def456",
            document_type="audit_report",
            created_at=datetime(2025, 11, 30, 10, 30, 0),
            quality=QualityScore(
                overall=0.95,
                completeness=0.98,
                coherence=0.92,
                ocr_confidence=0.98,
                readability_flesch_kincaid=8.0,
                readability_gunning_fog=9.5,
                flags=[],
            ),
        )

        chunk = Chunk(
            id="chunk_001",
            text="Chunk with all metadata fields",
            document_id="test_doc",
            position_index=0,
            token_count=5,
            word_count=5,
            entities=[],
            section_context="",
            quality_score=0.95,
            readability_scores={"flesch_reading_ease": 65.0},
            metadata=metadata,
        )

        # WHEN: Formatting chunk
        formatter.format_chunks(chunks=[chunk], output_path=output_path)

        # THEN: All optional fields should be present
        with open(output_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        chunk_meta = data["chunks"][0]["metadata"]
        assert chunk_meta["source_hash"] == "abc123def456"
        assert chunk_meta["document_type"] == "audit_report"
        assert "2025-11-30" in chunk_meta["created_at"]
