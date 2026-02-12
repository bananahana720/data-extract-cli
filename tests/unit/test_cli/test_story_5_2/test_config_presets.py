"""TDD RED Phase Tests: Preset System (AC-5.2-3, AC-5.2-5).

These tests verify:
- AC-5.2-3: Preset loading/saving commands functional
- AC-5.2-5: Journey 5 (Preset Configuration) operational

All tests are designed to FAIL initially (TDD RED phase).
"""

import pytest

# P1: Core functionality - run on PR
pytestmark = [
    pytest.mark.P1,
    pytest.mark.story_5_2,
    pytest.mark.unit,
    pytest.mark.presets,
    pytest.mark.cli,
]


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.presets
class TestPresetInfrastructureExists:
    """AC-5.2-3: Verify preset system infrastructure exists."""

    def test_load_preset_function_exists(self):
        """
        RED: Verify load_preset function exists.

        Given: The CLI config module
        When: We import load_preset
        Then: It should exist and accept preset name

        Expected RED failure: ImportError
        """
        # Given/When
        try:
            from data_extract.cli.config import load_preset
        except ImportError as e:
            pytest.fail(f"Cannot import load_preset: {e}")

        # Then - function should be callable
        assert callable(load_preset), "load_preset should be callable"

    def test_save_preset_function_exists(self):
        """
        RED: Verify save_preset function exists.

        Given: The CLI config module
        When: We import save_preset
        Then: It should exist and accept name and config

        Expected RED failure: ImportError
        """
        # Given/When
        try:
            from data_extract.cli.config import save_preset
        except ImportError as e:
            pytest.fail(f"Cannot import save_preset: {e}")

        # Then
        assert callable(save_preset), "save_preset should be callable"

    def test_list_presets_function_exists(self):
        """
        RED: Verify list_presets function exists.

        Given: The CLI config module
        When: We import list_presets
        Then: It should return list of available presets

        Expected RED failure: ImportError
        """
        # Given/When
        try:
            from data_extract.cli.config import list_presets
        except ImportError as e:
            pytest.fail(f"Cannot import list_presets: {e}")

        # Then
        assert callable(list_presets), "list_presets should be callable"

    def test_presets_directory_constant_exists(self):
        """
        RED: Verify PRESETS_DIR constant is defined.

        Given: The CLI config module
        When: We import PRESETS_DIR
        Then: It should be ~/.data-extract/presets/

        Expected RED failure: ImportError or wrong path
        """
        # Given/When
        try:
            from data_extract.cli.config import PRESETS_DIR
        except ImportError as e:
            pytest.fail(f"Cannot import PRESETS_DIR: {e}")

        # Then
        assert (
            "presets" in str(PRESETS_DIR).lower()
        ), f"PRESETS_DIR should contain 'presets', got: {PRESETS_DIR}"


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.presets
class TestBuiltInPresets:
    """AC-5.2-3: Test built-in presets are available."""

    @pytest.mark.parametrize(
        "preset_name",
        [
            "audit-standard",
            "rag-optimized",
            "quick-scan",
        ],
    )
    def test_built_in_preset_exists(self, preset_name: str):
        """
        RED: Test built-in preset is available.

        Given: A built-in preset name
        When: We load the preset
        Then: It should return valid configuration

        Expected RED failure: Preset not found or load error
        """
        # Given/When
        try:
            from data_extract.cli.config import load_preset

            preset = load_preset(preset_name)
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")
        except FileNotFoundError:
            pytest.fail(f"Built-in preset '{preset_name}' not found")

        # Then
        assert preset is not None, f"Preset '{preset_name}' should not be None"
        assert (
            hasattr(preset, "semantic") or "semantic" in preset
        ), f"Preset '{preset_name}' should have semantic config"

    def test_audit_standard_preset_values(self, preset_corpus):
        """
        RED: Test audit-standard preset has correct values.

        Given: The audit-standard preset
        When: We load it
        Then: It should have expected configuration values

        Expected RED failure: Wrong values or structure
        """
        # Given
        expected = preset_corpus["audit-standard"]

        # When
        try:
            from data_extract.cli.config import load_preset

            actual = load_preset("audit-standard")
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then - check key values
        if hasattr(actual, "semantic"):
            # Object-based config
            assert actual.semantic.tfidf.max_features == 5000
            assert actual.semantic.similarity.duplicate_threshold == 0.95
        else:
            # Dict-based config
            assert actual["semantic"]["tfidf"]["max_features"] == 5000

    def test_rag_optimized_preset_has_smaller_chunks(self, preset_corpus):
        """
        RED: Test rag-optimized preset has smaller chunk settings.

        Given: The rag-optimized preset
        When: We load it
        Then: It should have smaller max_tokens for RAG use

        Expected RED failure: Wrong chunk configuration
        """
        # Given
        expected = preset_corpus["rag-optimized"]

        # When
        try:
            from data_extract.cli.config import load_preset

            actual = load_preset("rag-optimized")
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        if hasattr(actual, "chunk"):
            assert (
                actual.chunk.max_tokens == 256
            ), f"RAG preset should have max_tokens=256, got: {actual.chunk.max_tokens}"
        else:
            assert actual["chunk"]["max_tokens"] == 256

    def test_quick_scan_preset_disables_cache(self, preset_corpus):
        """
        RED: Test quick-scan preset disables caching.

        Given: The quick-scan preset
        When: We load it
        Then: cache.enabled should be False

        Expected RED failure: Cache not disabled
        """
        # When
        try:
            from data_extract.cli.config import load_preset

            actual = load_preset("quick-scan")
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        if hasattr(actual, "semantic"):
            cache_config = getattr(actual.semantic, "cache", None)
            if cache_config:
                assert cache_config.enabled is False
        else:
            cache = actual.get("semantic", {}).get("cache", {})
            assert cache.get("enabled") is False, "quick-scan should disable cache"


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.presets
class TestPresetLoading:
    """AC-5.2-3: Test preset loading functionality."""

    def test_load_preset_from_user_directory(self, mock_home_directory):
        """
        RED: Test loading custom preset from ~/.data-extract/presets/.

        Given: A custom preset file exists in presets directory
        When: We load the preset by name
        Then: Configuration should be loaded

        Expected RED failure: Custom preset not found
        """
        # Given
        mock_home_directory.create_preset(
            "my-custom-preset",
            {
                "semantic": {
                    "tfidf": {"max_features": 9999},
                },
            },
        )

        # When
        try:
            from data_extract.cli.config import load_preset

            preset = load_preset("my-custom-preset")
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        if hasattr(preset, "semantic"):
            assert preset.semantic.tfidf.max_features == 9999
        else:
            assert preset["semantic"]["tfidf"]["max_features"] == 9999

    def test_load_nonexistent_preset_raises_error(self):
        """
        RED: Test loading nonexistent preset raises clear error.

        Given: A preset name that doesn't exist
        When: We try to load it
        Then: PresetNotFoundError or similar should be raised

        Expected RED failure: Wrong error type or no error
        """
        # Given
        nonexistent_name = "this-preset-does-not-exist"

        # When/Then
        try:
            from data_extract.cli.config import PresetNotFoundError, load_preset

            preset_not_found_error = PresetNotFoundError
        except ImportError:
            # Try alternative exception
            try:
                from data_extract.cli.config import load_preset

                preset_not_found_error = FileNotFoundError
            except ImportError as e:
                pytest.fail(f"Cannot import: {e}")

        with pytest.raises((preset_not_found_error, FileNotFoundError)) as exc_info:
            load_preset(nonexistent_name)

        assert nonexistent_name in str(
            exc_info.value
        ), f"Error should mention preset name: {exc_info.value}"

    def test_load_preset_with_preset_flag(self, mock_home_directory, typer_cli_runner):
        """
        RED: Test --preset flag loads preset configuration.

        Given: A preset exists
        When: CLI is invoked with --preset=<name>
        Then: Preset configuration should be applied

        Expected RED failure: --preset flag not implemented
        """
        # Given
        mock_home_directory.create_preset(
            "test-preset",
            {"semantic": {"tfidf": {"max_features": 7777}}},
        )

        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(
                app,
                ["config", "show", "--preset", "test-preset"],
            )
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "7777" in result.output, f"Preset value should be shown: {result.output}"


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.presets
class TestPresetSaving:
    """AC-5.2-3: Test preset saving functionality."""

    def test_save_preset_creates_file(self, mock_home_directory):
        """
        RED: Test save_preset creates file in presets directory.

        Given: A configuration to save
        When: save_preset is called
        Then: File should be created in ~/.data-extract/presets/

        Expected RED failure: File not created
        """
        # Given
        config = {
            "semantic": {
                "tfidf": {"max_features": 8888},
            },
        }

        # When
        try:
            from data_extract.cli.config import save_preset

            save_preset("my-saved-preset", config)
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        preset_file = mock_home_directory.presets_dir / "my-saved-preset.yaml"
        assert preset_file.exists(), f"Preset file should be created at {preset_file}"

    def test_saved_preset_can_be_loaded(self, mock_home_directory):
        """
        RED: Test saved preset can be loaded back.

        Given: A preset is saved
        When: We load it back
        Then: Configuration should match

        Expected RED failure: Round-trip fails
        """
        # Given
        config = {
            "semantic": {
                "tfidf": {"max_features": 6666},
            },
        }

        # When
        try:
            from data_extract.cli.config import load_preset, save_preset

            save_preset("roundtrip-test", config)
            loaded = load_preset("roundtrip-test")
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        if hasattr(loaded, "semantic"):
            assert loaded.semantic.tfidf.max_features == 6666
        else:
            assert loaded["semantic"]["tfidf"]["max_features"] == 6666

    def test_save_preset_overwrites_existing(self, mock_home_directory):
        """
        RED: Test save_preset overwrites existing preset.

        Given: A preset already exists
        When: save_preset is called with same name
        Then: Preset should be updated

        Expected RED failure: Original values remain
        """
        # Given
        mock_home_directory.create_preset(
            "overwrite-test",
            {"semantic": {"tfidf": {"max_features": 1111}}},
        )

        new_config = {"semantic": {"tfidf": {"max_features": 2222}}}

        # When
        try:
            from data_extract.cli.config import load_preset, save_preset

            save_preset("overwrite-test", new_config)
            loaded = load_preset("overwrite-test")
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        if hasattr(loaded, "semantic"):
            assert loaded.semantic.tfidf.max_features == 2222
        else:
            assert loaded["semantic"]["tfidf"]["max_features"] == 2222


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.presets
class TestPresetListCommand:
    """AC-5.2-3, AC-5.2-5: Test preset listing functionality."""

    def test_list_presets_returns_built_in(self):
        """
        RED: Test list_presets includes built-in presets.

        Given: The preset system
        When: list_presets is called
        Then: Built-in presets should be included

        Expected RED failure: Built-in presets not listed
        """
        # When
        try:
            from data_extract.cli.config import list_presets

            presets = list_presets()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        preset_names = [p["name"] if isinstance(p, dict) else p for p in presets]
        assert "audit-standard" in preset_names, "audit-standard should be listed"
        assert "rag-optimized" in preset_names, "rag-optimized should be listed"
        assert "quick-scan" in preset_names, "quick-scan should be listed"

    def test_list_presets_includes_custom(self, mock_home_directory):
        """
        RED: Test list_presets includes custom user presets.

        Given: A custom preset exists
        When: list_presets is called
        Then: Custom preset should be included

        Expected RED failure: Custom preset not listed
        """
        # Given
        mock_home_directory.create_preset(
            "my-custom",
            {"semantic": {"tfidf": {"max_features": 5000}}},
        )

        # When
        try:
            from data_extract.cli.config import list_presets

            presets = list_presets()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        preset_names = [p["name"] if isinstance(p, dict) else p for p in presets]
        assert "my-custom" in preset_names, "Custom preset should be listed"

    def test_list_presets_distinguishes_builtin_custom(self, mock_home_directory):
        """
        RED: Test list_presets indicates if preset is built-in or custom.

        Given: Both built-in and custom presets exist
        When: list_presets is called
        Then: Each preset should indicate its type

        Expected RED failure: No type indication
        """
        # Given
        mock_home_directory.create_preset(
            "custom-preset",
            {"semantic": {"tfidf": {"max_features": 5000}}},
        )

        # When
        try:
            from data_extract.cli.config import list_presets

            presets = list_presets()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then - presets should have type info
        for preset in presets:
            if isinstance(preset, dict):
                assert (
                    "type" in preset or "is_builtin" in preset
                ), f"Preset should indicate type: {preset}"
            else:
                # Simple list - check we can distinguish somehow
                pass


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.presets
class TestPresetCLICommands:
    """AC-5.2-3: Test preset CLI commands."""

    def test_config_presets_command_exists(self, typer_cli_runner):
        """
        RED: Test 'data-extract config presets list' command exists.

        Given: The CLI app
        When: We invoke 'config presets list'
        Then: It should list available presets

        Expected RED failure: Command not found
        """
        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "presets", "list"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "quality" in result.output, f"Should list built-in presets: {result.output}"

    def test_config_save_command_exists(self, typer_cli_runner, mock_home_directory):
        """
        Test 'data-extract config presets save <name>' command exists.

        Given: The CLI app
        When: We invoke 'config save my-preset'
        Then: Current config should be saved as preset

        Expected RED failure: Command not found
        """
        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "presets", "save", "test-save"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert (
            "saved" in result.output.lower() or "created" in result.output.lower()
        ), f"Should confirm save: {result.output}"

    def test_config_load_command_exists(self, typer_cli_runner):
        """
        Test 'data-extract config presets load <name>' command exists.

        Given: The CLI app
        When: We invoke 'config load audit-standard'
        Then: Preset should be loaded and shown

        Expected RED failure: Command not found
        """
        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "presets", "load", "quality"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code == 0, f"Command failed: {result.output}"
        # Should show loaded config
        assert (
            "audit" in result.output.lower() or "loaded" in result.output.lower()
        ), f"Should confirm load: {result.output}"


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.presets
class TestJourney5PresetConfiguration:
    """AC-5.2-5: Test Journey 5 (Preset Configuration) from UX Design Spec."""

    def test_journey5_list_presets(self, typer_cli_runner):
        """
        RED: Journey 5 Step 1 - List available presets.

        Given: User wants to see available presets
        When: 'data-extract config presets list' is run
        Then: Formatted list of presets with descriptions shown

        Expected RED failure: Rich output not implemented
        """
        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "presets", "list"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then - should have formatted output
        assert result.exit_code == 0
        # Check for Rich-formatted output indicators
        assert (
            "built-in" in result.output.lower() or "quality" in result.output.lower()
        ), f"Should show preset list: {result.output}"
        # Should include descriptions
        assert (
            "quality" in result.output.lower() or "speed" in result.output.lower()
        ), f"Should show preset descriptions: {result.output}"

    def test_journey5_create_custom_preset(self, typer_cli_runner, mock_home_directory):
        """
        Journey 5 Step 2 - Create custom preset from current config.

        Given: User has a configuration they want to save
        When: 'data-extract config save "quarterly-audit"' is run
        Then: Custom preset is created

        Expected RED failure: Custom preset creation not working
        """
        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "presets", "save", "quarterly-audit"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Verify preset was created
        preset_file = mock_home_directory.presets_dir / "quarterly-audit.yaml"
        assert preset_file.exists(), "Custom preset file should be created"

    def test_journey5_apply_preset_with_flag(self, typer_cli_runner, mock_home_directory):
        """
        RED: Journey 5 Step 3 - Apply preset via --preset flag.

        Given: A preset exists (built-in or custom)
        When: 'data-extract process ./docs/ --preset=quarterly-audit' is run
        Then: Preset configuration is applied to processing

        Expected RED failure: --preset flag not passed to processing
        """
        # Given
        mock_home_directory.create_preset(
            "quarterly-audit",
            {
                "semantic": {"tfidf": {"max_features": 4000}},
                "chunk": {"max_tokens": 300},
            },
        )

        # When - test with config show to verify preset is applied
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "show", "--preset", "quarterly-audit"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code == 0, f"Command failed: {result.output}"
        # Preset values should be shown
        assert (
            "4000" in result.output or "300" in result.output
        ), f"Preset values should be applied: {result.output}"

    def test_journey5_rich_formatted_preset_list(self, typer_cli_runner):
        """
        RED: Journey 5 - Verify Rich-formatted preset list.

        Given: The config presets list command
        When: Run in terminal
        Then: Should show Rich-formatted panel with categories

        Expected RED failure: Plain text instead of Rich output

        UX Design Spec format:
        +-- Available Presets --+
        | Built-in:             |
        |   * audit-standard    |
        |   * rag-optimized     |
        | Custom:               |
        |   * my-workflow       |
        +-----------------------+
        """
        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "presets", "list"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then - check for structured output
        assert result.exit_code == 0
        output = result.output

        # Should have some form of categorization
        has_categories = (
            ("Built-in" in output or "built-in" in output)
            or ("Custom" in output or "custom" in output)
            or ("PRESET" in output.upper())
        )
        assert has_categories, f"Should categorize presets: {output}"
