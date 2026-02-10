"""Journey runner framework for UAT testing.

Provides high-level orchestration of multi-step CLI user journeys with
assertions, timeouts, and debugging support.

Story 5-0: UAT Testing Framework
AC-5.0-3: Journey runner framework with step execution and debugging
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from tests.uat.framework.tmux_wrapper import TmuxSession


@dataclass
class JourneyStep:
    """A single step in a user journey test.

    Represents one user interaction with the CLI, including the command
    to execute, assertions to validate output, and timing constraints.

    Attributes:
        name: Human-readable name for the step (e.g., "Launch help command")
        command: CLI command to send to the session
        assertions: List of callable assertions that validate output
        timeout: Maximum time to wait for step completion (seconds)
        skip_reason: If set, this step will be skipped with the given reason

    Example:
        >>> def assert_help_shown(output: str) -> None:
        ...     assert "Usage:" in output
        >>> step = JourneyStep(
        ...     name="Show help",
        ...     command="data-extract --help",
        ...     assertions=[assert_help_shown],
        ...     timeout=10.0,
        ... )
    """

    name: str
    command: str
    assertions: list[Callable[[str], None]]
    timeout: float = 30.0
    skip_reason: str | None = None

    def __post_init__(self) -> None:
        """Validate step configuration."""
        if not self.name:
            raise ValueError("Step name cannot be empty")
        if not self.command and not self.skip_reason:
            raise ValueError("Step command cannot be empty unless skipped")
        if self.timeout <= 0:
            raise ValueError(f"Timeout must be positive, got {self.timeout}")


@dataclass
class StepResult:
    """Result of executing a journey step.

    Attributes:
        step_name: Name of the step that was executed
        success: Whether all assertions passed
        output: Captured output from the CLI
        duration: Time taken to execute the step (seconds)
        error: Exception message if step failed
        skipped: Whether the step was skipped
        skip_reason: Reason for skipping if applicable
    """

    step_name: str
    success: bool
    output: str
    duration: float
    error: str | None = None
    skipped: bool = False
    skip_reason: str | None = None


class JourneyRunner:
    """Orchestrates execution of multi-step CLI user journeys.

    Manages step-by-step execution of user journeys with tmux session
    control, assertion validation, timeout handling, and debugging support.

    Attributes:
        session: The TmuxSession used for CLI interaction
        steps: List of journey steps to execute
        screenshot_dir: Directory for saving debug screenshots (optional)

    Example:
        >>> session = TmuxSession()
        >>> session.launch("zsh")
        >>> steps = [
        ...     JourneyStep("Help", "data-extract --help", [assert_help]),
        ...     JourneyStep("Version", "data-extract --version", [assert_version]),
        ... ]
        >>> runner = JourneyRunner(session, steps)
        >>> results = runner.run_all()
        >>> assert all(r.success for r in results)
    """

    def __init__(
        self,
        session: TmuxSession,
        steps: list[JourneyStep],
        screenshot_dir: Path | None = None,
    ) -> None:
        """Initialize the journey runner.

        Args:
            session: Active TmuxSession for running commands
            steps: List of journey steps to execute
            screenshot_dir: Optional directory for saving debug screenshots

        Raises:
            ValueError: If session is not launched or steps list is empty
        """
        if not session._launched or not session.pane_id:
            raise ValueError("Session must be launched before creating JourneyRunner")
        if not steps:
            raise ValueError("Steps list cannot be empty")

        self.session = session
        self.steps = steps
        self.screenshot_dir = screenshot_dir
        self._step_counter = 0

        if screenshot_dir:
            screenshot_dir.mkdir(parents=True, exist_ok=True)

    def run_step(self, step: JourneyStep) -> StepResult:
        """Execute a single journey step.

        Sends the command, waits for idle state, captures output,
        and runs all assertions. Handles timeouts and errors gracefully.

        Args:
            step: The journey step to execute

        Returns:
            StepResult: Execution result including success status and output

        Example:
            >>> step = JourneyStep("Test", "echo hello", [lambda o: assert "hello" in o])
            >>> result = runner.run_step(step)
            >>> assert result.success
        """
        self._step_counter += 1
        start_time = time.time()

        # Handle skipped steps
        if step.skip_reason:
            return StepResult(
                step_name=step.name,
                success=True,
                output="",
                duration=0.0,
                skipped=True,
                skip_reason=step.skip_reason,
            )

        try:
            # Send command and wait for completion
            self.session.send(step.command)
            self.session.wait_idle(idle_time=2.0, timeout=step.timeout)
            output = self.session.capture()

            # Save screenshot if configured
            if self.screenshot_dir:
                self.capture_screenshot(
                    step_name=step.name,
                    step_number=self._step_counter,
                    output=output,
                )

            # Run all assertions
            for assertion in step.assertions:
                assertion(output)

            duration = time.time() - start_time
            return StepResult(
                step_name=step.name,
                success=True,
                output=output,
                duration=duration,
            )

        except AssertionError as e:
            duration = time.time() - start_time
            output_captured = self._safe_capture()

            # Save failure screenshot
            if self.screenshot_dir:
                self.capture_screenshot(
                    step_name=f"{step.name}_FAILED",
                    step_number=self._step_counter,
                    output=output_captured,
                )

            return StepResult(
                step_name=step.name,
                success=False,
                output=output_captured,
                duration=duration,
                error=f"Assertion failed: {str(e)}",
            )

        except Exception as e:
            duration = time.time() - start_time
            output_captured = self._safe_capture()

            # Save error screenshot
            if self.screenshot_dir:
                self.capture_screenshot(
                    step_name=f"{step.name}_ERROR",
                    step_number=self._step_counter,
                    output=output_captured,
                )

            return StepResult(
                step_name=step.name,
                success=False,
                output=output_captured,
                duration=duration,
                error=f"Step execution failed: {str(e)}",
            )

    def run_all(self) -> list[StepResult]:
        """Execute all journey steps sequentially.

        Runs each step in order, stopping at the first failure unless
        skip_on_failure is True. Returns results for all executed steps.

        Returns:
            List of StepResult objects, one per executed step

        Example:
            >>> results = runner.run_all()
            >>> success_count = sum(1 for r in results if r.success)
            >>> print(f"{success_count}/{len(results)} steps passed")
        """
        results: list[StepResult] = []

        for step in self.steps:
            result = self.run_step(step)
            results.append(result)

            # Stop on first failure (unless skipped)
            if not result.success and not result.skipped:
                break

        return results

    def capture_screenshot(
        self,
        step_name: str,
        step_number: int,
        output: str,
    ) -> Path:
        """Save terminal output to file for debugging.

        Creates a timestamped file containing the raw terminal output
        including ANSI escape codes for full reproduction.

        Args:
            step_name: Name of the step for filename
            step_number: Step number for ordering
            output: Terminal output to save

        Returns:
            Path to the saved screenshot file

        Example:
            >>> path = runner.capture_screenshot("Help command", 1, output)
            >>> assert path.exists()
            >>> assert "01_Help_command" in path.name
        """
        if not self.screenshot_dir:
            raise ValueError("screenshot_dir not configured")

        # Sanitize filename
        safe_name = step_name.replace(" ", "_").replace("/", "_")
        filename = f"{step_number:02d}_{safe_name}.txt"
        filepath = self.screenshot_dir / filename

        # Save with timestamp header
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        content = f"""=== Journey Step Screenshot ===
Step: {step_name}
Number: {step_number}
Timestamp: {timestamp}
{'=' * 50}

