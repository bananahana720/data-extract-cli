"""Unit tests for normalization configuration.

Tests configuration loading with cascade precedence:
- Default configuration instantiation
- YAML loading with valid/invalid files
- Cascade precedence (CLI overrides YAML, env vars, defaults)
- Field validation (invalid thresholds, missing files)
- Environment variable parsing (DATA_EXTRACT_NORMALIZE_* prefix)
"""

from pathlib import Path
from typing import Dict

import pytest
import yaml

from src.data_extract.normalize.config import NormalizationConfig, load_config

pytestmark = [pytest.mark.P0, pytest.mark.unit]


class TestNormalizationConfig:
    """Test NormalizationConfig model instantiation and validation."""

    def test_default_configuration(self) -> None:
        """Test default configuration instantiation."""
        config = NormalizationConfig()

        assert config.remove_ocr_artifacts is True
        assert config.remove_headers_footers is True
        assert config.normalize_whitespace is True
        assert config.header_repetition_threshold == 3
        assert config.whitespace_max_consecutive_newlines == 2
        assert config.ocr_artifact_patterns_file is None
        assert config.header_footer_patterns_file is None

    def test_custom_configuration(self) -> None:
        """Test custom configuration with overridden values."""
        config = NormalizationConfig(
            remove_ocr_artifacts=False,
            header_repetition_threshold=5,
            whitespace_max_consecutive_newlines=3,
        )

        assert config.remove_ocr_artifacts is False
        assert config.remove_headers_footers is True  # Default
        assert config.header_repetition_threshold == 5
        assert config.whitespace_max_consecutive_newlines == 3

    def test_threshold_validation_minimum(self) -> None:
        """Test that thresholds must be >= 1."""
        with pytest.raises(ValueError, match="greater than or equal to 1"):
            NormalizationConfig(header_repetition_threshold=0)

        with pytest.raises(ValueError, match="greater than or equal to 1"):
            NormalizationConfig(whitespace_max_consecutive_newlines=0)

    def test_threshold_validation_negative(self) -> None:
        """Test that thresholds cannot be negative."""
        with pytest.raises(ValueError, match="greater than or equal to 1"):
            NormalizationConfig(header_repetition_threshold=-1)

        with pytest.raises(ValueError, match="greater than or equal to 1"):
            NormalizationConfig(whitespace_max_consecutive_newlines=-5)

    def test_file_path_validation_nonexistent(self, tmp_path: Path) -> None:
        """Test that nonexistent file paths raise ValueError."""
        nonexistent_file = tmp_path / "does_not_exist.yaml"

        with pytest.raises(ValueError, match="Configuration file not found"):
            NormalizationConfig(ocr_artifact_patterns_file=nonexistent_file)

        with pytest.raises(ValueError, match="Configuration file not found"):
            NormalizationConfig(header_footer_patterns_file=nonexistent_file)

    def test_file_path_validation_exists(self, tmp_path: Path) -> None:
        """Test that existing file paths are accepted."""
        existing_file = tmp_path / "patterns.yaml"
        existing_file.write_text("# Empty config")

        config = NormalizationConfig(ocr_artifact_patterns_file=existing_file)
        assert config.ocr_artifact_patterns_file == existing_file

        config = NormalizationConfig(header_footer_patterns_file=existing_file)
        assert config.header_footer_patterns_file == existing_file

    def test_file_path_none_allowed(self) -> None:
        """Test that None file paths are allowed (optional)."""
        config = NormalizationConfig(
            ocr_artifact_patterns_file=None, header_footer_patterns_file=None
        )
        assert config.ocr_artifact_patterns_file is None
        assert config.header_footer_patterns_file is None


