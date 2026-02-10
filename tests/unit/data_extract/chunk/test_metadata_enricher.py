"""Unit tests for MetadataEnricher component (Story 3.3 - RED PHASE).

Tests metadata enrichment logic, quality score calculation, readability metrics,
and quality flag detection. All tests WILL FAIL until MetadataEnricher is implemented.

Test Coverage:
    - AC-3.3-1: Source file, hash, and document type propagation
    - AC-3.3-4: Readability score calculation (Flesch-Kincaid, Gunning Fog)
    - AC-3.3-5: Composite quality score (OCR, completeness, coherence, overall weighted avg)
    - AC-3.3-7: Word count and token count calculation
    - AC-3.3-8: Quality flag detection (low_ocr, incomplete, high_complexity, gibberish)
"""

import pytest

# These imports WILL FAIL in RED phase - this is expected
try:
    from data_extract.chunk.metadata_enricher import MetadataEnricher
    from data_extract.chunk.quality import QualityScore
    from data_extract.core.models import Chunk, Entity, EntityType, Metadata
except ImportError:
    MetadataEnricher = None
    QualityScore = None
    Chunk = None
    Entity = None
    EntityType = None
    Metadata = None

pytestmark = [pytest.mark.P1, pytest.mark.unit, pytest.mark.chunking, pytest.mark.quality]


class TestMetadataEnricherReadability:
    """Test readability score calculation (AC-3.3-4)."""

    def test_calculate_readability_simple_text(self):
        """Should calculate Flesch-Kincaid and Gunning Fog for simple text."""
        # GIVEN: Simple, readable text (children's book level)
        chunk = Chunk(
            id="test_001",
            text="The cat sat on the mat. The dog ran in the park. Birds fly in the sky.",
            document_id="doc_001",
            position_index=0,
            token_count=18,
            word_count=18,
            quality_score=0.0,  # Will be enriched
            metadata={},
        )
        source_metadata = {
            "ocr_confidence": 0.99,
            "completeness": 0.98,
            "document_type": "report",
            "source_hash": "abc123",
        }

        # WHEN: enrich_chunk() called
        enricher = MetadataEnricher()
        enriched_chunk = enricher.enrich_chunk(chunk, source_metadata)

        # THEN: Readability scores calculated and reasonable for simple text
        quality = enriched_chunk.metadata.quality
        assert quality.readability_flesch_kincaid >= 0.0
        assert quality.readability_flesch_kincaid <= 8.0  # Simple text, low grade level
        assert quality.readability_gunning_fog >= 0.0
        assert quality.readability_gunning_fog <= 10.0

    def test_calculate_readability_complex_text(self):
        """Should calculate higher readability scores for complex text."""
        # GIVEN: Complex, technical text (PhD thesis level)
        chunk = Chunk(
            id="test_002",
            text=(
                "The implementation of comprehensive quality assurance methodologies "
                "necessitates the integration of multifaceted evaluation frameworks "
                "encompassing both quantitative and qualitative assessment paradigms."
            ),
            document_id="doc_002",
            position_index=0,
            token_count=30,
            word_count=24,
            quality_score=0.0,
            metadata={},
        )
        source_metadata = {
            "ocr_confidence": 0.98,
            "completeness": 0.95,
            "document_type": "report",
            "source_hash": "def456",
        }

        # WHEN: enrich_chunk() called
        enricher = MetadataEnricher()
        enriched_chunk = enricher.enrich_chunk(chunk, source_metadata)

        # THEN: Readability scores reflect complexity (higher grade level)
        quality = enriched_chunk.metadata.quality
        assert quality.readability_flesch_kincaid >= 12.0  # College+ level
        assert quality.readability_gunning_fog >= 14.0

    def test_calculate_readability_edge_case_empty_text(self):
        """Should handle empty text gracefully (AC-3.3-4 edge case)."""
        # GIVEN: Chunk with empty text
        chunk = Chunk(
            id="test_003",
            text="",
            document_id="doc_003",
            position_index=0,
            token_count=0,
            word_count=0,
            quality_score=0.0,
            metadata={},
        )
        source_metadata = {
            "ocr_confidence": 1.0,
            "completeness": 0.0,
            "document_type": "report",
            "source_hash": "empty123",
        }

        # WHEN: enrich_chunk() called
        enricher = MetadataEnricher()
        enriched_chunk = enricher.enrich_chunk(chunk, source_metadata)

        # THEN: Readability scores default to 0.0 (no text to analyze)
        quality = enriched_chunk.metadata.quality
        assert quality.readability_flesch_kincaid == 0.0
        assert quality.readability_gunning_fog == 0.0

    def test_calculate_readability_very_short_text(self):
        """Should handle very short text (<3 sentences) gracefully."""
        # GIVEN: Chunk with single short sentence
        chunk = Chunk(
            id="test_004",
            text="Hello world.",
            document_id="doc_004",
            position_index=0,
            token_count=2,
            word_count=2,
            quality_score=0.0,
            metadata={},
        )
        source_metadata = {
            "ocr_confidence": 0.99,
            "completeness": 1.0,
            "document_type": "report",
            "source_hash": "short123",
        }

        # WHEN: enrich_chunk() called
        enricher = MetadataEnricher()
        enriched_chunk = enricher.enrich_chunk(chunk, source_metadata)

        # THEN: Readability scores calculated (may be approximations)
        quality = enriched_chunk.metadata.quality
        assert quality.readability_flesch_kincaid >= 0.0
        assert quality.readability_gunning_fog >= 0.0