{output}
"""

        filepath.write_text(content, encoding="utf-8")
        return filepath

    def _safe_capture(self) -> str:
        """Safely capture output even if session is in error state.

        Returns:
            Captured output or error message if capture fails
        """
        try:
            return self.session.capture()
        except Exception as e:
            return f"[Failed to capture output: {str(e)}]"

    def get_summary(self, results: list[StepResult]) -> str:
        """Generate a human-readable summary of journey execution.

        Args:
            results: List of step results to summarize

        Returns:
            Formatted summary string with pass/fail counts and timing

        Example:
            >>> summary = runner.get_summary(results)
            >>> print(summary)
            Journey Summary:
            ✓ 5 passed, ✗ 1 failed, ⊘ 0 skipped
            Total time: 12.34s
        """
        passed = sum(1 for r in results if r.success and not r.skipped)
        failed = sum(1 for r in results if not r.success and not r.skipped)
        skipped = sum(1 for r in results if r.skipped)
        total_time = sum(r.duration for r in results)

        summary_lines = [
            "Journey Summary:",
            f"✓ {passed} passed, ✗ {failed} failed, ⊘ {skipped} skipped",
            f"Total time: {total_time:.2f}s",
        ]

        # Add failure details
        if failed > 0:
            summary_lines.append("\nFailures:")
            for result in results:
                if not result.success and not result.skipped:
                    summary_lines.append(f"  • {result.step_name}: {result.error}")

        return "\n".join(summary_lines)
