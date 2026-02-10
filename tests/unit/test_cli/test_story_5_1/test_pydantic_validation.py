"""TDD RED Phase Tests: Pydantic Validation (AC-5.1-4).

These tests verify:
- AC-5.1-4: Pydantic validation for config models

All tests are designed to FAIL initially (TDD RED phase).
"""

from typing import Any

import pytest

# P0: Config validation - critical for data integrity
pytestmark = [
    pytest.mark.P0,
    pytest.mark.unit,
    pytest.mark.story_5_1,
    pytest.mark.cli,
]


@pytest.mark.unit
@pytest.mark.story_5_1
class TestPydanticConfigModels:
    """AC-5.1-4: Pydantic validation for configuration models."""

    @pytest.mark.test_id("5.1-UNIT-001")
    def test_semantic_config_model_exists(self):
        """
        RED: Verify SemanticConfig Pydantic model exists.

        Given: The CLI config module
        When: We import SemanticConfig
        Then: It should be a Pydantic BaseModel subclass

        Expected RED failure: ImportError or not a Pydantic model
        """
        # Given/When
        try:
            from pydantic import BaseModel

            from data_extract.cli.models import SemanticConfig
        except ImportError as e:
            pytest.fail(f"Cannot import SemanticConfig: {e}")

        # Then
        assert issubclass(
            SemanticConfig, BaseModel
        ), "SemanticConfig should be a Pydantic BaseModel subclass"

    @pytest.mark.test_id("5.1-UNIT-002")
    def test_tfidf_config_model_exists(self):
        """
        RED: Verify TfidfConfig Pydantic model exists.

        Given: The CLI config module
        When: We import TfidfConfig
        Then: It should be a Pydantic BaseModel

        Expected RED failure: ImportError
        """
        # Given/When
        try:
            from pydantic import BaseModel

            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Cannot import TfidfConfig: {e}")

        # Then
        assert issubclass(TfidfConfig, BaseModel), "TfidfConfig should be a Pydantic BaseModel"

    @pytest.mark.test_id("5.1-UNIT-003")
    def test_cli_config_model_exists(self):
        """
        RED: Verify CliConfig (root config) Pydantic model exists.

        Given: The CLI config module
        When: We import CliConfig
        Then: It should be a Pydantic BaseModel with nested models

        Expected RED failure: ImportError
        """
        # Given/When
        try:
            from pydantic import BaseModel

            from data_extract.cli.models import CliConfig
        except ImportError as e:
            pytest.fail(f"Cannot import CliConfig: {e}")

        # Then
        assert issubclass(CliConfig, BaseModel), "CliConfig should be a Pydantic BaseModel"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestPydanticFieldValidation:
    """Test Pydantic field-level validation with custom validators."""

    @pytest.mark.test_id("5.1-UNIT-004")
    def test_tfidf_max_features_positive_validation(self):
        """
        RED: Verify tfidf_max_features rejects negative values.

        Given: A TfidfConfig model
        When: We create it with tfidf_max_features = -100
        Then: ValidationError should be raised

        Expected RED failure: Model doesn't exist or no validation
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

        # Verify error message mentions the constraint
        error_str = str(exc_info.value)
        assert (
            "max_features" in error_str.lower() or "greater" in error_str.lower()
        ), f"Error should mention max_features constraint: {error_str}"

    @pytest.mark.test_id("5.1-UNIT-005")
    def test_tfidf_max_features_type_validation(self):
        """
        RED: Verify tfidf_max_features rejects string values.

        Given: A TfidfConfig model
        When: We create it with tfidf_max_features = "not_a_number"
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
            "int" in error_str.lower() or "type" in error_str.lower()
        ), f"Error should mention type constraint: {error_str}"

    @pytest.mark.test_id("5.1-UNIT-006")
    def test_tfidf_max_df_range_validation_upper(self):
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

        error_str = str(exc_info.value)
        assert (
            "max_df" in error_str.lower() or "1.0" in error_str or "le" in error_str.lower()
        ), f"Error should mention max_df <= 1.0 constraint: {error_str}"

    @pytest.mark.test_id("5.1-UNIT-007")
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
            "min_df" in error_str.lower() or "greater" in error_str.lower()
        ), f"Error should mention min_df constraint: {error_str}"

    @pytest.mark.test_id("5.1-UNIT-008")
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
            "ngram" in error_str.lower() or "min" in error_str.lower()
        ), f"Error should mention ngram_range order constraint: {error_str}"

    @pytest.mark.test_id("5.1-UNIT-009")
    def test_similarity_threshold_range_validation(self):
        """
        RED: Verify similarity_threshold rejects values > 1.0.

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
            "threshold" in error_str.lower() or "1.0" in error_str
        ), f"Error should mention threshold range: {error_str}"

    @pytest.mark.test_id("5.1-UNIT-010")
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
            "size" in error_str.lower() or "greater" in error_str.lower()
        ), f"Error should mention cache size constraint: {error_str}"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestPydanticConfigDefaults:
    """Test Pydantic models have sensible defaults."""

    @pytest.mark.test_id("5.1-UNIT-011")
    def test_tfidf_config_has_defaults(self):
        """
        RED: Verify TfidfConfig can be created with all defaults.

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
        assert config.max_features is not None, "max_features should have default"
        assert config.max_features > 0, "max_features default should be positive"
        assert config.min_df is not None, "min_df should have default"
        assert config.max_df is not None, "max_df should have default"
        assert 0.0 < config.max_df <= 1.0, "max_df default should be in (0, 1]"

    @pytest.mark.test_id("5.1-UNIT-012")
    def test_semantic_config_has_defaults(self):
        """
        RED: Verify SemanticConfig can be created with all defaults.

        Given: SemanticConfig model
        When: We create it without arguments
        Then: It should have sensible default values

        Expected RED failure: Model requires arguments
        """
        # Given
        try:
            from data_extract.cli.models import SemanticConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        config = SemanticConfig()

        # Then
        assert hasattr(config, "tfidf"), "SemanticConfig should have tfidf nested config"
        assert hasattr(config, "similarity"), "SemanticConfig should have similarity config"
        assert hasattr(config, "lsa"), "SemanticConfig should have lsa config"

    @pytest.mark.test_id("5.1-UNIT-013")
    def test_cli_config_has_defaults(self):
        """
        RED: Verify CliConfig can be created with all defaults.

        Given: CliConfig model
        When: We create it without arguments
        Then: It should have all required nested configs

        Expected RED failure: Model requires arguments
        """
        # Given
        try:
            from data_extract.cli.models import CliConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        config = CliConfig()

        # Then
        assert hasattr(config, "semantic"), "CliConfig should have semantic config"
        assert hasattr(config, "cache"), "CliConfig should have cache config"
        assert hasattr(config, "output"), "CliConfig should have output config"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestPydanticModelSerialization:
    """Test Pydantic model serialization for config files."""

    @pytest.mark.test_id("5.1-UNIT-014")
    def test_config_can_be_serialized_to_dict(self):
        """
        RED: Verify config models can be serialized to dict.

        Given: A CliConfig instance
        When: We call model_dump()
        Then: It should return a valid dictionary

        Expected RED failure: Model doesn't support serialization
        """
        # Given
        try:
            from data_extract.cli.models import CliConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        config = CliConfig()

        # When
        result = config.model_dump()

        # Then
        assert isinstance(result, dict), "model_dump() should return dict"
        assert "semantic" in result, "Serialized config should have semantic key"

    @pytest.mark.test_id("5.1-UNIT-015")
    def test_config_can_be_serialized_to_json(self):
        """
        RED: Verify config models can be serialized to JSON.

        Given: A CliConfig instance
        When: We call model_dump_json()
        Then: It should return valid JSON string

        Expected RED failure: Model doesn't support JSON serialization
        """
        # Given
        try:
            import json

            from data_extract.cli.models import CliConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        config = CliConfig()

        # When
        result = config.model_dump_json()

        # Then
        assert isinstance(result, str), "model_dump_json() should return string"
        # Verify it's valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, dict), "JSON should parse to dict"

    @pytest.mark.test_id("5.1-UNIT-016")
    def test_config_can_be_loaded_from_dict(self):
        """
        RED: Verify config models can be loaded from dict.

        Given: A valid config dictionary
        When: We create CliConfig from it
        Then: It should validate and create the model

        Expected RED failure: Model validation fails
        """
        # Given
        try:
            from data_extract.cli.models import CliConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        config_dict = {
            "semantic": {
                "tfidf": {
                    "max_features": 5000,
                    "min_df": 2,
                },
            },
            "cache": {
                "enabled": True,
                "max_size_mb": 512,
            },
        }

        # When
        config = CliConfig.model_validate(config_dict)

        # Then
        assert config.semantic.tfidf.max_features == 5000
        assert config.cache.enabled is True


@pytest.mark.unit
@pytest.mark.story_5_1
class TestPydanticValidationCorpus:
    """Test Pydantic validation using the validation corpus fixture."""

    @pytest.mark.parametrize(
        "field,invalid_value,expected_error_contains",
        [
            ("max_features", -100, "greater"),
            ("max_features", "not_a_number", "int"),
            ("max_df", 1.5, "less than or equal to 1"),
            ("min_df", -1, "greater"),
        ],
    )
    @pytest.mark.test_id("5.1-UNIT-017")
    def test_tfidf_validation_errors(
        self,
        field: str,
        invalid_value: Any,
        expected_error_contains: str,
    ):
        """
        RED: Parameterized test for TfidfConfig validation.

        Given: An invalid value for a TfidfConfig field
        When: We create TfidfConfig with that value
        Then: ValidationError should be raised with descriptive message

        Expected RED failure: Model doesn't validate properly
        """
        # Given
        try:
            from pydantic import ValidationError

            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            TfidfConfig(**{field: invalid_value})

        error_str = str(exc_info.value).lower()
        assert expected_error_contains.lower() in error_str, (
            f"Expected '{expected_error_contains}' in error for {field}={invalid_value}, "
            f"got: {exc_info.value}"
        )
