"""TDD RED Phase Tests: Preset Configuration Models (Story 5-5).

These tests verify the PresetConfig model and PresetManager functionality.
All tests are designed to FAIL initially (TDD RED phase).

AC-5.5-1: PresetConfig model with validation
AC-5.5-2: Built-in presets (quality, speed, balanced)
AC-5.5-3: PresetManager directory operations
AC-5.5-4: Preset serialization/deserialization
"""

from datetime import datetime
from pathlib import Path

import pytest

# P1: Core functionality - run on PR
pytestmark = [
    pytest.mark.P1,
    pytest.mark.unit,
    pytest.mark.story_5_5,
    pytest.mark.cli,
]


@pytest.mark.unit
@pytest.mark.story_5_5
class TestPresetConfigModel:
    """Test PresetConfig model creation and validation."""

    def test_preset_config_can_be_created(self):
        """
        RED: Verify PresetConfig model can be instantiated.

        Given: PresetConfig class is defined
        When: We create a PresetConfig instance
        Then: It should have all required attributes

        Expected RED failure: ImportError or AttributeError
        """
        # Given/When
        try:
            from data_extract.cli.config.models import PresetConfig, ValidationLevel

            preset = PresetConfig(
                name="test_preset",
                description="Test preset for verification",
                chunk_size=500,
                quality_threshold=0.7,
                output_format="json",
                dedup_threshold=0.85,
                include_metadata=True,
                validation_level=ValidationLevel.STANDARD,
            )
        except (ImportError, AttributeError) as e:
            pytest.fail(f"Cannot create PresetConfig: {e}")

        # Then
        assert preset is not None
        assert preset.name == "test_preset"
        assert preset.chunk_size == 500

    def test_preset_config_name_required(self):
        """
        RED: Verify name field is required.

        Given: PresetConfig model
        When: We create without name field
        Then: Should raise validation error

        Expected RED failure: ValidationError
        """
        # Given/When
        try:
            from data_extract.cli.config.models import PresetConfig, ValidationLevel
        except ImportError as e:
            pytest.fail(f"Cannot import PresetConfig: {e}")

        # Then - expect validation error when name is missing
        with pytest.raises(Exception):  # ValidationError or TypeError
            PresetConfig(
                description="Test preset without name",
                chunk_size=500,
                quality_threshold=0.7,
                output_format="json",
                dedup_threshold=0.85,
                include_metadata=True,
                validation_level=ValidationLevel.STANDARD,
            )

    def test_preset_config_chunk_size_validation(self):
        """
        RED: Verify chunk_size has valid range (128-2048).

        Given: PresetConfig model
        When: We create with chunk_size outside valid range
        Then: Should raise validation error

        Expected RED failure: ValidationError
        """
        # Given
        try:
            from data_extract.cli.config.models import PresetConfig, ValidationLevel
        except ImportError as e:
            pytest.fail(f"Cannot import PresetConfig: {e}")

        # When/Then - test too small
        with pytest.raises(Exception):  # ValidationError
            PresetConfig(
                name="invalid_small",
                description="Too small chunk size",
                chunk_size=64,  # Below minimum 128
                quality_threshold=0.7,
                output_format="json",
                dedup_threshold=0.85,
                include_metadata=True,
                validation_level=ValidationLevel.STANDARD,
            )

        # When/Then - test too large
        with pytest.raises(Exception):  # ValidationError
            PresetConfig(
                name="invalid_large",
                description="Too large chunk size",
                chunk_size=4096,  # Above maximum 2048
                quality_threshold=0.7,
                output_format="json",
                dedup_threshold=0.85,
                include_metadata=True,
                validation_level=ValidationLevel.STANDARD,
            )

    def test_preset_config_quality_threshold_range(self):
        """
        RED: Verify quality_threshold is between 0.0 and 1.0.

        Given: PresetConfig model
        When: We create with quality_threshold outside range
        Then: Should raise validation error

        Expected RED failure: ValidationError
        """
        # Given
        try:
            from data_extract.cli.config.models import PresetConfig, ValidationLevel
        except ImportError as e:
            pytest.fail(f"Cannot import PresetConfig: {e}")

        # When/Then - test below 0.0
        with pytest.raises(Exception):  # ValidationError
            PresetConfig(
                name="invalid_threshold_low",
                description="Threshold too low",
                chunk_size=500,
                quality_threshold=-0.1,  # Below 0.0
                output_format="json",
                dedup_threshold=0.85,
                include_metadata=True,
                validation_level=ValidationLevel.STANDARD,
            )

        # When/Then - test above 1.0
        with pytest.raises(Exception):  # ValidationError
            PresetConfig(
                name="invalid_threshold_high",
                description="Threshold too high",
                chunk_size=500,
                quality_threshold=1.5,  # Above 1.0
                output_format="json",
                dedup_threshold=0.85,
                include_metadata=True,
                validation_level=ValidationLevel.STANDARD,
            )

    def test_preset_config_dedup_threshold_range(self):
        """
        RED: Verify dedup_threshold is between 0.0 and 1.0.

        Given: PresetConfig model
        When: We create with dedup_threshold outside range
        Then: Should raise validation error

        Expected RED failure: ValidationError
        """
        # Given
        try:
            from data_extract.cli.config.models import PresetConfig, ValidationLevel
        except ImportError as e:
            pytest.fail(f"Cannot import PresetConfig: {e}")

        # When/Then - test outside valid range
        with pytest.raises(Exception):  # ValidationError
            PresetConfig(
                name="invalid_dedup",
                description="Invalid dedup threshold",
                chunk_size=500,
                quality_threshold=0.7,
                output_format="json",
                dedup_threshold=1.5,  # Above 1.0
                include_metadata=True,
                validation_level=ValidationLevel.STANDARD,
            )

    def test_preset_config_serialization(self):
        """
        RED: Verify PresetConfig can be serialized to dict.

        Given: PresetConfig instance
        When: We serialize it to dict
        Then: Should include all fields

        Expected RED failure: AttributeError or TypeError
        """
        # Given
        try:
            from data_extract.cli.config.models import PresetConfig, ValidationLevel
        except ImportError as e:
            pytest.fail(f"Cannot import PresetConfig: {e}")

        preset = PresetConfig(
            name="test_serialize",
            description="Serialization test",
            chunk_size=500,
            quality_threshold=0.7,
            output_format="json",
            dedup_threshold=0.85,
            include_metadata=True,
            validation_level=ValidationLevel.STANDARD,
        )

        # When
        try:
            preset_dict = preset.model_dump() if hasattr(preset, "model_dump") else dict(preset)
        except AttributeError as e:
            pytest.fail(f"Cannot serialize PresetConfig: {e}")

        # Then
        assert isinstance(preset_dict, dict)
        assert preset_dict["name"] == "test_serialize"
        assert preset_dict["chunk_size"] == 500

    def test_preset_config_created_timestamp(self):
        """
        RED: Verify PresetConfig tracks creation timestamp.

        Given: PresetConfig instance
        When: We access the created field
        Then: Should be datetime or None

        Expected RED failure: AttributeError
        """
        # Given
        try:
            from data_extract.cli.config.models import PresetConfig, ValidationLevel
        except ImportError as e:
            pytest.fail(f"Cannot import PresetConfig: {e}")

        # When
        preset = PresetConfig(
            name="test_timestamp",
            description="Timestamp test",
            chunk_size=500,
            quality_threshold=0.7,
            output_format="json",
            dedup_threshold=0.85,
            include_metadata=True,
            validation_level=ValidationLevel.STANDARD,
        )

        # Then
        assert hasattr(preset, "created")
        # Should be datetime or None (auto-set on creation)
        assert preset.created is None or isinstance(preset.created, datetime)

    def test_validation_level_enum_exists(self):
        """
        RED: Verify ValidationLevel enum is defined.

        Given: ValidationLevel enum
        When: We access its values
        Then: Should have minimal, standard, strict

        Expected RED failure: ImportError
        """
        # Given/When
        try:
            from data_extract.cli.config.models import ValidationLevel
        except ImportError as e:
            pytest.fail(f"Cannot import ValidationLevel: {e}")

        # Then
        assert hasattr(ValidationLevel, "MINIMAL")
        assert hasattr(ValidationLevel, "STANDARD")
        assert hasattr(ValidationLevel, "STRICT")


