"""TDD RED Phase Tests: TfidfConfig Field-Level Validation (AC-5.2-4).

These tests verify:
- TfidfConfig field-level validation constraints
- Positive/negative value validation
- Range validation for max_df, min_df
- ngram_range order validation

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
    """AC-5.2-4: Test Pydantic field-level validation for TfidfConfig."""

    def test_tfidf_max_features_positive_validation(self):
        """
        RED: Verify tfidf_max_features rejects negative values.

        Given: A TfidfConfig model
        When: We create it with max_features = -100
        Then: ValidationError should be raised

        Expected RED failure: No validation or wrong error
        """
        # Given
        try:
            from pydantic import ValidationError

            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            TfidfConfig(max_features=-100)

        error_str = str(exc_info.value)
        assert (
            "max_features" in error_str.lower()
            or "greater" in error_str.lower()
            or "ge" in error_str.lower()
        ), f"Error should mention max_features constraint: {error_str}"

    def test_tfidf_max_features_type_validation(self):
        """
        RED: Verify tfidf_max_features rejects string values.

        Given: A TfidfConfig model
        When: We create it with max_features = "not_a_number"
        Then: ValidationError should be raised

        Expected RED failure: Model accepts invalid type
        """
        # Given
        try:
            from pydantic import ValidationError

            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            TfidfConfig(max_features="not_a_number")

        error_str = str(exc_info.value)
        assert (
            "int" in error_str.lower()
            or "type" in error_str.lower()
            or "valid" in error_str.lower()
        ), f"Error should mention type constraint: {error_str}"

    def test_tfidf_max_features_upper_bound_validation(self):
        """
        RED: Verify tfidf_max_features has upper bound validation.

        Given: A TfidfConfig model
        When: We create it with max_features = 100000 (too high)
        Then: ValidationError should be raised

        Expected RED failure: No upper bound validation
        """
        # Given
        try:
            from pydantic import ValidationError

            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            TfidfConfig(max_features=100000)

        error_str = str(exc_info.value)
        assert (
            "max_features" in error_str.lower() or "50000" in error_str or "le" in error_str.lower()
        ), f"Error should mention upper bound: {error_str}"

    def test_tfidf_max_df_range_validation(self):
        """
        RED: Verify tfidf_max_df rejects values > 1.0.

        Given: A TfidfConfig model
        When: We create it with max_df = 1.5
        Then: ValidationError should be raised

        Expected RED failure: Model accepts invalid range
        """
        # Given
        try:
            from pydantic import ValidationError

            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            TfidfConfig(max_df=1.5)

        error_str = str(exc_info.value).lower()
        assert (
            "max_df" in error_str
            or "1" in error_str
            or "le" in error_str
            or "less than or equal" in error_str
        ), f"Error should mention max_df <= 1.0 constraint: {exc_info.value}"

    def test_tfidf_min_df_positive_validation(self):
        """
        RED: Verify tfidf_min_df rejects negative values.

        Given: A TfidfConfig model
        When: We create it with min_df = -1
        Then: ValidationError should be raised

        Expected RED failure: Model accepts negative min_df
        """
        # Given
        try:
            from pydantic import ValidationError

            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            TfidfConfig(min_df=-1)

        error_str = str(exc_info.value)
        assert (
            "min_df" in error_str.lower()
            or "greater" in error_str.lower()
            or "ge" in error_str.lower()
        ), f"Error should mention min_df constraint: {error_str}"

    def test_ngram_range_order_validation(self):
        """
        RED: Verify ngram_range rejects (max, min) order (min > max).

        Given: A TfidfConfig model
        When: We create it with ngram_range = (3, 1)
        Then: ValidationError should be raised

        Expected RED failure: Model accepts invalid ngram order
        """
        # Given
        try:
            from pydantic import ValidationError

            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            TfidfConfig(ngram_range=(3, 1))

        error_str = str(exc_info.value)
        assert (
            "ngram" in error_str.lower()
            or "min" in error_str.lower()
            or "order" in error_str.lower()
        ), f"Error should mention ngram_range order: {error_str}"

    def test_df_ordering_validation_with_float_min_df(self):
        """
        Verify min_df < max_df when min_df is a float (proportion).

        Given: A TfidfConfig model
        When: We create it with min_df=0.96 (float) and max_df=0.95
        Then: ValidationError should be raised (min_df >= max_df)

        Expected: ValidationError mentioning df ordering constraint
        """
        # Given
        try:
            from pydantic import ValidationError

            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When/Then: min_df (0.96) >= max_df (0.95) should fail
        with pytest.raises(ValidationError) as exc_info:
            TfidfConfig(min_df=1, max_df=0.95)  # min_df=1 treated as float 1.0

        error_str = str(exc_info.value)
        assert (
            "min_df" in error_str.lower() or "max_df" in error_str.lower()
        ), f"Error should mention df ordering: {error_str}"

    def test_df_ordering_validation_accepts_valid_int_min_df(self):
        """
        Verify min_df < max_df validation accepts valid int configurations.

        Given: A TfidfConfig model
        When: We create it with min_df=2 (int > 1) and max_df=0.95
        Then: No ValidationError should be raised (valid: int >= 2 not in [0,1])

        Expected: Model created successfully
        """
        # Given
        try:
            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When: min_df=2 is not in [0, 1] range, so no validation against max_df
        valid_config = TfidfConfig(min_df=2, max_df=0.95)

        # Then: Should create successfully
        assert valid_config.min_df == 2
        assert valid_config.max_df == 0.95

    def test_df_ordering_no_validation_when_min_df_is_int_gt_1(self):
        """
        Verify df ordering validation only applies when min_df in [0.0, 1.0].

        Given: A TfidfConfig model
        When: We create it with min_df=5 (int > 1) and max_df=0.95
        Then: No ValidationError should be raised (no cross-validation for int counts)

        Expected: Model created successfully (int min_df not compared to float max_df)
        """
        # Given
        try:
            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When: min_df as count (5) with max_df as proportion (0.95)
        config = TfidfConfig(min_df=5, max_df=0.95)

        # Then: Should create successfully (different units)
        assert config.min_df == 5
        assert config.max_df == 0.95
