"""Unit tests for QualityScore dataclass (Story 3.3 - RED PHASE).

Tests quality score model creation, validation, serialization, and helper methods.
All tests WILL FAIL until QualityScore is implemented (GREEN phase).

Test Coverage:
    - AC-3.3-4: Readability score fields (Flesch-Kincaid, Gunning Fog)
    - AC-3.3-5: Composite quality score calculation (OCR, completeness, coherence, overall)
    - AC-3.3-8: Low-quality flags list (low_ocr, incomplete_extraction, high_complexity, gibberish)
"""

import json

import pytest

# These imports WILL FAIL in RED phase - this is expected
try:
    from data_extract.chunk.quality import QualityScore
except ImportError:
    QualityScore = None

pytestmark = [pytest.mark.P1, pytest.mark.unit, pytest.mark.chunking, pytest.mark.quality]


class TestQualityScoreModel:
    """Test QualityScore dataclass creation and validation (AC-3.3-4, AC-3.3-5, AC-3.3-8)."""

    def test_quality_score_creation_all_fields(self):
        """Should create QualityScore with all required fields populated."""
        # GIVEN: Quality metrics for a high-quality chunk
        readability_fk = 8.5  # Flesch-Kincaid Grade Level
        readability_fog = 10.2  # Gunning Fog Index
        ocr_confidence = 0.99
        completeness = 0.95
        coherence = 0.88
        overall = 0.93
        flags = []

        # WHEN: QualityScore instantiated
        quality = QualityScore(
            readability_flesch_kincaid=readability_fk,
            readability_gunning_fog=readability_fog,
            ocr_confidence=ocr_confidence,
            completeness=completeness,
            coherence=coherence,
            overall=overall,
            flags=flags,
        )

        # THEN: All fields populated correctly
        assert quality.readability_flesch_kincaid == readability_fk
        assert quality.readability_gunning_fog == readability_fog
        assert quality.ocr_confidence == ocr_confidence
        assert quality.completeness == completeness
        assert quality.coherence == coherence
        assert quality.overall == overall
        assert quality.flags == flags

    def test_quality_score_frozen_immutability(self):
        """Should enforce immutability with frozen=True (ADR-001)."""
        # GIVEN: QualityScore instance
        quality = QualityScore(
            readability_flesch_kincaid=8.0,
            readability_gunning_fog=9.0,
            ocr_confidence=0.98,
            completeness=0.96,
            coherence=0.85,
            overall=0.92,
            flags=[],
        )

        # WHEN/THEN: Attempting to modify raises AttributeError
        with pytest.raises(AttributeError):
            quality.overall = 0.50

    def test_quality_score_validation_score_ranges(self):
        """Should validate score ranges (0.0-1.0 for quality scores, 0.0-30.0 for readability)."""
        # GIVEN/WHEN/THEN: Scores outside valid ranges should raise validation error

        # Test OCR confidence out of range
        with pytest.raises((ValueError, TypeError)):
            QualityScore(
                readability_flesch_kincaid=8.0,
                readability_gunning_fog=9.0,
                ocr_confidence=1.5,  # Invalid: > 1.0
                completeness=0.95,
                coherence=0.88,
                overall=0.93,
                flags=[],
            )

        # Test negative completeness
        with pytest.raises((ValueError, TypeError)):
            QualityScore(
                readability_flesch_kincaid=8.0,
                readability_gunning_fog=9.0,
                ocr_confidence=0.98,
                completeness=-0.1,  # Invalid: < 0.0
                coherence=0.88,
                overall=0.93,
                flags=[],
            )

        # Test Flesch-Kincaid out of typical range (0.0-30.0)
        with pytest.raises((ValueError, TypeError)):
            QualityScore(
                readability_flesch_kincaid=35.0,  # Invalid: > 30.0
                readability_gunning_fog=9.0,
                ocr_confidence=0.98,
                completeness=0.95,
                coherence=0.88,
                overall=0.93,
                flags=[],
            )


class TestQualityScoreSerialization:
    """Test QualityScore serialization (AC-3.3-5)."""

    def test_to_dict_serialization(self):
        """Should serialize to JSON-compatible dict."""
        # GIVEN: QualityScore with all fields
        quality = QualityScore(
            readability_flesch_kincaid=12.3,
            readability_gunning_fog=14.5,
            ocr_confidence=0.87,
            completeness=0.92,
            coherence=0.78,
            overall=0.85,
            flags=["low_ocr", "high_complexity"],
        )

        # WHEN: to_dict() called
        result = quality.to_dict()

        # THEN: Returns dict with all fields
        assert isinstance(result, dict)
        assert result["readability_flesch_kincaid"] == 12.3
        assert result["readability_gunning_fog"] == 14.5
        assert result["ocr_confidence"] == 0.87
        assert result["completeness"] == 0.92
        assert result["coherence"] == 0.78
        assert result["overall"] == 0.85
        assert result["flags"] == ["low_ocr", "high_complexity"]

        # AND: Dict is JSON serializable
        json_str = json.dumps(result)
        assert json_str is not None

    def test_to_dict_empty_flags(self):
        """Should serialize empty flags as empty list (not null) (AC-3.3-8)."""
        # GIVEN: QualityScore with no quality issues
        quality = QualityScore(
            readability_flesch_kincaid=8.0,
            readability_gunning_fog=9.0,
            ocr_confidence=0.99,
            completeness=0.98,
            coherence=0.95,
            overall=0.97,
            flags=[],  # No issues
        )

        # WHEN: to_dict() called
        result = quality.to_dict()

        # THEN: flags is empty list, not null
        assert result["flags"] == []
        assert result["flags"] is not None