@pytest.mark.unit
@pytest.mark.story_5_5
class TestPresetManager:
    """Test PresetManager directory and preset operations."""

    def test_preset_manager_class_exists(self):
        """
        RED: Verify PresetManager class can be imported.

        Given: PresetManager class
        When: We import it
        Then: Should be instantiable

        Expected RED failure: ImportError
        """
        # Given/When
        try:
            from data_extract.cli.config.presets import PresetManager
        except ImportError as e:
            pytest.fail(f"Cannot import PresetManager: {e}")

        # Then
        assert PresetManager is not None
        assert callable(PresetManager)

    def test_get_preset_directory_function(self):
        """
        RED: Verify get_preset_directory function exists.

        Given: get_preset_directory function
        When: We call it
        Then: Should return a Path object

        Expected RED failure: ImportError or TypeError
        """
        # Given/When
        try:
            from data_extract.cli.config.presets import get_preset_directory
        except ImportError as e:
            pytest.fail(f"Cannot import get_preset_directory: {e}")

        # Then
        directory = get_preset_directory()
        assert isinstance(directory, Path)

    def test_preset_manager_get_directory(self, tmp_path, monkeypatch):
        """
        RED: Verify PresetManager.get_directory() returns correct path.

        Given: PresetManager instance with HOME env var mocked
        When: We call get_directory()
        Then: Should return ~/.data-extract/presets/ path

        Expected RED failure: AttributeError or incorrect path
        """
        # Given
        monkeypatch.setenv("HOME", str(tmp_path))

        try:
            from data_extract.cli.config.presets import PresetManager
        except ImportError as e:
            pytest.fail(f"Cannot import PresetManager: {e}")

        manager = PresetManager()

        # When
        preset_dir = manager.get_directory()

        # Then
        assert preset_dir is not None
        assert isinstance(preset_dir, Path)
        # Should end with .data-extract/presets
        assert str(preset_dir).endswith("presets")
        assert ".data-extract" in str(preset_dir)

    def test_preset_manager_list_builtins(self):
        """
        RED: Verify PresetManager.list_builtins() returns built-in presets.

        Given: PresetManager instance
        When: We call list_builtins()
        Then: Should return dict with quality, speed, balanced

        Expected RED failure: AttributeError or KeyError
        """
        # Given
        try:
            from data_extract.cli.config.presets import PresetManager
        except ImportError as e:
            pytest.fail(f"Cannot import PresetManager: {e}")

        manager = PresetManager()

        # When
        builtins = manager.list_builtins()

        # Then
        assert isinstance(builtins, dict)
        assert "quality" in builtins
        assert "speed" in builtins
        assert "balanced" in builtins

    def test_builtin_presets_quality(self):
        """
        RED: Verify quality preset has correct values.

        Given: PresetManager with quality preset
        When: We retrieve the quality preset
        Then: Should have strict validation and high quality threshold

        Expected RED failure: KeyError or AttributeError
        """
        # Given
        try:
            from data_extract.cli.config.presets import PresetManager
        except ImportError as e:
            pytest.fail(f"Cannot import PresetManager: {e}")

        manager = PresetManager()
        builtins = manager.list_builtins()

        # When
        quality_preset = builtins.get("quality")

        # Then
        assert quality_preset is not None
        assert quality_preset.name == "quality"
        # Quality preset should prioritize quality
        assert quality_preset.quality_threshold >= 0.8
        assert quality_preset.validation_level.value == "strict"

    def test_builtin_presets_speed(self):
        """
        RED: Verify speed preset has correct values.

        Given: PresetManager with speed preset
        When: We retrieve the speed preset
        Then: Should have minimal validation and larger chunks

        Expected RED failure: KeyError or AttributeError
        """
        # Given
        try:
            from data_extract.cli.config.presets import PresetManager
        except ImportError as e:
            pytest.fail(f"Cannot import PresetManager: {e}")

        manager = PresetManager()
        builtins = manager.list_builtins()

        # When
        speed_preset = builtins.get("speed")

        # Then
        assert speed_preset is not None
        assert speed_preset.name == "speed"
        # Speed preset should prioritize speed
        assert speed_preset.chunk_size >= 1000
        assert speed_preset.validation_level.value == "minimal"

    def test_builtin_presets_balanced(self):
        """
        RED: Verify balanced preset has correct values.

        Given: PresetManager with balanced preset
        When: We retrieve the balanced preset
        Then: Should have standard validation and medium values

        Expected RED failure: KeyError or AttributeError
        """
        # Given
        try:
            from data_extract.cli.config.presets import PresetManager
        except ImportError as e:
            pytest.fail(f"Cannot import PresetManager: {e}")

        manager = PresetManager()
        builtins = manager.list_builtins()

        # When
        balanced_preset = builtins.get("balanced")

        # Then
        assert balanced_preset is not None
        assert balanced_preset.name == "balanced"
        # Balanced should be in middle ranges
        assert 400 < balanced_preset.chunk_size < 700
        assert balanced_preset.validation_level.value == "standard"

    def test_preset_manager_list_custom(self, tmp_path, monkeypatch):
        """
        RED: Verify PresetManager.list_custom() returns user presets.

        Given: PresetManager with custom preset directory
        When: We call list_custom()
        Then: Should return list of custom presets

        Expected RED failure: AttributeError or FileNotFoundError
        """
        # Given
        monkeypatch.setenv("HOME", str(tmp_path))

        try:
            from data_extract.cli.config.presets import PresetManager
        except ImportError as e:
            pytest.fail(f"Cannot import PresetManager: {e}")

        manager = PresetManager()

        # When
        custom_presets = manager.list_custom()

        # Then
        assert isinstance(custom_presets, (dict, list))
        # Initially should be empty or provide meaningful response

    def test_preset_manager_save_preset(self, tmp_path, monkeypatch):
        """
        RED: Verify PresetManager.save() creates preset file.

        Given: PresetManager and PresetConfig instance
        When: We call save() with a preset
        Then: Should create YAML file in preset directory

        Expected RED failure: AttributeError or FileNotFoundError
        """
        # Given
        monkeypatch.setenv("HOME", str(tmp_path))

        try:
            from data_extract.cli.config.models import PresetConfig, ValidationLevel
            from data_extract.cli.config.presets import PresetManager
        except ImportError as e:
            pytest.fail(f"Cannot import required modules: {e}")

        manager = PresetManager()
        preset = PresetConfig(
            name="custom_test",
            description="Test custom preset",
            chunk_size=512,
            quality_threshold=0.75,
            output_format="json",
            dedup_threshold=0.8,
            include_metadata=True,
            validation_level=ValidationLevel.STANDARD,
        )

        # When
        try:
            manager.save(preset)
        except Exception as e:
            pytest.fail(f"Cannot save preset: {e}")

        # Then
        preset_dir = manager.get_directory()
        assert (preset_dir / "custom_test.yaml").exists() or (
            preset_dir / "custom_test.yml"
        ).exists()

    def test_preset_manager_load_preset(self, tmp_path, monkeypatch):
        """
        RED: Verify PresetManager.load() loads preset from file.

        Given: PresetManager and saved preset file
        When: We call load() with preset name
        Then: Should return PresetConfig instance

        Expected RED failure: AttributeError or FileNotFoundError
        """
        # Given
        monkeypatch.setenv("HOME", str(tmp_path))

        try:
            from data_extract.cli.config.models import PresetConfig, ValidationLevel
            from data_extract.cli.config.presets import PresetManager
        except ImportError as e:
            pytest.fail(f"Cannot import required modules: {e}")

        manager = PresetManager()
        original_preset = PresetConfig(
            name="load_test",
            description="Test loading preset",
            chunk_size=512,
            quality_threshold=0.75,
            output_format="json",
            dedup_threshold=0.8,
            include_metadata=True,
            validation_level=ValidationLevel.STANDARD,
        )

        # Save first
        manager.save(original_preset)

        # When
        try:
            loaded_preset = manager.load("load_test")
        except Exception as e:
            pytest.fail(f"Cannot load preset: {e}")

        # Then
        assert loaded_preset is not None
        assert loaded_preset.name == "load_test"
        assert loaded_preset.chunk_size == 512

    def test_builtin_presets_immutable(self):
        """
        RED: Verify built-in presets cannot be overwritten.

        Given: PresetManager with built-in preset
        When: We try to save over a built-in preset
        Then: Should raise error or prevent overwrite

        Expected RED failure: No protection mechanism
        """
        # Given
        try:
            from data_extract.cli.config.models import PresetConfig, ValidationLevel
            from data_extract.cli.config.presets import PresetManager
        except ImportError as e:
            pytest.fail(f"Cannot import required modules: {e}")

        manager = PresetManager()
        malicious_preset = PresetConfig(
            name="quality",  # Try to overwrite built-in
            description="Attempting to overwrite built-in",
            chunk_size=256,  # Use valid chunk_size to test overwrite protection
            quality_threshold=0.1,
            output_format="json",
            dedup_threshold=0.1,
            include_metadata=False,
            validation_level=ValidationLevel.MINIMAL,
        )

        # When/Then - should raise error or silently reject
        with pytest.raises(Exception):  # PermissionError or ValueError
            manager.save(malicious_preset, force=False)