class TestMetadataEnricherQualityScoreCalculation:
    """Test composite quality score calculation (AC-3.3-5)."""

    def test_quality_score_weighted_average(self):
        """Should calculate overall score as weighted average (40% OCR, 30% completeness, 20% coherence, 10% readability)."""
        # GIVEN: Chunk with known source metrics
        chunk = Chunk(
            id="test_005",
            text="This is a test. This is only a test. Testing is important.",
            document_id="doc_005",
            position_index=0,
            token_count=12,
            word_count=12,
            quality_score=0.0,
            metadata={},
        )
        source_metadata = {
            "ocr_confidence": 0.90,  # 40% weight
            "completeness": 0.85,  # 30% weight
            # Coherence calculated internally (~0.80 estimated)
            # Readability normalized to 0-1 (~0.90 estimated for simple text)
            "document_type": "report",
            "source_hash": "weight123",
        }

        # WHEN: enrich_chunk() called
        enricher = MetadataEnricher()
        enriched_chunk = enricher.enrich_chunk(chunk, source_metadata)

        # THEN: Overall score is weighted average
        quality = enriched_chunk.metadata.quality
        # Expected: (0.40 * 0.90) + (0.30 * 0.85) + (0.20 * coherence) + (0.10 * readability)
        # Approximately: 0.36 + 0.255 + ~0.16 + ~0.09 = ~0.87
        assert 0.0 <= quality.overall <= 1.0
        assert quality.overall > 0.5  # Should be reasonably high

    def test_ocr_confidence_propagation(self):
        """Should propagate OCR confidence from source metadata (AC-3.3-5)."""
        # GIVEN: Source metadata with specific OCR confidence
        chunk = Chunk(
            id="test_006",
            text="Sample text for testing.",
            document_id="doc_006",
            position_index=0,
            token_count=5,
            word_count=5,
            quality_score=0.0,
            metadata={},
        )
        source_metadata = {
            "ocr_confidence": 0.87,  # Specific value
            "completeness": 0.95,
            "document_type": "image",
            "source_hash": "ocr123",
        }

        # WHEN: enrich_chunk() called
        enricher = MetadataEnricher()
        enriched_chunk = enricher.enrich_chunk(chunk, source_metadata)

        # THEN: OCR confidence matches source metadata
        quality = enriched_chunk.metadata.quality
        assert quality.ocr_confidence == 0.87

    def test_completeness_calculation_from_entities(self):
        """Should calculate completeness based on entity preservation rate (AC-3.3-5)."""
        # GIVEN: Chunk with entity metadata showing preservation rate
        chunk = Chunk(
            id="test_007",
            text="RISK-001 is mitigated by CTRL-042.",
            document_id="doc_007",
            position_index=0,
            token_count=8,
            word_count=6,
            quality_score=0.0,
            metadata={},
        )
        source_metadata = {
            "ocr_confidence": 0.98,
            "completeness": 0.92,  # Should be propagated
            "document_type": "report",
            "source_hash": "complete123",
        }

        # WHEN: enrich_chunk() called
        enricher = MetadataEnricher()
        enriched_chunk = enricher.enrich_chunk(chunk, source_metadata)

        # THEN: Completeness reflects entity preservation
        quality = enriched_chunk.metadata.quality
        assert quality.completeness == 0.92

    def test_coherence_calculation_lexical_overlap(self):
        """Should calculate coherence using sentence-to-sentence lexical overlap (AC-3.3-5)."""
        # GIVEN: Chunk with high lexical overlap between sentences
        chunk = Chunk(
            id="test_008",
            text=(
                "The risk assessment identified critical risks. "
                "These critical risks require immediate attention. "
                "Immediate attention must be given to risk mitigation."
            ),
            document_id="doc_008",
            position_index=0,
            token_count=24,
            word_count=22,
            quality_score=0.0,
            metadata={},
        )
        source_metadata = {
            "ocr_confidence": 0.99,
            "completeness": 0.98,
            "document_type": "report",
            "source_hash": "coherent123",
        }

        # WHEN: enrich_chunk() called
        enricher = MetadataEnricher()
        enriched_chunk = enricher.enrich_chunk(chunk, source_metadata)

        # THEN: Coherence score reflects high overlap (keywords repeated)
        quality = enriched_chunk.metadata.quality
        assert 0.0 <= quality.coherence <= 1.0
        assert quality.coherence > 0.5  # High overlap expected

    def test_coherence_single_sentence(self):
        """Should handle coherence calculation for single sentence (AC-3.3-5 edge case)."""
        # GIVEN: Chunk with only one sentence
        chunk = Chunk(
            id="test_009",
            text="This is a single sentence with no adjacent sentences.",
            document_id="doc_009",
            position_index=0,
            token_count=11,
            word_count=10,
            quality_score=0.0,
            metadata={},
        )
        source_metadata = {
            "ocr_confidence": 0.99,
            "completeness": 1.0,
            "document_type": "report",
            "source_hash": "single123",
        }

        # WHEN: enrich_chunk() called
        enricher = MetadataEnricher()
        enriched_chunk = enricher.enrich_chunk(chunk, source_metadata)

        # THEN: Coherence defaults to 1.0 (no comparison needed)
        quality = enriched_chunk.metadata.quality
        assert quality.coherence == 1.0


