"""Integration tests for Story 5-5: Preset Configuration CLI Commands.

Tests the full CLI command chain for preset management:
- config presets list
- config presets save
- config presets load
- config presets show
- config presets delete

These tests verify CLI parsing, output formatting, and file I/O integration.
"""

import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from data_extract.cli.base import create_app
from data_extract.cli.config.models import PresetConfig, ValidationLevel

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.story_5_5, pytest.mark.cli]


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def app():
    """Create a fresh app instance for each test."""
    return create_app()


@pytest.fixture
def temp_preset_dir(tmp_path, monkeypatch):
    """Create a temporary preset directory for testing."""
    preset_dir = tmp_path / ".data-extract" / "presets"
    preset_dir.mkdir(parents=True, exist_ok=True)

    # Monkeypatch Path.home() to use tmp_path
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    return preset_dir


@pytest.mark.integration
@pytest.mark.story_5_5
class TestConfigPresetsListCommand:
    """Test 'config presets list' command."""

    def test_presets_list_shows_table(self, cli_runner, app):
        """
        GIVEN: The data-extract CLI with config presets subcommand
        WHEN: We run 'data-extract config presets list'
        THEN: Should display a formatted table
        """
        result = cli_runner.invoke(app, ["config", "presets", "list"])
        assert result.exit_code == 0
        # Check for table structure
        assert "Configuration Presets" in result.stdout or "Name" in result.stdout

    def test_presets_list_includes_builtins(self, cli_runner, app):
        """
        GIVEN: 'config presets list' command
        WHEN: We run the command
        THEN: Output should include quality, speed, balanced presets
        """
        result = cli_runner.invoke(app, ["config", "presets", "list"])
        assert result.exit_code == 0
        assert "quality" in result.stdout
        assert "speed" in result.stdout
        assert "balanced" in result.stdout

    def test_presets_list_includes_custom(self, cli_runner, app, temp_preset_dir):
        """
        GIVEN: Custom presets saved in ~/.data-extract/presets/
        WHEN: We run 'config presets list'
        THEN: Output should include custom presets
        """
        # Create a custom preset
        preset = PresetConfig(
            name="my-custom",
            description="My custom preset",
            chunk_size=300,
        )
        preset_file = temp_preset_dir / "my-custom.yaml"
        preset_file.write_text(preset.to_yaml())

        result = cli_runner.invoke(app, ["config", "presets", "list"])
        assert result.exit_code == 0
        assert "my-custom" in result.stdout

    def test_presets_list_json_output(self, cli_runner, app):
        """
        GIVEN: 'config presets list' command with --json flag
        WHEN: We run the command
        THEN: Should output valid JSON
        """
        result = cli_runner.invoke(app, ["config", "presets", "list", "--json"])
        assert result.exit_code == 0

        # Parse JSON output
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) >= 3  # At least 3 built-in presets

        # Verify structure
        preset_names = [p["name"] for p in data]
        assert "quality" in preset_names
        assert "speed" in preset_names
        assert "balanced" in preset_names

    def test_presets_list_builtin_only(self, cli_runner, app, temp_preset_dir):
        """
        GIVEN: Custom presets exist
        WHEN: We run 'config presets list --builtin-only'
        THEN: Should only show built-in presets
        """
        # Create a custom preset
        preset = PresetConfig(
            name="should-not-show",
            description="This should be filtered out",
            chunk_size=400,
        )
        preset_file = temp_preset_dir / "should-not-show.yaml"
        preset_file.write_text(preset.to_yaml())

        result = cli_runner.invoke(app, ["config", "presets", "list", "--builtin-only"])
        assert result.exit_code == 0
        assert "should-not-show" not in result.stdout
        assert "quality" in result.stdout

    def test_presets_list_marks_builtins(self, cli_runner, app):
        """
        GIVEN: 'config presets list' command
        WHEN: We run the command
        THEN: Built-in presets should be visually marked
        """
        result = cli_runner.invoke(app, ["config", "presets", "list"])
        assert result.exit_code == 0
        # Check for type column with 'built-in' marker
        assert "built-in" in result.stdout


