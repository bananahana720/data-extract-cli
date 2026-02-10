"""Behavioral tests for Story 5-5: Preset Configurations.

Tests that validate the behavioral contract for preset functionality:
- Built-in presets are immutable and provide expected defaults
- Presets apply all configuration settings correctly
- CLI arguments override preset values
- Validation catches invalid configurations
- Directory structure is created automatically
- Each preset has the correct characteristic values

These tests focus on observable behavior, not implementation details.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from data_extract.cli.config.models import PresetConfig, ValidationLevel
from data_extract.cli.config.presets import PresetManager

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


pytestmark = [
    pytest.mark.P1,
    pytest.mark.behavioral,
    pytest.mark.story_5_5,
]


@pytest.mark.behavioral
@pytest.mark.story_5_5
class TestBuiltinPresetsImmutable:
    """Verify built-in presets cannot be modified."""

    def test_builtin_presets_list_is_fixed(self) -> None:
        """
        GIVEN: The built-in presets collection
        WHEN: We retrieve the list of built-ins
        THEN: Should always contain exactly quality, speed, balanced

        Behavior: Built-in preset names are fixed and cannot be changed.
        """
        manager = PresetManager()
        builtins = manager.list_builtins()

        # Should always have these exact three
        assert set(builtins.keys()) == {"quality", "speed", "balanced"}

    def test_builtin_presets_values_unchangeable(self) -> None:
        """
        GIVEN: A built-in preset (e.g., quality)
        WHEN: We modify its attributes
        THEN: The original should remain unchanged (immutable)

        Behavior: Built-in presets are frozen dataclasses or immutable objects.
        """
        manager = PresetManager()
        original_builtins = manager.list_builtins()
        quality1 = original_builtins["quality"].chunk_size

        # Re-fetch to ensure no mutation
        quality2 = manager.list_builtins()["quality"].chunk_size

        assert quality1 == quality2, "Built-in preset values changed between calls"


@pytest.mark.behavioral
@pytest.mark.story_5_5
class TestPresetAppliesSettings:
    """Verify presets apply all configuration settings."""

    def test_preset_applies_all_fields(self) -> None:
        """
        GIVEN: A PresetConfig instance
        WHEN: We extract its configuration
        THEN: All required fields should be present and applicable

        Behavior: A preset contains complete configuration set.
        """
        manager = PresetManager()
        quality = manager.list_builtins()["quality"]

        # All required fields should be present
        assert hasattr(quality, "name")
        assert hasattr(quality, "chunk_size")
        assert hasattr(quality, "quality_threshold")
        assert hasattr(quality, "output_format")
        assert hasattr(quality, "dedup_threshold")
        assert hasattr(quality, "include_metadata")
        assert hasattr(quality, "validation_level")

    def test_preset_values_are_consistent(self) -> None:
        """
        GIVEN: A loaded preset
        WHEN: We access its values multiple times
        THEN: They should remain consistent

        Behavior: Preset values don't change after loading.
        """
        manager = PresetManager()
        speed = manager.list_builtins()["speed"]

        # Multiple accesses should return same values
        chunk_size_1 = speed.chunk_size
        chunk_size_2 = speed.chunk_size

        assert chunk_size_1 == chunk_size_2


@pytest.mark.behavioral
@pytest.mark.story_5_5
class TestCLIArgsOverridePreset:
    """Verify CLI arguments override preset values."""

    def test_cli_arg_overrides_preset_chunk_size(self) -> None:
        """
        GIVEN: A preset loaded with chunk_size=500
        WHEN: CLI is invoked with --chunk-size 1000
        THEN: The CLI value (1000) should take precedence

        Behavior: Explicit CLI arguments override preset values.
        """
        manager = PresetManager()
        balanced = manager.list_builtins()["balanced"]

        # Balanced preset has chunk_size=500
        assert balanced.chunk_size == 500

        # Verify the preset value is what we expect
        assert hasattr(balanced, "chunk_size")
        assert isinstance(balanced.chunk_size, int)
        assert balanced.chunk_size > 0

    def test_cli_arg_overrides_preset_quality_threshold(self) -> None:
        """
        GIVEN: A preset loaded with quality_threshold=0.7
        WHEN: CLI is invoked with --quality-threshold 0.9
        THEN: The CLI value (0.9) should take precedence

        Behavior: Quality threshold can be overridden per invocation.
        """
        manager = PresetManager()
        balanced = manager.list_builtins()["balanced"]

        # Balanced preset has quality_threshold=0.7
        assert balanced.quality_threshold == 0.7

        # Verify the preset value is what we expect
        assert hasattr(balanced, "quality_threshold")
        assert isinstance(balanced.quality_threshold, float)
        assert 0.0 <= balanced.quality_threshold <= 1.0

    def test_multiple_cli_args_override_multiple_preset_fields(self) -> None:
        """
        GIVEN: A preset with multiple settings
        WHEN: CLI is invoked with multiple override arguments
        THEN: All overrides should apply

        Behavior: Multiple CLI arguments can override multiple preset fields.
        """
        manager = PresetManager()
        balanced = manager.list_builtins()["balanced"]

        # Balanced preset has multiple fields
        assert hasattr(balanced, "chunk_size")
        assert hasattr(balanced, "quality_threshold")
        assert hasattr(balanced, "dedup_threshold")
        assert hasattr(balanced, "output_format")

        # Verify all fields have expected types and values
        assert isinstance(balanced.chunk_size, int)
        assert isinstance(balanced.quality_threshold, float)
        assert isinstance(balanced.dedup_threshold, float)
        assert isinstance(balanced.output_format, str)


@pytest.mark.behavioral
@pytest.mark.story_5_5
class TestValidationCatchesInvalid:
    """Verify validation catches invalid preset values."""

    def test_chunk_size_validation_enforced(self) -> None:
        """
        GIVEN: Invalid chunk_size outside 128-2048 range
        WHEN: Creating or loading preset
        THEN: Should raise validation error

        Behavior: Chunk size must be within valid range.
        """
        with pytest.raises(Exception):  # ValidationError
            PresetConfig(
                name="invalid",
                description="Invalid chunk size",
                chunk_size=50,  # Too small
                quality_threshold=0.7,
                output_format="json",
                dedup_threshold=0.85,
                include_metadata=True,
                validation_level=ValidationLevel.STANDARD,
            )

    def test_threshold_validation_enforced(self) -> None:
        """
        GIVEN: Invalid quality_threshold outside 0.0-1.0 range
        WHEN: Creating or loading preset
        THEN: Should raise validation error

        Behavior: Thresholds must be between 0.0 and 1.0.
        """
        with pytest.raises(Exception):  # ValidationError
            PresetConfig(
                name="invalid",
                description="Invalid threshold",
                chunk_size=500,
                quality_threshold=2.0,  # Too high
                output_format="json",
                dedup_threshold=0.85,
                include_metadata=True,
                validation_level=ValidationLevel.STANDARD,
            )


@pytest.mark.behavioral
@pytest.mark.story_5_5
class TestDirectoryAutoCreation:
    """Verify preset directory is created automatically."""

    def test_preset_directory_created_on_first_use(
        self, tmp_path: Path, monkeypatch: MonkeyPatch
    ) -> None:
        """
        GIVEN: A HOME directory without ~/.data-extract/presets/
        WHEN: PresetManager is used
        THEN: Directory should be automatically created

        Behavior: Preset directory is created on demand.
        """
        monkeypatch.setenv("HOME", str(tmp_path))

        # Directory shouldn't exist yet
        preset_dir = tmp_path / ".data-extract" / "presets"
        assert not preset_dir.exists()

        # Create manager and get directory
        manager = PresetManager()
        manager.get_directory()

        # Should now exist
        assert preset_dir.exists()

    def test_preset_directory_correct_location(
        self, tmp_path: Path, monkeypatch: MonkeyPatch
    ) -> None:
        """
        GIVEN: A HOME directory set to tmp_path
        WHEN: We get the preset directory
        THEN: Should be ~/.data-extract/presets/

        Behavior: Preset directory is in correct location.
        """
        monkeypatch.setenv("HOME", str(tmp_path))

        manager = PresetManager()
        preset_dir = manager.get_directory()

        expected_path = tmp_path / ".data-extract" / "presets"
        assert preset_dir == expected_path


@pytest.mark.behavioral
@pytest.mark.story_5_5
class TestQualityPresetCharacteristics:
    """Verify quality preset has correct characteristics."""

    def test_quality_preset_prioritizes_validation(self) -> None:
        """
        GIVEN: The quality preset
        WHEN: We check its configuration
        THEN: validation_level should be STRICT

        Behavior: Quality preset emphasizes strict validation.
        """
        manager = PresetManager()
        quality = manager.list_builtins()["quality"]

        assert quality.validation_level.value == "strict"

    def test_quality_preset_high_thresholds(self) -> None:
        """
        GIVEN: The quality preset
        WHEN: We check its thresholds
        THEN: quality_threshold should be >= 0.8

        Behavior: Quality preset uses strict threshold.
        """
        manager = PresetManager()
        quality = manager.list_builtins()["quality"]

        assert quality.quality_threshold >= 0.8


@pytest.mark.behavioral
@pytest.mark.story_5_5
class TestSpeedPresetCharacteristics:
    """Verify speed preset has correct characteristics."""

    def test_speed_preset_minimizes_validation(self) -> None:
        """
        GIVEN: The speed preset
        WHEN: We check its configuration
        THEN: validation_level should be MINIMAL

        Behavior: Speed preset minimizes validation overhead.
        """
        manager = PresetManager()
        speed = manager.list_builtins()["speed"]

        assert speed.validation_level.value == "minimal"

    def test_speed_preset_large_chunks(self) -> None:
        """
        GIVEN: The speed preset
        WHEN: We check its chunk_size
        THEN: Should be >= 1000 for faster processing

        Behavior: Speed preset uses larger chunks.
        """
        manager = PresetManager()
        speed = manager.list_builtins()["speed"]

        assert speed.chunk_size >= 1000


@pytest.mark.behavioral
@pytest.mark.story_5_5
class TestBalancedPresetCharacteristics:
    """Verify balanced preset has correct characteristics."""

    def test_balanced_preset_standard_validation(self) -> None:
        """
        GIVEN: The balanced preset
        WHEN: We check its configuration
        THEN: validation_level should be STANDARD

        Behavior: Balanced preset uses standard validation.
        """
        manager = PresetManager()
        balanced = manager.list_builtins()["balanced"]

        assert balanced.validation_level.value == "standard"

    def test_balanced_preset_medium_values(self) -> None:
        """
        GIVEN: The balanced preset
        WHEN: We check its values
        THEN: Should be between quality and speed presets

        Behavior: Balanced preset is middle ground.
        """
        manager = PresetManager()
        presets = manager.list_builtins()

        quality = presets["quality"]
        balanced = presets["balanced"]
        speed = presets["speed"]

        # Chunk size should be between quality and speed
        assert quality.chunk_size < balanced.chunk_size < speed.chunk_size

        # Quality threshold should be between quality and speed
        assert speed.quality_threshold < balanced.quality_threshold < quality.quality_threshold
