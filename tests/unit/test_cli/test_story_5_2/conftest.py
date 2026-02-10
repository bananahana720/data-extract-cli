"""Story 5-2 specific test fixtures and configuration.

These fixtures extend the shared CLI fixtures for Story 5-2 configuration management testing.
Supports testing of:
- 6-layer configuration cascade (AC-5.2-1)
- Environment variable overrides (AC-5.2-2)
- Preset system (AC-5.2-3, AC-5.2-5)
- Config commands (AC-5.2-6, AC-5.2-7, AC-5.2-8)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Generator, Optional

import pytest
import yaml

# Import shared fixtures from tests/fixtures/cli_fixtures.py
from tests.fixtures.cli_fixtures import (
    EnvVarsController,
    MockHomeStructure,
    config_factory,
    env_vars_fixture,
    mock_home_directory,
    pydantic_validation_corpus,
    six_layer_cascade_fixture,
    typer_cli_runner,
)

# Re-export for local use
__all__ = [
    "typer_cli_runner",
    "env_vars_fixture",
    "mock_home_directory",
    "six_layer_cascade_fixture",
    "config_factory",
    "pydantic_validation_corpus",
    # Story 5-2 specific fixtures
    "cascade_layer_values",
    "preset_corpus",
    "env_var_mappings",
    "config_commands_fixture",
    "config_file_factory",
    "six_layer_full_setup",
]


# ==============================================================================
# Story 5-2 Specific Fixtures
# ==============================================================================


@dataclass
class CascadeLayerValues:
    """Test values for each configuration layer to verify precedence.

    Each layer has distinct values to verify which layer wins in the cascade.
    """

    # Layer 1: CLI flags (highest priority)
    cli: Dict[str, Any] = field(
        default_factory=lambda: {
            "output_dir": "/from/cli",
            "tfidf_max_features": 10000,
            "chunk_size": 1000,
            "format": "json",
        }
    )

    # Layer 2: Environment variables
    env: Dict[str, str] = field(
        default_factory=lambda: {
            "OUTPUT_DIR": "/from/env",
            "TFIDF_MAX_FEATURES": "8000",
            "CHUNK_SIZE": "800",
            "FORMAT": "csv",
        }
    )

    # Layer 3: Project config (.data-extract.yaml in cwd)
    project: Dict[str, Any] = field(
        default_factory=lambda: {
            "output_dir": "/from/project",
            "semantic": {
                "tfidf": {"max_features": 6000},
            },
            "chunk": {"size": 600},
            "format": "txt",
        }
    )

    # Layer 4: User config (~/.config/data-extract/config.yaml)
    user: Dict[str, Any] = field(
        default_factory=lambda: {
            "output_dir": "/from/user",
            "semantic": {
                "tfidf": {"max_features": 4000},
            },
            "chunk": {"size": 400},
            "format": "html",
        }
    )

    # Layer 5: Preset config (~/.data-extract/presets/*.yaml)
    preset: Dict[str, Any] = field(
        default_factory=lambda: {
            "output_dir": "/from/preset",
            "semantic": {
                "tfidf": {"max_features": 2000},
            },
            "chunk": {"size": 200},
            "format": "xml",
        }
    )

    # Layer 6: Defaults (lowest priority)
    default: Dict[str, Any] = field(
        default_factory=lambda: {
            "output_dir": "/default/output",
            "semantic": {
                "tfidf": {"max_features": 5000},
            },
            "chunk": {"size": 500},
            "format": "json",
        }
    )


@pytest.fixture
def cascade_layer_values() -> CascadeLayerValues:
    """
    Provide distinct test values for each configuration layer.

    Returns:
        CascadeLayerValues with unique values per layer for precedence testing

    Usage:
        def test_precedence(cascade_layer_values, six_layer_cascade_fixture):
            # CLI should override all other layers
            cascade = six_layer_cascade_fixture
            cascade.set_project_config(cascade_layer_values.project)
            cascade.set_env_vars(cascade_layer_values.env)
            # Pass CLI args when invoking command
    """
    return CascadeLayerValues()


@pytest.fixture
def preset_corpus() -> Dict[str, Dict[str, Any]]:
    """
    Provide built-in preset configurations for testing.

    Returns:
        Dict mapping preset name to configuration dict

    Presets match Story 5-2 spec:
    - audit-standard: Default for audit documents
    - rag-optimized: RAG-ready output with smaller chunks
    - quick-scan: Fast preview mode
    """
    return {
        "audit-standard": {
            "name": "audit-standard",
            "description": "Audit document processing (default)",
            "semantic": {
                "tfidf": {
                    "max_features": 5000,
                    "ngram_range": [1, 2],
                    "min_df": 2,
                    "max_df": 0.95,
                },
                "similarity": {
                    "duplicate_threshold": 0.95,
                    "related_threshold": 0.7,
                },
            },
            "chunk": {
                "max_tokens": 512,
                "overlap": 128,
            },
            "quality": {
                "min_score": 0.3,
            },
            "cache": {
                "enabled": True,
                "max_size_mb": 500,
            },
        },
        "rag-optimized": {
            "name": "rag-optimized",
            "description": "RAG-ready output, smaller chunks",
            "semantic": {
                "tfidf": {
                    "max_features": 3000,
                    "ngram_range": [1, 1],
                },
            },
            "chunk": {
                "max_tokens": 256,
                "overlap": 64,
            },
            "quality": {
                "min_score": 0.5,
            },
        },
        "quick-scan": {
            "name": "quick-scan",
            "description": "Fast preview mode, minimal processing",
            "semantic": {
                "tfidf": {
                    "max_features": 1000,
                },
                "cache": {
                    "enabled": False,
                },
            },
            "quality": {
                "skip_readability": True,
            },
        },
    }


@pytest.fixture
def env_var_mappings() -> Dict[str, str]:
    """
    Provide mapping of environment variables to config fields.

    Returns:
        Dict mapping DATA_EXTRACT_* env var to config field path

    Follows naming convention from Story 5-2:
    - DATA_EXTRACT_OUTPUT_DIR -> output_dir
    - DATA_EXTRACT_TFIDF_MAX_FEATURES -> tfidf.max_features
    """
    return {
        "DATA_EXTRACT_OUTPUT_DIR": "output_dir",
        "DATA_EXTRACT_FORMAT": "format",
        "DATA_EXTRACT_CHUNK_SIZE": "chunk.size",
        "DATA_EXTRACT_CHUNK_OVERLAP": "chunk.overlap",
        "DATA_EXTRACT_TFIDF_MAX_FEATURES": "semantic.tfidf.max_features",
        "DATA_EXTRACT_TFIDF_MIN_DF": "semantic.tfidf.min_df",
        "DATA_EXTRACT_TFIDF_MAX_DF": "semantic.tfidf.max_df",
        "DATA_EXTRACT_SIMILARITY_DUPLICATE_THRESHOLD": "semantic.similarity.duplicate_threshold",
        "DATA_EXTRACT_SIMILARITY_RELATED_THRESHOLD": "semantic.similarity.related_threshold",
        "DATA_EXTRACT_LSA_N_COMPONENTS": "semantic.lsa.n_components",
        "DATA_EXTRACT_CACHE_ENABLED": "cache.enabled",
        "DATA_EXTRACT_CACHE_MAX_SIZE_MB": "cache.max_size_mb",
        "DATA_EXTRACT_QUALITY_MIN_SCORE": "quality.min_score",
    }


@dataclass
class ConfigCommandsFixture:
    """Fixture for testing config CLI commands.

    Provides helpers for testing:
    - config init
    - config show
    - config validate
    - config load/save
    """

    home_structure: MockHomeStructure
    env_controller: EnvVarsController

    def get_expected_init_content(self) -> list[str]:
        """Return expected content/comments in generated config file."""
        return [
            "# Data Extract Configuration",
            "# Generated by: data-extract config init",
            "semantic:",
            "tfidf:",
            "max_features:",
            "similarity:",
            "chunk:",
            "cache:",
            "output_dir:",
        ]

    def get_expected_show_source_indicators(self) -> list[str]:
        """Return expected source indicators in config show output."""
        return [
            "[cli]",
            "[env]",
            "[project]",
            "[user]",
            "[preset]",
            "[default]",
        ]

    def get_expected_validation_errors(self) -> Dict[str, str]:
        """Return invalid configs and expected error messages."""
        return {
            "invalid_yaml": "YAML syntax error",
            "invalid_type_int": "expected int",
            "invalid_type_float": "expected float",
            "invalid_range_threshold": "must be between 0 and 1",
            "invalid_ngram_order": "min must be <= max",
            "missing_required": "required field",
        }


@pytest.fixture
def config_commands_fixture(
    mock_home_directory: MockHomeStructure,
    env_vars_fixture: EnvVarsController,
) -> ConfigCommandsFixture:
    """
    Provide fixture for testing config CLI commands.

    Returns:
        ConfigCommandsFixture with helpers for config command testing
    """
    return ConfigCommandsFixture(
        home_structure=mock_home_directory,
        env_controller=env_vars_fixture,
    )


class ConfigFileFactory:
    """Factory for creating test configuration files.

    Creates various config file states for testing:
    - Valid configs at different layers
    - Invalid configs for error testing
    - Partial configs for merge testing
    """

    def __init__(self, base_path: Path):
        self.base_path = base_path

    def create_valid_project_config(
        self,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Create valid .data-extract.yaml in base_path."""
        config = {
            "semantic": {
                "tfidf": {"max_features": 5000, "min_df": 2},
                "similarity": {"duplicate_threshold": 0.95},
            },
            "chunk": {"max_tokens": 512},
            "cache": {"enabled": True},
        }
        if overrides:
            self._deep_merge(config, overrides)

        config_path = self.base_path / ".data-extract.yaml"
        config_path.write_text(yaml.dump(config, default_flow_style=False))
        return config_path

    def create_invalid_yaml_config(self) -> Path:
        """Create config file with invalid YAML syntax."""
        config_path = self.base_path / ".data-extract.yaml"
        # Invalid YAML: missing colon, bad indentation
        config_path.write_text(
            """
semantic
  tfidf:
    max_features 5000
  invalid: [unclosed
"""
        )
        return config_path

    def create_invalid_type_config(self) -> Path:
        """Create config with invalid field types."""
        config = {
            "semantic": {
                "tfidf": {
                    "max_features": "not_a_number",  # Should be int
                    "max_df": "also_not_a_number",  # Should be float
                },
            },
        }
        config_path = self.base_path / ".data-extract.yaml"
        config_path.write_text(yaml.dump(config))
        return config_path

    def create_invalid_range_config(self) -> Path:
        """Create config with out-of-range values."""
        config = {
            "semantic": {
                "tfidf": {
                    "max_features": -100,  # Must be positive
                    "max_df": 1.5,  # Must be <= 1.0
                },
                "similarity": {
                    "duplicate_threshold": 2.0,  # Must be <= 1.0
                },
            },
        }
        config_path = self.base_path / ".data-extract.yaml"
        config_path.write_text(yaml.dump(config))
        return config_path

    def create_invalid_ngram_config(self) -> Path:
        """Create config with invalid ngram_range (min > max)."""
        config = {
            "semantic": {
                "tfidf": {
                    "ngram_range": [3, 1],  # Invalid: min > max
                },
            },
        }
        config_path = self.base_path / ".data-extract.yaml"
        config_path.write_text(yaml.dump(config))
        return config_path

    def _deep_merge(self, base: Dict, overrides: Dict) -> None:
        """Deep merge overrides into base dict."""
        for key, value in overrides.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value


