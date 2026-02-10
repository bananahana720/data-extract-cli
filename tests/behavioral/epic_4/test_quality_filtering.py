"""Behavioral tests for quality filtering (Story 4.4).

Tests the real-world behavior of quality metrics and filtering,
including OCR gibberish detection, readability assessment, and
quality-based chunk filtering.
"""

from typing import List

import pytest

from data_extract.core.models import Chunk
from data_extract.semantic.quality_metrics import (
    QualityConfig,
    QualityFlag,
    QualityMetricsStage,
)

pytestmark = [
    pytest.mark.P1,
    pytest.mark.behavioral,
    pytest.mark.semantic,
    pytest.mark.story_4_4,
]


class TestQualityFiltering:
    """Test quality-based content filtering behaviors."""

    @pytest.fixture
    def quality_stage(self):
        """Create quality metrics stage for testing."""
        config = QualityConfig(
            min_quality=0.3,
            detect_gibberish=True,
            use_cache=False,  # Disable for behavioral tests
        )
        return QualityMetricsStage(config=config)

    @pytest.fixture
    def gibberish_chunks(self) -> List[Chunk]:
        """Create chunks with OCR gibberish."""
        return [
            Chunk(
                id="gibberish_001",
                text="@#$%^&*()_+ !@#$ %^&* ()_+ xyz abc 123",
                document_id="ocr_doc",
                position_index=0,
                token_count=10,
                word_count=5,
                quality_score=0.0,
                metadata={},
            ),
            Chunk(
                id="gibberish_002",
                text="aaaaaa bbbbbb cccccc dddddd eeeeee ffffff",
                document_id="ocr_doc",
                position_index=1,
                token_count=6,
                word_count=6,
                quality_score=0.0,
                metadata={},
            ),
            Chunk(
                id="gibberish_003",
                text="1234567890" * 20,  # Just numbers
                document_id="ocr_doc",
                position_index=2,
                token_count=1,
                word_count=1,
                quality_score=0.0,
                metadata={},
            ),
        ]

    @pytest.fixture
    def high_quality_chunks(self) -> List[Chunk]:
        """Create high-quality, readable chunks."""
        return [
            Chunk(
                id="high_001",
                text=(
                    "The financial audit revealed significant improvements in revenue "
                    "management. Our analysis shows that operational efficiency increased "
                    "by 15% over the previous quarter."
                ),
                document_id="audit_doc",
                position_index=0,
                token_count=25,
                word_count=25,
                quality_score=0.0,
                metadata={},
            ),
            Chunk(
                id="high_002",
                text=(
                    "Risk assessment procedures have been updated to reflect current "
                    "market conditions. The compliance team has implemented new controls "
                    "to address identified vulnerabilities."
                ),
                document_id="audit_doc",
                position_index=1,
                token_count=25,
                word_count=25,
                quality_score=0.0,
                metadata={},
            ),
        ]

    @pytest.fixture
    def mixed_quality_chunks(self) -> List[Chunk]:
        """Create chunks with varying quality levels."""
        return [
            # High quality - clear business text
            Chunk(
                id="mixed_001",
                text=(
                    "The quarterly earnings report demonstrates strong financial performance "
                    "with revenue growth exceeding expectations by 8%."
                ),
                document_id="mixed_doc",
                position_index=0,
                token_count=20,
                word_count=20,
                quality_score=0.0,
                metadata={},
            ),
            # Medium quality - technical but readable
            Chunk(
                id="mixed_002",
                text=(
                    "Implementation of the ISO 27001 cybersecurity framework necessitates "
                    "comprehensive reconfiguration of existing authentication protocols and "
                    "multifactor authorization mechanisms."
                ),
                document_id="mixed_doc",
                position_index=1,
                token_count=20,
                word_count=20,
                quality_score=0.0,
                metadata={},
            ),
            # Low quality - OCR errors
            Chunk(
                id="mixed_003",
                text="Th3 f1n@nc1al st@t3m3nt sh0ws @bnorm@l p@tt3rns !n th3 d@t@.",
                document_id="mixed_doc",
                position_index=2,
                token_count=12,
                word_count=12,
                quality_score=0.0,
                metadata={},
            ),
            # Review needed - mostly gibberish
            Chunk(
                id="mixed_004",
                text="!!!### $$$ %%% &&& *** ((( ))) ___",
                document_id="mixed_doc",
                position_index=3,
                token_count=8,
                word_count=0,
                quality_score=0.0,
                metadata={},
            ),
        ]

    def test_gibberish_detection(self, quality_stage, gibberish_chunks):
        """Test detection of OCR gibberish content."""
        results = quality_stage.process(gibberish_chunks)

        for chunk in results:
            # All gibberish chunks should have low quality scores
            assert chunk.quality_score < 0.3, f"Chunk {chunk.id} not flagged as low quality"

            # Check quality flag
            flag = chunk.metadata.get("quality_flag")
            assert flag in [
                QualityFlag.LOW.value,
                QualityFlag.REVIEW.value,
            ], f"Chunk {chunk.id} should be flagged for review or as low quality"

    def test_high_quality_identification(self, quality_stage, high_quality_chunks):
        """Test identification of high-quality content."""
        results = quality_stage.process(high_quality_chunks)

        for chunk in results:
            # High-quality chunks should score well
            assert chunk.quality_score > 0.5, f"Chunk {chunk.id} scored too low"

            # Check quality flag
            flag = chunk.metadata.get("quality_flag")
            assert flag in [
                QualityFlag.HIGH.value,
                QualityFlag.MEDIUM.value,
            ], f"Chunk {chunk.id} should be flagged as high or medium quality"

            # Verify readability metrics are reasonable
            assert "flesch_reading_ease" in chunk.readability_scores
            assert 0 <= chunk.readability_scores["flesch_reading_ease"] <= 100

    def test_quality_distribution(self, quality_stage, mixed_quality_chunks):
        """Test quality distribution across mixed content."""
        results = quality_stage.process(mixed_quality_chunks)

        # Collect quality flags
        flags = [chunk.metadata.get("quality_flag") for chunk in results]

        # Should have at least one of each quality level
        assert QualityFlag.HIGH.value in flags or QualityFlag.MEDIUM.value in flags
        assert QualityFlag.LOW.value in flags or QualityFlag.REVIEW.value in flags

        # Verify score ordering makes sense
        high_quality_score = results[0].quality_score  # Business text
        low_quality_score = results[3].quality_score  # Gibberish

        assert (
            high_quality_score > low_quality_score
        ), "High-quality text should score better than gibberish"

    def test_readability_metrics_presence(self, quality_stage, high_quality_chunks):
        """Test that all required readability metrics are computed."""
        results = quality_stage.process(high_quality_chunks)

        required_metrics = [
            "flesch_reading_ease",
            "flesch_kincaid_grade",
            "gunning_fog",
            "smog_index",
            "coleman_liau_index",
            "lexical_diversity",
        ]

        for chunk in results:
            for metric in required_metrics:
                assert metric in chunk.readability_scores, f"Missing required metric: {metric}"

                # Verify metric is a number
                value = chunk.readability_scores[metric]
                assert isinstance(value, (int, float)), f"Metric {metric} should be numeric"

    def test_quality_filtering_threshold(self, quality_stage):
        """Test filtering based on quality threshold."""
        # Create chunks with specific quality characteristics
        chunks = [
            Chunk(
                id=f"filter_{i}",
                text=text,
                document_id="filter_doc",
                position_index=i,
                token_count=10,
                word_count=10,
                quality_score=0.0,
                metadata={},
            )
            for i, text in enumerate(
                [
                    "This is high-quality content with clear meaning and good structure.",
                    "Medium quality text with some technical terms.",
                    "L0w qu@l1ty t3xt w1th 3rr0rs",
                    "@#$%^&*()_+",
                ]
            )
        ]

        results = quality_stage.process(chunks)

        # Count chunks by quality level
        high_count = sum(
            1 for c in results if c.metadata.get("quality_flag") == QualityFlag.HIGH.value
        )
        low_count = sum(
            1
            for c in results
            if c.metadata.get("quality_flag") in [QualityFlag.LOW.value, QualityFlag.REVIEW.value]
        )

        assert high_count > 0, "Should identify at least one high-quality chunk"
        assert low_count > 0, "Should identify at least one low-quality chunk"

    def test_empty_and_edge_cases(self, quality_stage):
        """Test edge cases like empty or very short text."""
        edge_chunks = [
            Chunk(
                id="empty",
                text="",
                document_id="edge_doc",
                position_index=0,
                token_count=0,
                word_count=0,
                quality_score=0.0,
                metadata={},
            ),
            Chunk(
                id="single_word",
                text="Word",
                document_id="edge_doc",
                position_index=1,
                token_count=1,
                word_count=1,
                quality_score=0.0,
                metadata={},
            ),
            Chunk(
                id="spaces_only",
                text="     ",
                document_id="edge_doc",
                position_index=2,
                token_count=0,
                word_count=0,
                quality_score=0.0,
                metadata={},
            ),
        ]

        results = quality_stage.process(edge_chunks)

        for chunk in results:
            # Edge cases should be flagged for review or as low quality
            flag = chunk.metadata.get("quality_flag")
            assert flag in [
                QualityFlag.LOW.value,
                QualityFlag.REVIEW.value,
            ], f"Edge case {chunk.id} should be flagged appropriately"

    def test_lexical_diversity_impact(self, quality_stage):
        """Test that lexical diversity affects quality scoring."""
        chunks = [
            Chunk(
                id="diverse",
                text="The quick brown fox jumps over the lazy dog near the river bank.",
                document_id="diversity_doc",
                position_index=0,
                token_count=14,
                word_count=14,
                quality_score=0.0,
                metadata={},
            ),
            Chunk(
                id="repetitive",
                text="the the the the the the the the the the the the",
                document_id="diversity_doc",
                position_index=1,
                token_count=12,
                word_count=12,
                quality_score=0.0,
                metadata={},
            ),
        ]

        results = quality_stage.process(chunks)

        diverse_chunk = next(c for c in results if c.id == "diverse")
        repetitive_chunk = next(c for c in results if c.id == "repetitive")

        # Diverse text should have better quality score
        assert (
            diverse_chunk.quality_score > repetitive_chunk.quality_score
        ), "Diverse text should score higher than repetitive text"

        # Check lexical diversity values
        assert (
            diverse_chunk.readability_scores["lexical_diversity"]
            > repetitive_chunk.readability_scores["lexical_diversity"]
        ), "Diverse text should have higher lexical diversity"

    def test_special_character_detection(self, quality_stage):
        """Test detection of excessive special characters."""
        chunks = [
            Chunk(
                id="normal_punctuation",
                text="This is a normal sentence, with proper punctuation!",
                document_id="special_doc",
                position_index=0,
                token_count=10,
                word_count=10,
                quality_score=0.0,
                metadata={},
            ),
            Chunk(
                id="excessive_special",
                text="!!!@@@###$$$%%%^^^&&&***((()))",
                document_id="special_doc",
                position_index=1,
                token_count=1,
                word_count=0,
                quality_score=0.0,
                metadata={},
            ),
        ]

        results = quality_stage.process(chunks)

        normal = next(c for c in results if c.id == "normal_punctuation")
        special = next(c for c in results if c.id == "excessive_special")

        assert (
            normal.quality_score > special.quality_score
        ), "Normal text should score better than text with excessive special characters"

        assert special.metadata.get("quality_flag") in [
            QualityFlag.LOW.value,
            QualityFlag.REVIEW.value,
        ], "Text with excessive special characters should be flagged"

    def test_grade_level_boundaries(self, quality_stage):
        """Test handling of extreme grade levels."""
        chunks = [
            Chunk(
                id="simple",
                text="See the cat. The cat is big. The cat runs fast.",
                document_id="grade_doc",
                position_index=0,
                token_count=12,
                word_count=12,
                quality_score=0.0,
                metadata={},
            ),
            Chunk(
                id="complex",
                text=(
                    "Notwithstanding the aforementioned considerations regarding the "
                    "implementation of multifaceted organizational restructuring paradigms, "
                    "the quintessential ramifications necessitate comprehensive evaluation."
                ),
                document_id="grade_doc",
                position_index=1,
                token_count=25,
                word_count=25,
                quality_score=0.0,
                metadata={},
            ),
        ]

        results = quality_stage.process(chunks)

        simple = next(c for c in results if c.id == "simple")
        complex = next(c for c in results if c.id == "complex")

        # Both should have grade levels computed
        assert "flesch_kincaid_grade" in simple.readability_scores
        assert "flesch_kincaid_grade" in complex.readability_scores

        # Simple text should have lower grade level
        assert (
            simple.readability_scores["flesch_kincaid_grade"]
            < complex.readability_scores["flesch_kincaid_grade"]
        ), "Simple text should have lower grade level than complex text"
