"""TDD RED Phase Tests: Pydantic Default Values and Error Messages (AC-5.2-4).

These tests verify:
- Pydantic models have sensible defaults
- Error messages include field names and constraints
- Multiple validation errors are all reported

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
class TestPydanticDefaultValues:
    """AC-5.2-4: Test Pydantic models have sensible defaults."""

    def test_tfidf_config_defaults(self):
        """
        RED: Verify TfidfConfig has sensible defaults.

        Given: TfidfConfig model
        When: We create it without arguments
        Then: It should have sensible default values

        Expected RED failure: Model requires arguments or bad defaults
        """
        # Given
        try:
            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        config = TfidfConfig()

        # Then
        assert config.max_features is not None
        assert config.max_features > 0
        assert config.min_df is not None
        assert config.max_df is not None
        assert 0.0 < config.max_df <= 1.0
        assert config.ngram_range is not None
        assert len(config.ngram_range) == 2

    def test_similarity_config_defaults(self):
        """
        RED: Verify SimilarityConfig has sensible defaults.

        Given: SimilarityConfig model
        When: We create it without arguments
        Then: It should have sensible default values

        Expected RED failure: Model requires arguments
        """
        # Given
        try:
            from data_extract.cli.models import SimilarityConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        config = SimilarityConfig()

        # Then
        assert config.duplicate_threshold is not None
        assert 0.0 <= config.duplicate_threshold <= 1.0
        assert config.related_threshold is not None
        assert 0.0 <= config.related_threshold <= 1.0

    def test_cache_config_defaults(self):
        """
        RED: Verify CacheConfig has sensible defaults.

        Given: CacheConfig model
        When: We create it without arguments
        Then: It should have sensible default values

        Expected RED failure: Model requires arguments
        """
        # Given
        try:
            from data_extract.cli.models import CacheConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        config = CacheConfig()

        # Then
        assert config.enabled is not None
        assert isinstance(config.enabled, bool)
        assert config.max_size_mb is not None
        assert config.max_size_mb > 0

    def test_config_model_defaults(self):
        """
        RED: Verify ConfigModel has all nested configs with defaults.

        Given: ConfigModel (root config)
        When: We create it without arguments
        Then: All nested configs should be initialized

        Expected RED failure: Nested configs missing
        """
        # Given
        try:
            from data_extract.cli.models import ConfigModel
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        config = ConfigModel()

        # Then
        assert hasattr(config, "semantic")
        assert hasattr(config, "cache")
        assert config.semantic is not None
        assert config.cache is not None


@pytest.mark.unit
@pytest.mark.story_5_2
class TestPydanticErrorMessages:
    """AC-5.2-4: Test Pydantic provides clear error messages."""

    def test_validation_error_includes_field_name(self):
        """
        RED: Verify validation error includes field name.

        Given: Invalid config value
        When: Validation fails
        Then: Error message should include field name

        Expected RED failure: Unclear error message
        """
        # Given
        try:
            from pydantic import ValidationError

            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            TfidfConfig(max_features=-1)

        # Should mention the field
        errors = exc_info.value.errors()
        field_names = [error.get("loc", [None])[0] for error in errors]
        assert "max_features" in field_names, f"Error should mention field name: {exc_info.value}"

    def test_validation_error_includes_constraint(self):
        """
        RED: Verify validation error includes constraint description.

        Given: Value violating constraint
        When: Validation fails
        Then: Error should describe the constraint

        Expected RED failure: Generic error without constraint info
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
        # Should mention the constraint
        assert any(
            term in error_str for term in ["1.0", "less than", "le", "at most", "maximum"]
        ), f"Error should describe constraint: {exc_info.value}"

    def test_multiple_validation_errors_all_reported(self):
        """
        RED: Verify multiple validation errors are all reported.

        Given: Multiple invalid values
        When: Validation fails
        Then: All errors should be reported

        Expected RED failure: Only first error reported
        """
        # Given
        try:
            from pydantic import ValidationError

            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            TfidfConfig(
                max_features=-1,  # Invalid
                min_df=-1,  # Invalid
                max_df=2.0,  # Invalid
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 2, f"Should report multiple errors: {exc_info.value}"
