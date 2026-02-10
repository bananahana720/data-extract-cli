"""TDD RED Phase Tests: Pydantic Serialization and Validation Corpus (AC-5.2-4).

These tests verify:
- Config serialization to dict and JSON
- Config deserialization from dict
- Parameterized validation using test corpus

All tests are designed to FAIL initially (TDD RED phase).
"""

from typing import Any

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
class TestPydanticSerialization:
    """AC-5.2-4: Test Pydantic model serialization."""

    def test_config_model_dump(self):
        """
        RED: Verify config can be dumped to dict.

        Given: A ConfigModel instance
        When: model_dump() is called
        Then: Returns valid dictionary

        Expected RED failure: Serialization fails
        """
        # Given
        try:
            from data_extract.cli.models import ConfigModel
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        config = ConfigModel()

        # When
        result = config.model_dump()

        # Then
        assert isinstance(result, dict)
        assert "semantic" in result or "cache" in result

    def test_config_model_dump_json(self):
        """
        RED: Verify config can be dumped to JSON.

        Given: A ConfigModel instance
        When: model_dump_json() is called
        Then: Returns valid JSON string

        Expected RED failure: JSON serialization fails
        """
        # Given
        import json

        try:
            from data_extract.cli.models import ConfigModel
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        config = ConfigModel()

        # When
        result = config.model_dump_json()

        # Then
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_config_model_validate(self):
        """
        RED: Verify config can be created from dict.

        Given: A valid config dictionary
        When: ConfigModel.model_validate() is called
        Then: Returns valid ConfigModel instance

        Expected RED failure: Validation from dict fails
        """
        # Given
        try:
            from data_extract.cli.models import ConfigModel
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        config_dict = {
            "semantic": {
                "tfidf": {"max_features": 3000},
            },
            "cache": {
                "enabled": True,
            },
        }

        # When
        config = ConfigModel.model_validate(config_dict)

        # Then
        assert config.semantic.tfidf.max_features == 3000
        assert config.cache.enabled is True


@pytest.mark.unit
@pytest.mark.story_5_2
class TestPydanticValidationCorpus:
    """AC-5.2-4: Test validation using corpus fixture."""

    @pytest.mark.parametrize(
        "field,invalid_value,error_contains",
        [
            ("max_features", -100, "greater"),
            ("max_features", "not_a_number", "int"),
            ("max_df", 1.5, "less than or equal"),
            ("min_df", -1, "greater"),
        ],
    )
    def test_tfidf_validation_with_corpus(
        self,
        field: str,
        invalid_value: Any,
        error_contains: str,
    ):
        """
        RED: Parameterized validation test for TfidfConfig.

        Given: An invalid value from validation corpus
        When: TfidfConfig is created with that value
        Then: ValidationError with descriptive message

        Expected RED failure: Validation not working correctly
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
        assert error_contains.lower() in error_str, (
            f"Expected '{error_contains}' in error for {field}={invalid_value}, "
            f"got: {exc_info.value}"
        )