class TestLoadConfig:
    """Test load_config() function with cascade precedence."""

    def test_load_defaults_only(self) -> None:
        """Test loading with defaults only (no YAML, env vars, or CLI flags)."""
        config = load_config()

        assert config.remove_ocr_artifacts is True
        assert config.remove_headers_footers is True
        assert config.normalize_whitespace is True
        assert config.header_repetition_threshold == 3
        assert config.whitespace_max_consecutive_newlines == 2

    def test_load_from_yaml(self, tmp_path: Path) -> None:
        """Test loading configuration from YAML file."""
        yaml_file = tmp_path / "config.yaml"
        yaml_content = {
            "remove_ocr_artifacts": False,
            "header_repetition_threshold": 5,
            "whitespace_max_consecutive_newlines": 3,
        }
        yaml_file.write_text(yaml.dump(yaml_content))

        config = load_config(yaml_path=yaml_file)

        assert config.remove_ocr_artifacts is False
        assert config.header_repetition_threshold == 5
        assert config.whitespace_max_consecutive_newlines == 3
        assert config.remove_headers_footers is True  # Default

    def test_load_from_yaml_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading from nonexistent YAML file (ignored, uses defaults)."""
        nonexistent_file = tmp_path / "does_not_exist.yaml"

        config = load_config(yaml_path=nonexistent_file)

        # Should use defaults since file doesn't exist
        assert config.remove_ocr_artifacts is True
        assert config.header_repetition_threshold == 3

    def test_load_from_empty_yaml(self, tmp_path: Path) -> None:
        """Test loading from empty YAML file (uses defaults)."""
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("")

        config = load_config(yaml_path=yaml_file)

        # Should use defaults
        assert config.remove_ocr_artifacts is True
        assert config.header_repetition_threshold == 3

    def test_env_vars_override_yaml(self, tmp_path: Path) -> None:
        """Test that environment variables override YAML configuration."""
        yaml_file = tmp_path / "config.yaml"
        yaml_content = {"remove_ocr_artifacts": True, "header_repetition_threshold": 3}
        yaml_file.write_text(yaml.dump(yaml_content))

        env_vars = {
            "DATA_EXTRACT_NORMALIZE_REMOVE_OCR_ARTIFACTS": "false",
            "DATA_EXTRACT_NORMALIZE_HEADER_REPETITION_THRESHOLD": "7",
        }

        config = load_config(yaml_path=yaml_file, env_vars=env_vars)

        assert config.remove_ocr_artifacts is False  # From env var
        assert config.header_repetition_threshold == 7  # From env var

    def test_cli_flags_override_all(self, tmp_path: Path) -> None:
        """Test that CLI flags override env vars and YAML (highest precedence)."""
        yaml_file = tmp_path / "config.yaml"
        yaml_content = {"remove_ocr_artifacts": True, "header_repetition_threshold": 3}
        yaml_file.write_text(yaml.dump(yaml_content))

        env_vars = {"DATA_EXTRACT_NORMALIZE_REMOVE_OCR_ARTIFACTS": "false"}

        cli_flags = {"remove_ocr_artifacts": True, "whitespace_max_consecutive_newlines": 5}

        config = load_config(yaml_path=yaml_file, env_vars=env_vars, cli_flags=cli_flags)

        assert config.remove_ocr_artifacts is True  # From CLI (overrides env var)
        assert config.whitespace_max_consecutive_newlines == 5  # From CLI
        assert config.header_repetition_threshold == 3  # From YAML

    def test_env_var_boolean_parsing(self) -> None:
        """Test parsing of boolean environment variables."""
        env_vars = {
            "DATA_EXTRACT_NORMALIZE_REMOVE_OCR_ARTIFACTS": "true",
            "DATA_EXTRACT_NORMALIZE_REMOVE_HEADERS_FOOTERS": "false",
            "DATA_EXTRACT_NORMALIZE_NORMALIZE_WHITESPACE": "1",
        }

        config = load_config(env_vars=env_vars)

        assert config.remove_ocr_artifacts is True
        assert config.remove_headers_footers is False
        assert config.normalize_whitespace is True

    def test_env_var_integer_parsing(self) -> None:
        """Test parsing of integer environment variables."""
        env_vars = {
            "DATA_EXTRACT_NORMALIZE_HEADER_REPETITION_THRESHOLD": "10",
            "DATA_EXTRACT_NORMALIZE_WHITESPACE_MAX_CONSECUTIVE_NEWLINES": "5",
        }

        config = load_config(env_vars=env_vars)

        assert config.header_repetition_threshold == 10
        assert config.whitespace_max_consecutive_newlines == 5

    def test_env_var_path_parsing(self, tmp_path: Path) -> None:
        """Test parsing of Path environment variables."""
        patterns_file = tmp_path / "patterns.yaml"
        patterns_file.write_text("# Patterns")

        env_vars = {"DATA_EXTRACT_NORMALIZE_OCR_ARTIFACT_PATTERNS_FILE": str(patterns_file)}

        config = load_config(env_vars=env_vars)

        assert config.ocr_artifact_patterns_file == patterns_file

    def test_cascade_precedence_full_stack(self, tmp_path: Path) -> None:
        """Test full cascade precedence: defaults < YAML < env < CLI."""
        yaml_file = tmp_path / "config.yaml"
        yaml_content = {
            "remove_ocr_artifacts": False,  # YAML says False
            "header_repetition_threshold": 5,  # YAML says 5
            "whitespace_max_consecutive_newlines": 3,  # YAML says 3
        }
        yaml_file.write_text(yaml.dump(yaml_content))

        env_vars = {
            "DATA_EXTRACT_NORMALIZE_HEADER_REPETITION_THRESHOLD": "7",  # Env says 7
            "DATA_EXTRACT_NORMALIZE_NORMALIZE_WHITESPACE": "false",  # Env says false
        }

        cli_flags = {
            "remove_ocr_artifacts": True,  # CLI says True (highest)
        }

        config = load_config(yaml_path=yaml_file, env_vars=env_vars, cli_flags=cli_flags)

        # CLI overrides all
        assert config.remove_ocr_artifacts is True  # CLI (was False in YAML)

        # Env overrides YAML but not CLI
        assert config.header_repetition_threshold == 7  # Env (was 5 in YAML)
        assert config.normalize_whitespace is False  # Env (default was True)

        # YAML overrides defaults
        assert config.whitespace_max_consecutive_newlines == 3  # YAML (default was 2)

        # Defaults used when no override
        assert config.remove_headers_footers is True  # Default (no override)

    def test_invalid_yaml_content(self, tmp_path: Path) -> None:
        """Test handling of invalid YAML content."""
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text("{ invalid yaml content")

        with pytest.raises(yaml.YAMLError):
            load_config(yaml_path=yaml_file)

    def test_yaml_with_invalid_field_values(self, tmp_path: Path) -> None:
        """Test YAML with invalid field values (e.g., threshold < 1)."""
        yaml_file = tmp_path / "config.yaml"
        yaml_content = {"header_repetition_threshold": 0}  # Invalid: must be >= 1
        yaml_file.write_text(yaml.dump(yaml_content))

        with pytest.raises(ValueError, match="greater than or equal to 1"):
            load_config(yaml_path=yaml_file)

    def test_yaml_with_nonexistent_file_path(self, tmp_path: Path) -> None:
        """Test YAML specifying nonexistent file paths."""
        yaml_file = tmp_path / "config.yaml"
        yaml_content = {"ocr_artifact_patterns_file": str(tmp_path / "nonexistent.yaml")}
        yaml_file.write_text(yaml.dump(yaml_content))

        with pytest.raises(ValueError, match="Configuration file not found"):
            load_config(yaml_path=yaml_file)

    def test_empty_env_vars_dict(self) -> None:
        """Test with empty environment variables dict (uses defaults)."""
        config = load_config(env_vars={})

        assert config.remove_ocr_artifacts is True
        assert config.header_repetition_threshold == 3

    def test_env_vars_case_insensitivity(self) -> None:
        """Test that environment variable keys are case-insensitive after prefix."""
        env_vars: Dict[str, str] = {
            "DATA_EXTRACT_NORMALIZE_REMOVE_OCR_ARTIFACTS": "false",
            "DATA_EXTRACT_NORMALIZE_HEADER_REPETITION_THRESHOLD": "10",
        }

        config = load_config(env_vars=env_vars)

        assert config.remove_ocr_artifacts is False
        assert config.header_repetition_threshold == 10
