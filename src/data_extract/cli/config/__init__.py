"""CLI configuration module.

This module provides preset configuration management for the data extraction
pipeline, including built-in presets and custom user configurations.

Note: This package shadows the sibling config.py module. To access items from
config.py, they are re-exported here using importlib to avoid circular imports.
"""

# Story 5-5: Preset configuration models
# Re-export items from sibling config.py module to maintain backward compatibility
# We use importlib to avoid circular import issues since this package shadows config.py
import importlib.util
from pathlib import Path
from typing import Any

from .models import PresetConfig, ValidationLevel
from .presets import BUILTIN_PRESETS, PresetManager, get_preset_directory


def _load_config_module() -> Any:
    """Load the sibling config.py module."""
    config_py_path = Path(__file__).parent.parent / "config.py"
    spec = importlib.util.spec_from_file_location("data_extract.cli._config_py", config_py_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return None


_config_py = _load_config_module()

# Export items from config.py if successfully loaded
if _config_py:
    SemanticCliConfig = _config_py.SemanticCliConfig
    load_config_file = _config_py.load_config_file
    merge_config = _config_py.merge_config
    ConfigLayer = _config_py.ConfigLayer
    ConfigResult = _config_py.ConfigResult
    validate_config_file = _config_py.validate_config_file
    load_merged_config = (
        _config_py.load_merged_config if hasattr(_config_py, "load_merged_config") else None
    )
    list_presets = _config_py.list_presets if hasattr(_config_py, "list_presets") else None
    save_preset = _config_py.save_preset if hasattr(_config_py, "save_preset") else None
    load_preset = _config_py.load_preset if hasattr(_config_py, "load_preset") else None
    # Environment variable support (Story 5-2)
    load_env_config = _config_py.load_env_config
    ENV_VAR_PREFIX = _config_py.ENV_VAR_PREFIX
    ENV_VAR_MAPPINGS = _config_py.ENV_VAR_MAPPINGS
    # Preset constants and exceptions
    PRESETS_DIR = _config_py.PRESETS_DIR
    PresetNotFoundError = _config_py.PresetNotFoundError

    __all__ = [
        # Story 5-5: Preset configuration
        "PresetConfig",
        "ValidationLevel",
        "PresetManager",
        "get_preset_directory",
        "BUILTIN_PRESETS",
        # Re-exports from config.py
        "SemanticCliConfig",
        "load_config_file",
        "merge_config",
        "ConfigLayer",
        "ConfigResult",
        "validate_config_file",
        "load_merged_config",
        "list_presets",
        "save_preset",
        "load_preset",
        # Environment variable support (Story 5-2)
        "load_env_config",
        "ENV_VAR_PREFIX",
        "ENV_VAR_MAPPINGS",
        # Preset constants and exceptions
        "PRESETS_DIR",
        "PresetNotFoundError",
    ]
else:
    __all__ = [
        "PresetConfig",
        "ValidationLevel",
        "PresetManager",
        "get_preset_directory",
        "BUILTIN_PRESETS",
    ]
