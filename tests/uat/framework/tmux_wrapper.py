"""TmuxSession wrapper for tmux-cli integration.

Provides a Python interface for controlling CLI applications via tmux-cli.
Implements context manager for automatic cleanup.

Story 5-0: UAT Testing Framework
AC-5.0-2: TmuxSession wrapper implements launch, send, capture, wait_idle, kill
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from typing import Self


class TmuxError(Exception):
    """Exception raised for tmux-cli operation failures."""


@dataclass
class TmuxSession:
    """Wrapper for tmux-cli operations.

    Provides a high-level interface for interacting with CLI applications
    running in tmux panes via the tmux-cli tool.

    Attributes:
        pane_id: The tmux pane identifier (set after launch)
        shell: The shell to launch (default: zsh)
        default_idle_time: Default idle time for wait_idle (seconds)
        default_timeout: Default timeout for operations (seconds)

    Example:
        >>> with TmuxSession() as session:
        ...     session.send("data-extract --help")
        ...     session.wait_idle()
        ...     output = session.capture()
        ...     assert "process" in output
    """

    pane_id: str | None = None
    shell: str = "zsh"
    default_idle_time: float = 2.0
    default_timeout: float = 60.0
    _launched: bool = field(default=False, repr=False)

    def __enter__(self) -> Self:
        """Enter context manager and launch shell."""
        self.launch(self.shell)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context manager and cleanup pane."""
        if self._launched:
            try:
                self.kill()
            except TmuxError:
                pass  # Ignore cleanup errors

    def launch(self, command: str) -> str:
        """Launch a command in a new tmux pane.

        Args:
            command: The shell command to launch (e.g., "zsh", "python")

        Returns:
            str: The pane identifier (e.g., "myapp:1.2")

        Raises:
            TmuxError: If launch fails
        """
        result = self._run_tmux_cli(["launch", command])
        # Extract pane ID from last non-empty line (tmux-cli may include notes/warnings)
        lines = result.strip().split("\n")
        self.pane_id = lines[-1].strip() if lines else result.strip()
        self._launched = True
        # Small delay to ensure pane is ready
        time.sleep(0.3)
        return self.pane_id

    def send(self, text: str, enter: bool = True, delay_enter: float | None = None) -> None:
        """Send text input to the tmux pane.

        Args:
            text: The text to send to the pane
            enter: Whether to press Enter after sending text (default: True)
            delay_enter: Custom delay between text and Enter key (seconds)

        Raises:
            TmuxError: If send fails or pane not launched
        """
        self._ensure_pane()

        args = ["send", text, f"--pane={self.pane_id}"]
        if not enter:
            args.append("--enter=False")
        elif delay_enter is not None:
            args.append(f"--delay-enter={delay_enter}")

        self._run_tmux_cli(args)

    def capture(self) -> str:
        """Capture the current output from the tmux pane.

        Uses tmux's native capture-pane with scrollback history to ensure
        we get the full output including lines scrolled out of visible area.

        Returns:
            str: The captured pane output (including ANSI escape codes)

        Raises:
            TmuxError: If capture fails or pane not launched
        """
        self._ensure_pane()

        # Use native tmux capture-pane with scrollback history to get full output
        # -S -500: Start from 500 lines back in history (covers most CLI outputs)
        try:
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", f"{self.pane_id}.0", "-p", "-S", "-500"],
                capture_output=True,
                text=True,
                timeout=self.default_timeout + 10,
                check=False,
            )
            if result.returncode != 0:
                raise TmuxError(f"tmux capture failed: {result.stderr}")

            output = result.stdout
            # Filter out tmux-cli notes if present (when using tmux-cli)
            lines = output.split("\n")
            note_patterns = {
                "Note:",
                "tmux-cli is running outside tmux",
                "For better integration",
                "Use 'tmux-cli attach'",
            }

            filtered_lines = [
                line for line in lines if not any(pattern in line for pattern in note_patterns)
            ]

            return "\n".join(filtered_lines)
        except FileNotFoundError as e:
            raise TmuxError("tmux not found. Install tmux first") from e
        except subprocess.TimeoutExpired as e:
            raise TmuxError(f"tmux capture timed out: {e}") from e

    def wait_idle(
        self,
        idle_time: float | None = None,
        timeout: float | None = None,
    ) -> None:
        """Wait for the pane to become idle (no output changes).

        Args:
            idle_time: Time with no output changes to consider idle (seconds)
            timeout: Maximum time to wait before giving up (seconds)

        Raises:
            TmuxError: If wait fails or times out
        """
        self._ensure_pane()

        idle = idle_time or self.default_idle_time
        tout = timeout or self.default_timeout

        args = [
            "wait_idle",
            f"--pane={self.pane_id}",
            f"--idle-time={idle}",
            f"--timeout={tout}",
        ]
        self._run_tmux_cli(args)

    def kill(self) -> None:
        """Kill the tmux pane and cleanup.

        Raises:
            TmuxError: If kill fails
        """
        if self.pane_id:
            try:
                self._run_tmux_cli(["kill", f"--pane={self.pane_id}"])
            finally:
                self.pane_id = None
                self._launched = False

    def interrupt(self) -> None:
        """Send Ctrl+C interrupt to the pane.

        Raises:
            TmuxError: If interrupt fails or pane not launched
        """
        self._ensure_pane()
        self._run_tmux_cli(["interrupt", f"--pane={self.pane_id}"])

    def escape(self) -> None:
        """Send escape key to the pane.

        Raises:
            TmuxError: If escape fails or pane not launched
        """
        self._ensure_pane()
        self._run_tmux_cli(["escape", f"--pane={self.pane_id}"])

    def send_and_capture(
        self,
        command: str,
        idle_time: float | None = None,
        timeout: float | None = None,
    ) -> str:
        """Send a command and wait for output.

        Convenience method that combines send, wait_idle, and capture.

        Args:
            command: The command to send
            idle_time: Time to wait for idle (seconds)
            timeout: Maximum wait time (seconds)

        Returns:
            str: The captured output after command execution
        """
        self.send(command)
        self.wait_idle(idle_time, timeout)
        return self.capture()

    def _ensure_pane(self) -> None:
        """Ensure a pane has been launched."""
        if not self._launched or not self.pane_id:
            raise TmuxError("No pane launched. Call launch() first.")

    def _run_tmux_cli(self, args: list[str]) -> str:
        """Run a tmux-cli command and return output.

        Args:
            args: Command arguments for tmux-cli

        Returns:
            str: Command stdout (with tmux-cli notes filtered out)

        Raises:
            TmuxError: If command fails
        """
        cmd = ["tmux-cli", *args]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.default_timeout + 10,
                check=False,
            )
            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
                raise TmuxError(f"tmux-cli {args[0]} failed: {error_msg}")

            # Filter out tmux-cli notes that appear when running outside tmux
            # (in remote mode). These notes appear in the first few lines and should
            # not be part of the actual command output.
            output = result.stdout
            lines = output.split("\n")

            # Find where the actual output starts (after the tmux-cli notes)
            # Notes appear as the first contiguous block of 3 lines
            actual_output_start = 0
            note_count = 0

            for i, line in enumerate(lines):
                if (
                    "Note:" in line
                    or "tmux-cli is running outside tmux" in line
                    or "For better integration" in line
                    or "Use 'tmux-cli attach'" in line
                ):
                    note_count += 1
                    actual_output_start = i + 1
                elif note_count > 0 and line.strip():
                    # We've hit real content after notes, stop skipping
                    break
                elif note_count == 0:
                    # Haven't started seeing notes yet, content starts here
                    break

            # Return everything after the note lines
            return "\n".join(lines[actual_output_start:])
        except subprocess.TimeoutExpired as e:
            raise TmuxError(f"tmux-cli command timed out: {cmd}") from e
        except FileNotFoundError as e:
            raise TmuxError("tmux-cli not found. Install with: uv tool install tmux-cli") from e
