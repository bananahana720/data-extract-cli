"""TDD RED Phase Tests: CommandResult Serialization (AC-5.1-9).

These tests verify:
- Serialization to dictionary (model_dump)
- Serialization to JSON (model_dump_json)
- Deserialization from dictionary (model_validate)

Domain: Serialization and deserialization
"""

import json

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
class TestCommandResultSerialization:
    """Test CommandResult serialization for logging and pipeline composition."""

    @pytest.mark.test_id("5.1-UNIT-001")
    def test_command_result_to_dict(self):
        """
        RED: Verify CommandResult can be serialized to dictionary.

        Given: A CommandResult instance
        When: We call model_dump()
        Then: It should return a valid dictionary

        Expected RED failure: Serialization not working
        """
        # Given
        try:
            from data_extract.cli.models import CommandResult
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        result = CommandResult(
            success=True,
            exit_code=0,
            output="Test output",
            metadata={"key": "value"},
        )

        # When
        result_dict = result.model_dump()

        # Then
        assert isinstance(result_dict, dict)
        assert result_dict["success"] is True
        assert result_dict["exit_code"] == 0
        assert result_dict["output"] == "Test output"
        assert result_dict["metadata"] == {"key": "value"}

    @pytest.mark.test_id("5.1-UNIT-002")
    def test_command_result_to_json(self):
        """
        RED: Verify CommandResult can be serialized to JSON string.

        Given: A CommandResult instance
        When: We call model_dump_json()
        Then: It should return valid JSON

        Expected RED failure: JSON serialization fails
        """
        # Given
        try:
            from data_extract.cli.models import CommandResult
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        result = CommandResult(
            success=True,
            exit_code=0,
            output="Done",
        )

        # When
        json_str = result.model_dump_json()

        # Then
        assert isinstance(json_str, str)
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["success"] is True

    @pytest.mark.test_id("5.1-UNIT-003")
    def test_command_result_from_dict(self):
        """
        RED: Verify CommandResult can be created from dictionary.

        Given: A dictionary representing command result
        When: We use model_validate
        Then: It should create valid CommandResult

        Expected RED failure: model_validate fails
        """
        # Given
        try:
            from data_extract.cli.models import CommandResult
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        data = {
            "success": False,
            "exit_code": 1,
            "output": "",
            "errors": ["Test error"],
        }

        # When
        result = CommandResult.model_validate(data)

        # Then
        assert result.success is False
        assert result.exit_code == 1
        assert "Test error" in result.errors
