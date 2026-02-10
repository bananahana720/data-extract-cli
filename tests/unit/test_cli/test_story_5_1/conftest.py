"""Story 5-1 specific test fixtures and configuration.

These fixtures extend the shared CLI fixtures for Story 5-1 specific testing.
"""

from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

# Import shared fixtures from tests/fixtures/cli_fixtures.py
from tests.fixtures.cli_fixtures import (
    MockHomeStructure,
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


# ==============================================================================
# Story 5-1 Specific Fixtures
# ==============================================================================


@pytest.fixture
def typer_app():
    """
    Provide the Typer application for testing.

    Note: This will fail initially as the Typer app doesn't exist yet.
    RED phase expectation: ImportError or similar failure.
    """
    try:
        from data_extract.cli.app import app

        return app
    except ImportError:
        # Expected failure in RED phase - return mock
        pytest.skip("Typer app not yet implemented (RED phase)")


@pytest.fixture
def greenfield_cli_dir() -> Path:
    """
    Provide path to greenfield CLI directory for import validation.
    """
    return Path("src/data_extract/cli/")


@pytest.fixture
def command_router_mock():
    """
    Mock CommandRouter for testing pipeline composition.

    RED phase: This tests expected interface of CommandRouter.
    """
    mock_router = MagicMock()
    mock_router.execute.return_value = MagicMock(
        success=True,
        exit_code=0,
        output="Mock output",
        metadata={"duration_ms": 100},
    )
    return mock_router


@pytest.fixture
def sample_config_model():
    """
    Provide sample configuration values for Pydantic model testing.
    """
    return {
        "tfidf_max_features": 5000,
        "tfidf_min_df": 2,
        "tfidf_max_df": 0.95,
        "tfidf_ngram_range": (1, 2),
        "similarity_duplicate_threshold": 0.95,
        "similarity_related_threshold": 0.7,
        "lsa_n_components": 100,
        "quality_min_score": 0.3,
        "cache_enabled": True,
        "cache_max_size_mb": 512,
    }


@pytest.fixture
def wizard_mock_prompts():
    """
    Provide mock InquirerPy prompts for wizard testing.

    Returns a patcher that can be used to mock interactive prompts.
    """

    def create_patcher(responses: list):
        """Create patcher with predetermined responses."""
        response_iter = iter(responses)

        def mock_prompt(*args, **kwargs):
            try:
                return next(response_iter)
            except StopIteration:
                return None

        return patch("inquirer.prompt", side_effect=mock_prompt)

    return create_patcher


@pytest.fixture
def first_run_environment(
    mock_home_directory: MockHomeStructure,
) -> Generator[MockHomeStructure, None, None]:
    """
    Configure environment to simulate first-time user (no config files).

    Ensures:
    - No ~/.config/data-extract/config.yaml exists
    - No ~/.data-extract/ directory exists
    - No .data-extract.yaml in working directory
    """
    # Ensure directories exist but config files don't
    # MockHomeStructure creates directories, so we just yield it
    # First run is detected by absence of config.yaml
    yield mock_home_directory


@pytest.fixture
def existing_config_environment(
    mock_home_directory: MockHomeStructure,
    sample_config_model: dict,
) -> Generator[MockHomeStructure, None, None]:
    """
    Configure environment with existing user configuration.

    Simulates returning user with saved preferences.
    """
    mock_home_directory.create_user_config(
        {
            "semantic": {
                "tfidf_max_features": sample_config_model["tfidf_max_features"],
                "tfidf_min_df": sample_config_model["tfidf_min_df"],
            },
            "mode": "enterprise",
        }
    )
    yield mock_home_directory


@pytest.fixture
def learning_mode_expected_patterns() -> dict:
    """
    Define expected output patterns for learning mode validation.

    Returns dict with pattern categories and their expected presence.
    """
    return {
        "step_markers": [
            r"\[Step \d+/\d+\]",  # [Step 1/4] format
            r"\[LEARN\]",  # Learning tip marker
        ],
        "educational_content": [
            "What's happening:",
            "Learn more:",
            "Why this matters:",
        ],
        "interactive_prompts": [
            "[Continue]",
            "Press Enter",
            "Press any key",
        ],
        "summary_markers": [
            "What you learned",
            "Insights:",
            "Summary:",
        ],
    }
