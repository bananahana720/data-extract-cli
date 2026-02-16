"""Configuration management for CLI commands.

Implements 6-layer configuration cascade for Story 5-2:
1. CLI arguments (highest priority)
2. Environment variables (DATA_EXTRACT_* prefix)
3. Project config (.data-extract.yaml in cwd)
4. User config (~/.data-extract/config.yaml)
5. Preset config (~/.data-extract/presets/*.yaml)
6. Defaults (lowest priority)

Supports .data-extract.yaml configuration file.
"""

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
import yaml

# =============================================================================
# Configuration Layer Tracking (Story 5-2)
# =============================================================================


class ConfigLayer(str, Enum):
    """Enumeration of configuration sources for tracking.

    Each configuration value tracks which layer it came from,
    enabling display in 'config show' command.
    """

    CLI = "cli"
    ENV = "env"
    PROJECT = "project"
    USER = "user"
    PRESET = "preset"
    DEFAULT = "default"


class ConfigError(ValueError):
    """Base exception for configuration parsing/validation errors."""


class ConfigFileError(ConfigError):
    """Raised when a config YAML file cannot be loaded safely."""


class ConfigEnvVarError(ConfigError):
    """Raised when a DATA_EXTRACT_* environment variable is malformed."""


class ConfigResult:
    """Configuration result with source tracking.

    Wraps the merged configuration dictionary and provides methods
    to query which layer each value came from.
    """

    def __init__(self, config: Dict[str, Any], sources: Dict[str, ConfigLayer]):
        """Initialize config result.

        Args:
            config: Merged configuration dictionary
            sources: Mapping of config keys to their source layers
        """
        self._config = config
        self._sources = sources

    def __getattr__(self, name: str) -> Any:
        """Access config values as attributes."""
        if name.startswith("_"):
            return object.__getattribute__(self, name)
        if name in self._config:
            value = self._config[name]
            if isinstance(value, dict):
                # Return nested ConfigResult for dict values
                # Build sources for this nested dict
                prefix = f"{name}."
                nested_sources = {
                    k[len(prefix) :]: v for k, v in self._sources.items() if k.startswith(prefix)
                }
                return ConfigResult(value, nested_sources)
            return value
        raise AttributeError(f"Config has no attribute '{name}'")

    def get_source(self, key: str) -> ConfigLayer:
        """Get the source layer for a configuration key.

        Args:
            key: Configuration key (e.g., "output_dir" or "tfidf.max_features")

        Returns:
            ConfigLayer indicating source of the value
        """
        return self._sources.get(key, ConfigLayer.DEFAULT)

    def get_all_sources(self) -> Dict[str, ConfigLayer]:
        """Get all configuration keys and their sources.

        Returns:
            Dictionary mapping config keys to source layers
        """
        return self._sources.copy()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to plain dictionary.

        Returns:
            Configuration as dictionary
        """
        return self._config.copy()

    def __getitem__(self, key: str) -> Any:
        """Access config values via dict-like syntax."""
        return self._config[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value with default.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)


# =============================================================================
# Environment Variable Support (Story 5-2)
# =============================================================================

ENV_VAR_PREFIX = "DATA_EXTRACT_"

# Mapping from environment variable suffixes to nested config paths
ENV_VAR_MAPPINGS: Dict[str, str] = {
    "OUTPUT_DIR": "output_dir",
    "FORMAT": "format",
    "TFIDF_MAX_FEATURES": "semantic.tfidf.max_features",
    "TFIDF_MIN_DF": "semantic.tfidf.min_df",
    "TFIDF_MAX_DF": "semantic.tfidf.max_df",
    "SIMILARITY_DUPLICATE_THRESHOLD": "semantic.similarity.duplicate_threshold",
    "LSA_N_COMPONENTS": "semantic.lsa.n_components",
    "CACHE_ENABLED": "cache.enabled",
    "CACHE_MAX_SIZE_MB": "cache.max_size_mb",
    "QUALITY_MIN_SCORE": "quality.min_score",
    "CHUNK_SIZE": "chunk.size",
}


def _is_float(value: str) -> bool:
    """Check if string can be converted to float."""
    try:
        float(value)
        return "." in value
    except ValueError:
        return False


def _set_nested(config: Dict[str, Any], path: str, value: Any) -> None:
    """Set a nested value in a dictionary using dot notation.

    Args:
        config: Dictionary to modify
        path: Dot-separated path (e.g., "tfidf.max_features")
        value: Value to set
    """
    parts = path.split(".")
    current = config
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def _get_nested(config: Dict[str, Any], path: str, default: Any = None) -> Any:
    """Get a nested value from a dictionary using dot notation.

    Args:
        config: Dictionary to read from
        path: Dot-separated path (e.g., "tfidf.max_features")
        default: Default value if path not found

    Returns:
        Value at path or default
    """
    parts = path.split(".")
    current = config
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def _flatten_keys(config: Dict[str, Any], prefix: str = "") -> List[str]:
    """Flatten nested dictionary keys to dot notation.

    Args:
        config: Dictionary to flatten
        prefix: Current path prefix

    Returns:
        List of dot-notation keys
    """
    keys = []
    for key, value in config.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            keys.extend(_flatten_keys(value, full_key))
        else:
            keys.append(full_key)
    return keys


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries, with override taking precedence.

    Args:
        base: Base dictionary
        override: Dictionary with values to override

    Returns:
        New merged dictionary
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_env_config() -> Dict[str, Any]:
    """Load configuration from environment variables.

    Environment variables use the DATA_EXTRACT_ prefix and are mapped
    to nested config paths. Type coercion is automatic:
    - "true"/"false"/"yes"/"no"/"1"/"0" -> bool
    - Digit strings -> int
    - Float strings -> float

    Returns:
        Configuration dictionary from environment variables

    Raises:
        ConfigEnvVarError: If a numeric env var contains invalid value
    """
    # Fields that should be numeric (not strings or bools)
    numeric_fields = {
        "TFIDF_MAX_FEATURES",
        "TFIDF_MIN_DF",
        "TFIDF_MAX_DF",
        "SIMILARITY_DUPLICATE_THRESHOLD",
        "LSA_N_COMPONENTS",
        "CACHE_MAX_SIZE_MB",
        "QUALITY_MIN_SCORE",
        "CHUNK_SIZE",
    }

    config: Dict[str, Any] = {}
    for env_suffix, config_path in ENV_VAR_MAPPINGS.items():
        env_var = f"{ENV_VAR_PREFIX}{env_suffix}"
        value: Any = os.environ.get(env_var)
        if value is not None and value != "":
            # Type coercion based on field requirements
            try:
                lower_value = value.lower()
                if env_suffix in numeric_fields:
                    if _is_float(value):
                        value = float(value)
                    elif value.lstrip("-").isdigit():
                        value = int(value)
                    else:
                        raise ConfigEnvVarError(
                            f"Invalid value for {env_var}: {value}. "
                            "Expected a valid integer or float."
                        )
                else:
                    # Boolean coercion (case-insensitive)
                    if lower_value in ("true", "1", "yes", "on"):
                        value = True
                    elif lower_value in ("false", "0", "no", "off"):
                        value = False
                    # Float coercion (must have decimal point)
                    elif _is_float(value):
                        value = float(value)
                    # Integer coercion
                    elif value.lstrip("-").isdigit():
                        value = int(value)

                _set_nested(config, config_path, value)
            except ConfigEnvVarError:
                raise
            except (ValueError, AttributeError) as e:
                raise ConfigEnvVarError(
                    f"Invalid value for {env_var}: {value}. Expected a valid integer or float."
                ) from e
    return config


# =============================================================================
# Preset System (Story 5-2)
# =============================================================================

PRESETS_DIR = Path.home() / ".data-extract" / "presets"
USER_CONFIG_DIR = Path.home() / ".data-extract"
USER_CONFIG_PATH = USER_CONFIG_DIR / "config.yaml"

LEGACY_PRESET_BRIDGE: Dict[str, Dict[str, Any]] = {
    "quality": {
        "format": "json",
        "chunk": {"max_tokens": 256},
        "semantic": {
            "quality": {"min_score": 0.9},
            "similarity": {"duplicate_threshold": 0.85},
        },
        "metadata": {"include": True},
        "validation": {"level": "strict"},
    },
    "speed": {
        "format": "json",
        "chunk": {"max_tokens": 1024},
        "semantic": {
            "quality": {"min_score": 0.5},
            "similarity": {"duplicate_threshold": 0.99},
        },
        "metadata": {"include": False},
        "validation": {"level": "minimal"},
    },
    "balanced": {
        "format": "json",
        "chunk": {"max_tokens": 500},
        "semantic": {
            "quality": {"min_score": 0.7},
            "similarity": {"duplicate_threshold": 0.95},
        },
        "metadata": {"include": True},
        "validation": {"level": "standard"},
    },
}


# Convenience exception for preset not found
class PresetNotFoundError(ValueError):
    """Raised when a requested preset cannot be found."""

    pass


def _load_yaml(path: Path) -> Dict[str, Any]:
    """Load YAML file safely.

    Args:
        path: Path to YAML file

    Returns:
        Dictionary parsed from YAML.

    Raises:
        ConfigFileError: If file contents are invalid or cannot be read.
    """
    try:
        with open(path, encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigFileError(f"Invalid YAML in config file '{path}': {e}") from e
    except OSError as e:
        raise ConfigFileError(f"Unable to read config file '{path}': {e}") from e

    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ConfigFileError(
            f"Invalid config structure in '{path}': expected a top-level mapping/object."
        )
    return loaded


def _save_yaml(path: Path, data: Dict[str, Any]) -> None:
    """Save dictionary to YAML file.

    Args:
        path: Path to save to
        data: Dictionary to save
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def load_preset(name: str) -> Dict[str, Any]:
    """Load a preset configuration by name.

    Searches in order:
    1. User presets (~/.data-extract/presets/)
    2. Built-in presets (package presets/)

    Args:
        name: Preset name (without .yaml extension)

    Returns:
        Preset configuration dictionary

    Raises:
        PresetNotFoundError: If preset not found
        FileNotFoundError: If preset not found (alias for compatibility)
    """
    # Check user presets first - compute path dynamically for test compatibility
    user_preset_dir = Path.home() / ".data-extract" / "presets"
    user_preset_path = user_preset_dir / f"{name}.yaml"
    if user_preset_path.exists():
        return _load_yaml(user_preset_path)

    # Check built-in presets
    builtin_path = Path(__file__).parent / "presets" / f"{name}.yaml"
    if builtin_path.exists():
        return _load_yaml(builtin_path)

    # Bridge legacy PresetManager built-ins into config cascade presets.
    legacy = LEGACY_PRESET_BRIDGE.get(name)
    if legacy is not None:
        return legacy.copy()

    # Raise both types for compatibility
    raise PresetNotFoundError(f"Preset not found: {name}")