@pytest.fixture
def config_file_factory(tmp_path: Path) -> ConfigFileFactory:
    """
    Provide factory for creating test configuration files.

    Returns:
        ConfigFileFactory instance for creating various config states
    """
    return ConfigFileFactory(base_path=tmp_path)


@dataclass
class SixLayerFullSetup:
    """Complete 6-layer configuration setup for integration tests.

    Provides all 6 layers pre-configured with distinct values for
    comprehensive precedence testing.
    """

    tmp_path: Path
    home_structure: MockHomeStructure
    env_controller: EnvVarsController
    layer_values: CascadeLayerValues

    # Paths to created config files
    project_config_path: Optional[Path] = None
    user_config_path: Optional[Path] = None
    preset_config_path: Optional[Path] = None

    # Current CLI overrides (for load_merged_config)
    cli_overrides: Optional[Dict[str, Any]] = None

    def setup_all_layers(self, active_preset: str = "test-preset") -> None:
        """Configure all 6 layers with distinct values."""
        # Layer 3: Project config
        self.project_config_path = self.home_structure.create_project_config(
            self.layer_values.project
        )

        # Layer 4: User config
        self.user_config_path = self.home_structure.create_user_config(self.layer_values.user)

        # Layer 5: Preset config
        self.preset_config_path = self.home_structure.create_preset(
            active_preset,
            self.layer_values.preset,
        )

        # Layer 2: Environment variables
        for key, value in self.layer_values.env.items():
            self.env_controller.set(key, value)

    def setup_single_layer(self, layer_name: str) -> None:
        """Configure only one specific layer for isolation testing."""
        values = getattr(self.layer_values, layer_name)

        if layer_name == "cli":
            # Store CLI overrides for load_merged_config() calls
            self.cli_overrides = values
        elif layer_name == "env":
            for key, value in values.items():
                self.env_controller.set(key, value)
        elif layer_name == "project":
            self.project_config_path = self.home_structure.create_project_config(values)
        elif layer_name == "user":
            self.user_config_path = self.home_structure.create_user_config(values)
        elif layer_name == "preset":
            self.preset_config_path = self.home_structure.create_preset("test-preset", values)

    def clear_all_layers(self) -> None:
        """Remove all configuration to test defaults."""
        # Clear CLI overrides
        self.cli_overrides = None

        # Clear env vars
        self.env_controller.reset()

        # Remove config files
        if self.project_config_path and self.project_config_path.exists():
            self.project_config_path.unlink()
        if self.user_config_path and self.user_config_path.exists():
            self.user_config_path.unlink()
        if self.preset_config_path and self.preset_config_path.exists():
            self.preset_config_path.unlink()

    def get_cli_args(self, field: str) -> list[str]:
        """Get CLI args for a specific field from layer 1 values."""
        cli_values = self.layer_values.cli
        if field == "output_dir":
            return ["--output-dir", cli_values["output_dir"]]
        elif field == "tfidf_max_features":
            return ["--tfidf-max-features", str(cli_values["tfidf_max_features"])]
        elif field == "chunk_size":
            return ["--chunk-size", str(cli_values["chunk_size"])]
        elif field == "format":
            return ["--format", cli_values["format"]]
        return []

    def load_config(self, preset_name: Optional[str] = None):
        """Load configuration with current fixture state.

        This is a convenience method for tests that calls load_merged_config()
        with the correct cli_overrides from the current fixture state.

        Args:
            preset_name: Optional preset name to load

        Returns:
            ConfigResult from load_merged_config()
        """
        from data_extract.cli.config import load_merged_config

        # Use "test-preset" if preset layer was configured but no name given
        if preset_name is None and self.preset_config_path:
            preset_name = "test-preset"

        return load_merged_config(
            cli_overrides=self.cli_overrides, preset_name=preset_name, cwd=self.tmp_path
        )