class TestQualityScoreHelperMethods:
    """Test QualityScore helper methods (AC-3.3-5)."""

    def test_is_high_quality_above_threshold(self):
        """Should return True when overall score >= 0.75 threshold."""
        # GIVEN: QualityScore with high overall score
        quality = QualityScore(
            readability_flesch_kincaid=8.0,
            readability_gunning_fog=9.0,
            ocr_confidence=0.98,
            completeness=0.96,
            coherence=0.90,
            overall=0.92,  # Above 0.75 threshold
            flags=[],
        )

        # WHEN: is_high_quality() called
        result = quality.is_high_quality()

        # THEN: Returns True
        assert result is True

    def test_is_high_quality_below_threshold(self):
        """Should return False when overall score < 0.75 threshold."""
        # GIVEN: QualityScore with low overall score
        quality = QualityScore(
            readability_flesch_kincaid=18.0,
            readability_gunning_fog=20.0,
            ocr_confidence=0.85,
            completeness=0.70,
            coherence=0.60,
            overall=0.72,  # Below 0.75 threshold
            flags=["low_ocr", "incomplete_extraction"],
        )

        # WHEN: is_high_quality() called
        result = quality.is_high_quality()

        # THEN: Returns False
        assert result is False

    def test_is_high_quality_at_threshold(self):
        """Should return True when overall score exactly equals 0.75 threshold."""
        # GIVEN: QualityScore at threshold boundary
        quality = QualityScore(
            readability_flesch_kincaid=10.0,
            readability_gunning_fog=11.0,
            ocr_confidence=0.90,
            completeness=0.85,
            coherence=0.75,
            overall=0.75,  # Exactly at threshold
            flags=[],
        )

        # WHEN: is_high_quality() called
        result = quality.is_high_quality()

        # THEN: Returns True (>= threshold)
        assert result is True


class TestQualityScoreFlagVariations:
    """Test QualityScore with various flag combinations (AC-3.3-8)."""

    def test_single_flag_low_ocr(self):
        """Should handle single quality flag (low_ocr)."""
        # GIVEN: QualityScore with low OCR confidence
        quality = QualityScore(
            readability_flesch_kincaid=8.0,
            readability_gunning_fog=9.0,
            ocr_confidence=0.87,  # Below 0.95 threshold
            completeness=0.95,
            coherence=0.88,
            overall=0.90,
            flags=["low_ocr"],
        )

        # THEN: Flag list contains expected flag
        assert "low_ocr" in quality.flags
        assert len(quality.flags) == 1

    def test_multiple_flags_combination(self):
        """Should handle multiple quality flags simultaneously (AC-3.3-8)."""
        # GIVEN: QualityScore with multiple issues
        quality = QualityScore(
            readability_flesch_kincaid=18.0,  # High complexity
            readability_gunning_fog=20.0,
            ocr_confidence=0.85,  # Low OCR
            completeness=0.88,  # Incomplete
            coherence=0.70,
            overall=0.78,
            flags=["low_ocr", "incomplete_extraction", "high_complexity"],
        )

        # THEN: All flags present
        assert "low_ocr" in quality.flags
        assert "incomplete_extraction" in quality.flags
        assert "high_complexity" in quality.flags
        assert len(quality.flags) == 3

    def test_all_quality_flags(self):
        """Should support all defined quality flag types (AC-3.3-8)."""
        # GIVEN: QualityScore with all possible flags
        all_flags = ["low_ocr", "incomplete_extraction", "high_complexity", "gibberish"]
        quality = QualityScore(
            readability_flesch_kincaid=20.0,
            readability_gunning_fog=22.0,
            ocr_confidence=0.70,
            completeness=0.75,
            coherence=0.60,
            overall=0.65,
            flags=all_flags,
        )

        # THEN: All flags preserved
        assert set(quality.flags) == set(all_flags)
        assert len(quality.flags) == 4


class TestQualityScoreEdgeCases:
    """Test QualityScore edge cases and boundary conditions."""

    def test_perfect_quality_scores(self):
        """Should handle perfect quality scores (1.0 across all metrics)."""
        # GIVEN: Perfect quality chunk
        quality = QualityScore(
            readability_flesch_kincaid=5.0,  # Very readable (grade 5)
            readability_gunning_fog=6.0,
            ocr_confidence=1.0,  # Perfect OCR
            completeness=1.0,  # Complete extraction
            coherence=1.0,  # Perfect coherence
            overall=1.0,  # Perfect overall
            flags=[],  # No issues
        )

        # THEN: All scores at maximum
        assert quality.ocr_confidence == 1.0
        assert quality.completeness == 1.0
        assert quality.coherence == 1.0
        assert quality.overall == 1.0
        assert quality.is_high_quality() is True

    def test_zero_quality_scores(self):
        """Should handle minimum quality scores (0.0 for extreme cases)."""
        # GIVEN: Extremely low quality chunk
        quality = QualityScore(
            readability_flesch_kincaid=0.0,
            readability_gunning_fog=0.0,
            ocr_confidence=0.0,  # OCR completely failed
            completeness=0.0,  # Nothing extracted
            coherence=0.0,  # No coherence
            overall=0.0,  # Worst overall
            flags=["low_ocr", "incomplete_extraction", "gibberish"],
        )

        # THEN: All scores at minimum
        assert quality.ocr_confidence == 0.0
        assert quality.completeness == 0.0
        assert quality.coherence == 0.0
        assert quality.overall == 0.0
        assert quality.is_high_quality() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