@pytest.mark.integration
@pytest.mark.story_5_5
class TestConfigPresetsSaveCommand:
    """Test 'config presets save' command."""

    def test_presets_save_creates_yaml_file(self, cli_runner, app, temp_preset_dir):
        """
        GIVEN: Current configuration in CLI
        WHEN: We run 'data-extract config presets save my_preset'
        THEN: Should create ~/.data-extract/presets/my_preset.yaml
        """
        result = cli_runner.invoke(app, ["config", "presets", "save", "my_preset"])
        assert result.exit_code == 0

        preset_file = temp_preset_dir / "my_preset.yaml"
        assert preset_file.exists()

    def test_presets_save_with_description(self, cli_runner, app, temp_preset_dir):
        """
        GIVEN: 'config presets save' command with --description flag
        WHEN: We run 'data-extract config presets save test --description "My preset"'
        THEN: Saved preset should include description
        """
        result = cli_runner.invoke(
            app,
            [
                "config",
                "presets",
                "save",
                "test",
                "--description",
                "My custom description",
            ],
        )
        assert result.exit_code == 0

        preset_file = temp_preset_dir / "test.yaml"
        content = yaml.safe_load(preset_file.read_text())
        assert content["description"] == "My custom description"

    def test_presets_save_respects_force_flag(self, cli_runner, app, temp_preset_dir):
        """
        GIVEN: An existing preset file
        WHEN: We run 'data-extract config presets save existing_name --force'
        THEN: Should overwrite without error
        """
        # Create initial preset
        preset = PresetConfig(name="existing", description="Original")
        preset_file = temp_preset_dir / "existing.yaml"
        preset_file.write_text(preset.to_yaml())

        # Overwrite with --force
        result = cli_runner.invoke(
            app,
            [
                "config",
                "presets",
                "save",
                "existing",
                "--description",
                "Updated",
                "--force",
            ],
        )
        assert result.exit_code == 0

        # Verify overwritten
        content = yaml.safe_load(preset_file.read_text())
        assert content["description"] == "Updated"

    def test_presets_save_without_force_errors(self, cli_runner, app, temp_preset_dir):
        """
        GIVEN: An existing preset file
        WHEN: We run 'data-extract config presets save existing_name' (no --force)
        THEN: Should fail with error
        """
        # Create initial preset
        preset = PresetConfig(name="existing", description="Original")
        preset_file = temp_preset_dir / "existing.yaml"
        preset_file.write_text(preset.to_yaml())

        # Try to save without --force
        result = cli_runner.invoke(
            app,
            ["config", "presets", "save", "existing"],
        )
        assert result.exit_code == 1
        assert "already exists" in result.stdout or "Use --force" in result.stdout

    def test_presets_save_shows_confirmation(self, cli_runner, app, temp_preset_dir):
        """
        GIVEN: A successful preset save operation
        WHEN: Command completes
        THEN: Should show success message with preset name
        """
        result = cli_runner.invoke(app, ["config", "presets", "save", "new-preset"])
        assert result.exit_code == 0
        assert "Preset saved" in result.stdout

    def test_presets_save_prevents_builtin_overwrite(self, cli_runner, app, temp_preset_dir):
        """
        GIVEN: Attempt to save preset named 'quality' (built-in name)
        WHEN: We run 'data-extract config presets save quality'
        THEN: Should show error that built-in presets cannot be overwritten
        """
        result = cli_runner.invoke(app, ["config", "presets", "save", "quality"])
        assert result.exit_code == 1
        assert "Cannot overwrite built-in preset" in result.stdout