def save_preset(name: str, config: Dict[str, Any]) -> Path:
    """Save configuration as a user preset.

    Args:
        name: Preset name (without .yaml extension)
        config: Configuration dictionary to save

    Returns:
        Path to saved preset file
    """
    # Compute path dynamically for test compatibility
    presets_dir = Path.home() / ".data-extract" / "presets"
    presets_dir.mkdir(parents=True, exist_ok=True)
    preset_path = presets_dir / f"{name}.yaml"
    _save_yaml(preset_path, config)
    return preset_path


def list_presets() -> List[Dict[str, Any]]:
    """List all available presets (built-in + user).

    Returns:
        List of preset dictionaries with name and type information
    """
    presets: Dict[str, str] = {}  # name -> type

    # Built-in presets
    builtin_dir = Path(__file__).parent / "presets"
    if builtin_dir.exists():
        for p in builtin_dir.glob("*.yaml"):
            presets[p.stem] = "builtin"
    for preset_name in LEGACY_PRESET_BRIDGE:
        presets.setdefault(preset_name, "builtin")

    # User presets (can override built-in indication) - compute path dynamically
    user_presets_dir = Path.home() / ".data-extract" / "presets"
    if user_presets_dir.exists():
        for p in user_presets_dir.glob("*.yaml"):
            if p.stem not in presets:
                presets[p.stem] = "custom"

    # Return as list of dicts
    return [
        {"name": name, "type": type_, "is_builtin": type_ == "builtin"}
        for name, type_ in sorted(presets.items())
    ]


