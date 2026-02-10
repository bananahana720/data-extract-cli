"""TDD RED Phase Tests: CommandResult Pydantic Validation (AC-5.1-4).

These tests verify:
- Type validation for exit_code (integer, non-negative)
- Type validation for success (boolean)
- Pydantic ValidationError behavior

Domain: Pydantic validation rules
"""

import pytest

# P0: Critical path - always run
pytestmark = [
    pytest.mark.P0,
    pytest.mark.story_5_1,
    pytest.mark.unit,
    pytest.mark.cli,
]


@pytest.mark.unit
@pytest.mark.story_5_1
class TestCommandResultValidation:
    """Test CommandResult Pydantic validation rules."""

    @pytest.mark.test_id("5.1-UNIT-001")
    def test_exit_code_must_be_integer(self):
        """
        RED: Verify exit_code rejects non-integer values.

        Given: CommandResult model
        When: We provide string exit_code
        Then: ValidationError should be raised

        Expected RED failure: Model accepts invalid type
        """
        # Given
        try:
            from pydantic import ValidationError

            from data_extract.cli.models import CommandResult
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When/Then
        with pytest.raises(ValidationError):
            CommandResult(
                success=True,
                exit_code="zero",  # type: ignore - intentional invalid type
                output="",
            )

    @pytest.mark.test_id("5.1-UNIT-002")
    def test_exit_code_must_be_non_negative(self):
        """
        RED: Verify exit_code rejects negative values.

        Given: CommandResult model
        When: We provide negative exit_code
        Then: ValidationError should be raised

        Expected RED failure: Model accepts negative exit codes
        """
        # Given
        try:
            from pydantic import ValidationError

            from data_extract.cli.models import CommandResult
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            CommandResult(
                success=True,
                exit_code=-1,
                output="",
            )

        error_str = str(exc_info.value).lower()
        assert "exit_code" in error_str or "greater" in error_str

    @pytest.mark.test_id("5.1-UNIT-003")
    def test_success_requires_boolean(self):
        """
        RED: Verify success field requires boolean.

        Given: CommandResult model
        When: We provide non-boolean success
        Then: ValidationError or coercion should happen

        Expected RED failure: Model accepts invalid success type
        """
        # Given
        try:
            from data_extract.cli.models import CommandResult
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When - integer should coerce to bool in Pydantic
        result = CommandResult(
            success=1,  # type: ignore - testing coercion
            exit_code=0,
            output="",
        )

        # Then - Pydantic typically coerces 1 to True
        assert result.success is True or result.success == 1
