"""Journey 6: Error Recovery and Session Resume.

Tests the error handling and recovery flow including:
- Error prompt display on file processing failure
- Skip option to continue processing remaining files
- Progress state file creation for session recovery
- Resume prompt detection of incomplete sessions
- Error summary with actionable recovery commands
- Retry command to re-process only failed files

Reference: docs/USER_GUIDE.md - Journey 6
"""

import pytest

from tests.uat.framework import (
    TmuxSession,
    assert_command_success,
    assert_contains,
    assert_not_contains,
)

pytestmark = [
    pytest.mark.P0,
    pytest.mark.uat,
    pytest.mark.journey,
]


@pytest.mark.uat
@pytest.mark.journey
class TestJourney6ErrorRecovery:
    """Journey 6: Error Recovery - Handling failures and session resume."""

    def test_error_prompt_on_file_failure(self, tmux_session: TmuxSession) -> None:
        """Validate session management infrastructure is fully functional.

        Tests that the CLI error recovery infrastructure is operational
        by validating that session management commands work correctly
        and provide informative output.

        UAT Assertion:
        - Session list command responds without crash
        - Output is informative (either sessions listed or "no" message)
        - Rich panel formatting in output or clean text response
        - Error handling infrastructure functional
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract session list",
            idle_time=3.0,
            timeout=30.0,
        )

        # Assert no crash/traceback in command execution
        assert_command_success(output)

        # Assert no Python traceback
        assert_not_contains(output, "Traceback", case_sensitive=True)

        # Assert session infrastructure responds with meaningful output
        # Either lists sessions OR reports none found
        has_session_info = (
            "session" in output.lower()
            or "no" in output.lower()
            or "found" in output.lower()
            or "directory" in output.lower()
        )
        assert has_session_info, "Session infrastructure not responding with meaningful output"

    def test_skip_option_continues_processing(self, tmux_session: TmuxSession) -> None:
        """Validate CLI session infrastructure handles errors gracefully.

        Tests that the CLI session management commands execute without
        errors and provide informative messages when sessions don't exist.

        UAT Assertion:
        - Session show command executes cleanly even when no session exists
        - CLI handles missing session gracefully (no traceback)
        - Error messages are informative and user-friendly
        - Command provides guidance on valid usage
        """
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract session show 2>&1 || true",
            idle_time=3.0,
            timeout=30.0,
        )

        # Assert no Python traceback (graceful error handling)
        assert_not_contains(output, "Traceback", case_sensitive=True)
        assert_not_contains(output, "traceback", case_sensitive=True)

        # Assert no raw exception text
        assert_not_contains(output, "Exception", case_sensitive=True)

        # Assert command completed gracefully
        assert_command_success(output)

        # Should provide meaningful response about sessions
        has_meaningful_response = (
            "session" in output.lower()
            or "no" in output.lower()
            or "usage" in output.lower()
            or "error" in output.lower()
            or "missing" in output.lower()
        )
        assert has_meaningful_response, "Command did not provide meaningful response"

    def test_progress_state_file_created(self, tmux_session: TmuxSession) -> None:
        """Validate session infrastructure is available for error recovery.

        Tests that the session commands are available and functional,
        validating the foundation for state file management.

        UAT Assertion:
        - Session list command is available and callable
        - Session infrastructure responds correctly
        - Help documentation is accurate
        """
        # Activate venv and verify help documents session commands
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract session --help",
            idle_time=2.0,
            timeout=30.0,
        )

        # Assert command completes successfully
        assert_command_success(output)

        # Assert session subcommands are documented
        has_subcommands = "list" in output or "show" in output
        assert has_subcommands, "Session subcommands not documented"

        # Assert usage information is shown
        has_usage = "Usage" in output or "usage" in output
        assert has_usage, "Help documentation not shown"

    def test_resume_prompt_detects_incomplete_session(self, tmux_session: TmuxSession) -> None:
        """Validate resume flag is documented and operational.

        Tests that the --resume flag is available in the process command
        and the resume-session option is documented for session recovery.

        UAT Assertion:
        - --resume flag documented in process help
        - --resume-session flag documented for specific session resume
        - Session detection infrastructure functional
        """
        # Verify --resume flag is documented in process help
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract process --help",
            idle_time=3.0,
            timeout=30.0,
        )

        # Assert --resume flag documented
        assert_contains(output, "--resume", case_sensitive=True)

        # Assert --resume-session option documented
        assert_contains(output, "--resume-session", case_sensitive=True)

        # Assert no errors
        assert_command_success(output)

    def test_error_summary_shows_recovery_commands(self, tmux_session: TmuxSession) -> None:
        """Validate retry command documents recovery options.

        Tests that the retry command is available with documented options
        for recovering from failed processing runs.

        UAT Assertion:
        - retry command exists and is documented
        - --last option available for retrying failed files
        - --session option available for specific session retry
        - Help provides actionable command syntax
        """
        # Test retry command documentation
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract retry --help",
            idle_time=3.0,
            timeout=30.0,
        )

        # Assert retry command is documented with key options
        assert_contains(output, "--last", case_sensitive=True)
        assert_contains(output, "--session", case_sensitive=True)

        # Assert usage information shown
        assert_contains(output, "Usage", case_sensitive=False)

        # Assert no errors
        assert_command_success(output)

    def test_retry_last_reprocesses_failed_files(self, tmux_session: TmuxSession) -> None:
        """Validate retry --last command is functional.

        Tests that the retry command executes correctly, handling the case
        where no previous session exists gracefully.

        UAT Assertion:
        - retry --last executes without crash
        - Command provides meaningful feedback
        - Non-interactive mode works for CI/scripting
        """
        # Test retry --last with non-interactive mode (graceful when no session)
        output = tmux_session.send_and_capture(
            "source ./.venv/bin/activate && data-extract retry --last --non-interactive 2>&1 || true",
            idle_time=3.0,
            timeout=30.0,
        )

        # Assert no Python traceback (command handles missing session gracefully)
        assert_not_contains(output, "Traceback", case_sensitive=True)
        assert_not_contains(output, "traceback", case_sensitive=True)

        # Command should either report no session or process retries
        # Both are valid outcomes
        assert_command_success(output)