def delete_preset(name: str) -> bool:
    """Delete a user preset.

    Args:
        name: Preset name (without .yaml extension)

    Returns:
        True if deleted, False if not found or is built-in
    """
    # Compute path dynamically for test compatibility
    presets_dir = Path.home() / ".data-extract" / "presets"
    preset_path = presets_dir / f"{name}.yaml"
    if preset_path.exists():
        preset_path.unlink()
        return True
    return False


# =============================================================================
# Configuration Loading Functions (Story 5-2)
# =============================================================================


def load_user_config() -> Dict[str, Any]:
    """Load user configuration from ~/.data-extract/config.yaml.

    Returns:
        User configuration dictionary or empty dict if not found
    """
    # Compute path dynamically to support testing with Path.home() monkeypatch
    user_config_path = Path.home() / ".data-extract" / "config.yaml"
    if user_config_path.exists():
        return _load_yaml(user_config_path)
    return {}


def load_project_config(cwd: Optional[Path] = None) -> Dict[str, Any]:
    """Load project configuration from .data-extract.yaml in working directory.

    Args:
        cwd: Working directory to search (defaults to Path.cwd())

    Returns:
        Project configuration dictionary or empty dict if not found
    """
    if cwd is None:
        cwd = Path.cwd()
    project_config_path = cwd / ".data-extract.yaml"
    if project_config_path.exists():
        return _load_yaml(project_config_path)
    return {}


