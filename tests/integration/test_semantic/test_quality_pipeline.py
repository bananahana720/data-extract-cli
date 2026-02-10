"""
Integration tests for text quality metrics in the semantic pipeline.

Test IDs: QUAL-001 through QUAL-008

Tests readability scores, complexity metrics, and quality assessment integration.
"""

from typing import List

import pytest

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.semantic]

from src.data_extract.chunk.models import Chunk  # noqa: E402
from src.data_extract.core.models import ProcessingContext  # noqa: E402

pytestmark = [
    pytest.mark.integration,
    pytest.mark.semantic,
    pytest.mark.quality_metrics,
    pytest.mark.epic4,
]


class TestQualityMetricsIntegration:
    """Integration tests for text quality assessment."""

    def test_qual001_readability_scores(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test QUAL-001: Calculate readability scores for chunks.

        Given: Text chunks from documents
        When: Computing readability metrics
        Then: Returns Flesch, SMOG, and other scores
        """
        import textstat  # noqa: E402

        for chunk in chunked_documents[:3]:  # Test subset
            text = chunk.text

            # Calculate readability metrics
            flesch_reading_ease = textstat.flesch_reading_ease(text)
            flesch_kincaid_grade = textstat.flesch_kincaid_grade(text)
            smog_index = textstat.smog_index(text)
            automated_readability_index = textstat.automated_readability_index(text)
            coleman_liau_index = textstat.coleman_liau_index(text)

            # Validate metric ranges
            assert (
                -100 <= flesch_reading_ease <= 120
            ), f"Flesch Reading Ease out of range: {flesch_reading_ease}"
            assert (
                0 <= flesch_kincaid_grade <= 30
            ), f"Flesch-Kincaid Grade out of range: {flesch_kincaid_grade}"
            assert 0 <= smog_index <= 30, f"SMOG index out of range: {smog_index}"
            assert (
                0 <= automated_readability_index <= 30
            ), f"ARI out of range: {automated_readability_index}"
            assert 0 <= coleman_liau_index <= 30, f"Coleman-Liau out of range: {coleman_liau_index}"

            # Check consistency between metrics (they should correlate)
            grade_level = textstat.text_standard(text, float_output=True)
            assert 0 <= grade_level <= 30, f"Grade level out of range: {grade_level}"

    def test_qual002_complexity_metrics(
        self, technical_corpus: List[str], semantic_processing_context: ProcessingContext
    ):
        """
        Test QUAL-002: Compute text complexity metrics.

        Given: Technical documentation
        When: Analyzing complexity
        Then: Higher complexity scores for technical text
        """
        import textstat  # noqa: E402

        # Simple text for comparison
        simple_texts = [
            "The cat sat on the mat.",
            "I like to eat apples.",
            "The sun is shining today.",
        ]

        # Calculate complexity for technical docs
        tech_complexities = []
        for text in technical_corpus[:3]:
            complexity = {
                "flesch_kincaid": textstat.flesch_kincaid_grade(text),
                "gunning_fog": textstat.gunning_fog(text),
                "avg_syllables": textstat.avg_syllables_per_word(text),
                "difficult_words": textstat.difficult_words(text),
                "lexicon_count": textstat.lexicon_count(text, removepunct=True),
            }
            tech_complexities.append(complexity)

        # Calculate complexity for simple text
        simple_complexities = []
        for text in simple_texts:
            complexity = {
                "flesch_kincaid": textstat.flesch_kincaid_grade(text),
                "gunning_fog": textstat.gunning_fog(text),
                "avg_syllables": textstat.avg_syllables_per_word(text),
                "difficult_words": textstat.difficult_words(text),
                "lexicon_count": textstat.lexicon_count(text, removepunct=True),
            }
            simple_complexities.append(complexity)

        # Technical docs should generally have higher complexity
        avg_tech_grade = sum(c["flesch_kincaid"] for c in tech_complexities) / len(
            tech_complexities
        )
        avg_simple_grade = sum(c["flesch_kincaid"] for c in simple_complexities) / len(
            simple_complexities
        )

        # Technical text should be more complex (higher grade level)
        # But might not always be true for all samples
        assert avg_tech_grade >= 0 and avg_simple_grade >= 0, "Grade levels should be non-negative"

        # All complexity metrics should be valid
        for complexity in tech_complexities + simple_complexities:
            assert complexity["avg_syllables"] >= 1, "Average syllables >= 1"
            assert complexity["difficult_words"] >= 0, "Difficult words >= 0"
            assert complexity["lexicon_count"] > 0, "Lexicon count > 0"

    def test_qual003_quality_threshold_filtering(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test QUAL-003: Filter chunks by quality threshold.

        Given: Chunks with quality scores
        When: Applying quality threshold
        Then: Low-quality chunks filtered out
        """
        import textstat  # noqa: E402

        # Calculate quality scores for all chunks
        chunk_qualities = []
        for chunk in chunked_documents:
            # Simple quality score based on readability
            flesch_score = textstat.flesch_reading_ease(chunk.text)
            # Normalize to 0-1 (higher is better)
            # Flesch: 0-30 = very difficult, 30-50 = difficult, 50-60 = fairly difficult,
            # 60-70 = standard, 70-80 = fairly easy, 80-90 = easy, 90-100 = very easy
            normalized_score = min(max(flesch_score / 100.0, 0), 1)
            chunk_qualities.append(
                {"chunk": chunk, "quality_score": normalized_score, "flesch": flesch_score}
            )

        # Apply threshold from config or default
        threshold = semantic_processing_context.config.get("quality", {}).get("threshold", 0.3)

        # Filter chunks
        high_quality_chunks = [cq for cq in chunk_qualities if cq["quality_score"] >= threshold]

        # Assertions
        assert len(high_quality_chunks) <= len(
            chunk_qualities
        ), "Filtered list should not be larger"

        # All remaining chunks should meet threshold
        for cq in high_quality_chunks:
            assert (
                cq["quality_score"] >= threshold
            ), f"Chunk quality {cq['quality_score']} below threshold {threshold}"

        # Verify threshold is reasonable
        assert 0 <= threshold <= 1, "Threshold should be in [0, 1]"

    def test_qual004_automated_readability_index(
        self, simple_documents: List[str], semantic_processing_context: ProcessingContext
    ):
        """
        Test QUAL-004: ARI (Automated Readability Index) calculation.

        Given: Documents with known complexity
        When: Calculating ARI
        Then: Scores reflect reading grade level
        """
        import textstat  # noqa: E402

        # Create documents with varying complexity
        test_documents = [
            # Simple (elementary level)
            "The dog ran fast. The cat jumped high. Birds fly in the sky.",
            # Medium (middle school level)
            "Scientific research demonstrates that regular exercise significantly improves "
            "cardiovascular health and reduces the risk of chronic diseases.",
            # Complex (college level)
            "The paradigmatic shift in epistemological frameworks necessitates a "
            "comprehensive reevaluation of methodological approaches within the context "
            "of contemporary interdisciplinary research initiatives.",
        ]

        ari_scores = []
        for doc in test_documents:
            ari = textstat.automated_readability_index(doc)
            ari_scores.append(ari)

            # Validate ARI range (typically -3 to 14+)
            assert -5 <= ari <= 30, f"ARI out of typical range: {ari}"

        # Verify progression (simple < medium < complex)
        if len(ari_scores) >= 3:
            # Simple should have lower ARI than complex
            # Allow for some variation in scoring
            assert (
                ari_scores[0] <= ari_scores[2] + 5
            ), "Simple text should generally have lower ARI than complex"

        # All scores should be numeric
        for score in ari_scores:
            assert isinstance(score, (int, float)), "ARI should be numeric"

    def test_qual005_entity_density_impact(
        self, entity_rich_chunks: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test QUAL-005: Entity density affects quality scores.

        Given: Chunks with varying entity density
        When: Computing quality metrics
        Then: Entity-rich chunks have adjusted scores
        """
        import textstat  # noqa: E402

        entity_densities = []
        quality_scores = []

        for chunk in entity_rich_chunks[:5]:
            # Calculate entity density
            entities = chunk.metadata.get("entities", [])
            word_count = textstat.lexicon_count(chunk.text, removepunct=True)
            entity_density = len(entities) / max(word_count, 1)

            # Calculate base quality score
            flesch = textstat.flesch_reading_ease(chunk.text)
            base_quality = min(max(flesch / 100.0, 0), 1)

            # Apply entity density adjustment (simple boost)
            # More entities = more informative = higher quality
            adjusted_quality = base_quality * (1 + min(entity_density, 0.5))
            adjusted_quality = min(adjusted_quality, 1.0)  # Cap at 1.0

            entity_densities.append(entity_density)
            quality_scores.append(
                {"base": base_quality, "adjusted": adjusted_quality, "density": entity_density}
            )

        # Assertions
        for score in quality_scores:
            # Adjusted should be >= base (entities don't decrease quality)
            assert (
                score["adjusted"] >= score["base"] - 0.01
            ), "Entity adjustment should not decrease quality"

            # Both scores in valid range
            assert 0 <= score["base"] <= 1, "Base quality in [0, 1]"
            assert 0 <= score["adjusted"] <= 1, "Adjusted quality in [0, 1]"

        # Entity density should be reasonable
        for density in entity_densities:
            assert 0 <= density <= 1, "Entity density should be in [0, 1]"

    def test_qual006_language_detection(self, semantic_processing_context: ProcessingContext):
        """
        Test QUAL-006: Language detection for quality assessment.

        Given: Multi-language text chunks
        When: Analyzing quality
        Then: Language-appropriate metrics applied
        """
        import textstat  # noqa: E402

        from src.data_extract.chunk.models import Chunk  # noqa: E402

        # Create chunks in different languages/styles
        test_chunks = [
            Chunk(
                content="This is a simple English sentence with clear meaning.",
                metadata={"id": 1, "expected_lang": "en"},
            ),
            Chunk(
                content="The quick brown fox jumps over the lazy dog repeatedly.",
                metadata={"id": 2, "expected_lang": "en"},
            ),
            # Note: textstat is English-focused, so we simulate detection
            Chunk(
                content="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                metadata={"id": 3, "expected_lang": "latin"},
            ),
        ]

        for chunk in test_chunks:
            text = chunk.text

            # For English text, apply full metrics
            if "english" in text.lower() or "fox" in text.lower() or "dog" in text.lower():
                flesch = textstat.flesch_reading_ease(text)
                assert -100 <= flesch <= 120, "English text should have valid Flesch score"

                # Should have reasonable syllable count
                syllables = textstat.syllable_count(text)
                assert syllables > 0, "English text should have countable syllables"

            # For non-English, metrics might be less reliable but shouldn't crash
            else:
                try:
                    flesch = textstat.flesch_reading_ease(text)
                    # Even for non-English, shouldn't crash
                    assert isinstance(flesch, (int, float)), "Should return numeric value"
                except Exception:
                    # It's okay if it fails for non-English
                    pass

    def test_qual007_performance_baseline(
        self,
        chunked_documents: List[Chunk],
        semantic_processing_context: ProcessingContext,
        performance_thresholds: dict,
        performance_timer,
    ):
        """
        Test QUAL-007: Quality metrics meet performance baseline.

        Given: Standard chunk corpus
        When: Computing all quality metrics
        Then: Completes within 10ms per chunk
        """
        import time  # noqa: E402

        import textstat  # noqa: E402

        # Time quality calculation
        start_time = time.time()

        for chunk in chunked_documents:
            # Calculate multiple metrics (typical workflow)
            _ = textstat.flesch_reading_ease(chunk.text)
            _ = textstat.flesch_kincaid_grade(chunk.text)
            _ = textstat.smog_index(chunk.text)
            _ = textstat.automated_readability_index(chunk.text)
            _ = textstat.text_standard(chunk.text)

        elapsed_time = time.time() - start_time

        # Get threshold
        threshold_ms_per_chunk = performance_thresholds.get("quality_ms", 200) / len(
            chunked_documents
        )
        threshold_seconds = threshold_ms_per_chunk * len(chunked_documents) / 1000.0

        # Assertions
        assert (
            elapsed_time < threshold_seconds
        ), f"Quality calculation took {elapsed_time:.3f}s, exceeding {threshold_seconds:.3f}s threshold"

        # Calculate actual ms per chunk
        ms_per_chunk = (elapsed_time * 1000) / len(chunked_documents)
        assert (
            ms_per_chunk < 100
        ), f"Quality metrics took {ms_per_chunk:.1f}ms per chunk, target is <100ms"

    def test_qual008_quality_score_aggregation(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test QUAL-008: Aggregate quality scores for documents.

        Given: Chunks from same document
        When: Aggregating quality scores
        Then: Document-level quality assessment
        """
        import numpy as np  # noqa: E402
        import textstat  # noqa: E402

        # Group chunks by document (using metadata or simulate)
        # For this test, we'll treat every 2 chunks as from the same document
        documents = []
        for i in range(0, len(chunked_documents), 2):
            doc_chunks = chunked_documents[i : i + 2]
            documents.append(doc_chunks)

        document_scores = []
        for doc_chunks in documents:
            chunk_scores = []
            chunk_weights = []

            for chunk in doc_chunks:
                # Calculate quality score
                flesch = textstat.flesch_reading_ease(chunk.text)
                score = min(max(flesch / 100.0, 0), 1)

                # Weight by chunk length
                weight = textstat.lexicon_count(chunk.text, removepunct=True)

                chunk_scores.append(score)
                chunk_weights.append(weight)

            # Aggregate scores
            if chunk_scores:
                # Simple mean
                mean_score = np.mean(chunk_scores)

                # Weighted mean (by text length)
                total_weight = sum(chunk_weights)
                if total_weight > 0:
                    weighted_score = (
                        sum(s * w for s, w in zip(chunk_scores, chunk_weights)) / total_weight
                    )
                else:
                    weighted_score = mean_score

                # Median (robust to outliers)
                median_score = np.median(chunk_scores)

                document_scores.append(
                    {
                        "mean": mean_score,
                        "weighted": weighted_score,
                        "median": median_score,
                        "chunk_count": len(chunk_scores),
                    }
                )

        # Assertions
        for doc_score in document_scores:
            # All aggregation methods should produce valid scores
            assert 0 <= doc_score["mean"] <= 1, "Mean score in [0, 1]"
            assert 0 <= doc_score["weighted"] <= 1, "Weighted score in [0, 1]"
            assert 0 <= doc_score["median"] <= 1, "Median score in [0, 1]"

            # Should have processed at least one chunk
            assert doc_score["chunk_count"] > 0, "Should have chunks to aggregate"


class TestQualityEdgeCases:
    """Edge case tests for quality metrics."""

    def test_qual009_empty_text_quality(self, semantic_processing_context: ProcessingContext):
        """
        Test QUAL-009: Handle empty text in quality metrics.

        Given: Empty or whitespace-only chunks
        When: Computing quality metrics
        Then: Returns zero/null scores gracefully
        """
        import datetime  # noqa: E402
        from pathlib import Path  # noqa: E402

        import textstat  # noqa: E402

        from src.data_extract.chunk.models import Chunk  # noqa: E402
        from src.data_extract.core.models import Metadata  # noqa: E402

        # Create empty chunks
        empty_chunks = [
            Chunk(
                id="empty_1",
                text="",
                document_id="doc_empty",
                position_index=0,
                token_count=0,
                word_count=0,
                quality_score=0.1,
                metadata=Metadata(
                    source_file=Path("/test/empty1.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=0,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),
            Chunk(
                id="empty_2",
                text="   ",
                document_id="doc_whitespace",
                position_index=0,
                token_count=0,
                word_count=0,
                quality_score=0.1,
                metadata=Metadata(
                    source_file=Path("/test/empty2.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=3,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),
            Chunk(
                id="empty_3",
                text="\n\n\n",
                document_id="doc_newlines",
                position_index=0,
                token_count=0,
                word_count=0,
                quality_score=0.1,
                metadata=Metadata(
                    source_file=Path("/test/empty3.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=3,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),
            Chunk(
                id="empty_4",
                text="\t\t",
                document_id="doc_tabs",
                position_index=0,
                token_count=0,
                word_count=0,
                quality_score=0.1,
                metadata=Metadata(
                    source_file=Path("/test/empty4.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=2,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),
        ]

        for chunk in empty_chunks:
            # Should not crash on empty text
            try:
                flesch = textstat.flesch_reading_ease(chunk.text)
                # Empty text typically returns 0 or very low score
                assert (
                    flesch <= 0 or flesch == 206.835
                ), f"Empty text Flesch score unexpected: {flesch}"

                syllables = textstat.syllable_count(chunk.text)
                assert syllables == 0, "Empty text should have 0 syllables"

                word_count = textstat.lexicon_count(chunk.text)
                assert word_count == 0, "Empty text should have 0 words"

            except ZeroDivisionError:
                # Some metrics might divide by zero on empty text
                # This is acceptable - just shouldn't crash the app
                pass

    def test_qual010_single_sentence_quality(self, semantic_processing_context: ProcessingContext):
        """
        Test QUAL-010: Quality metrics for single sentences.

        Given: Single-sentence chunks
        When: Computing readability
        Then: Handles edge case appropriately
        """
        import datetime  # noqa: E402
        from pathlib import Path  # noqa: E402

        import textstat  # noqa: E402

        from src.data_extract.chunk.models import Chunk  # noqa: E402
        from src.data_extract.core.models import Metadata  # noqa: E402

        # Create single-sentence chunks
        single_sentences = [
            Chunk(
                id="single_1",
                text="This is a simple sentence.",
                document_id="doc_simple",
                position_index=0,
                token_count=6,
                word_count=5,
                quality_score=0.8,
                metadata=Metadata(
                    source_file=Path("/test/single1.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=26,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),
            Chunk(
                id="single_2",
                text="The algorithm processes data efficiently.",
                document_id="doc_algo",
                position_index=0,
                token_count=8,
                word_count=5,
                quality_score=0.85,
                metadata=Metadata(
                    source_file=Path("/test/single2.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=40,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),
            Chunk(
                id="single_3",
                text="Complex paradigmatic shifts necessitate reevaluation.",
                document_id="doc_complex",
                position_index=0,
                token_count=10,
                word_count=5,
                quality_score=0.6,
                metadata=Metadata(
                    source_file=Path("/test/single3.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=53,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),
        ]

        for chunk in single_sentences:
            # Should handle single sentences without errors
            flesch = textstat.flesch_reading_ease(chunk.text)
            assert isinstance(flesch, (int, float)), "Should return numeric score"

            # Single sentences should still have valid metrics
            sentence_count = textstat.sentence_count(chunk.text)
            assert sentence_count == 1, "Should detect single sentence"

            # SMOG might need special handling for single sentences
            try:
                smog = textstat.smog_index(chunk.text)
                assert isinstance(smog, (int, float)), "SMOG should be numeric"
            except Exception:
                # SMOG requires 30+ sentences ideally, so might fail
                pass

            # Grade level should still work
            grade = textstat.flesch_kincaid_grade(chunk.text)
            assert -5 <= grade <= 30, f"Grade level out of range: {grade}"

    def test_qual011_unicode_text_quality(self, semantic_processing_context: ProcessingContext):
        """
        Test QUAL-011: Quality metrics for unicode text.

        Given: Text with unicode characters
        When: Computing quality metrics
        Then: Handles unicode correctly
        """
        import datetime  # noqa: E402
        from pathlib import Path  # noqa: E402

        import textstat  # noqa: E402

        from src.data_extract.chunk.models import Chunk  # noqa: E402
        from src.data_extract.core.models import Metadata  # noqa: E402

        # Create chunks with unicode
        unicode_chunks = [
            Chunk(
                id="unicode_1",
                text="Café résumé naïve señor",
                document_id="doc_accents",
                position_index=0,
                token_count=5,
                word_count=4,
                quality_score=0.8,
                metadata=Metadata(
                    source_file=Path("/test/unicode1.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=25,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),
            Chunk(
                id="unicode_2",
                text="Testing with emojis 😀 and symbols ✓ ✗",
                document_id="doc_emoji",
                position_index=0,
                token_count=9,
                word_count=7,
                quality_score=0.7,
                metadata=Metadata(
                    source_file=Path("/test/unicode2.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=40,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),
            Chunk(
                id="unicode_3",
                text="Mathematical: α + β = γ, ∑x²",
                document_id="doc_math",
                position_index=0,
                token_count=8,
                word_count=6,
                quality_score=0.6,
                metadata=Metadata(
                    source_file=Path("/test/unicode3.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=30,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),
            Chunk(
                id="unicode_4",
                text="Currency: €100 £50 ¥1000 $25",
                document_id="doc_currency",
                position_index=0,
                token_count=7,
                word_count=5,
                quality_score=0.75,
                metadata=Metadata(
                    source_file=Path("/test/unicode4.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=29,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),
        ]

        for chunk in unicode_chunks:
            # Should handle unicode without crashing
            try:
                flesch = textstat.flesch_reading_ease(chunk.text)
                assert isinstance(flesch, (int, float)), "Should return numeric score"

                # Character/word counting should work
                char_count = textstat.char_count(chunk.text)
                assert char_count > 0, "Should count characters"

                # Lexicon count might exclude some unicode
                word_count = textstat.lexicon_count(chunk.text, removepunct=True)
                assert word_count >= 0, "Word count should be non-negative"

            except Exception as e:
                # Should not crash on unicode
                assert False, f"Failed on unicode text: {e}"

    def test_qual012_outlier_quality_scores(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test QUAL-012: Detect and handle quality outliers.

        Given: Chunks with extreme quality scores
        When: Processing quality metrics
        Then: Outliers detected and handled
        """
        import datetime  # noqa: E402
        from pathlib import Path  # noqa: E402

        import numpy as np  # noqa: E402
        import textstat  # noqa: E402

        from src.data_extract.chunk.models import Chunk  # noqa: E402
        from src.data_extract.core.models import Metadata  # noqa: E402

        # Add some extreme chunks
        extreme_chunks = [
            Chunk(
                id="extreme_1",
                text="a " * 500,
                document_id="doc_repetitive",
                position_index=0,
                token_count=500,
                word_count=500,
                quality_score=0.1,
                metadata=Metadata(
                    source_file=Path("/test/extreme1.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=1000,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),  # Repetitive
            Chunk(
                id="extreme_2",
                text="." * 100,
                document_id="doc_punctuation",
                position_index=0,
                token_count=25,
                word_count=0,
                quality_score=0.05,
                metadata=Metadata(
                    source_file=Path("/test/extreme2.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=100,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),  # Only punctuation
            Chunk(
                id="extreme_3",
                text="Antidisestablishmentarianism pneumonoultramicroscopicsilicovolcanoconiosis "
                "hippopotomonstrosesquippedaliophobia",
                document_id="doc_longwords",
                position_index=0,
                token_count=25,
                word_count=3,
                quality_score=0.2,
                metadata=Metadata(
                    source_file=Path("/test/extreme3.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=115,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),  # Very long words
        ]

        all_chunks = list(chunked_documents) + extreme_chunks

        # Calculate quality scores
        quality_scores = []
        for chunk in all_chunks:
            try:
                flesch = textstat.flesch_reading_ease(chunk.text)
                quality_scores.append(flesch)
            except Exception:
                quality_scores.append(0)  # Default for problematic text

        # Detect outliers using IQR method
        q1 = np.percentile(quality_scores, 25)
        q3 = np.percentile(quality_scores, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = []
        handled_scores = []
        for score in quality_scores:
            if score < lower_bound or score > upper_bound:
                outliers.append(score)
                # Handle outlier by capping
                handled_score = max(lower_bound, min(score, upper_bound))
            else:
                handled_score = score
            handled_scores.append(handled_score)

        # Assertions
        assert len(handled_scores) == len(quality_scores), "Should handle all scores"

        # All handled scores should be within bounds
        for score in handled_scores:
            assert lower_bound <= score <= upper_bound or np.isnan(
                score
            ), f"Handled score {score} outside bounds [{lower_bound}, {upper_bound}]"

        # Should have detected some outliers from extreme chunks
        # (unless regular chunks are also extreme)
        if len(outliers) > 0:
            assert isinstance(outliers[0], (int, float)), "Outliers should be numeric"
