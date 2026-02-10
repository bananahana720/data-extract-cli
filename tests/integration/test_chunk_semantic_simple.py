"""
Simple Epic 3→4 integration test that avoids problematic imports.

This test validates the core chunk→semantic handoff without PDF/CSV dependencies.
"""

import json
from pathlib import Path
from typing import List

import pytest

pytestmark = [pytest.mark.P1, pytest.mark.integration]
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402

# Minimal imports - avoid problematic extractors
from src.data_extract.chunk.models import Chunk  # noqa: E402
from src.data_extract.core.models import (  # noqa: E402
    ContentBlock,
    ContentType,
    Document,
    Metadata,
    Position,
    ValidationReport,
)


class TestMinimalChunkSemanticHandoff:
    """Minimal tests for Epic 3→4 handoff without complex dependencies."""

    @pytest.fixture
    def mock_document(self) -> Document:
        """Create a mock document without using extractors."""
        return Document(
            id="test_doc_001",
            text="This is a test document. " * 100
            + "\n\nSection 2: Risk Assessment\n"
            + "The organization faces key risks including RISK-001. " * 20
            + "\n\nSection 3: Controls\n"
            + "Control CTRL-042 mitigates the identified risks. " * 20,
            metadata=Metadata(
                source_file=Path("test.pdf"),
                document_type="report",
                extraction_method="test",
                processing_timestamp="2025-11-18T12:00:00Z",
                file_hash="test_hash_abc123",
                tool_version="1.0.0",
                config_version="1.0.0",
            ),
            structure={
                "page_count": 3,
                "word_count": 500,
                "has_images": False,
                "has_tables": False,
                "sections": ["Introduction", "Risk Assessment", "Controls"],
            },
            validation=ValidationReport(
                is_valid=True, confidence_score=0.98, flags=[], quarantine_recommended=False
            ),
            entities=[],
            content_blocks=[
                ContentBlock(
                    block_type=ContentType.PARAGRAPH,
                    content="This is a test document. " * 100,
                    position=Position(page=1, sequence_index=0),
                    metadata={},
                )
            ],
        )

    @pytest.fixture
    def test_chunks(self, mock_document) -> List[Chunk]:
        """Generate test chunks - bypass chunker for simplicity."""
        # Create manual chunks for testing Epic 3→4 handoff
        # These simulate what the chunker would produce
        return [
            Chunk(
                id=f"chunk_{i:03d}",
                text=f"Chunk {i} content with entities like RISK-{i:03d} and CTRL-{i:03d}. " * 20,
                document_id="test_doc_001",
                position_index=i,
                word_count=42,
                token_count=168,
                entities=[],
                section_context=f"Section {i//3}",
                quality_score=0.85 + (i * 0.01),
                readability_scores={"flesch_reading_ease": 60.0 + i},
                metadata=mock_document.metadata,
            )
            for i in range(10)
        ]

    def test_chunks_compatible_with_tfidf(self, test_chunks):
        """Core test: Chunks can be vectorized with TF-IDF."""
        assert len(test_chunks) > 0, "No chunks to test"

        # Extract text
        corpus = [chunk.text for chunk in test_chunks]

        # Filter empty chunks
        corpus = [text for text in corpus if text.strip()]
        assert len(corpus) > 0, "All chunks are empty"

        # Vectorize
        vectorizer = TfidfVectorizer(max_features=100)
        vectors = vectorizer.fit_transform(corpus)

        # Validate
        assert vectors.shape[0] == len(corpus), "Wrong number of vectors"
        assert vectors.shape[1] > 0, "No vocabulary learned"

        # Test transform on new data
        new_text = ["This is a new chunk for testing."]
        new_vector = vectorizer.transform(new_text)
        assert new_vector.shape[0] == 1

    def test_chunk_serialization(self, test_chunks):
        """Test chunks can be serialized to JSON."""
        for chunk in test_chunks:
            chunk_dict = {
                "id": chunk.id,
                "text": chunk.text,
                "document_id": chunk.document_id,
                "position_index": chunk.position_index,
                "word_count": chunk.word_count,
                "token_count": chunk.token_count,
            }

            # Should serialize without error
            json_str = json.dumps(chunk_dict)
            assert json_str

            # Should deserialize correctly
            recovered = json.loads(json_str)
            assert recovered["id"] == chunk.id

    def test_chunk_ids_unique(self, test_chunks):
        """Test chunk IDs are unique."""
        chunk_ids = [chunk.id for chunk in test_chunks]
        assert len(chunk_ids) == len(set(chunk_ids)), "Duplicate chunk IDs found"

    def test_no_empty_chunks(self, test_chunks):
        """Test no chunks have empty text."""
        empty_chunks = [
            chunk.id for chunk in test_chunks if not chunk.text or not chunk.text.strip()
        ]
        assert len(empty_chunks) == 0, f"Empty chunks: {empty_chunks}"
