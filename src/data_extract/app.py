"""CLI entry point for data-extract command.

Epic 5 Story 5-1: Refactored Command Structure with Typer.
Story 5-2: Configuration Management Commands.

This module re-exports the Typer-based CLI application from data_extract.cli.base
for backward compatibility and test imports.

The actual CLI implementation is in:
- data_extract.cli.base - Main Typer app with all commands
- data_extract.cli.config - Configuration management
- cli.semantic_commands - Semantic analysis (brownfield, wrapped)
- cli.cache_commands - Cache management (brownfield, wrapped)
"""

# Import the Typer-based app which has all the config commands
from data_extract.cli.base import app, create_app, get_app

# Re-export for backward compatibility
__all__ = ["app", "create_app", "get_app"]
