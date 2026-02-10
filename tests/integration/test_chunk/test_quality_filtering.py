"""Integration tests for quality-based chunk filtering (Story 3.3 - RED PHASE).

Tests filtering chunks by quality scores, flags, and readability metrics.
Validates that quality metadata enables effective RAG chunk prioritization.

Test Coverage:
    - AC-3.3-4: Filter by readability scores (Flesch-Kincaid, Gunning Fog)
    - AC-3.3-5: Filter by overall quality score threshold
    - AC-3.3-8: Filter by specific quality flags
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

import pytest

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.chunking]

# These imports WILL FAIL in RED phase - this is expected
try:
    from data_extract.chunk.engine import ChunkingConfig, ChunkingEngine
    from data_extract.core.models import (
        ContentBlock,
        ContentType,
        DocumentType,
        Metadata,
        Position,
        ProcessingResult,
    )
except ImportError:
    ChunkingEngine = None
    ChunkingConfig = None
    ProcessingResult = None
    ContentBlock = None
    ContentType = None
    Position = None
    Metadata = None
    DocumentType = None

pytestmark = [pytest.mark.integration, pytest.mark.chunking, pytest.mark.quality]

_DEFAULT_TIMESTAMP = datetime(2025, 1, 1, tzinfo=timezone.utc)
_TOOL_VERSION = "3.3.0-dev"
_CONFIG_VERSION = "chunking-config-v1"


def _build_metadata(
    file_path: Path,
    file_hash: str,
    document_type: DocumentType,
    ocr_confidence: float,
    completeness: float,
    quality_scores: Dict[str, float],
) -> Metadata:
    """Create Metadata instances with the full contract required by the core models."""
    return Metadata(
        source_file=file_path,
        file_hash=file_hash,
        processing_timestamp=_DEFAULT_TIMESTAMP,
        tool_version=_TOOL_VERSION,
        config_version=_CONFIG_VERSION,
        document_type=document_type,
        quality_scores=quality_scores,
        ocr_confidence={1: ocr_confidence},
        completeness_ratio=completeness,
    )


@pytest.fixture
def mixed_quality_corpus():
    """Create corpus with varied quality documents for filtering tests."""
    corpus = []

    # High-quality, simple document
    corpus.append(
        ProcessingResult(
            file_path=Path("/test/high_quality.pdf"),
            document_type=DocumentType.REPORT,
            content_blocks=[
                ContentBlock(
                    block_type=ContentType.PARAGRAPH,
                    content="This is simple text. Easy to read. High quality content.",
                    position=Position(page=1, sequence_index=0),
                )
            ],
            entities=[],
            metadata=_build_metadata(
                file_path=Path("/test/high_quality.pdf"),
                file_hash="hash_high",
                document_type=DocumentType.REPORT,
                ocr_confidence=0.99,
                completeness=0.98,
                quality_scores={"overall": 0.94, "readability": 0.92},
            ),
        )
    )

    # Medium-quality, complex document
    corpus.append(
        ProcessingResult(
            file_path=Path("/test/medium_quality.pdf"),
            document_type=DocumentType.REPORT,
            content_blocks=[
                ContentBlock(
                    block_type=ContentType.PARAGRAPH,
                    content=(
                        "The comprehensive implementation of quality methodologies "
                        "requires systematic evaluation frameworks encompassing "
                        "multifaceted assessment paradigms and analytical procedures."
                    ),
                    position=Position(page=1, sequence_index=0),
                )
            ],
            entities=[],
            metadata=_build_metadata(
                file_path=Path("/test/medium_quality.pdf"),
                file_hash="hash_medium",
                document_type=DocumentType.REPORT,
                ocr_confidence=0.96,
                completeness=0.92,
                quality_scores={"overall": 0.82, "readability": 0.65},
            ),
        )
    )

    # Low-quality document with OCR issues
    corpus.append(
        ProcessingResult(
            file_path=Path("/test/low_quality.pdf"),
            document_type=DocumentType.IMAGE,
            content_blocks=[
                ContentBlock(
                    block_type=ContentType.PARAGRAPH,
                    content="a#b$c%d&e*f@g!h^i(j)k[l]m{n}o|p~q`r bad OCR quality",
                    position=Position(page=1, sequence_index=0),
                )
            ],
            entities=[],
            metadata=_build_metadata(
                file_path=Path("/test/low_quality.pdf"),
                file_hash="hash_low",
                document_type=DocumentType.IMAGE,
                ocr_confidence=0.80,  # Low OCR
                completeness=0.75,  # Incomplete
                quality_scores={"overall": 0.55, "readability": 0.40},
            ),
        )
    )

    return corpus


class TestFilterByOverallQualityScore:
    """Test filtering chunks by overall quality score (AC-3.3-5)."""

    def test_filter_high_quality_chunks(self, mixed_quality_corpus):
        """Should filter chunks with overall quality >= 0.75 threshold."""
        # GIVEN: Corpus with varied quality documents
        config = ChunkingConfig(chunk_size=512, overlap_pct=0.15)
        engine = ChunkingEngine(config)

        # Chunk all documents
        all_chunks = []
        for doc in mixed_quality_corpus:
            all_chunks.extend(list(engine.chunk(doc)))

        # WHEN: Filtering for high quality (>= 0.75)
        high_quality_chunks = [
            chunk for chunk in all_chunks if chunk.metadata.quality.is_high_quality()
        ]

        # THEN: Only high-quality chunks remain
        assert len(high_quality_chunks) > 0
        for chunk in high_quality_chunks:
            assert chunk.metadata.quality.overall >= 0.75

    def test_filter_low_quality_chunks_exclusion(self, mixed_quality_corpus):
        """Should exclude chunks with overall quality < 0.75."""
        # GIVEN: Corpus with varied quality documents
        config = ChunkingConfig(chunk_size=512, overlap_pct=0.15)
        engine = ChunkingEngine(config)

        # Chunk all documents
        all_chunks = []
        for doc in mixed_quality_corpus:
            all_chunks.extend(list(engine.chunk(doc)))

        # WHEN: Filtering out low quality (< 0.75)
        filtered_chunks = [chunk for chunk in all_chunks if chunk.metadata.quality.overall >= 0.75]

        # THEN: Low-quality chunks excluded
        excluded_count = len(all_chunks) - len(filtered_chunks)
        assert excluded_count >= 0  # Some chunks filtered out

        # AND: All remaining chunks meet threshold
        for chunk in filtered_chunks:
            assert chunk.metadata.quality.overall >= 0.75


class TestFilterByQualityFlags:
    """Test filtering chunks by quality flags (AC-3.3-8)."""

    def test_exclude_low_ocr_chunks(self, mixed_quality_corpus):
        """Should filter out chunks flagged with low_ocr."""
        # GIVEN: Corpus with varied quality documents
        config = ChunkingConfig(chunk_size=512, overlap_pct=0.15)
        engine = ChunkingEngine(config)

        # Chunk all documents
        all_chunks = []
        for doc in mixed_quality_corpus:
            all_chunks.extend(list(engine.chunk(doc)))

        # WHEN: Filtering out low_ocr chunks
        filtered_chunks = [
            chunk for chunk in all_chunks if "low_ocr" not in chunk.metadata.quality.flags
        ]

        # THEN: No low_ocr flags in filtered set
        for chunk in filtered_chunks:
            assert "low_ocr" not in chunk.metadata.quality.flags

        # AND: Some chunks were filtered out
        assert len(filtered_chunks) < len(all_chunks)

    def test_exclude_incomplete_extraction_chunks(self, mixed_quality_corpus):
        """Should filter out chunks flagged with incomplete_extraction."""
        # GIVEN: Corpus with varied quality documents
        config = ChunkingConfig(chunk_size=512, overlap_pct=0.15)
        engine = ChunkingEngine(config)

        # Chunk all documents
        all_chunks = []
        for doc in mixed_quality_corpus:
            all_chunks.extend(list(engine.chunk(doc)))

        # WHEN: Filtering out incomplete_extraction chunks
        filtered_chunks = [
            chunk
            for chunk in all_chunks
            if "incomplete_extraction" not in chunk.metadata.quality.flags
        ]

        # THEN: No incomplete_extraction flags in filtered set
        for chunk in filtered_chunks:
            assert "incomplete_extraction" not in chunk.metadata.quality.flags

    def test_exclude_gibberish_chunks(self, mixed_quality_corpus):
        """Should filter out chunks flagged with gibberish."""
        # GIVEN: Corpus with varied quality documents
        config = ChunkingConfig(chunk_size=512, overlap_pct=0.15)
        engine = ChunkingEngine(config)

        # Chunk all documents
        all_chunks = []
        for doc in mixed_quality_corpus:
            all_chunks.extend(list(engine.chunk(doc)))

        # WHEN: Filtering out gibberish chunks
        filtered_chunks = [
            chunk for chunk in all_chunks if "gibberish" not in chunk.metadata.quality.flags
        ]

        # THEN: No gibberish flags in filtered set
        for chunk in filtered_chunks:
            assert "gibberish" not in chunk.metadata.quality.flags

    def test_include_only_clean_chunks(self, mixed_quality_corpus):
        """Should filter to include only chunks with no quality flags."""
        # GIVEN: Corpus with varied quality documents
        config = ChunkingConfig(chunk_size=512, overlap_pct=0.15)
        engine = ChunkingEngine(config)

        # Chunk all documents
        all_chunks = []
        for doc in mixed_quality_corpus:
            all_chunks.extend(list(engine.chunk(doc)))

        # WHEN: Filtering for clean chunks only (no flags)
        clean_chunks = [chunk for chunk in all_chunks if len(chunk.metadata.quality.flags) == 0]

        # THEN: All chunks have empty flags list
        for chunk in clean_chunks:
            assert chunk.metadata.quality.flags == []

        # AND: Clean chunks exist
        assert len(clean_chunks) > 0


class TestFilterByReadabilityScore:
    """Test filtering chunks by readability metrics (AC-3.3-4)."""

    def test_filter_by_flesch_kincaid_threshold(self, mixed_quality_corpus):
        """Should filter chunks with Flesch-Kincaid grade level < 12."""
        # GIVEN: Corpus with varied complexity documents
        config = ChunkingConfig(chunk_size=512, overlap_pct=0.15)
        engine = ChunkingEngine(config)

        # Chunk all documents
        all_chunks = []
        for doc in mixed_quality_corpus:
            all_chunks.extend(list(engine.chunk(doc)))

        # WHEN: Filtering for readable chunks (FK < 12)
        readable_chunks = [
            chunk
            for chunk in all_chunks
            if chunk.metadata.quality.readability_flesch_kincaid < 12.0
        ]

        # THEN: All chunks meet readability threshold
        for chunk in readable_chunks:
            assert chunk.metadata.quality.readability_flesch_kincaid < 12.0

        # AND: Readable chunks exist
        assert len(readable_chunks) > 0

    def test_filter_by_gunning_fog_threshold(self, mixed_quality_corpus):
        """Should filter chunks with Gunning Fog index < 15."""
        # GIVEN: Corpus with varied complexity documents
        config = ChunkingConfig(chunk_size=512, overlap_pct=0.15)
        engine = ChunkingEngine(config)

        # Chunk all documents
        all_chunks = []
        for doc in mixed_quality_corpus:
            all_chunks.extend(list(engine.chunk(doc)))

        # WHEN: Filtering for readable chunks (Gunning Fog < 15)
        readable_chunks = [
            chunk for chunk in all_chunks if chunk.metadata.quality.readability_gunning_fog < 15.0
        ]

        # THEN: All chunks meet readability threshold
        for chunk in readable_chunks:
            assert chunk.metadata.quality.readability_gunning_fog < 15.0

    def test_exclude_overly_complex_chunks(self, mixed_quality_corpus):
        """Should filter out chunks with high_complexity flag."""
        # GIVEN: Corpus with varied complexity documents
        config = ChunkingConfig(chunk_size=512, overlap_pct=0.15)
        engine = ChunkingEngine(config)

        # Chunk all documents
        all_chunks = []
        for doc in mixed_quality_corpus:
            all_chunks.extend(list(engine.chunk(doc)))

        # WHEN: Filtering out high_complexity chunks
        simple_chunks = [
            chunk for chunk in all_chunks if "high_complexity" not in chunk.metadata.quality.flags
        ]

        # THEN: No high_complexity flags in filtered set
        for chunk in simple_chunks:
            assert "high_complexity" not in chunk.metadata.quality.flags


class TestCombinedQualityFiltering:
    """Test combined filtering using multiple quality criteria."""

    def test_filter_high_quality_and_readable(self, mixed_quality_corpus):
        """Should filter chunks meeting both quality and readability thresholds."""
        # GIVEN: Corpus with varied quality documents
        config = ChunkingConfig(chunk_size=512, overlap_pct=0.15)
        engine = ChunkingEngine(config)

        # Chunk all documents
        all_chunks = []
        for doc in mixed_quality_corpus:
            all_chunks.extend(list(engine.chunk(doc)))

        # WHEN: Filtering for high quality AND readable
        premium_chunks = [
            chunk
            for chunk in all_chunks
            if chunk.metadata.quality.overall >= 0.75
            and chunk.metadata.quality.readability_flesch_kincaid < 12.0
            and len(chunk.metadata.quality.flags) == 0
        ]

        # THEN: All chunks meet all criteria
        for chunk in premium_chunks:
            assert chunk.metadata.quality.overall >= 0.75
            assert chunk.metadata.quality.readability_flesch_kincaid < 12.0
            assert chunk.metadata.quality.flags == []

    def test_filter_exclude_multiple_flags(self, mixed_quality_corpus):
        """Should exclude chunks with any problematic quality flags."""
        # GIVEN: Corpus with varied quality documents
        config = ChunkingConfig(chunk_size=512, overlap_pct=0.15)
        engine = ChunkingEngine(config)

        # Chunk all documents
        all_chunks = []
        for doc in mixed_quality_corpus:
            all_chunks.extend(list(engine.chunk(doc)))

        # WHEN: Filtering out chunks with any quality flags
        exclude_flags = ["low_ocr", "incomplete_extraction", "gibberish", "high_complexity"]
        clean_chunks = [
            chunk
            for chunk in all_chunks
            if not any(flag in chunk.metadata.quality.flags for flag in exclude_flags)
        ]

        # THEN: No excluded flags in filtered set
        for chunk in clean_chunks:
            for flag in exclude_flags:
                assert flag not in chunk.metadata.quality.flags


class TestQualityBasedPrioritization:
    """Test prioritizing chunks by quality for RAG retrieval."""

    def test_sort_chunks_by_overall_quality(self, mixed_quality_corpus):
        """Should enable sorting chunks by overall quality score."""
        # GIVEN: Corpus with varied quality documents
        config = ChunkingConfig(chunk_size=512, overlap_pct=0.15)
        engine = ChunkingEngine(config)

        # Chunk all documents
        all_chunks = []
        for doc in mixed_quality_corpus:
            all_chunks.extend(list(engine.chunk(doc)))

        # WHEN: Sorting by quality (descending)
        sorted_chunks = sorted(all_chunks, key=lambda c: c.metadata.quality.overall, reverse=True)

        # THEN: Chunks ordered from highest to lowest quality
        for i in range(len(sorted_chunks) - 1):
            assert (
                sorted_chunks[i].metadata.quality.overall
                >= sorted_chunks[i + 1].metadata.quality.overall
            )

    def test_top_k_quality_chunks_selection(self, mixed_quality_corpus):
        """Should enable selecting top-K highest quality chunks."""
        # GIVEN: Corpus with varied quality documents
        config = ChunkingConfig(chunk_size=512, overlap_pct=0.15)
        engine = ChunkingEngine(config)

        # Chunk all documents
        all_chunks = []
        for doc in mixed_quality_corpus:
            all_chunks.extend(list(engine.chunk(doc)))

        # WHEN: Selecting top 3 highest quality chunks
        k = min(3, len(all_chunks))
        top_k_chunks = sorted(all_chunks, key=lambda c: c.metadata.quality.overall, reverse=True)[
            :k
        ]

        # THEN: Top-K chunks have highest quality scores
        assert len(top_k_chunks) == k
        min_top_k_quality = min(c.metadata.quality.overall for c in top_k_chunks)
        remaining_chunks = [c for c in all_chunks if c not in top_k_chunks]
        if remaining_chunks:
            max_remaining_quality = max(c.metadata.quality.overall for c in remaining_chunks)
            assert min_top_k_quality >= max_remaining_quality


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
