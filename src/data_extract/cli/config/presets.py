"""Preset management functionality.

This module provides the PresetManager class for managing built-in and
custom preset configurations, including directory operations and file I/O.
"""

import re
from pathlib import Path

from .models import PresetConfig, ValidationLevel


def get_preset_directory() -> Path:
    """Get preset directory, creating if needed.

    Returns:
        Path to ~/.data-extract/presets/ directory

    Note:
        Directory is created with parents=True if it doesn't exist
    """
    preset_dir = Path.home() / ".data-extract" / "presets"
    preset_dir.mkdir(parents=True, exist_ok=True)
    return preset_dir


_PRESET_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_PRESET_NAME_ERROR = (
    "Invalid preset name '{name}'. Use only letters, numbers, underscores, hyphens, "
    "or dots; path separators and '..' are not allowed."
)


def validate_preset_name(name: str) -> str:
    """Validate a preset name before using it in file paths."""
    if not name or name != name.strip():
        raise ValueError(_PRESET_NAME_ERROR.format(name=name))
    if "/" in name or "\\" in name or ".." in name:
        raise ValueError(_PRESET_NAME_ERROR.format(name=name))
    if not _PRESET_NAME_PATTERN.fullmatch(name):
        raise ValueError(_PRESET_NAME_ERROR.format(name=name))
    return name


# Built-in presets available to all users
BUILTIN_PRESETS: dict[str, PresetConfig] = {
    "quality": PresetConfig(
        name="quality",
        description="Maximum accuracy with thorough validation",
        chunk_size=256,
        quality_threshold=0.9,
        validation_level=ValidationLevel.STRICT,
        dedup_threshold=0.85,
        include_metadata=True,
        output_format="json",
    ),
    "speed": PresetConfig(
        name="speed",
        description="Fast processing with minimal overhead",
        chunk_size=1024,
        quality_threshold=0.5,
        validation_level=ValidationLevel.MINIMAL,
        dedup_threshold=0.99,
        include_metadata=False,
        output_format="json",
    ),
    "balanced": PresetConfig(
        name="balanced",
        description="Default trade-off for daily use",
        chunk_size=500,
        quality_threshold=0.7,
        validation_level=ValidationLevel.STANDARD,
        dedup_threshold=0.95,
        include_metadata=True,
        output_format="json",
    ),
}


class PresetManager:
    """Manages preset configurations for the data extraction pipeline.

    Handles both built-in presets and user-defined custom presets stored
    in ~/.data-extract/presets/.

    Attributes:
        _preset_dir: Directory where custom presets are stored
    """

    def __init__(self, preset_dir: Path | None = None) -> None:
        """Initialize preset manager.

        Args:
            preset_dir: Custom preset directory (defaults to ~/.data-extract/presets/)
        """
        self._preset_dir = preset_dir or get_preset_directory()

    @staticmethod
    def validate_name(name: str) -> str:
        """Validate and return a safe preset name."""
        return validate_preset_name(name)

    def get_directory(self) -> Path:
        """Get the preset directory path.

        Returns:
            Path to preset directory
        """
        return self._preset_dir

    def list_builtin(self) -> dict[str, PresetConfig]:
        """List built-in presets.

        Returns:
            Dictionary mapping preset names to PresetConfig instances
        """
        return BUILTIN_PRESETS.copy()

    def list_builtins(self) -> dict[str, PresetConfig]:
        """List built-in presets (alias for list_builtin).

        Returns:
            Dictionary mapping preset names to PresetConfig instances
        """
        return self.list_builtin()

    def list_custom(self) -> list[PresetConfig]:
        """List user-defined presets from directory.

        Returns:
            List of custom PresetConfig instances

        Note:
            Returns empty list if directory doesn't exist or contains no YAML files
        """
        if not self._preset_dir.exists():
            return []

        presets: list[PresetConfig] = []
        for yaml_file in self._preset_dir.glob("*.yaml"):
            try:
                content = yaml_file.read_text()
                preset = PresetConfig.from_yaml(content)
                presets.append(preset)
            except Exception:
                # Skip malformed preset files
                continue

        return presets

    def list_all(self) -> list[PresetConfig]:
        """List all presets (built-in + custom).

        Returns:
            List of all PresetConfig instances (built-in first, then custom)
        """
        builtin_list = list(BUILTIN_PRESETS.values())
        custom_list = self.list_custom()
        return builtin_list + custom_list

    def save(self, preset: PresetConfig, force: bool = False) -> Path:
        """Save preset to file.

        Args:
            preset: PresetConfig instance to save
            force: If True, overwrite existing custom preset

        Returns:
            Path to saved preset file

        Raises:
            ValueError: If attempting to overwrite a built-in preset
            FileExistsError: If preset exists and force=False
        """
        name = self.validate_name(preset.name)

        # Protect built-in presets from being overwritten
        if name in BUILTIN_PRESETS:
            raise ValueError(f"Cannot overwrite built-in preset: {name}")

        # Ensure directory exists
        self._preset_dir.mkdir(parents=True, exist_ok=True)

        # Check if file already exists
        preset_path = self._preset_dir / f"{name}.yaml"
        if preset_path.exists() and not force:
            raise FileExistsError(f"Preset already exists: {name}")

        # Write to file
        preset_path.write_text(preset.to_yaml())
        return preset_path

    def load(self, name: str) -> PresetConfig:
        """Load preset by name (custom first, then built-in).

        Args:
            name: Preset name to load

        Returns:
            PresetConfig instance

        Raises:
            KeyError: If preset is not found

        Note:
            Custom presets take precedence over built-in presets with the same name
        """
        name = self.validate_name(name)

        # Check custom presets first
        custom_path = self._preset_dir / f"{name}.yaml"
        if custom_path.exists():
            content = custom_path.read_text()
            return PresetConfig.from_yaml(content)

        # Check built-in presets
        if name in BUILTIN_PRESETS:
            return BUILTIN_PRESETS[name]

        # Not found
        raise KeyError(f"Preset not found: {name}")

    def delete(self, name: str) -> None:
        """Delete a custom preset.

        Args:
            name: Name of custom preset to delete

        Raises:
            ValueError: If attempting to delete a built-in preset
            KeyError: If custom preset is not found
        """
        name = self.validate_name(name)

        # Protect built-in presets
        if name in BUILTIN_PRESETS:
            raise ValueError(f"Cannot delete built-in preset: {name}")

        # Check if custom preset exists
        preset_path = self._preset_dir / f"{name}.yaml"
        if not preset_path.exists():
            raise KeyError(f"Custom preset not found: {name}")

        # Delete the file
        preset_path.unlink()
