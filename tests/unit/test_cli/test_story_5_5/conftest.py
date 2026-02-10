"""Story 5-5 specific test fixtures and configuration.

These fixtures extend the shared CLI fixtures for Story 5-5 specific testing.
"""

from unittest.mock import MagicMock

import pytest

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


# ==============================================================================
# Story 5-5 Specific Fixtures
# ==============================================================================


@pytest.fixture
def preset_manager_mock():
    """
    Provide a mock PresetManager for testing.

    Note: This will fail initially as the PresetManager doesn't exist yet.
    RED phase expectation: ImportError or similar failure.
    """
    try:
        from data_extract.cli.config.presets import PresetManager

        return MagicMock(spec=PresetManager)
    except ImportError:
        return MagicMock()


@pytest.fixture
def preset_config_factory():
    """
    Factory fixture for creating PresetConfig instances.

    Returns a callable that creates PresetConfig with default values.
    """

    def _create_preset(
        name: str = "test_preset",
        description: str = "Test preset",
        chunk_size: int = 500,
        quality_threshold: float = 0.7,
        output_format: str = "json",
        dedup_threshold: float = 0.85,
        include_metadata: bool = True,
        validation_level: str = "standard",
        **kwargs,
    ):
        try:
            from data_extract.cli.config.models import PresetConfig, ValidationLevel

            # Map string validation_level to enum
            if isinstance(validation_level, str):
                validation_level = ValidationLevel[validation_level.upper()]

            return PresetConfig(
                name=name,
                description=description,
                chunk_size=chunk_size,
                quality_threshold=quality_threshold,
                output_format=output_format,
                dedup_threshold=dedup_threshold,
                include_metadata=include_metadata,
                validation_level=validation_level,
                **kwargs,
            )
        except ImportError:
            # Return mock if PresetConfig not yet implemented
            preset = MagicMock()
            preset.name = name
            preset.description = description
            preset.chunk_size = chunk_size
            preset.quality_threshold = quality_threshold
            preset.output_format = output_format
            preset.dedup_threshold = dedup_threshold
            preset.include_metadata = include_metadata
            preset.validation_level = MagicMock(value=validation_level)
            return preset

    return _create_preset


@pytest.fixture
def isolated_preset_directory(tmp_path, monkeypatch):
    """
    Provide an isolated preset directory with HOME mocked.

    This fixture:
    1. Sets HOME to tmp_path
    2. Initializes .data-extract/presets directory
    3. Returns path to preset directory

    Use this to test file operations in isolation.
    """
    monkeypatch.setenv("HOME", str(tmp_path))

    preset_dir = tmp_path / ".data-extract" / "presets"
    preset_dir.mkdir(parents=True, exist_ok=True)

    return preset_dir


@pytest.fixture
def preset_with_custom_file(isolated_preset_directory):
    """
    Provide a preset directory with a sample custom preset file.

    Creates a YAML file at ~/.data-extract/presets/custom_test.yaml
    """
    preset_file = isolated_preset_directory / "custom_test.yaml"
    preset_file.write_text(
        """name: custom_test
description: Test custom preset
chunk_size: 512
quality_threshold: 0.75
output_format: json
dedup_threshold: 0.8
include_metadata: true
validation_level: standard
"""
    )

    return isolated_preset_directory


@pytest.fixture
def preset_typer_app():
    """
    Provide the Typer application for preset command testing.

    Note: This will fail initially as the Typer app doesn't exist yet.
    RED phase expectation: ImportError or similar failure.
    """
    try:
        from data_extract.cli.app import app

        return app
    except ImportError:
        return None