def get_default_config() -> Dict[str, Any]:
    """Get default configuration values.

    Returns:
        Dictionary with all default configuration values
    """
    return {
        "output_dir": "/default/output",
        "format": "json",
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
            "lsa": {
                "n_components": 100,
                "n_clusters": None,
            },
            "quality": {
                "min_score": 0.3,
            },
            "cache": {
                "enabled": True,
                "max_size_mb": 500,
            },
        },
        "chunk": {
            "max_tokens": 512,
            "overlap": 128,
        },
    }


def _expand_flat_keys(flat_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Expand flat CLI keys like 'tfidf_max_features' to nested structure.

    Converts keys with underscores to nested dicts:
    - 'tfidf_max_features' -> {'semantic': {'tfidf': {'max_features': ...}}}
    - 'output_dir' -> {'output_dir': ...} (no nesting needed)

    Args:
        flat_dict: Dictionary with possibly flat keys

    Returns:
        Dictionary with nested structure
    """
    result: Dict[str, Any] = {}

    # Mapping from flat CLI keys to nested paths
    cli_key_mappings = {
        "tfidf_max_features": "semantic.tfidf.max_features",
        "tfidf_min_df": "semantic.tfidf.min_df",
        "tfidf_max_df": "semantic.tfidf.max_df",
        "tfidf_ngram_range": "semantic.tfidf.ngram_range",
        "similarity_duplicate_threshold": "semantic.similarity.duplicate_threshold",
        "similarity_related_threshold": "semantic.similarity.related_threshold",
        "lsa_n_components": "semantic.lsa.n_components",
        "lsa_n_clusters": "semantic.lsa.n_clusters",
        "cache_enabled": "semantic.cache.enabled",
        "cache_max_size_mb": "semantic.cache.max_size_mb",
        "quality_min_score": "semantic.quality.min_score",
        "chunk_size": "chunk.size",
        "chunk_max_tokens": "chunk.max_tokens",
        "chunk_overlap": "chunk.overlap",
    }

    for key, value in flat_dict.items():
        if key in cli_key_mappings:
            # Expand to nested path
            nested_path = cli_key_mappings[key]
            _set_nested(result, nested_path, value)
        else:
            # Keep as-is (top-level keys like 'output_dir', 'format')
            result[key] = value

    return result


def load_merged_config(
    cli_args: Optional[Dict[str, Any]] = None,
    cli_overrides: Optional[Dict[str, Any]] = None,
    preset_name: Optional[str] = None,
    cwd: Optional[Path] = None,
) -> ConfigResult:
    """Load and merge configuration from all 6 layers.

    Layers (highest to lowest priority):
    1. CLI arguments
    2. Environment variables
    3. Project config (.data-extract.yaml)
    4. User config (~/.data-extract/config.yaml)
    5. Preset config
    6. Defaults

    Args:
        cli_args: Dictionary of CLI arguments (non-None values only) - deprecated, use cli_overrides
        cli_overrides: Dictionary of CLI arguments (non-None values only)
        preset_name: Name of preset to apply (optional)
        cwd: Working directory for project config (defaults to Path.cwd())

    Returns:
        ConfigResult with merged configuration and source tracking
    """
    # Support both parameter names for backward compatibility
    cli_values = cli_overrides if cli_overrides is not None else cli_args

    # Filter out None values from CLI args - they shouldn't override lower layers
    if cli_values:
        cli_values = {k: v for k, v in cli_values.items() if v is not None}
        # Expand flat CLI keys to nested structure
        cli_values = _expand_flat_keys(cli_values)

    sources: Dict[str, ConfigLayer] = {}

    # Layer 6: Defaults
    config = get_default_config()
    for key in _flatten_keys(config):
        sources[key] = ConfigLayer.DEFAULT

    # Layer 5: Preset
    if preset_name:
        try:
            preset_config = load_preset(preset_name)
            config = _deep_merge(config, preset_config)
            for key in _flatten_keys(preset_config):
                sources[key] = ConfigLayer.PRESET
        except PresetNotFoundError:
            pass  # Preset not found, skip

    # Layer 4: User config
    try:
        user_config = load_user_config()
    except ConfigFileError as e:
        raise click.ClickException(str(e)) from e
    if user_config:
        config = _deep_merge(config, user_config)
        for key in _flatten_keys(user_config):
            sources[key] = ConfigLayer.USER

    # Layer 3: Project config
    try:
        project_config = load_project_config(cwd)
    except ConfigFileError as e:
        raise click.ClickException(str(e)) from e
    if project_config:
        config = _deep_merge(config, project_config)
        for key in _flatten_keys(project_config):
            sources[key] = ConfigLayer.PROJECT

    # Layer 2: Environment variables
    try:
        env_config = load_env_config()
    except ConfigEnvVarError as e:
        raise click.ClickException(str(e)) from e
    if env_config:
        config = _deep_merge(config, env_config)
        for key in _flatten_keys(env_config):
            sources[key] = ConfigLayer.ENV

    # Layer 1: CLI arguments
    if cli_values:
        config = _deep_merge(config, cli_values)
        for key in _flatten_keys(cli_values):
            sources[key] = ConfigLayer.CLI

    return ConfigResult(config, sources)


# Alias for tests that look for merge_config_6layer
merge_config_6layer = load_merged_config


# =============================================================================
# Legacy Configuration (Backward Compatibility)
# =============================================================================


@dataclass
class SemanticCliConfig:
    """Configuration for semantic analysis CLI commands.

    Attributes:
        tfidf_max_features: Maximum vocabulary size for TF-IDF
        tfidf_ngram_range: N-gram range (min, max)
        tfidf_min_df: Minimum document frequency
        tfidf_max_df: Maximum document frequency
        similarity_duplicate_threshold: Threshold for duplicate detection
        similarity_related_threshold: Threshold for related documents
        lsa_n_components: Number of LSA components
        lsa_n_clusters: Number of clusters (None for auto)
        quality_min_score: Minimum quality score threshold
        cache_enabled: Whether to use caching
        cache_max_size_mb: Maximum cache size in MB
    """

    # TF-IDF configuration
    tfidf_max_features: int = 5000
    tfidf_ngram_range: Tuple[int, int] = (1, 2)
    tfidf_min_df: int = 2
    tfidf_max_df: float = 0.95

    # Similarity configuration
    similarity_duplicate_threshold: float = 0.95
    similarity_related_threshold: float = 0.7

    # LSA configuration
    lsa_n_components: int = 100
    lsa_n_clusters: Optional[int] = None

    # Quality configuration
    quality_min_score: float = 0.3

    # Cache configuration
    cache_enabled: bool = True
    cache_max_size_mb: int = 500


def load_config_file(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from .data-extract.yaml file.

    Args:
        config_path: Path to config file. If None, searches for .data-extract.yaml
                    in current directory and parents.

    Returns:
        Configuration dictionary, empty if no config found.

    Raises:
        click.ClickException: If the discovered/specified config file is invalid.
    """
    if config_path is None:
        # Search for config file in current directory and parents
        search_paths = [
            Path.cwd() / ".data-extract.yaml",
            Path.cwd() / "data-extract.yaml",
            Path.home() / ".config" / "data-extract" / "config.yaml",
        ]
        for path in search_paths:
            if path.exists():
                config_path = path
                break

    if config_path is None or not config_path.exists():
        return {}

    try:
        return _load_yaml(config_path)
    except ConfigFileError as e:
        raise click.ClickException(str(e)) from e


def merge_config(
    cli_args: Dict[str, Any],
    file_config: Dict[str, Any],
    defaults: SemanticCliConfig,
) -> SemanticCliConfig:
    """Merge configuration from CLI args, file, and defaults.

    Precedence: CLI args > config file > defaults

    Args:
        cli_args: Arguments from CLI (non-None values only)
        file_config: Configuration from file
        defaults: Default configuration

    Returns:
        Merged SemanticCliConfig
    """
    # Start with defaults
    result = SemanticCliConfig()

    # Get semantic section from file config
    semantic_config = file_config.get("semantic", {})
    tfidf_config = semantic_config.get("tfidf", {})
    similarity_config = semantic_config.get("similarity", {})
    lsa_config = semantic_config.get("lsa", {})
    quality_config = semantic_config.get("quality", {})
    cache_config = semantic_config.get("cache", {})

    # Apply file config
    if "max_features" in tfidf_config:
        result.tfidf_max_features = tfidf_config["max_features"]
    if "ngram_range" in tfidf_config:
        ngram = tfidf_config["ngram_range"]
        if isinstance(ngram, list) and len(ngram) == 2:
            result.tfidf_ngram_range = (ngram[0], ngram[1])
    if "min_df" in tfidf_config:
        result.tfidf_min_df = tfidf_config["min_df"]
    if "max_df" in tfidf_config:
        result.tfidf_max_df = tfidf_config["max_df"]

    if "duplicate_threshold" in similarity_config:
        result.similarity_duplicate_threshold = similarity_config["duplicate_threshold"]
    if "related_threshold" in similarity_config:
        result.similarity_related_threshold = similarity_config["related_threshold"]

    if "n_components" in lsa_config:
        result.lsa_n_components = lsa_config["n_components"]
    if "n_clusters" in lsa_config:
        n_clusters = lsa_config["n_clusters"]
        result.lsa_n_clusters = None if n_clusters == "auto" else n_clusters

    if "min_score" in quality_config:
        result.quality_min_score = quality_config["min_score"]

    if "enabled" in cache_config:
        result.cache_enabled = cache_config["enabled"]
    if "max_size_mb" in cache_config:
        result.cache_max_size_mb = cache_config["max_size_mb"]

    # Apply CLI args (highest precedence)
    for key, value in cli_args.items():
        if value is not None and hasattr(result, key):
            setattr(result, key, value)

    return result


@dataclass
class ExportConfig:
    """Configuration for export operations.

    Attributes:
        format: Export format (json, csv, html, graph)
        output_path: Output file or directory path
        include_matrix: Include full similarity matrix in output
        include_graph: Include similarity graph in output
        pretty_print: Pretty print JSON output
    """

    format: str = "json"
    output_path: Optional[Path] = None
    include_matrix: bool = False
    include_graph: bool = True
    pretty_print: bool = True


# =============================================================================
# Configuration Validation (Story 5-2)
# =============================================================================


def validate_config_file(config_path: Path) -> Tuple[bool, List[str]]:
    """Validate a configuration file for errors.

    Checks for:
    - YAML syntax errors
    - Type mismatches (e.g., string instead of int)
    - Range violations (e.g., negative values, out-of-bounds floats)
    - Structural issues (e.g., missing required keys)

    Args:
        config_path: Path to configuration file

    Returns:
        Tuple of (is_valid, error_messages)
        - is_valid: True if config is valid, False otherwise
        - error_messages: List of error messages with fix suggestions
    """
    errors: List[str] = []

    # Check if file exists
    if not config_path.exists():
        errors.append(f"Configuration file not found: {config_path}")
        errors.append("Suggestion: Run 'data-extract config init' to create a default config")
        return False, errors

    # Parse YAML
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(f"YAML syntax error: {e}")
        errors.append(
            "Suggestion: Check for missing colons, incorrect indentation, or unquoted strings"
        )
        return False, errors
    except Exception as e:
        errors.append(f"Error reading file: {e}")
        return False, errors

    # Handle empty file
    if config is None:
        config = {}

    # Get semantic section if present
    semantic = config.get("semantic", {})

    # Validate TF-IDF configuration
    tfidf = semantic.get("tfidf", {})
    if "max_features" in tfidf:
        max_features = tfidf["max_features"]
        if not isinstance(max_features, int):
            errors.append(
                f"tfidf.max_features must be an integer, got {type(max_features).__name__}: {max_features}"
            )
            errors.append("Suggestion: Use an integer value like 5000 or 10000")
        elif max_features <= 0:
            errors.append(f"tfidf.max_features must be greater than 0, got {max_features}")
            errors.append("Suggestion: Use a positive value like 5000")

    if "min_df" in tfidf:
        min_df = tfidf["min_df"]
        if not isinstance(min_df, (int, float)):
            errors.append(f"tfidf.min_df must be a number, got {type(min_df).__name__}: {min_df}")
            errors.append("Suggestion: Use an integer like 2 or a float like 0.01")
        elif isinstance(min_df, int) and min_df < 1:
            errors.append(f"tfidf.min_df must be >= 1 when an integer, got {min_df}")
            errors.append("Suggestion: Use 1 or 2 for minimum document frequency")
        elif isinstance(min_df, float) and not 0.0 < min_df <= 1.0:
            errors.append(f"tfidf.min_df must be in range (0.0, 1.0] when a float, got {min_df}")
            errors.append("Suggestion: Use a proportion like 0.01 (1%)")

    if "max_df" in tfidf:
        max_df = tfidf["max_df"]
        if not isinstance(max_df, (int, float)):
            errors.append(f"tfidf.max_df must be a number, got {type(max_df).__name__}: {max_df}")
            errors.append("Suggestion: Use a float like 0.95 or an integer")
        elif isinstance(max_df, float) and not 0.0 < max_df <= 1.0:
            errors.append(f"tfidf.max_df must be in range (0.0, 1.0] when a float, got {max_df}")
            errors.append("Suggestion: Use 0.95 to exclude very common terms")

    if "ngram_range" in tfidf:
        ngram_range = tfidf["ngram_range"]
        if not isinstance(ngram_range, list) or len(ngram_range) != 2:
            errors.append(
                f"tfidf.ngram_range must be a list of two integers, got {type(ngram_range).__name__}: {ngram_range}"
            )
            errors.append("Suggestion: Use [1, 2] for unigrams and bigrams")
        else:
            min_n, max_n = ngram_range
            if not isinstance(min_n, int) or not isinstance(max_n, int):
                errors.append(f"tfidf.ngram_range values must be integers, got {ngram_range}")
                errors.append("Suggestion: Use [1, 2] for unigrams and bigrams")
            elif min_n > max_n:
                errors.append(f"tfidf.ngram_range min must be <= max, got [{min_n}, {max_n}]")
                errors.append(
                    "Suggestion: First value should be less than or equal to second, like [1, 2]"
                )

    # Validate similarity configuration
    similarity = semantic.get("similarity", {})
    if "duplicate_threshold" in similarity:
        threshold = similarity["duplicate_threshold"]
        if not isinstance(threshold, (int, float)):
            errors.append(
                f"similarity.duplicate_threshold must be a number, got {type(threshold).__name__}: {threshold}"
            )
            errors.append("Suggestion: Use a float between 0.0 and 1.0, like 0.95")
        elif not 0.0 <= threshold <= 1.0:
            errors.append(
                f"similarity.duplicate_threshold must be in range [0.0, 1.0], got {threshold}"
            )
            errors.append("Suggestion: Use 0.95 for high similarity detection")

    if "related_threshold" in similarity:
        threshold = similarity["related_threshold"]
        if not isinstance(threshold, (int, float)):
            errors.append(
                f"similarity.related_threshold must be a number, got {type(threshold).__name__}: {threshold}"
            )
            errors.append("Suggestion: Use a float between 0.0 and 1.0, like 0.7")
        elif not 0.0 <= threshold <= 1.0:
            errors.append(
                f"similarity.related_threshold must be in range [0.0, 1.0], got {threshold}"
            )
            errors.append("Suggestion: Use 0.7 for related document detection")

    # Validate LSA configuration
    lsa = semantic.get("lsa", {})
    if "n_components" in lsa:
        n_components = lsa["n_components"]
        if not isinstance(n_components, int):
            errors.append(
                f"lsa.n_components must be an integer, got {type(n_components).__name__}: {n_components}"
            )
            errors.append("Suggestion: Use an integer like 100")
        elif n_components <= 0:
            errors.append(f"lsa.n_components must be greater than 0, got {n_components}")
            errors.append("Suggestion: Use a positive value like 100")

    # Validate cache configuration
    cache = semantic.get("cache", {})
    if "enabled" in cache:
        enabled = cache["enabled"]
        if not isinstance(enabled, bool):
            errors.append(
                f"cache.enabled must be a boolean, got {type(enabled).__name__}: {enabled}"
            )
            errors.append("Suggestion: Use true or false")

    if "max_size_mb" in cache:
        max_size = cache["max_size_mb"]
        if not isinstance(max_size, int):
            errors.append(
                f"cache.max_size_mb must be an integer, got {type(max_size).__name__}: {max_size}"
            )
            errors.append("Suggestion: Use an integer like 500 for 500 MB")
        elif max_size <= 0:
            errors.append(f"cache.max_size_mb must be greater than 0, got {max_size}")
            errors.append("Suggestion: Use a positive value like 500")

    # Return validation results
    return len(errors) == 0, errors
