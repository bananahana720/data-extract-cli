"""Quality scoring for chunks (Story 3.3).

Implements QualityScore dataclass for comprehensive chunk quality metrics
including readability scores, completeness, coherence, and quality flags.

This module satisfies:
    - AC-3.3-4: Readability score calculation (Flesch-Kincaid, Gunning Fog)
    - AC-3.3-5: Composite quality score (OCR, completeness, coherence, overall)
    - AC-3.3-8: Low-quality chunk flags (low_ocr, incomplete_extraction, high_complexity, gibberish)
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class QualityScore:
    """Quality metrics for a text chunk.

    Immutable quality score combining readability, OCR confidence, completeness,
    coherence, and specific quality issue flags. Designed for RAG chunk filtering
    and prioritization workflows.

    Immutability enforced per ADR-001 to prevent pipeline state corruption.

    Attributes:
        readability_flesch_kincaid: Flesch-Kincaid Grade Level (0.0-30.0).
            Lower is more readable. Grade 8 = 8th grade reading level.
        readability_gunning_fog: Gunning Fog Index (0.0-30.0).
            Lower is more readable. Measures years of education needed.
        ocr_confidence: OCR accuracy confidence (0.0-1.0).
            Propagated from Epic 2 source metadata. 1.0 = perfect OCR.
        completeness: Entity preservation rate (0.0-1.0).
            Calculated from Story 3.2 entity analysis. 1.0 = all entities intact.
        coherence: Sentence-to-sentence semantic overlap (0.0-1.0).
            Simple lexical overlap heuristic. 1.0 = high coherence.
        overall: Weighted composite quality score (0.0-1.0).
            Weighted average: OCR (40%), completeness (30%), coherence (20%), readability (10%).
            1.0 = perfect quality, 0.0 = unusable.
        flags: Quality issue flags for targeted review.
            Possible values: 'low_ocr', 'incomplete_extraction', 'high_complexity', 'gibberish'.
            Empty list if no issues detected.

    Example:
        >>> quality = QualityScore(
        ...     readability_flesch_kincaid=8.5,
        ...     readability_gunning_fog=10.2,
        ...     ocr_confidence=0.99,
        ...     completeness=0.95,
        ...     coherence=0.88,
        ...     overall=0.93,
        ...     flags=[]
        ... )
        >>> quality.is_high_quality()
        True
        >>> quality.to_dict()
        {'readability_flesch_kincaid': 8.5, 'readability_gunning_fog': 10.2, ...}

    Raises:
        ValueError: If scores outside valid ranges (quality 0.0-1.0, readability 0.0-30.0).
    """

    readability_flesch_kincaid: float
    readability_gunning_fog: float
    ocr_confidence: float
    completeness: float
    coherence: float
    overall: float
    flags: List[str]

    def __post_init__(self) -> None:
        """Validate score ranges after initialization.

        Ensures all quality scores in 0.0-1.0 range and readability scores in 0.0-30.0 range.

        Raises:
            ValueError: If any score outside valid range.
        """
        # Validate quality scores (0.0-1.0)
        quality_scores = {
            "ocr_confidence": self.ocr_confidence,
            "completeness": self.completeness,
            "coherence": self.coherence,
            "overall": self.overall,
        }
        for name, score in quality_scores.items():
            if not (0.0 <= score <= 1.0):
                raise ValueError(f"{name} must be in range [0.0, 1.0], got {score}")

        # Validate readability scores (0.0-30.0)
        readability_scores = {
            "readability_flesch_kincaid": self.readability_flesch_kincaid,
            "readability_gunning_fog": self.readability_gunning_fog,
        }
        for name, score in readability_scores.items():
            if not (0.0 <= score <= 30.0):
                raise ValueError(f"{name} must be in range [0.0, 30.0], got {score}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary.

        Returns:
            Dict with all QualityScore fields in JSON-compatible format.

        Example:
            >>> quality = QualityScore(..., flags=["low_ocr"])
            >>> quality.to_dict()
            {'readability_flesch_kincaid': 12.3, 'flags': ['low_ocr'], ...}
        """
        return {
            "readability_flesch_kincaid": self.readability_flesch_kincaid,
            "readability_gunning_fog": self.readability_gunning_fog,
            "ocr_confidence": self.ocr_confidence,
            "completeness": self.completeness,
            "coherence": self.coherence,
            "overall": self.overall,
            "flags": self.flags,
        }

    def is_high_quality(self) -> bool:
        """Check if chunk meets high-quality threshold.

        Uses overall score >= 0.75 threshold for RAG chunk filtering.

        Returns:
            True if overall quality >= 0.75, False otherwise.

        Example:
            >>> high_quality_chunk = QualityScore(..., overall=0.92, ...)
            >>> high_quality_chunk.is_high_quality()
            True
            >>> low_quality_chunk = QualityScore(..., overall=0.68, ...)
            >>> low_quality_chunk.is_high_quality()
            False
        """
        return self.overall >= 0.75


__all__ = ["QualityScore"]
