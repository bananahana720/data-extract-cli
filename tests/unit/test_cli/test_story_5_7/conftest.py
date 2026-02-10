"""Story 5-7 specific test fixtures and configuration.

These fixtures extend the shared CLI fixtures for Story 5-7 specific testing.
"""

# Import shared fixtures from tests/fixtures/cli_fixtures.py
from tests.fixtures.cli_fixtures import (
    config_factory,
    document_factory,
    env_vars_fixture,
    isolated_cli_runner,
    learning_mode_capture,
    mock_console,
    mock_home_directory,
    no_color_console,
    pydantic_validation_corpus,
    typer_cli_runner,
    wizard_responses_fixture,
)

# Re-export for local use
__all__ = [
    "typer_cli_runner",
    "isolated_cli_runner",
    "env_vars_fixture",
    "mock_home_directory",
    "mock_console",
    "no_color_console",
    "wizard_responses_fixture",
    "learning_mode_capture",
    "config_factory",
    "document_factory",
    "pydantic_validation_corpus",
]
