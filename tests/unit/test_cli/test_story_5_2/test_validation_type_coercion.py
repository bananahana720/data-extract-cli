"""TDD RED Phase Tests: Pydantic Type Coercion (AC-5.2-4).

These tests verify:
- String to int/float coercion
- Int to float coercion
- String to bool coercion (various formats)
- List to tuple coercion for ngram_range

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
class TestPydanticTypeCoercion:
    """AC-5.2-4: Test Pydantic type coercion for config values."""

    def test_string_to_int_coercion(self):
        """
        RED: Verify string numbers are coerced to int.

        Given: A TfidfConfig model
        When: We create it with max_features = "5000" (string)
        Then: Value should be coerced to int 5000

        Expected RED failure: Model rejects valid string number
        """
        # Given
        try:
            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        config = TfidfConfig(max_features="5000")

        # Then
        assert config.max_features == 5000
        assert isinstance(
            config.max_features, int
        ), f"max_features should be int, got {type(config.max_features)}"

    def test_string_to_float_coercion(self):
        """
        RED: Verify string numbers are coerced to float.

        Given: A TfidfConfig model
        When: We create it with max_df = "0.95" (string)
        Then: Value should be coerced to float 0.95

        Expected RED failure: Model rejects valid string number
        """
        # Given
        try:
            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        config = TfidfConfig(max_df="0.95")

        # Then
        assert config.max_df == 0.95
        assert isinstance(
            config.max_df, float
        ), f"max_df should be float, got {type(config.max_df)}"

    def test_int_to_float_coercion(self):
        """
        RED: Verify int is coerced to float where float expected.

        Given: A TfidfConfig model
        When: We create it with max_df = 1 (int)
        Then: Value should be coerced to float 1.0

        Expected RED failure: Model rejects int for float field
        """
        # Given
        try:
            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        config = TfidfConfig(max_df=1)

        # Then
        assert config.max_df == 1.0
        assert isinstance(
            config.max_df, float
        ), f"max_df should be float, got {type(config.max_df)}"

    @pytest.mark.parametrize(
        "input_value,expected",
        [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
        ],
    )
    def test_string_to_bool_coercion(self, input_value: str, expected: bool):
        """
        RED: Verify string booleans are coerced to bool.

        Given: A CacheConfig model
        When: We create it with enabled = various string booleans
        Then: Value should be coerced to correct bool

        Expected RED failure: String boolean not coerced
        """
        # Given
        try:
            from data_extract.cli.models import CacheConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        config = CacheConfig(enabled=input_value)

        # Then
        assert (
            config.enabled is expected
        ), f"'{input_value}' should coerce to {expected}, got {config.enabled}"

    def test_list_to_tuple_coercion_for_ngram_range(self):
        """
        RED: Verify list is coerced to tuple for ngram_range.

        Given: A TfidfConfig model
        When: We create it with ngram_range = [1, 2] (list from YAML)
        Then: Value should be coerced to tuple (1, 2)

        Expected RED failure: List not accepted or not converted
        """
        # Given
        try:
            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        config = TfidfConfig(ngram_range=[1, 2])

        # Then
        assert config.ngram_range == (
            1,
            2,
        ), f"ngram_range should be (1, 2), got {config.ngram_range}"
        assert isinstance(
            config.ngram_range, tuple
        ), f"ngram_range should be tuple, got {type(config.ngram_range)}"
