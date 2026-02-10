"""Typer application entry point for data-extract CLI.

This module provides the main app instance for the data-extract command-line tool.
It is the canonical import location for the Typer application.

Usage:
    from data_extract.cli.app import app

    # For testing
    from typer.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
"""

from .base import app, create_app, get_app

__all__ = ["app", "create_app", "get_app"]
