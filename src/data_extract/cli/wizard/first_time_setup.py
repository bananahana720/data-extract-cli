"""First-time setup wizard for Data Extraction Tool.

This module provides an interactive wizard that runs on first launch to:
- Detect if this is a first run
- Prompt user for preferences (mode, tutorial)
- Create configuration directory and save preferences
- Optionally run an interactive tutorial
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt


def prompt(prompt_type: str | None = None) -> Dict[str, bool | str]:
    """Collect user inputs for wizard.

    This function is separated to allow mocking in tests.
    When called without arguments, prompts for mode first, then tutorial on subsequent calls.

    Args:
        prompt_type: Type of prompt ('mode' or 'tutorial'). If None, auto-detect based on call count.

    Returns:
        dict: User selection(s). Returns both mode and tutorial when prompt_type is None (backward compat).
    """
    if prompt_type is None:
        # Backward compatible: return both values in one call
        mode = Prompt.ask("Select mode", choices=["enterprise", "hobbyist"], default="hobbyist")
        tutorial = Confirm.ask("Would you like to run the tutorial?", default=True)
        return {"mode": mode, "tutorial": tutorial}
    elif prompt_type == "mode":
        mode = Prompt.ask("Select mode", choices=["enterprise", "hobbyist"], default="hobbyist")
        return {"mode": mode}
    elif prompt_type == "tutorial":
        tutorial = Confirm.ask("Would you like to run the tutorial?", default=True)
        return {"tutorial": tutorial}
    else:
        raise ValueError(f"Unknown prompt_type: {prompt_type}")


# Configuration paths
def _get_config_path() -> Path:
    """Get config file path, respecting HOME environment variable for testing.

    Returns:
        Path: Config file path, preferring XDG standard location.
    """
    import os

    home_env = os.environ.get("HOME")
    if home_env:
        home = Path(home_env)
    else:
        home = Path.home()

    # Check both locations for backwards compatibility
    # Priority: ~/.config/data-extract/ (XDG) > ~/.data-extract/ (legacy)
    xdg_config = home / ".config" / "data-extract" / "config.yaml"
    data_extract_config = home / ".data-extract" / "config.yaml"

    # Return path that exists, or default to XDG standard
    if data_extract_config.exists() and not xdg_config.exists():
        # Legacy location exists, keep using it
        return data_extract_config
    # Prefer XDG standard for new installs
    return xdg_config


def _get_config_dir() -> Path:
    """Get config directory path."""
    return _get_config_path().parent


def is_first_run() -> bool:
    """Check if this is the first run of the tool.

    Returns:
        bool: True if config file doesn't exist, False otherwise.
    """
    import os

    home_env = os.environ.get("HOME")
    if home_env:
        home = Path(home_env)
    else:
        home = Path.home()

    # Check both possible config locations
    data_extract_config = home / ".data-extract" / "config.yaml"
    xdg_config = home / ".config" / "data-extract" / "config.yaml"

    return not (data_extract_config.exists() or xdg_config.exists())


def first_run_wizard(console: Optional[Console] = None) -> dict[str, Any]:
    """Run the interactive first-time setup wizard.

    This wizard:
    1. Displays a welcome message
    2. Prompts for mode selection (enterprise/hobbyist)
    3. Offers to run the tutorial
    4. Creates configuration directory
    5. Saves user preferences to YAML config

    Args:
        console: Rich Console instance for output. If None, creates a new one.

    Returns:
        dict: User preferences including mode, tutorial status, and first_run flag.
    """
    if console is None:
        console = Console()

    # Welcome panel with tool name
    welcome_text = (
        "[bold cyan]Welcome to Data Extraction Tool![/bold cyan]\n\n"
        "This wizard will help you set up your environment.\n"
        "Let's get started!"
    )
    console.print(Panel(welcome_text, title="[bold]First-Time Setup[/bold]", border_style="cyan"))
    console.print()

    # Mode selection prompt
    console.print("[bold]Step 1:[/bold] Choose your mode")
    console.print("  • [cyan]enterprise[/cyan]: Full features for business use")
    console.print("  • [cyan]hobbyist[/cyan]: Simplified interface for personal projects")
    console.print()

    # Collect user inputs (separated for testing)
    # Import here to allow test mocking via data_extract.cli.wizard.prompt
    from data_extract.cli.wizard import prompt as wizard_prompt

    # Call prompt for mode selection
    mode_input = wizard_prompt()
    mode = mode_input.get("mode", "hobbyist")

    console.print()
    console.print(f"[green]✓[/green] Mode set to: [bold]{mode}[/bold]")
    console.print()

    # Tutorial offer
    console.print("[bold]Step 2:[/bold] Optional tutorial")
    console.print("  The tutorial walks you through basic document extraction workflows.")
    console.print()

    # Call prompt for tutorial selection
    tutorial_input = wizard_prompt()
    run_tutorial = tutorial_input.get("tutorial", True)

    console.print()

    # Create configuration directory
    config_path = _get_config_path()
    config_dir = config_path.parent
    config_dir.mkdir(parents=True, exist_ok=True)

    # Build preferences dictionary
    preferences = {
        "mode": mode,
        "tutorial_completed": run_tutorial,
        "first_run_completed": True,
    }

    # Save to YAML config
    with open(config_path, "w") as f:
        yaml.safe_dump(preferences, f, default_flow_style=False, sort_keys=False)

    console.print(f"[green]✓[/green] Configuration saved to: [dim]{config_path}[/dim]")
    console.print()

    # Run tutorial if accepted
    if run_tutorial:
        console.print("[bold cyan]Starting tutorial...[/bold cyan]")
        console.print()
        _run_tutorial(console)
        console.print()
        console.print("[green]✓[/green] Tutorial completed!")
    else:
        console.print("[yellow]→[/yellow] Skipping tutorial (you can run it later)")

    console.print()
    console.print("[bold green]Setup complete![/bold green] You're ready to start.")
    console.print()

    return preferences


def _run_tutorial(console: Console) -> None:
    """Run the interactive tutorial.

    This is a placeholder tutorial that demonstrates basic concepts.
    In a full implementation, this would walk through document extraction workflows.

    Args:
        console: Rich Console instance for output.
    """
    console.print(Panel("Tutorial: Basic Extraction Workflow", border_style="blue"))
    console.print()
    console.print("[bold]Quick Start Guide:[/bold]")
    console.print("  1. Prepare your documents (PDF, DOCX, etc.)")
    console.print("  2. Run: [cyan]data-extract process <file>[/cyan]")
    console.print("  3. View results in the output directory")
    console.print()
    console.print("[dim]Tip: Use --help with any command to see all available options[/dim]")