@pytest.fixture
def six_layer_full_setup(
    tmp_path: Path,
    mock_home_directory: MockHomeStructure,
    env_vars_fixture: EnvVarsController,
    cascade_layer_values: CascadeLayerValues,
    monkeypatch,
) -> Generator[SixLayerFullSetup, None, None]:
    """
    Provide complete 6-layer configuration setup for integration tests.

    Yields:
        SixLayerFullSetup with all layers configurable

    Usage:
        def test_full_cascade(six_layer_full_setup, typer_cli_runner):
            setup = six_layer_full_setup
            setup.setup_all_layers()

            # CLI args should win
            result = runner.invoke(app, ["config", "show"] + setup.get_cli_args("output_dir"))
            assert "/from/cli" in result.output
    """
    setup = SixLayerFullSetup(
        tmp_path=tmp_path,
        home_structure=mock_home_directory,
        env_controller=env_vars_fixture,
        layer_values=cascade_layer_values,
    )

    # Monkeypatch Path.home() to use mock home directory
    monkeypatch.setattr(Path, "home", lambda: mock_home_directory.root)

    # Monkeypatch load_merged_config to inject CLI args from fixture
    from data_extract.cli import config as config_module

    original_load = config_module.load_merged_config

    def patched_load_merged_config(cli_args=None, cli_overrides=None, preset_name=None, cwd=None):
        # Use fixture's CLI overrides if not explicitly provided
        if cli_overrides is None and cli_args is None:
            cli_overrides = setup.cli_overrides
        # Use work_dir as cwd if not specified (where project config is located)
        if cwd is None:
            cwd = setup.home_structure.work_dir
        # Auto-detect preset if preset file exists and no preset name specified
        if preset_name is None and setup.preset_config_path and setup.preset_config_path.exists():
            preset_name = "test-preset"
        return original_load(
            cli_args=cli_args, cli_overrides=cli_overrides, preset_name=preset_name, cwd=cwd
        )

    monkeypatch.setattr(config_module, "load_merged_config", patched_load_merged_config)

    yield setup
    setup.clear_all_layers()


# ==============================================================================
# Pytest Markers for Story 5-2
# ==============================================================================


def pytest_configure(config):
    """Register custom markers for Story 5-2 tests."""
    config.addinivalue_line(
        "markers", "story_5_2: marks tests as Story 5-2 (Configuration Management)"
    )
    config.addinivalue_line("markers", "cascade: marks tests related to 6-layer cascade (AC-5.2-1)")
    config.addinivalue_line(
        "markers", "env_vars: marks tests related to environment variables (AC-5.2-2)"
    )
    config.addinivalue_line(
        "markers", "presets: marks tests related to preset system (AC-5.2-3, AC-5.2-5)"
    )
    config.addinivalue_line("markers", "config_commands: marks tests for config CLI commands")
