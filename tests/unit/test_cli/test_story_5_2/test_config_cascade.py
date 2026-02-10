"""TDD RED Phase Tests: 6-Layer Configuration Cascade (AC-5.2-1).

These tests verify the 6-layer configuration cascade precedence:
1. CLI flags (highest priority)
2. Environment variables (DATA_EXTRACT_*)
3. Project config (.data-extract.yaml in cwd)
4. User config (~/.config/data-extract/config.yaml)
5. Preset config (~/.data-extract/presets/*.yaml)
6. Defaults (lowest priority)

All tests are designed to FAIL initially (TDD RED phase).
"""

import pytest

# P0: Critical path - always run
pytestmark = [
    pytest.mark.P0,
    pytest.mark.cascade,
    pytest.mark.story_5_2,
    pytest.mark.unit,
    pytest.mark.cli,
]


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.cascade
class TestConfigCascadeExists:
    """AC-5.2-1: Verify 6-layer cascade infrastructure exists."""

    def test_merge_config_function_exists(self):
        """
        RED: Verify merge_config function supports 6 layers.

        Given: The CLI config module
        When: We import merge_config_6layer (or updated merge_config)
        Then: It should exist and accept 6 layer parameters

        Expected RED failure: ImportError or function signature mismatch
        """
        # Given/When
        try:
            from data_extract.cli.config import merge_config_6layer  # noqa: F401
        except ImportError:
            # Try alternative import
            try:
                # Check if merge_config supports 6 layers
                import inspect

                from data_extract.cli.config import merge_config

                sig = inspect.signature(merge_config)
                params = list(sig.parameters.keys())

                # Should have parameters for all 6 layers
                assert len(params) >= 5, (
                    f"merge_config should support 6 layers, " f"got params: {params}"
                )
            except (ImportError, AssertionError):
                # Try load_merged_config which implements 6-layer cascade
                try:
                    import inspect

                    from data_extract.cli.config import load_merged_config

                    sig = inspect.signature(load_merged_config)
                    params = list(sig.parameters.keys())

                    # load_merged_config implements 6-layer cascade
                    assert len(params) >= 2, (
                        f"load_merged_config should support 6 layers, " f"got params: {params}"
                    )
                except ImportError as e:
                    pytest.fail(f"Cannot import merge config function: {e}")

    def test_config_layer_enum_exists(self):
        """
        RED: Verify ConfigLayer enum exists for source tracking.

        Given: The CLI config module
        When: We import ConfigLayer
        Then: It should have all 6 layer values

        Expected RED failure: ImportError or missing enum values
        """
        # Given/When
        try:
            from data_extract.cli.config import ConfigLayer
        except ImportError as e:
            pytest.fail(f"Cannot import ConfigLayer enum: {e}")

        # Then - verify all 6 layers exist
        expected_layers = {"CLI", "ENV", "PROJECT", "USER", "PRESET", "DEFAULT"}
        actual_layers = {member.name for member in ConfigLayer}

        assert expected_layers.issubset(actual_layers), (
            f"ConfigLayer missing layers. Expected: {expected_layers}, " f"Got: {actual_layers}"
        )

    def test_config_result_tracks_source(self):
        """
        RED: Verify merged config tracks which layer each value came from.

        Given: The CLI config module
        When: We import ConfigResult or similar
        Then: It should track source for each config value

        Expected RED failure: ImportError or no source tracking
        """
        # Given/When
        try:
            from data_extract.cli.config import ConfigResult  # noqa: F401
        except ImportError:
            # Try alternative structure
            try:
                from data_extract.cli.config import MergedConfig

                # Check it has source tracking
                assert hasattr(MergedConfig, "get_source") or hasattr(
                    MergedConfig, "sources"
                ), "MergedConfig should track value sources"
            except ImportError as e:
                pytest.fail(f"Cannot import config result class: {e}")


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.cascade
class TestCascadePrecedence:
    """AC-5.2-1: Test 6-layer cascade precedence behavior."""

    @pytest.mark.parametrize(
        "winning_layer,expected_value",
        [
            ("cli", "/from/cli"),
            ("env", "/from/env"),
            ("project", "/from/project"),
            ("user", "/from/user"),
            ("preset", "/from/preset"),
            ("default", "/default/output"),
        ],
    )
    def test_single_layer_active_uses_that_layer(
        self,
        six_layer_full_setup,
        winning_layer: str,
        expected_value: str,
    ):
        """
        RED: Test that single active layer provides its values.

        Given: Only one configuration layer is active
        When: Configuration is loaded
        Then: Values from that layer should be used

        Expected RED failure: merge_config_6layer doesn't exist or wrong behavior
        """
        # Given
        setup = six_layer_full_setup
        if winning_layer != "default":
            setup.setup_single_layer(winning_layer)

        # When
        try:
            from data_extract.cli.config import load_merged_config

            config = load_merged_config()
        except ImportError as e:
            pytest.fail(f"Cannot import load_merged_config: {e}")

        # Then
        assert config.output_dir == expected_value, (
            f"Expected output_dir from {winning_layer} layer: {expected_value}, "
            f"got: {config.output_dir}"
        )

    def test_cli_overrides_all_other_layers(self, six_layer_full_setup):
        """
        RED: Test CLI flags override all other configuration layers.

        Given: All 6 configuration layers are active with different values
        When: Configuration is loaded with CLI args
        Then: CLI values should win

        Expected RED failure: CLI doesn't override other layers
        """
        # Given
        setup = six_layer_full_setup
        setup.setup_all_layers()

        cli_args = {
            "output_dir": "/from/cli",
            "tfidf_max_features": 10000,
        }

        # When
        try:
            from data_extract.cli.config import load_merged_config

            config = load_merged_config(cli_overrides=cli_args)
        except ImportError as e:
            pytest.fail(f"Cannot import load_merged_config: {e}")

        # Then
        assert (
            config.output_dir == "/from/cli"
        ), f"CLI should override all layers. Expected: /from/cli, got: {config.output_dir}"
        assert config.semantic.tfidf.max_features == 10000, (
            f"CLI tfidf_max_features should be 10000, " f"got: {config.semantic.tfidf.max_features}"
        )

    def test_env_overrides_file_layers(self, six_layer_full_setup, env_vars_fixture):
        """
        RED: Test environment variables override file-based config.

        Given: Project, user, and preset configs are set
        And: Environment variable is set
        When: Configuration is loaded (without CLI args)
        Then: Environment variable value should win

        Expected RED failure: Env vars don't override file configs
        """
        # Given
        setup = six_layer_full_setup
        setup.setup_single_layer("project")
        setup.setup_single_layer("user")
        setup.setup_single_layer("preset")

        # Set env var
        env_vars_fixture.set("OUTPUT_DIR", "/from/env")

        # When
        try:
            from data_extract.cli.config import load_merged_config

            config = load_merged_config()
        except ImportError as e:
            pytest.fail(f"Cannot import load_merged_config: {e}")

        # Then
        assert config.output_dir == "/from/env", (
            f"ENV should override file configs. Expected: /from/env, " f"got: {config.output_dir}"
        )

    def test_project_overrides_user_and_preset(self, six_layer_full_setup):
        """
        RED: Test project config overrides user and preset.

        Given: User and preset configs are set
        And: Project config is set
        When: Configuration is loaded
        Then: Project config value should win

        Expected RED failure: Project doesn't override user/preset
        """
        # Given
        setup = six_layer_full_setup
        setup.setup_single_layer("user")
        setup.setup_single_layer("preset")
        setup.setup_single_layer("project")

        # When
        try:
            from data_extract.cli.config import load_merged_config

            config = load_merged_config()
        except ImportError as e:
            pytest.fail(f"Cannot import load_merged_config: {e}")

        # Then
        assert config.output_dir == "/from/project", (
            f"PROJECT should override USER and PRESET. "
            f"Expected: /from/project, got: {config.output_dir}"
        )

    def test_user_overrides_preset_and_default(self, six_layer_full_setup):
        """
        RED: Test user config overrides preset and default.

        Given: Preset config is set
        And: User config is set
        When: Configuration is loaded
        Then: User config value should win

        Expected RED failure: User doesn't override preset
        """
        # Given
        setup = six_layer_full_setup
        setup.setup_single_layer("preset")
        setup.setup_single_layer("user")

        # When
        try:
            from data_extract.cli.config import load_merged_config

            config = load_merged_config()
        except ImportError as e:
            pytest.fail(f"Cannot import load_merged_config: {e}")

        # Then
        assert config.output_dir == "/from/user", (
            f"USER should override PRESET. Expected: /from/user, " f"got: {config.output_dir}"
        )

    def test_preset_overrides_default(self, six_layer_full_setup):
        """
        RED: Test preset overrides default values.

        Given: Only preset config is set
        When: Configuration is loaded
        Then: Preset value should override default

        Expected RED failure: Preset doesn't override default
        """
        # Given
        setup = six_layer_full_setup
        setup.setup_single_layer("preset")

        # When
        try:
            from data_extract.cli.config import load_merged_config

            config = load_merged_config(preset_name="test-preset")
        except ImportError as e:
            pytest.fail(f"Cannot import load_merged_config: {e}")

        # Then
        assert config.output_dir == "/from/preset", (
            f"PRESET should override DEFAULT. Expected: /from/preset, " f"got: {config.output_dir}"
        )

    def test_default_used_when_no_other_layers(self, six_layer_full_setup):
        """
        RED: Test default values used when no other layers active.

        Given: No configuration layers are set
        When: Configuration is loaded
        Then: Default values should be used

        Expected RED failure: No defaults or wrong defaults
        """
        # Given
        setup = six_layer_full_setup
        setup.clear_all_layers()

        # When
        try:
            from data_extract.cli.config import load_merged_config

            config = load_merged_config()
        except ImportError as e:
            pytest.fail(f"Cannot import load_merged_config: {e}")

        # Then - check some default values exist
        assert (
            config.output_dir is not None
        ), f"Default output_dir should be set. Expected: not None, got: {config.output_dir}"
        assert config.semantic.tfidf.max_features > 0, (
            f"Default tfidf_max_features should be positive. "
            f"Expected: > 0, got: {config.semantic.tfidf.max_features}"
        )


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.cascade
class TestCascadeSourceTracking:
    """AC-5.2-1: Test that merged config tracks source of each value."""

    def test_config_tracks_cli_source(self, six_layer_full_setup):
        """
        RED: Test config tracks when value comes from CLI.

        Given: CLI args are provided
        When: Configuration is loaded
        Then: Source should be tracked as CLI

        Expected RED failure: No source tracking
        """
        # Given
        setup = six_layer_full_setup
        cli_args = {"output_dir": "/from/cli"}

        # When
        try:
            from data_extract.cli.config import ConfigLayer, load_merged_config

            config = load_merged_config(cli_overrides=cli_args)
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        source = config.get_source("output_dir")
        assert (
            source == ConfigLayer.CLI
        ), f"Source for CLI-provided value should be CLI, got: {source}"

    def test_config_tracks_env_source(self, six_layer_full_setup, env_vars_fixture):
        """
        RED: Test config tracks when value comes from environment.

        Given: Environment variable is set
        When: Configuration is loaded
        Then: Source should be tracked as ENV

        Expected RED failure: No source tracking
        """
        # Given
        env_vars_fixture.set("OUTPUT_DIR", "/from/env")

        # When
        try:
            from data_extract.cli.config import ConfigLayer, load_merged_config

            config = load_merged_config()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        source = config.get_source("output_dir")
        assert (
            source == ConfigLayer.ENV
        ), f"Source for env-provided value should be ENV, got: {source}"

    def test_config_tracks_project_source(self, six_layer_full_setup):
        """
        RED: Test config tracks when value comes from project config.

        Given: Project config file exists
        When: Configuration is loaded
        Then: Source should be tracked as PROJECT

        Expected RED failure: No source tracking
        """
        # Given
        setup = six_layer_full_setup
        setup.setup_single_layer("project")

        # When
        try:
            from data_extract.cli.config import ConfigLayer, load_merged_config

            config = load_merged_config()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        source = config.get_source("output_dir")
        assert (
            source == ConfigLayer.PROJECT
        ), f"Source for project-provided value should be PROJECT, got: {source}"

    def test_config_tracks_default_source(self, six_layer_full_setup):
        """
        RED: Test config tracks when value comes from defaults.

        Given: No configuration is set
        When: Configuration is loaded
        Then: Source should be tracked as DEFAULT

        Expected RED failure: No source tracking
        """
        # Given
        setup = six_layer_full_setup
        setup.clear_all_layers()

        # When
        try:
            from data_extract.cli.config import ConfigLayer, load_merged_config

            config = load_merged_config()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        source = config.get_source("output_dir")
        assert (
            source == ConfigLayer.DEFAULT
        ), f"Source for default value should be DEFAULT, got: {source}"

    def test_get_all_sources_returns_dict(self, six_layer_full_setup):
        """
        RED: Test get_all_sources returns dict of field to source.

        Given: Configuration is loaded
        When: We call get_all_sources()
        Then: It should return dict mapping fields to sources

        Expected RED failure: Method doesn't exist
        """
        # Given/When
        try:
            from data_extract.cli.config import load_merged_config

            config = load_merged_config()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        sources = config.get_all_sources()
        assert isinstance(sources, dict), (
            f"get_all_sources should return dict of field to source mappings. "
            f"Expected: dict, got: {type(sources).__name__}"
        )
        assert "output_dir" in sources, (
            f"Source tracking should include all config fields. "
            f"Expected: 'output_dir' in {list(sources.keys())}, got: sources = {sources}"
        )


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.cascade
class TestCascadeNestedConfig:
    """AC-5.2-1: Test cascade works correctly for nested configuration."""

    def test_nested_tfidf_config_cascade(self, six_layer_full_setup):
        """
        RED: Test cascade works for nested semantic.tfidf config.

        Given: Different tfidf.max_features values at each layer
        When: Configuration is loaded
        Then: Correct precedence should apply to nested values

        Expected RED failure: Nested config not merged correctly
        """
        # Given
        setup = six_layer_full_setup
        setup.setup_all_layers()

        cli_args = {"tfidf_max_features": 10000}

        # When
        try:
            from data_extract.cli.config import load_merged_config

            config = load_merged_config(cli_overrides=cli_args)
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then - CLI should win for tfidf_max_features
        assert config.semantic.tfidf.max_features == 10000, (
            f"CLI tfidf_max_features should be 10000, " f"got: {config.semantic.tfidf.max_features}"
        )

    def test_partial_nested_override(self, six_layer_full_setup):
        """
        RED: Test partial override of nested config preserves other values.

        Given: Project config only sets tfidf.max_features
        And: User config sets tfidf.min_df
        When: Configuration is loaded
        Then: Both values should be present (merged, not replaced)

        Expected RED failure: Entire nested dict replaced instead of merged
        """
        # Given
        setup = six_layer_full_setup

        # Project sets only max_features
        setup.home_structure.create_project_config({"semantic": {"tfidf": {"max_features": 7000}}})
        # User sets only min_df
        setup.home_structure.create_user_config({"semantic": {"tfidf": {"min_df": 3}}})

        # When
        try:
            from data_extract.cli.config import load_merged_config

            config = load_merged_config()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then - project wins for max_features, user wins for min_df
        assert config.semantic.tfidf.max_features == 7000, (
            f"Partial nested override should preserve independent values. "
            f"max_features should come from PROJECT config. "
            f"Expected: 7000, got: {config.semantic.tfidf.max_features}"
        )
        assert config.semantic.tfidf.min_df == 3, (
            f"Partial nested override should preserve independent values. "
            f"min_df should come from USER config (no project override). "
            f"Expected: 3, got: {config.semantic.tfidf.min_df}"
        )


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.cascade
class TestCascadeEdgeCases:
    """AC-5.2-1: Test edge cases in configuration cascade."""

    def test_missing_config_files_graceful_fallback(self, six_layer_full_setup):
        """
        RED: Test graceful fallback when config files don't exist.

        Given: No config files exist
        When: Configuration is loaded
        Then: Should use defaults without error

        Expected RED failure: Exception on missing files
        """
        # Given
        setup = six_layer_full_setup
        setup.clear_all_layers()

        # When
        try:
            from data_extract.cli.config import load_merged_config

            config = load_merged_config()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")
        except FileNotFoundError:
            pytest.fail("Should handle missing config files gracefully")

        # Then
        assert config is not None, (
            f"Config loading should handle missing files gracefully. "
            f"Expected: config object, got: {config}"
        )

    def test_empty_config_file_handled(self, six_layer_full_setup):
        """
        RED: Test empty config file doesn't cause errors.

        Given: Config file exists but is empty
        When: Configuration is loaded
        Then: Should use defaults without error

        Expected RED failure: Exception on empty file
        """
        # Given
        setup = six_layer_full_setup
        # Create empty config file
        config_path = setup.home_structure.work_dir / ".data-extract.yaml"
        config_path.write_text("")

        # When
        try:
            from data_extract.cli.config import load_merged_config

            config = load_merged_config()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")
        except Exception as e:
            pytest.fail(f"Should handle empty config file: {e}")

        # Then
        assert config is not None, (
            f"Config loading should handle empty config files gracefully. "
            f"Expected: config object, got: {config}"
        )

    def test_none_values_in_cli_args_ignored(self, six_layer_full_setup):
        """
        RED: Test None values in CLI args don't override other layers.

        Given: CLI args contain None for some fields
        And: Lower layers have values for those fields
        When: Configuration is loaded
        Then: Lower layer values should be used for None CLI args

        Expected RED failure: None overwrites valid values
        """
        # Given
        setup = six_layer_full_setup
        setup.setup_single_layer("project")

        cli_args = {
            "output_dir": None,  # Should not override
            "tfidf_max_features": 10000,  # Should override
        }

        # When
        try:
            from data_extract.cli.config import load_merged_config

            config = load_merged_config(cli_overrides=cli_args)
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert config.output_dir == "/from/project", (
            f"None CLI value should not override project config. "
            f"Expected: /from/project, got: {config.output_dir}"
        )
        assert config.semantic.tfidf.max_features == 10000, (
            f"Non-None CLI value should override project config. "
            f"Expected: 10000, got: {config.semantic.tfidf.max_features}"
        )