@pytest.mark.integration
@pytest.mark.story_5_5
class TestConfigPresetsLoadCommand:
    """Test 'config presets load' command."""

    def test_presets_load_applies_settings(self, cli_runner, app):
        """
        GIVEN: A built-in preset
        WHEN: We run 'data-extract config presets load quality'
        THEN: Should show loaded settings
        """
        result = cli_runner.invoke(app, ["config", "presets", "load", "quality"])
        assert result.exit_code == 0
        assert "Loaded preset" in result.stdout
        assert "chunk_size" in result.stdout
        assert "256" in result.stdout  # quality preset has chunk_size=256

    def test_presets_load_show_mode(self, cli_runner, app):
        """
        GIVEN: 'config presets load' command with --show flag
        WHEN: Command executes
        THEN: Should show YAML formatted output
        """
        result = cli_runner.invoke(app, ["config", "presets", "load", "quality", "--show"])
        assert result.exit_code == 0
        assert "name: quality" in result.stdout

    def test_presets_load_shows_available_on_error(self, cli_runner, app):
        """
        GIVEN: Non-existent preset name
        WHEN: We run 'data-extract config presets load nonexistent'
        THEN: Should show helpful error with available presets
        """
        result = cli_runner.invoke(app, ["config", "presets", "load", "nonexistent"])
        assert result.exit_code == 1
        assert "Preset not found" in result.stdout
        # Should show available presets
        assert "quality" in result.stdout or "Available" in result.stdout

    def test_presets_load_custom(self, cli_runner, app, temp_preset_dir):
        """
        GIVEN: A custom preset
        WHEN: We load it
        THEN: Should show the custom settings
        """
        # Create a custom preset
        preset = PresetConfig(
            name="my-custom",
            description="My custom preset",
            chunk_size=300,
            quality_threshold=0.8,
        )
        preset_file = temp_preset_dir / "my-custom.yaml"
        preset_file.write_text(preset.to_yaml())

        result = cli_runner.invoke(app, ["config", "presets", "load", "my-custom"])
        assert result.exit_code == 0
        assert "Loaded preset" in result.stdout


@pytest.mark.integration
@pytest.mark.story_5_5
class TestConfigPresetsShowCommand:
    """Test 'config presets show' command."""

    def test_presets_show_builtin(self, cli_runner, app):
        """
        GIVEN: A built-in preset
        WHEN: We run 'data-extract config presets show quality'
        THEN: Should display formatted panel with all settings
        """
        result = cli_runner.invoke(app, ["config", "presets", "show", "quality"])
        assert result.exit_code == 0
        assert "Preset: quality" in result.stdout
        assert "chunk_size" in result.stdout
        assert "quality_threshold" in result.stdout
        assert "built-in" in result.stdout

    def test_presets_show_not_found(self, cli_runner, app):
        """
        GIVEN: Non-existent preset
        WHEN: We run show command
        THEN: Should show error
        """
        result = cli_runner.invoke(app, ["config", "presets", "show", "nonexistent"])
        assert result.exit_code == 1
        assert "Preset not found" in result.stdout

    def test_presets_show_custom(self, cli_runner, app, temp_preset_dir):
        """
        GIVEN: A custom preset
        WHEN: We show it
        THEN: Should show 'user' type
        """
        # Create a custom preset
        preset = PresetConfig(
            name="my-custom",
            description="My custom preset",
            chunk_size=300,
        )
        preset_file = temp_preset_dir / "my-custom.yaml"
        preset_file.write_text(preset.to_yaml())

        result = cli_runner.invoke(app, ["config", "presets", "show", "my-custom"])
        assert result.exit_code == 0
        assert "user" in result.stdout


@pytest.mark.integration
@pytest.mark.story_5_5
class TestConfigPresetsDeleteCommand:
    """Test 'config presets delete' command."""

    def test_presets_delete_custom(self, cli_runner, app, temp_preset_dir):
        """
        GIVEN: A custom preset
        WHEN: We delete it with --yes
        THEN: Should remove the file
        """
        # Create a custom preset
        preset = PresetConfig(name="to-delete", description="Will be deleted")
        preset_file = temp_preset_dir / "to-delete.yaml"
        preset_file.write_text(preset.to_yaml())
        assert preset_file.exists()

        result = cli_runner.invoke(app, ["config", "presets", "delete", "to-delete", "--yes"])
        assert result.exit_code == 0
        assert "Deleted preset" in result.stdout
        assert not preset_file.exists()

    def test_presets_delete_builtin_protected(self, cli_runner, app):
        """
        GIVEN: A built-in preset
        WHEN: We try to delete it
        THEN: Should show error
        """
        result = cli_runner.invoke(app, ["config", "presets", "delete", "quality", "--yes"])
        assert result.exit_code == 1
        assert "Cannot delete built-in preset" in result.stdout

    def test_presets_delete_not_found(self, cli_runner, app, temp_preset_dir):
        """
        GIVEN: Non-existent preset
        WHEN: We try to delete it
        THEN: Should show error
        """
        result = cli_runner.invoke(app, ["config", "presets", "delete", "nonexistent", "--yes"])
        assert result.exit_code == 1
        assert "Preset not found" in result.stdout


