"""TDD RED Phase Tests: SimilarityConfig and CacheConfig Field Validation (AC-5.2-4).

These tests verify:
- SimilarityConfig threshold range validation
- CacheConfig max_size_mb validation

All tests are designed to FAIL initially (TDD RED phase).
"""

import pytest

# P0: Critical path - always run
pytestmark = [
    pytest.mark.P0,
    pytest.mark.story_5_2,
    pytest.mark.unit,
    pytest.mark.cli,
]


@pytest.mark.unit
@pytest.mark.story_5_2
class TestPydanticFieldValidation:
    """AC-5.2-4: Test Pydantic field-level validation for SimilarityConfig and CacheConfig."""

    def test_similarity_threshold_range_validation(self):
        """
        RED: Verify similarity thresholds reject values > 1.0.

        Given: A SimilarityConfig model
        When: We create it with duplicate_threshold = 2.0
        Then: ValidationError should be raised

        Expected RED failure: Model accepts invalid threshold
        """
        # Given
        try:
            from pydantic import ValidationError

            from data_extract.cli.models import SimilarityConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            SimilarityConfig(duplicate_threshold=2.0)

        error_str = str(exc_info.value)
        assert (
            "threshold" in error_str.lower() or "1.0" in error_str or "le" in error_str.lower()
        ), f"Error should mention threshold range: {error_str}"

    def test_similarity_threshold_negative_validation(self):
        """
        RED: Verify similarity thresholds reject negative values.

        Given: A SimilarityConfig model
        When: We create it with related_threshold = -0.5
        Then: ValidationError should be raised

        Expected RED failure: Model accepts negative threshold
        """
        # Given
        try:
            from pydantic import ValidationError

            from data_extract.cli.models import SimilarityConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            SimilarityConfig(related_threshold=-0.5)

        error_str = str(exc_info.value)
        assert (
            "threshold" in error_str.lower() or "0" in error_str or "ge" in error_str.lower()
        ), f"Error should mention non-negative constraint: {error_str}"

    def test_cache_max_size_positive_validation(self):
        """
        RED: Verify cache_max_size_mb rejects zero/negative values.

        Given: A CacheConfig model
        When: We create it with max_size_mb = 0
        Then: ValidationError should be raised

        Expected RED failure: Model accepts zero cache size
        """
        # Given
        try:
            from pydantic import ValidationError

            from data_extract.cli.models import CacheConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            CacheConfig(max_size_mb=0)

        error_str = str(exc_info.value)
        assert (
            "size" in error_str.lower()
            or "greater" in error_str.lower()
            or "gt" in error_str.lower()
        ), f"Error should mention cache size constraint: {error_str}"

    def test_similarity_threshold_ordering_validation(self):
        """
        Verify duplicate_threshold >= related_threshold.

        Given: A SimilarityConfig model
        When: We create it with duplicate_threshold=0.6 and related_threshold=0.8
        Then: ValidationError should be raised (duplicate < related)

        Expected: ValidationError mentioning threshold ordering constraint
        """
        # Given
        try:
            from pydantic import ValidationError

            from data_extract.cli.models import SimilarityConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When/Then: duplicate_threshold (0.6) < related_threshold (0.8) should fail
        with pytest.raises(ValidationError) as exc_info:
            SimilarityConfig(duplicate_threshold=0.6, related_threshold=0.8)

        error_str = str(exc_info.value)
        assert (
            "duplicate_threshold" in error_str.lower() or "related_threshold" in error_str.lower()
        ), f"Error should mention threshold ordering: {error_str}"

    def test_similarity_threshold_ordering_accepts_valid_config(self):
        """
        Verify threshold ordering validation accepts valid configurations.

        Given: A SimilarityConfig model
        When: We create it with duplicate_threshold=0.95 and related_threshold=0.7
        Then: No ValidationError should be raised (valid: duplicate > related)

        Expected: Model created successfully
        """
        # Given
        try:
            from data_extract.cli.models import SimilarityConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When: duplicate_threshold (0.95) >= related_threshold (0.7) should succeed
        config = SimilarityConfig(duplicate_threshold=0.95, related_threshold=0.7)

        # Then: Should create successfully
        assert config.duplicate_threshold == 0.95
        assert config.related_threshold == 0.7

    def test_similarity_threshold_ordering_accepts_equal_values(self):
        """
        Verify threshold ordering validation accepts equal thresholds.

        Given: A SimilarityConfig model
        When: We create it with duplicate_threshold=0.8 and related_threshold=0.8
        Then: No ValidationError should be raised (valid: duplicate == related)

        Expected: Model created successfully
        """
        # Given
        try:
            from data_extract.cli.models import SimilarityConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When: duplicate_threshold == related_threshold should succeed
        config = SimilarityConfig(duplicate_threshold=0.8, related_threshold=0.8)

        # Then: Should create successfully
        assert config.duplicate_threshold == 0.8
        assert config.related_threshold == 0.8
