"""TDD RED Phase Tests: CommandResult Error State Handling (AC-5.1-9).

These tests verify:
- Error state handling
- Multiple error messages
- Exit code conventions

Domain: Error state handling and exit codes
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
class TestCommandResultErrorState:
    """Test CommandResult error state handling."""

    @pytest.mark.test_id("5.1-UNIT-001")
    def test_command_result_error_state_creation(self):
        """
        RED: Verify CommandResult can represent failed command execution.

        Given: A failed command execution
        When: We create CommandResult with success=False
        Then: It should have correct error attributes

        Expected RED failure: Model doesn't handle error state
        """
        # Given
        try:
            from data_extract.cli.models import CommandResult
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        result = CommandResult(
            success=False,
            exit_code=1,
            output="",
            errors=["File not found: input.pdf"],
        )

        # Then
        assert result.success is False, "success should be False"
        assert result.exit_code == 1, "exit_code should be non-zero for failure"
        assert len(result.errors) > 0, "errors should contain error messages"

    @pytest.mark.test_id("5.1-UNIT-002")
    def test_error_result_multiple_errors(self):
        """
        RED: Verify CommandResult can hold multiple error messages.

        Given: A command that failed with multiple errors
        When: We create CommandResult with multiple errors
        Then: All errors should be preserved

        Expected RED failure: errors attribute doesn't accept list
        """
        # Given
        try:
            from data_extract.cli.models import CommandResult
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        errors = [
            "File not found: input.pdf",
            "Permission denied: output/",
            "Invalid configuration: chunk_size must be positive",
        ]
        result = CommandResult(
            success=False,
            exit_code=1,
            output="",
            errors=errors,
        )

        # Then
        assert len(result.errors) == 3, f"Should have 3 errors, got {len(result.errors)}"
        assert "Permission denied" in result.errors[1]

    @pytest.mark.test_id("5.1-UNIT-003")
    def test_error_result_exit_codes(self):
        """
        RED: Verify different error types use appropriate exit codes.

        Given: Various error scenarios
        When: We check exit codes
        Then: Exit codes should follow conventions (1 for general, 2 for usage, etc.)

        Expected RED failure: Model doesn't validate exit codes
        """
        # Given
        try:
            from data_extract.cli.models import CommandResult
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When - general error
        general_error = CommandResult(
            success=False,
            exit_code=1,
            output="",
            errors=["General error"],
        )

        # When - usage error
        usage_error = CommandResult(
            success=False,
            exit_code=2,
            output="",
            errors=["Invalid argument"],
        )

        # Then
        assert general_error.exit_code == 1
        assert usage_error.exit_code == 2
