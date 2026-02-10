"""Quality metrics integration with textstat for content assessment.

This module implements Story 4.4: Quality Metrics Integration with Textstat.
It assesses readability and quality of document chunks using comprehensive metrics
from textstat, filtering out low-quality content to reduce LLM hallucinations.
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

import numpy as np
import textstat  # type: ignore[import-untyped]

from ..core.models import Chunk, ProcessingContext
from ..core.pipeline import PipelineStage
from .cache import CacheManager

logger = logging.getLogger(__name__)


class QualityFlag(Enum):
    """Quality level flags for chunk assessment."""

    HIGH = "high"  # Score >= 0.7
    MEDIUM = "medium"  # Score 0.3-0.7
    LOW = "low"  # Score < 0.3
    REVIEW = "review"  # Requires manual review (gibberish detected)


@dataclass
class ReadabilityScores:
    """Comprehensive readability scores from textstat.

    Attributes:
        flesch_reading_ease: 0-100, higher is easier (90-100: very easy)
        flesch_kincaid_grade: U.S. school grade level (target: 8-12)
        gunning_fog: Years of education needed (business docs: 10-12)
        smog_index: Years of education needed (health docs: 8-10)
        coleman_liau_index: U.S. grade level (character-based, OCR-robust)
        automated_readability_index: U.S. grade level
        dale_chall_readability_score: U.S. grade level (uses word familiarity)
        linsear_write_formula: U.S. grade level (simple texts)
        syllable_count: Total syllables in text
        lexical_diversity: Unique words / total words (0-1)
    """

    flesch_reading_ease: float = 0.0
    flesch_kincaid_grade: float = 0.0
    gunning_fog: float = 0.0
    smog_index: float = 0.0
    coleman_liau_index: float = 0.0
    automated_readability_index: float = 0.0
    dale_chall_readability_score: float = 0.0
    linsear_write_formula: float = 0.0
    syllable_count: int = 0
    lexical_diversity: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for metadata storage."""
        return {
            "flesch_reading_ease": self.flesch_reading_ease,
            "flesch_kincaid_grade": self.flesch_kincaid_grade,
            "gunning_fog": self.gunning_fog,
            "smog_index": self.smog_index,
            "coleman_liau_index": self.coleman_liau_index,
            "automated_readability_index": self.automated_readability_index,
            "dale_chall_readability_score": self.dale_chall_readability_score,
            "linsear_write_formula": self.linsear_write_formula,
            "syllable_count": float(self.syllable_count),
            "lexical_diversity": self.lexical_diversity,
        }


@dataclass
class QualityConfig:
    """Configuration for quality metrics assessment.

    Attributes:
        min_quality: Minimum quality score threshold (default 0.3)
        weights: Metric weights for composite scoring
        detect_gibberish: Enable OCR gibberish detection (default True)
        special_char_threshold: Max ratio of special characters (default 0.3)
        min_lexical_diversity: Minimum lexical diversity (default 0.1)
        max_grade_level: Maximum acceptable grade level (default 20)
        use_cache: Whether to use caching (default True)
    """

    min_quality: float = 0.3
    weights: Dict[str, float] = field(
        default_factory=lambda: {
            "flesch_ease": 0.2,
            "grade_level": 0.2,
            "lexical_diversity": 0.2,
            "anomaly_absence": 0.4,
        }
    )
    detect_gibberish: bool = True
    special_char_threshold: float = 0.3
    min_lexical_diversity: float = 0.1
    max_grade_level: float = 20.0
    use_cache: bool = True

    def get_cache_key_components(self) -> tuple:  # type: ignore[type-arg]
        """Get components for cache key generation."""
        return (
            self.min_quality,
            tuple(sorted(self.weights.items())),
            self.detect_gibberish,
            self.special_char_threshold,
            self.min_lexical_diversity,
            self.max_grade_level,
        )