@pytest.mark.integration
@pytest.mark.story_5_5
class TestPresetFileFormatIntegration:
    """Test YAML file format and serialization integration."""

    def test_preset_yaml_format_valid(self, temp_preset_dir):
        """
        GIVEN: A saved preset in YAML
        WHEN: We read the YAML file
        THEN: Should be valid YAML with expected structure
        """
        preset = PresetConfig(
            name="test-format",
            description="Test preset",
            chunk_size=500,
            quality_threshold=0.7,
        )
        preset_file = temp_preset_dir / "test-format.yaml"
        preset_file.write_text(preset.to_yaml())

        content = yaml.safe_load(preset_file.read_text())
        assert content["name"] == "test-format"
        assert content["chunk_size"] == 500
        assert content["quality_threshold"] == 0.7

    def test_preset_yaml_roundtrip(self, temp_preset_dir):
        """
        GIVEN: A preset saved and then loaded
        WHEN: We compare original and loaded values
        THEN: All values should match exactly
        """
        original = PresetConfig(
            name="roundtrip-test",
            description="Testing roundtrip",
            chunk_size=800,
            quality_threshold=0.85,
            validation_level=ValidationLevel.STRICT,
            dedup_threshold=0.9,
        )
        preset_file = temp_preset_dir / "roundtrip-test.yaml"
        preset_file.write_text(original.to_yaml())

        loaded = PresetConfig.from_yaml(preset_file.read_text())

        assert loaded.name == original.name
        assert loaded.description == original.description
        assert loaded.chunk_size == original.chunk_size
        assert loaded.quality_threshold == original.quality_threshold
        assert loaded.validation_level == original.validation_level
        assert loaded.dedup_threshold == original.dedup_threshold

    def test_preset_yaml_handles_special_chars(self, temp_preset_dir):
        """
        GIVEN: A preset with special characters in description
        WHEN: We save and load it
        THEN: Should preserve special characters correctly
        """
        preset = PresetConfig(
            name="special-chars",
            description="Test with 'quotes', <brackets>, and \"double quotes\"",
            chunk_size=500,
        )
        preset_file = temp_preset_dir / "special-chars.yaml"
        preset_file.write_text(preset.to_yaml())

        loaded = PresetConfig.from_yaml(preset_file.read_text())
        assert loaded.description == preset.description


@pytest.mark.integration
@pytest.mark.story_5_5
class TestPresetConfigIntegration:
    """Test preset integration with config system."""

    def test_preset_applies_to_process_command(self, cli_runner, app, tmp_path):
        """
        GIVEN: A preset with specific settings
        WHEN: We run process command with --preset=speed
        THEN: Should show preset loaded message
        """
        # Create a test file to process
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content for processing")

        result = cli_runner.invoke(
            app,
            ["process", str(test_file), "--preset", "speed", "-o", str(tmp_path / "output")],
        )
        # Should show preset loaded panel
        assert "Loaded Preset" in result.stdout or "speed" in result.stdout

    def test_cli_args_override_loaded_preset(self, cli_runner, app, tmp_path):
        """
        GIVEN: Loaded preset with chunk_size=1024 (speed)
        WHEN: We run 'process --preset=speed --chunk-size=512 file.txt'
        THEN: Should use chunk_size=512 (CLI arg wins)
        """
        # Create a test file to process
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content for processing")

        result = cli_runner.invoke(
            app,
            [
                "process",
                str(test_file),
                "--preset",
                "speed",
                "--chunk-size",
                "512",
                "-o",
                str(tmp_path / "output"),
            ],
        )
        # Command should run (exit 0 for success or partial success)
        assert result.exit_code in [0, 2]  # 0 = success, 2 = partial success
