"""TDD RED Phase Tests: CommandResult Metadata Tracking (AC-5.1-9).

These tests verify:
- Data field for carrying output data
- Command information tracking (command, args)
- Timestamp tracking (execution time, duration)

Domain: Metadata tracking (data, command info, timestamps)
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
class TestCommandResultDataField:
    """Test CommandResult data field for carrying output data."""

    @pytest.mark.test_id("5.1-UNIT-001")
    def test_command_result_has_data_field(self):
        """
        RED: Verify CommandResult has optional data field for output data.

        Given: A successful command that produces data
        When: We create CommandResult with data field
        Then: Data should be accessible

        Expected RED failure: data attribute missing
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
            output="Analysis complete",
            data={
                "chunks_analyzed": 42,
                "duplicates_found": 3,
                "topics": ["risk", "compliance", "audit"],
            },
        )

        # Then
        assert hasattr(result, "data"), "CommandResult should have data attribute"
        assert result.data is not None
        assert result.data.get("chunks_analyzed") == 42

    @pytest.mark.test_id("5.1-UNIT-002")
    def test_command_result_data_optional(self):
        """
        RED: Verify data field is optional.

        Given: A command without output data
        When: We create CommandResult without data
        Then: data should be None or empty dict

        Expected RED failure: data field is required
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
        assert (
            result.data is None or result.data == {}
        ), f"data should be None or empty dict when not provided, got: {result.data}"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestCommandResultCommandInfo:
    """Test CommandResult command information tracking."""

    @pytest.mark.test_id("5.1-UNIT-003")
    def test_command_result_has_command_field(self):
        """
        RED: Verify CommandResult tracks which command was executed.

        Given: A command execution
        When: We create CommandResult with command info
        Then: command field should identify the executed command

        Expected RED failure: command field missing
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
            command="semantic analyze",
        )

        # Then
        assert hasattr(result, "command"), "CommandResult should have command field"
        assert result.command == "semantic analyze"

    @pytest.mark.test_id("5.1-UNIT-004")
    def test_command_result_has_args_field(self):
        """
        RED: Verify CommandResult tracks command arguments.

        Given: A command with arguments
        When: We create CommandResult with args info
        Then: args should be preserved

        Expected RED failure: args field missing
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
            command="semantic analyze",
            args=["./input/", "--format", "json"],
        )

        # Then
        assert hasattr(result, "args"), "CommandResult should have args field"
        assert "./input/" in result.args


@pytest.mark.unit
@pytest.mark.story_5_1
class TestCommandResultTimestamps:
    """Test CommandResult timestamp tracking."""

    @pytest.mark.test_id("5.1-UNIT-005")
    def test_command_result_has_timestamp(self):
        """
        RED: Verify CommandResult has timestamp field.

        Given: A command execution
        When: We create CommandResult
        Then: It should have execution timestamp

        Expected RED failure: timestamp field missing
        """
        # Given
        try:
            from datetime import datetime

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
        assert hasattr(result, "timestamp"), "CommandResult should have timestamp field"
        # Should be auto-generated if not provided
        if result.timestamp is not None:
            assert isinstance(result.timestamp, (datetime, str))

    @pytest.mark.test_id("5.1-UNIT-006")
    def test_command_result_duration_in_metadata(self):
        """
        RED: Verify execution duration is tracked in metadata.

        Given: A command execution with timing
        When: We provide duration in metadata
        Then: It should be accessible

        Expected RED failure: metadata doesn't accept duration
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
                "duration_ms": 1234,
                "start_time": "2025-11-26T10:00:00Z",
                "end_time": "2025-11-26T10:00:01.234Z",
            },
        )

        # Then
        assert result.metadata["duration_ms"] == 1234