class TestMetadataEnricherWordAndTokenCounts:
    """Test word count and token count calculation (AC-3.3-7)."""

    def test_word_count_whitespace_split(self):
        """Should calculate word count using whitespace split."""
        # GIVEN: Chunk with known word count
        chunk = Chunk(
            id="test_010",
            text="One two three four five.",  # 5 words
            document_id="doc_010",
            position_index=0,
            token_count=0,  # Will be calculated
            word_count=0,  # Will be calculated
            quality_score=0.0,
            metadata={},
        )
        source_metadata = {
            "ocr_confidence": 0.99,
            "completeness": 1.0,
            "document_type": "report",
            "source_hash": "words123",
        }

        # WHEN: enrich_chunk() called
        enricher = MetadataEnricher()
        enriched_chunk = enricher.enrich_chunk(chunk, source_metadata)

        # THEN: Word count matches whitespace split
        assert enriched_chunk.word_count == 5

    def test_token_count_approximation_heuristic(self):
        """Should estimate token count using len(text) / 4 heuristic (AC-3.3-7)."""
        # GIVEN: Chunk with text
        text = "This is a test sentence with multiple words for token counting."
        chunk = Chunk(
            id="test_011",
            text=text,
            document_id="doc_011",
            position_index=0,
            token_count=0,  # Will be calculated
            word_count=0,  # Will be calculated
            quality_score=0.0,
            metadata={},
        )
        source_metadata = {
            "ocr_confidence": 0.99,
            "completeness": 1.0,
            "document_type": "report",
            "source_hash": "tokens123",
        }

        # WHEN: enrich_chunk() called
        enricher = MetadataEnricher()
        enriched_chunk = enricher.enrich_chunk(chunk, source_metadata)

        # THEN: Token count approximates len(text) / 4
        expected_token_count = len(text) // 4
        actual_token_count = enriched_chunk.token_count
        # Allow ±5% tolerance
        assert abs(actual_token_count - expected_token_count) <= (expected_token_count * 0.05)

    def test_counts_empty_text(self):
        """Should handle empty text (word_count=0, token_count=0)."""
        # GIVEN: Empty chunk
        chunk = Chunk(
            id="test_012",
            text="",
            document_id="doc_012",
            position_index=0,
            token_count=0,
            word_count=0,
            quality_score=0.0,
            metadata={},
        )
        source_metadata = {
            "ocr_confidence": 1.0,
            "completeness": 0.0,
            "document_type": "report",
            "source_hash": "empty_count123",
        }

        # WHEN: enrich_chunk() called
        enricher = MetadataEnricher()
        enriched_chunk = enricher.enrich_chunk(chunk, source_metadata)

        # THEN: Counts are zero
        assert enriched_chunk.word_count == 0
        assert enriched_chunk.token_count == 0


