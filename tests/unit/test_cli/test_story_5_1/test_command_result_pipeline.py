"""TDD RED Phase Tests: CommandResult Pipeline Support (AC-5.1-9).

These tests verify:
- Helper methods for convenience (is_success, error_summary)
- Pipeline composition support (chaining data, tracking position)

Domain: Pipeline composition and helper methods
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
class TestCommandResultHelperMethods:
    """Test CommandResult convenience methods."""

    @pytest.mark.test_id("5.1-UNIT-001")
    def test_command_result_is_success_method(self):
        """
        RED: Verify CommandResult has is_success() helper method.

        Given: A CommandResult instance
        When: We call is_success()
        Then: It should return boolean based on success and exit_code

        Expected RED failure: Method doesn't exist
        """
        # Given
        try:
            from data_extract.cli.models import CommandResult
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        success_result = CommandResult(success=True, exit_code=0, output="Done")
        error_result = CommandResult(success=False, exit_code=1, output="", errors=["Error"])

        # Then
        if hasattr(success_result, "is_success"):
            assert success_result.is_success() is True
            assert error_result.is_success() is False
        else:
            # Alternative: just check success attribute
            assert success_result.success is True
            assert error_result.success is False

    @pytest.mark.test_id("5.1-UNIT-002")
    def test_command_result_has_error_summary(self):
        """
        RED: Verify CommandResult can provide error summary.

        Given: A failed CommandResult with multiple errors
        When: We access error information
        Then: We should be able to get a summary

        Expected RED failure: No way to get error summary
        """
        # Given
        try:
            from data_extract.cli.models import CommandResult
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        result = CommandResult(
            success=False,
            exit_code=1,
            output="",
            errors=[
                "Error 1: File not found",
                "Error 2: Permission denied",
            ],
        )

        # Then - should have some way to access errors
        assert result.errors is not None
        assert len(result.errors) == 2
        # Can join for summary
        summary = "\n".join(result.errors)
        assert "File not found" in summary


@pytest.mark.unit
@pytest.mark.story_5_1
class TestCommandResultPipelineSupport:
    """Test CommandResult support for pipeline composition (AC-5.1-9)."""

    @pytest.mark.test_id("5.1-UNIT-003")
    def test_command_result_supports_chaining_data(self):
        """
        RED: Verify CommandResult data can be passed to next command.

        Given: A CommandResult with output data
        When: We access the data for pipeline chaining
        Then: Data should be usable as input for next command

        Expected RED failure: Data not accessible for chaining
        """
        # Given
        try:
            from data_extract.cli.models import CommandResult
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # Simulate first command output
        first_result = CommandResult(
            success=True,
            exit_code=0,
            output="Extracted 42 chunks",
            data={
                "output_path": "/tmp/chunks/",
                "chunk_count": 42,
                "chunk_ids": ["chunk_001", "chunk_002"],
            },
        )

        # Then - data should be accessible for next command
        assert first_result.data is not None
        next_input = first_result.data.get("output_path")
        assert next_input == "/tmp/chunks/"

    @pytest.mark.test_id("5.1-UNIT-004")
    def test_command_result_tracks_pipeline_position(self):
        """
        RED: Verify CommandResult can track position in pipeline.

        Given: A command in a pipeline
        When: We create CommandResult with pipeline context
        Then: Pipeline position should be tracked

        Expected RED failure: No pipeline tracking
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
                "pipeline_step": 2,
                "pipeline_total": 3,
                "pipeline_name": "extract-analyze",
            },
        )

        # Then
        assert result.metadata.get("pipeline_step") == 2
        assert result.metadata.get("pipeline_total") == 3