@dataclass
class QualityDistributionReport:
    """Quality distribution statistics for a corpus.

    Attributes:
        total_chunks: Total number of chunks analyzed
        high_quality_count: Number of high-quality chunks
        medium_quality_count: Number of medium-quality chunks
        low_quality_count: Number of low-quality chunks
        review_required_count: Number of chunks needing review
        score_histogram: Histogram bins for score distribution
        mean_score: Mean quality score
        std_score: Standard deviation of quality scores
        flagged_chunks: List of chunk IDs flagged for issues
    """

    total_chunks: int = 0
    high_quality_count: int = 0
    medium_quality_count: int = 0
    low_quality_count: int = 0
    review_required_count: int = 0
    score_histogram: Dict[str, int] = field(default_factory=dict)
    mean_score: float = 0.0
    std_score: float = 0.0
    flagged_chunks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, any]:  # type: ignore[valid-type]
        """Convert to dictionary for reporting."""
        return {
            "total_chunks": self.total_chunks,
            "distribution": {
                "high": self.high_quality_count,
                "medium": self.medium_quality_count,
                "low": self.low_quality_count,
                "review": self.review_required_count,
            },
            "statistics": {
                "mean": self.mean_score,
                "std": self.std_score,
            },
            "histogram": self.score_histogram,
            "flagged_chunks": self.flagged_chunks,
        }