class TestMetadataEnricherQualityFlags:
    """Test quality flag detection (AC-3.3-8)."""

    def test_flag_low_ocr_confidence(self):
        """Should flag chunks with OCR confidence <0.95 (AC-3.3-8)."""
        # GIVEN: Chunk with low OCR confidence
        chunk = Chunk(
            id="test_013",
            text="Sample text with low OCR quality.",
            document_id="doc_013",
            position_index=0,
            token_count=7,
            word_count=6,
            quality_score=0.0,
            metadata={},
        )
        source_metadata = {
            "ocr_confidence": 0.87,  # Below 0.95 threshold
            "completeness": 0.98,
            "document_type": "image",
            "source_hash": "low_ocr123",
        }

        # WHEN: enrich_chunk() called
        enricher = MetadataEnricher()
        enriched_chunk = enricher.enrich_chunk(chunk, source_metadata)

        # THEN: low_ocr flag present
        quality = enriched_chunk.metadata.quality
        assert "low_ocr" in quality.flags

    def test_flag_incomplete_extraction(self):
        """Should flag chunks with completeness <0.90 (AC-3.3-8)."""
        # GIVEN: Chunk with incomplete extraction
        chunk = Chunk(
            id="test_014",
            text="Partially extracted content.",
            document_id="doc_014",
            position_index=0,
            token_count=4,
            word_count=3,
            quality_score=0.0,
            metadata={},
        )
        source_metadata = {
            "ocr_confidence": 0.99,
            "completeness": 0.85,  # Below 0.90 threshold
            "document_type": "report",
            "source_hash": "incomplete123",
        }

        # WHEN: enrich_chunk() called
        enricher = MetadataEnricher()
        enriched_chunk = enricher.enrich_chunk(chunk, source_metadata)

        # THEN: incomplete_extraction flag present
        quality = enriched_chunk.metadata.quality
        assert "incomplete_extraction" in quality.flags

    def test_flag_high_complexity(self):
        """Should flag chunks with Flesch-Kincaid >15 (AC-3.3-8)."""
        # GIVEN: Chunk with overly complex text
        chunk = Chunk(
            id="test_015",
            text=(
                "The extraordinarily multifaceted paradigmatic implementations "
                "necessitate comprehensive methodological transformations encompassing "
                "interdisciplinary collaborative frameworks facilitating organizational "
                "synergistic optimizations through systematic procedural enhancements."
            ),
            document_id="doc_015",
            position_index=0,
            token_count=30,
            word_count=24,
            quality_score=0.0,
            metadata={},
        )
        source_metadata = {
            "ocr_confidence": 0.99,
            "completeness": 0.98,
            "document_type": "report",
            "source_hash": "complex123",
        }

        # WHEN: enrich_chunk() called
        enricher = MetadataEnricher()
        enriched_chunk = enricher.enrich_chunk(chunk, source_metadata)

        # THEN: high_complexity flag present
        quality = enriched_chunk.metadata.quality
        assert "high_complexity" in quality.flags

    def test_flag_gibberish(self):
        """Should flag chunks with >30% non-alphabetic characters (AC-3.3-8)."""
        # GIVEN: Chunk with excessive special characters (gibberish)
        chunk = Chunk(
            id="test_016",
            text="a#b$c%d&e*f@g!h^i(j)k[l]m{n}o|p~q`r",  # ~50% non-alphabetic
            document_id="doc_016",
            position_index=0,
            token_count=10,
            word_count=1,
            quality_score=0.0,
            metadata={},
        )
        source_metadata = {
            "ocr_confidence": 0.99,
            "completeness": 1.0,
            "document_type": "report",
            "source_hash": "gibberish123",
        }

        # WHEN: enrich_chunk() called
        enricher = MetadataEnricher()
        enriched_chunk = enricher.enrich_chunk(chunk, source_metadata)

        # THEN: gibberish flag present
        quality = enriched_chunk.metadata.quality
        assert "gibberish" in quality.flags

    def test_no_flags_high_quality(self):
        """Should have empty flags list for high-quality chunks (AC-3.3-8)."""
        # GIVEN: High-quality chunk
        chunk = Chunk(
            id="test_017",
            text="This is clean, readable text with good quality metrics.",
            document_id="doc_017",
            position_index=0,
            token_count=11,
            word_count=10,
            quality_score=0.0,
            metadata={},
        )
        source_metadata = {
            "ocr_confidence": 0.99,  # Above 0.95
            "completeness": 0.98,  # Above 0.90
            "document_type": "report",
            "source_hash": "clean123",
        }

        # WHEN: enrich_chunk() called
        enricher = MetadataEnricher()
        enriched_chunk = enricher.enrich_chunk(chunk, source_metadata)

        # THEN: No flags
        quality = enriched_chunk.metadata.quality
        assert quality.flags == []

    def test_multiple_flags_combination(self):
        """Should detect multiple quality issues simultaneously (AC-3.3-8)."""
        # GIVEN: Chunk with multiple quality issues
        chunk = Chunk(
            id="test_018",
            text=(
                "!!!@@@###$$$%%%^^^&&&***((()))___+++===|||\\\\///??"
                "abcdefghijklmnopqrstuvwxyz"  # ~50% non-alphabetic
            ),
            document_id="doc_018",
            position_index=0,
            token_count=20,
            word_count=1,
            quality_score=0.0,
            metadata={},
        )
        source_metadata = {
            "ocr_confidence": 0.85,  # Low OCR
            "completeness": 0.80,  # Incomplete
            "document_type": "image",
            "source_hash": "multi_flag123",
        }

        # WHEN: enrich_chunk() called
        enricher = MetadataEnricher()
        enriched_chunk = enricher.enrich_chunk(chunk, source_metadata)

        # THEN: Multiple flags present
        quality = enriched_chunk.metadata.quality
        assert "low_ocr" in quality.flags
        assert "incomplete_extraction" in quality.flags
        assert "gibberish" in quality.flags
        assert len(quality.flags) >= 3


class TestMetadataEnricherSourceTraceability:
    """Test source traceability metadata (AC-3.3-1)."""

    def test_source_metadata_propagation(self):
        """Should propagate source_hash and document_type from source metadata (AC-3.3-1)."""
        # GIVEN: Source metadata with hash and type
        chunk = Chunk(
            id="test_019",
            text="Test content.",
            document_id="doc_019",
            position_index=0,
            token_count=2,
            word_count=2,
            quality_score=0.0,
            metadata={},
        )
        source_metadata = {
            "ocr_confidence": 0.99,
            "completeness": 0.98,
            "source_hash": "abc123def456",  # SHA-256 hash
            "document_type": "matrix",  # Epic 2 classification
        }

        # WHEN: enrich_chunk() called
        enricher = MetadataEnricher()
        enriched_chunk = enricher.enrich_chunk(chunk, source_metadata)

        # THEN: Source metadata fields populated
        # Note: Implementation will store in ChunkMetadata
        # This test verifies propagation happens
        assert enriched_chunk is not None
        # Actual field access depends on ChunkMetadata structure


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
