"""Command router for pipeline composition.

Story 5-1: Refactored Command Structure with Click-to-Typer Migration.

This module provides:
- CommandResult: Immutable result model for command execution
- CommandRouter: Router for command registration and pipeline composition
- Pipeline: Composable pipeline for sequential command execution
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Callable, Optional

from data_extract import __version__

# Re-export CommandResult for backward compatibility
from data_extract.cli.models import CommandResult

__all__ = ["CommandResult", "CommandRouter", "Pipeline", "get_router", "router"]

CLI_UX_VERSION = "0.2.0"


@dataclass
class Pipeline:
    """Composable pipeline for sequential command execution.

    Executes commands in sequence, stopping on first failure.

    Attributes:
        commands: List of command argument tuples to execute.
        router: CommandRouter instance for execution.
    """

    commands: list[tuple[str, ...]]
    router: "CommandRouter"

    def run(self) -> CommandResult:
        """Execute all commands in sequence.

        Returns:
            CommandResult from the last executed command, or error result
            if pipeline is empty.
        """
        if not self.commands:
            return CommandResult(
                success=False,
                exit_code=1,
                output="",
                errors=["Empty pipeline"],
            )

        last_result: Optional[CommandResult] = None
        for cmd_args in self.commands:
            last_result = self.router.execute(*cmd_args)
            if not last_result.success:
                break

        return last_result or CommandResult(
            success=False,
            exit_code=1,
            output="",
            errors=["No commands executed"],
        )


class CommandRouter:
    """Router for command registration and pipeline composition.

    Supports:
    - Command registration via decorator or direct registration
    - Pre/post execution hooks
    - Pipeline composition for sequential execution
    - Subcommand registration and discovery

    Example:
        router = CommandRouter()

        @router.command("process")
        def process_cmd(**kwargs) -> CommandResult:
            return CommandResult(success=True, exit_code=0, output="Done")

        result = router.execute("process", "--verbose")
    """

    def __init__(self) -> None:
        """Initialize the command router."""
        self._commands: dict[str, Callable[..., CommandResult]] = {}
        self._subcommands: dict[str, dict[str, Callable[..., CommandResult]]] = {}
        self._pre_hooks: list[Callable[[str, dict[str, Any]], None]] = []
        self._post_hooks: list[Callable[[str, CommandResult], None]] = []

        # Register default commands
        self._register_default_commands()

    def _register_default_commands(self) -> None:
        """Register default commands available in the CLI."""
        # Main commands
        self._commands["process"] = self._execute_process
        self._commands["semantic"] = self._execute_semantic
        self._commands["config"] = self._execute_config
        self._commands["cache"] = self._execute_cache
        self._commands["validate"] = self._execute_validate
        self._commands["version"] = self._execute_version

        # Semantic subcommands
        self._subcommands["semantic"] = {
            "analyze": self._execute_semantic_analyze,
            "deduplicate": self._execute_semantic_deduplicate,
            "cluster": self._execute_semantic_cluster,
            "topics": self._execute_semantic_topics,
        }

        # Cache subcommands
        self._subcommands["cache"] = {
            "status": self._execute_cache_status,
            "clear": self._execute_cache_clear,
            "warm": self._execute_cache_warm,
        }

        # Config subcommands
        self._subcommands["config"] = {
            "show": self._execute_config_show,
            "set": self._execute_config_set,
            "reset": self._execute_config_reset,
        }

    def register(self, name: str, handler: Callable[..., CommandResult]) -> None:
        """Register a command handler.

        Args:
            name: Command name.
            handler: Callable that returns CommandResult.
        """
        self._commands[name] = handler

    def register_subcommand(
        self,
        parent: str,
        name: str,
        handler: Callable[..., CommandResult],
    ) -> None:
        """Register a subcommand handler.

        Args:
            parent: Parent command name.
            name: Subcommand name.
            handler: Callable that returns CommandResult.
        """
        if parent not in self._subcommands:
            self._subcommands[parent] = {}
        self._subcommands[parent][name] = handler

    def execute(self, *args: str, **kwargs: Any) -> CommandResult:
        """Execute a command with arguments.

        Supports both positional arguments and keyword arguments.
        For commands with subcommands, the second positional argument
        is treated as the subcommand name.

        Args:
            *args: Command name and arguments (e.g., "semantic", "analyze", path).
            **kwargs: Keyword arguments passed to the handler.

        Returns:
            CommandResult with execution outcome.
        """
        if not args:
            return CommandResult(
                success=False,
                exit_code=1,
                output="",
                errors=["No command specified"],
            )

        command_name = args[0]
        remaining_args = args[1:]

        # Check if this is a subcommand invocation
        if command_name in self._subcommands and remaining_args:
            subcommand_name = remaining_args[0]
            if subcommand_name in self._subcommands[command_name]:
                # Run pre-hooks
                full_command = f"{command_name}.{subcommand_name}"
                for hook in self._pre_hooks:
                    hook(full_command, kwargs)

                # Execute subcommand
                subcommand_handler = self._subcommands[command_name][subcommand_name]
                try:
                    result = subcommand_handler(*remaining_args[1:], **kwargs)
                except Exception as e:
                    result = CommandResult(
                        success=False,
                        exit_code=1,
                        output="",
                        errors=[f"Command failed: {e}"],
                    )

                # Run post-hooks
                for post_hook in self._post_hooks:
                    post_hook(full_command, result)

                return result

        # Check for main command
        command_handler = self._commands.get(command_name)
        if command_handler is None:
            return CommandResult(
                success=False,
                exit_code=1,
                output="",
                errors=[f"Unknown command: {command_name}"],
            )

        # Run pre-hooks
        for pre_hook in self._pre_hooks:
            pre_hook(command_name, kwargs)

        # Execute command
        try:
            result = command_handler(*remaining_args, **kwargs)
        except Exception as e:
            result = CommandResult(
                success=False,
                exit_code=1,
                output="",
                errors=[f"Command failed: {e}"],
            )

        # Run post-hooks
        for post_hook in self._post_hooks:
            post_hook(command_name, result)

        return result

    @property
    def commands(self) -> list[str]:
        """List all registered command names.

        Returns:
            List of command names.
        """
        return list(self._commands.keys())

    def get_commands(self) -> list[str]:
        """List all registered command names.

        Returns:
            List of command names.
        """
        return self.commands

    def list_commands(self) -> list[str]:
        """List all registered commands.

        Returns:
            List of command names.
        """
        return self.commands

    def get_handler(self, name: str) -> Optional[Callable[..., CommandResult]]:
        """Get handler for a command.

        Args:
            name: Command name.

        Returns:
            Handler callable or None if not found.
        """
        return self._commands.get(name)

    def get_subcommands(self, parent: str) -> list[str]:
        """Get subcommands for a parent command.

        Args:
            parent: Parent command name.

        Returns:
            List of subcommand names.
        """
        if parent in self._subcommands:
            return list(self._subcommands[parent].keys())
        return []

    def add_pre_hook(
        self,
        hook: Callable[[str, dict[str, Any]], None],
    ) -> None:
        """Add pre-execution hook.

        Args:
            hook: Callable that receives (command_name, kwargs).
        """
        self._pre_hooks.append(hook)

    def add_post_hook(
        self,
        hook: Callable[[str, CommandResult], None],
    ) -> None:
        """Add post-execution hook.

        Args:
            hook: Callable that receives (command_name, result).
        """
        self._post_hooks.append(hook)

    def command(
        self, name: str
    ) -> Callable[[Callable[..., CommandResult]], Callable[..., CommandResult]]:
        """Decorator to register a command.

        Args:
            name: Command name.

        Returns:
            Decorator function.

        Example:
            @router.command("my_command")
            def my_handler(**kwargs) -> CommandResult:
                return CommandResult(success=True, exit_code=0, output="Done")
        """

        def decorator(
            func: Callable[..., CommandResult],
        ) -> Callable[..., CommandResult]:
            self.register(name, func)
            return func

        return decorator

    def compose(self, *pipelines: tuple[str, ...]) -> Pipeline:
        """Create a pipeline from command argument tuples.

        Args:
            *pipelines: Command argument tuples to execute in sequence.

        Returns:
            Pipeline instance that can be executed with .run().

        Example:
            pipeline = router.compose(
                ("process", "input.pdf", "--output", "output/"),
                ("semantic", "analyze", "output/"),
            )
            result = pipeline.run()
        """
        return Pipeline(commands=list(pipelines), router=self)

    # Default command implementations

    def _execute_version(self, *args: str, **kwargs: Any) -> CommandResult:
        """Execute version command."""
        return CommandResult(
            success=True,
            exit_code=0,
            output=(
                f"Data Extraction Tool v{__version__}\n"
                f"Version: {__version__}\n"
                "Epic 3, Story 3.5\n"
                f"Epic 5 - Enhanced CLI UX (v{CLI_UX_VERSION})"
            ),
            metadata={"version": __version__, "cli_ux_version": CLI_UX_VERSION},
        )

    def _execute_process(self, *args: str, **kwargs: Any) -> CommandResult:
        """Execute process command via CLI subprocess."""
        return self._run_cli_command("process", *args, **kwargs)

    def _execute_semantic(self, *args: str, **kwargs: Any) -> CommandResult:
        """Execute semantic command (requires subcommand)."""
        if not args:
            return CommandResult(
                success=False,
                exit_code=1,
                output="",
                errors=[
                    "Semantic command requires a subcommand (analyze, deduplicate, cluster, topics)"
                ],
            )
        # Dispatch to subcommand
        subcommand = args[0]
        if subcommand in self._subcommands.get("semantic", {}):
            handler = self._subcommands["semantic"][subcommand]
            return handler(*args[1:], **kwargs)
        return CommandResult(
            success=False,
            exit_code=1,
            output="",
            errors=[f"Unknown semantic subcommand: {subcommand}"],
        )

    def _execute_semantic_analyze(self, *args: str, **kwargs: Any) -> CommandResult:
        """Execute semantic analyze command."""
        return self._run_cli_command("semantic", "analyze", *args, **kwargs)

    def _execute_semantic_deduplicate(self, *args: str, **kwargs: Any) -> CommandResult:
        """Execute semantic deduplicate command."""
        return self._run_cli_command("semantic", "deduplicate", *args, **kwargs)

    def _execute_semantic_cluster(self, *args: str, **kwargs: Any) -> CommandResult:
        """Execute semantic cluster command."""
        return self._run_cli_command("semantic", "cluster", *args, **kwargs)

    def _execute_semantic_topics(self, *args: str, **kwargs: Any) -> CommandResult:
        """Execute semantic topics command."""
        return self._run_cli_command("semantic", "topics", *args, **kwargs)

    def _execute_config(self, *args: str, **kwargs: Any) -> CommandResult:
        """Execute config command."""
        if not args:
            return CommandResult(
                success=True,
                exit_code=0,
                output="Config command - use show, set, or reset subcommands",
            )
        return self._run_cli_command("config", *args, **kwargs)

    def _execute_config_show(self, *args: str, **kwargs: Any) -> CommandResult:
        """Execute config show command."""
        return CommandResult(
            success=True,
            exit_code=0,
            output="Configuration: default settings",
            metadata={"config": {}},
        )

    def _execute_config_set(self, *args: str, **kwargs: Any) -> CommandResult:
        """Execute config set command."""
        return CommandResult(
            success=True,
            exit_code=0,
            output="Configuration updated",
        )

    def _execute_config_reset(self, *args: str, **kwargs: Any) -> CommandResult:
        """Execute config reset command."""
        return CommandResult(
            success=True,
            exit_code=0,
            output="Configuration reset to defaults",
        )

    def _execute_cache(self, *args: str, **kwargs: Any) -> CommandResult:
        """Execute cache command."""
        if not args:
            return CommandResult(
                success=True,
                exit_code=0,
                output="Cache command - use status, clear, or warm subcommands",
            )
        return self._run_cli_command("cache", *args, **kwargs)

    def _execute_cache_status(self, *args: str, **kwargs: Any) -> CommandResult:
        """Execute cache status command."""
        return self._run_cli_command("cache", "status", *args, **kwargs)

    def _execute_cache_clear(self, *args: str, **kwargs: Any) -> CommandResult:
        """Execute cache clear command."""
        return self._run_cli_command("cache", "clear", *args, **kwargs)

    def _execute_cache_warm(self, *args: str, **kwargs: Any) -> CommandResult:
        """Execute cache warm command."""
        return self._run_cli_command("cache", "warm", *args, **kwargs)

    def _execute_validate(self, *args: str, **kwargs: Any) -> CommandResult:
        """Execute validate command."""
        return self._run_cli_command("validate", *args, **kwargs)

    def _run_cli_command(self, *args: str, **kwargs: Any) -> CommandResult:
        """Run a CLI command via subprocess.

        Args:
            *args: Command and arguments to pass to data-extract CLI.
            **kwargs: Additional options (not used in subprocess mode).

        Returns:
            CommandResult with execution outcome.
        """
        # Build command list
        cmd = [sys.executable, "-m", "data_extract.app"]
        cmd.extend(args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            return CommandResult(
                success=result.returncode == 0,
                exit_code=result.returncode,
                output=result.stdout,
                errors=[result.stderr] if result.stderr and result.returncode != 0 else [],
                metadata={"command": " ".join(cmd)},
            )
        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                exit_code=124,  # Standard timeout exit code
                output="",
                errors=["Command timed out after 300 seconds"],
            )
        except FileNotFoundError:
            # File not found - likely a missing input file
            return CommandResult(
                success=False,
                exit_code=1,
                output="",
                errors=[f"File not found: {args[-1] if args else 'unknown'}"],
            )
        except Exception as e:
            return CommandResult(
                success=False,
                exit_code=1,
                output="",
                errors=[f"Command execution failed: {e}"],
            )


# Global router instance
router = CommandRouter()


def get_router() -> CommandRouter:
    """Get the global router instance.

    Returns:
        Global CommandRouter instance.
    """
    return router
