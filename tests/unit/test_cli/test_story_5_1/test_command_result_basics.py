"""TDD RED Phase Tests: CommandResult Model Basics (AC-5.1-9).

These tests verify:
- CommandResult model exists and is a Pydantic BaseModel
- Success state handling and attributes

Domain: CommandResult model foundation and success states
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
class TestCommandResultModelExists:
    """Verify CommandResult model exists in cli/models.py."""

    @pytest.mark.test_id("5.1-UNIT-001")
    def test_command_result_can_be_imported(self):
        """
        RED: Verify CommandResult class can be imported from cli/models.

        Given: The CLI models module
        When: We import CommandResult
        Then: It should be a valid class

        Expected RED failure: ImportError - models module doesn't exist
        """
        # Given/When
        try:
            from data_extract.cli.models import CommandResult
        except ImportError as e:
            pytest.fail(
                f"Cannot import CommandResult from data_extract.cli.models: {e}\n"
                "Expected: src/data_extract/cli/models.py with CommandResult class"
            )

        # Then
        assert CommandResult is not None
        assert callable(CommandResult), "CommandResult should be instantiable"

    @pytest.mark.test_id("5.1-UNIT-002")
    def test_command_result_is_pydantic_model(self):
        """
        RED: Verify CommandResult is a Pydantic BaseModel subclass.

        Given: The CommandResult class
        When: We check its base classes
        Then: It should inherit from pydantic.BaseModel

        Expected RED failure: Not a Pydantic model
        """
        # Given
        try:
            from pydantic import BaseModel

            from data_extract.cli.models import CommandResult
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # Then
        assert issubclass(CommandResult, BaseModel), (
            f"CommandResult should be a Pydantic BaseModel subclass, "
            f"got bases: {CommandResult.__bases__}"
        )


@pytest.mark.unit
@pytest.mark.story_5_1
class TestCommandResultSuccessState:
    """Test CommandResult success state handling."""

    @pytest.mark.test_id("5.1-UNIT-003")
    def test_command_result_success_state_creation(self):
        """
        RED: Verify CommandResult can represent successful command execution.

        Given: A successful command execution
        When: We create CommandResult with success=True
        Then: It should have correct success attributes

        Expected RED failure: Model doesn't exist or missing attributes
        """
        # Given
        try:
            from data_extract.cli.models import CommandResult
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        result = CommandResult(
            success=True,
            exit_code=0,
            output="Operation completed successfully",
        )

        # Then
        assert result.success is True, "success should be True"
        assert result.exit_code == 0, "exit_code should be 0 for success"
        assert "successfully" in result.output, "output should contain success message"

    @pytest.mark.test_id("5.1-UNIT-004")
    def test_success_result_has_no_errors(self):
        """
        RED: Verify successful CommandResult has empty errors list.

        Given: A successful command
        When: We check the errors attribute
        Then: It should be an empty list

        Expected RED failure: errors attribute missing or not empty
        """
        # Given
        try:
            from data_extract.cli.models import CommandResult
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        result = CommandResult(
            success=True,
            exit_code=0,
            output="Done",
        )

        # Then
        assert hasattr(result, "errors"), "CommandResult should have errors attribute"
        assert (
            result.errors == [] or result.errors is None
        ), f"Successful result should have empty/None errors, got: {result.errors}"

    @pytest.mark.test_id("5.1-UNIT-005")
    def test_success_result_accepts_metadata(self):
        """
        RED: Verify successful CommandResult can include metadata.

        Given: A successful command with execution metadata
        When: We create CommandResult with metadata dict
        Then: Metadata should be accessible

        Expected RED failure: metadata attribute missing
        """
        # Given
        try:
            from data_extract.cli.models import CommandResult
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        result = CommandResult(
            success=True,
            exit_code=0,
            output="Done",
            metadata={
                "duration_ms": 150,
                "cached": False,
                "chunks_processed": 42,
            },
        )

        # Then
        assert hasattr(result, "metadata"), "CommandResult should have metadata attribute"
        assert isinstance(result.metadata, dict), "metadata should be a dict"
        assert result.metadata.get("duration_ms") == 150
        assert result.metadata.get("cached") is False