class QualityMetricsStage(PipelineStage[List[Chunk], List[Chunk]]):
    """Quality metrics assessment pipeline stage using textstat.

    This stage enriches chunks with comprehensive readability scores,
    computes composite quality scores, and flags low-quality content
    for filtering or review. Implements aggressive caching for performance.
    """

    def __init__(self, config: Optional[QualityConfig] = None):
        """Initialize quality metrics stage.

        Args:
            config: Quality configuration (uses defaults if not provided)
        """
        self.config = config or QualityConfig()
        self.cache_manager = CacheManager() if self.config.use_cache else None
        self._syllable_cache: Dict[str, int] = {}  # Word -> syllable count cache

    def process(
        self, input_data: List[Chunk], context: Optional[ProcessingContext] = None
    ) -> List[Chunk]:
        """Process chunks to add quality metrics.

        Args:
            input_data: List of text chunks to assess
            context: Processing context with configuration and logging

        Returns:
            List of chunks enriched with quality scores and readability metrics
        """
        start_time = time.time()

        # Validate input
        if not input_data:
            logger.warning("No chunks provided for quality assessment")
            return input_data

        # Process each chunk
        enriched_chunks = []
        scores = []

        for chunk in input_data:
            # Check cache if enabled
            cache_hit = False
            if self.cache_manager:
                cache_key = self._generate_cache_key(chunk.text)
                cached_result = self.cache_manager.get(cache_key)
                if cached_result:
                    cache_hit = True
                    readability = cached_result["readability"]
                    composite_score = cached_result["composite_score"]
                    quality_flag = QualityFlag(cached_result["quality_flag"])
                    logger.debug(f"Cache hit for chunk {chunk.id}")

            if not cache_hit:
                # Compute readability metrics
                readability = self._compute_readability_scores(chunk.text)

                # Compute composite quality score
                composite_score = self._compute_composite_score(chunk.text, readability)

                # Determine quality flag
                quality_flag = self._determine_quality_flag(
                    composite_score, chunk.text, readability
                )

                # Cache result if enabled
                if self.cache_manager:
                    cache_data = {
                        "readability": readability,
                        "composite_score": composite_score,
                        "quality_flag": quality_flag.value,
                    }
                    self.cache_manager.set(cache_key, cache_data)

            # Enrich chunk with quality metrics
            enriched_chunk = self._enrich_chunk(chunk, readability, composite_score, quality_flag)
            enriched_chunks.append(enriched_chunk)
            scores.append(composite_score)

        # Generate quality distribution report
        report = self._generate_quality_report(enriched_chunks, scores)

        # Log processing statistics
        processing_time_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Processed {len(input_data)} chunks in {processing_time_ms:.2f}ms "
            f"(avg: {processing_time_ms/len(input_data):.2f}ms per chunk)"
        )
        logger.info(
            f"Quality distribution: High={report.high_quality_count}, "
            f"Medium={report.medium_quality_count}, Low={report.low_quality_count}, "
            f"Review={report.review_required_count}"
        )

        # Store report in context if provided
        if context and hasattr(context, "metadata"):
            if not hasattr(context.metadata, "quality_report"):
                context.metadata.quality_report = report

        return enriched_chunks

    def _compute_readability_scores(self, text: str) -> ReadabilityScores:
        """Compute comprehensive readability metrics using textstat.

        Args:
            text: Text to analyze

        Returns:
            ReadabilityScores with all metrics computed
        """
        # Handle edge cases
        if not text or len(text.strip()) == 0:
            return ReadabilityScores()

        try:
            # Compute standard readability metrics
            scores = ReadabilityScores(
                flesch_reading_ease=max(0, min(100, textstat.flesch_reading_ease(text))),
                flesch_kincaid_grade=max(0, min(30, textstat.flesch_kincaid_grade(text))),
                gunning_fog=max(0, min(30, textstat.gunning_fog(text))),
                smog_index=max(0, min(30, textstat.smog_index(text))),
                coleman_liau_index=max(0, min(30, textstat.coleman_liau_index(text))),
                automated_readability_index=max(
                    0, min(30, textstat.automated_readability_index(text))
                ),
                dale_chall_readability_score=max(
                    0, min(30, textstat.dale_chall_readability_score(text))
                ),
                linsear_write_formula=max(0, min(30, textstat.linsear_write_formula(text))),
                syllable_count=textstat.syllable_count(text),
                lexical_diversity=self._calculate_lexical_diversity(text),
            )
            return scores
        except Exception as e:
            logger.warning(f"Error computing readability scores: {e}")
            return ReadabilityScores()

    def _calculate_lexical_diversity(self, text: str) -> float:
        """Calculate lexical diversity (type-token ratio).

        Args:
            text: Text to analyze

        Returns:
            Lexical diversity score (0-1)
        """
        words = text.lower().split()
        if not words:
            return 0.0
        unique_words = set(words)
        return len(unique_words) / len(words)

    def _compute_composite_score(self, text: str, readability: ReadabilityScores) -> float:
        """Compute weighted composite quality score.

        Args:
            text: Original text for anomaly detection
            readability: Computed readability scores

        Returns:
            Composite quality score (0.0-1.0)
        """
        # Detect anomalies (gibberish, special chars, etc.) first
        anomaly_score = self._detect_anomalies(text, readability)

        # If strong anomalies detected (>0.5), heavily penalize the score
        if anomaly_score > 0.5:
            return max(0.0, (1.0 - anomaly_score) * 0.3)  # Cap at 0.3 max

        # Normalize Flesch Reading Ease to 0-1 scale
        flesch_ease_norm = readability.flesch_reading_ease / 100.0

        # Normalize grade level (invert and cap at 12)
        grade_level_norm = max(0, 1.0 - (readability.flesch_kincaid_grade / 12.0))

        # Lexical diversity is already 0-1
        lexical_diversity = readability.lexical_diversity

        # Anomaly absence factor
        anomaly_absence = 1.0 - anomaly_score

        # Compute weighted composite
        weights = self.config.weights
        composite = (
            weights.get("flesch_ease", 0.2) * flesch_ease_norm
            + weights.get("grade_level", 0.2) * grade_level_norm
            + weights.get("lexical_diversity", 0.2) * lexical_diversity
            + weights.get("anomaly_absence", 0.4) * anomaly_absence
        )

        return max(0.0, min(1.0, composite))

    def _detect_anomalies(self, text: str, readability: ReadabilityScores) -> float:
        """Detect OCR gibberish and text anomalies.

        Args:
            text: Text to analyze
            readability: Readability scores for validation

        Returns:
            Anomaly score (0.0-1.0, higher = more anomalies)
        """
        if not self.config.detect_gibberish:
            return 0.0

        anomaly_score = 0.0

        # Quick check: special character ratio - strong indicator of gibberish
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        special_ratio = special_chars / max(1, len(text))
        if special_ratio > self.config.special_char_threshold:
            return 0.9  # Very strong signal - return early

        # Check lexical diversity - low diversity indicates gibberish
        if readability.lexical_diversity < self.config.min_lexical_diversity:
            anomaly_score = 0.8  # Strong signal

        # Check for repetitive single-character words only if needed
        if anomaly_score < 0.8:
            words = text.lower().split()
            if words:
                repetitive_words = sum(1 for word in words if len(set(word)) == 1 and len(word) > 3)
                repetitive_ratio = repetitive_words / len(words)
                if repetitive_ratio > 0.3:  # More than 30% are repetitive
                    anomaly_score = 0.85

        # Check for very low entropy text (long repeating patterns)
        if anomaly_score < 0.8 and len(text) > 50:
            words = text.lower().split()
            if len(words) <= 2:
                alphanumeric = sum(1 for c in text if c.isalnum())
                alphanumeric_ratio = alphanumeric / len(text)
                if alphanumeric_ratio > 0.95 and len(set(text)) < 20:
                    anomaly_score = 0.8

        # Grade level check
        if anomaly_score == 0:
            if (
                readability.flesch_kincaid_grade > self.config.max_grade_level
                or readability.flesch_kincaid_grade < 0
            ):
                anomaly_score = 0.7

        return anomaly_score

    def _determine_quality_flag(
        self, score: float, text: str, readability: ReadabilityScores
    ) -> QualityFlag:
        """Determine quality flag based on score and analysis.

        Args:
            score: Composite quality score
            text: Original text for additional checks
            readability: Readability scores for validation

        Returns:
            QualityFlag enum value
        """
        # Check for review requirement (severe anomalies)
        if self._requires_review(text, readability):
            return QualityFlag.REVIEW

        # Categorize by score thresholds
        if score >= 0.7:
            return QualityFlag.HIGH
        elif score >= 0.3:
            return QualityFlag.MEDIUM
        else:
            return QualityFlag.LOW

    def _requires_review(self, text: str, readability: ReadabilityScores) -> bool:
        """Check if text requires manual review.

        Args:
            text: Text to check
            readability: Readability scores

        Returns:
            True if manual review required
        """
        # Extreme grade levels
        if readability.flesch_kincaid_grade > 25 or readability.flesch_kincaid_grade < -5:
            return True

        # No readable content
        if len(text.strip()) < 10:
            return True

        # Extreme lexical poverty
        if readability.lexical_diversity < 0.05 and len(text) > 50:
            return True

        return False

    def _enrich_chunk(
        self,
        chunk: Chunk,
        readability: ReadabilityScores,
        composite_score: float,
        quality_flag: QualityFlag,
    ) -> Chunk:
        """Enrich chunk with quality metrics.

        Args:
            chunk: Original chunk
            readability: Computed readability scores
            composite_score: Composite quality score
            quality_flag: Quality flag

        Returns:
            Enriched chunk with quality metrics
        """
        # Update quality_score field
        chunk.quality_score = composite_score

        # Add readability scores to metadata
        chunk.readability_scores = readability.to_dict()

        # Add quality flag to metadata if it's a dict
        if isinstance(chunk.metadata, dict):
            chunk.metadata["quality_flag"] = quality_flag.value
            chunk.metadata["readability_scores"] = readability.to_dict()
        elif hasattr(chunk.metadata, "__dict__"):
            # For object-based metadata
            setattr(chunk.metadata, "quality_flag", quality_flag.value)
            setattr(chunk.metadata, "readability_scores", readability.to_dict())

        return chunk

    def _generate_cache_key(self, text: str) -> str:
        """Generate cache key for text content.

        Args:
            text: Text content

        Returns:
            Cache key string
        """
        if not self.cache_manager:
            return ""
        return self.cache_manager.generate_cache_key(text, self.config)

    def _generate_quality_report(
        self, chunks: List[Chunk], scores: List[float]
    ) -> QualityDistributionReport:
        """Generate quality distribution report.

        Args:
            chunks: Processed chunks with quality metrics
            scores: List of composite scores

        Returns:
            Quality distribution report
        """
        report = QualityDistributionReport(total_chunks=len(chunks))

        if not chunks:
            return report

        # Count by quality level
        for i, chunk in enumerate(chunks):
            # Get quality flag from metadata
            if isinstance(chunk.metadata, dict):
                flag_value = chunk.metadata.get("quality_flag", "medium")
            elif hasattr(chunk.metadata, "quality_flag"):
                flag_value = chunk.metadata.quality_flag
            else:
                flag_value = "medium"

            # Count by flag
            if flag_value == QualityFlag.HIGH.value:
                report.high_quality_count += 1
            elif flag_value == QualityFlag.MEDIUM.value:
                report.medium_quality_count += 1
            elif flag_value == QualityFlag.LOW.value:
                report.low_quality_count += 1
                report.flagged_chunks.append(chunk.id)
            elif flag_value == QualityFlag.REVIEW.value:
                report.review_required_count += 1
                report.flagged_chunks.append(chunk.id)

        # Compute statistics
        scores_array = np.array(scores)
        report.mean_score = float(np.mean(scores_array))
        report.std_score = float(np.std(scores_array))

        # Create histogram (10 bins)
        hist, bin_edges = np.histogram(scores_array, bins=10, range=(0, 1))
        for i, count in enumerate(hist):
            bin_label = f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}"
            report.score_histogram[bin_label] = int(count)

        return report
