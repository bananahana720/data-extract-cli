"""TDD RED Phase Tests: Environment Variable Support (AC-5.2-2).

These tests verify:
- DATA_EXTRACT_* prefix environment variables are recognized
- Environment variables map correctly to config fields
- Type coercion from string env vars to typed config values
- Nested config field mapping (e.g., DATA_EXTRACT_TFIDF_MAX_FEATURES)

All tests are designed to FAIL initially (TDD RED phase).
"""

import pytest

# P0: Critical path - always run
pytestmark = [
    pytest.mark.P0,
    pytest.mark.env_vars,
    pytest.mark.story_5_2,
    pytest.mark.unit,
    pytest.mark.cli,
]


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.env_vars
class TestEnvVarLoaderExists:
    """AC-5.2-2: Verify environment variable loading infrastructure exists."""

    def test_load_env_config_function_exists(self):
        """
        RED: Verify load_env_config function exists.

        Given: The CLI config module
        When: We import load_env_config
        Then: It should exist and return a dict

        Expected RED failure: ImportError
        """
        # Given/When
        try:
            from data_extract.cli.config import load_env_config
        except ImportError as e:
            pytest.fail(f"Cannot import load_env_config: {e}")

        # Then
        result = load_env_config()
        assert isinstance(result, dict), "load_env_config should return a dict"

    def test_env_var_prefix_constant_exists(self):
        """
        RED: Verify ENV_VAR_PREFIX constant is defined.

        Given: The CLI config module
        When: We import ENV_VAR_PREFIX
        Then: It should be "DATA_EXTRACT_"

        Expected RED failure: ImportError or wrong value
        """
        # Given/When
        try:
            from data_extract.cli.config import ENV_VAR_PREFIX
        except ImportError as e:
            pytest.fail(f"Cannot import ENV_VAR_PREFIX: {e}")

        # Then
        assert (
            ENV_VAR_PREFIX == "DATA_EXTRACT_"
        ), f"ENV_VAR_PREFIX should be 'DATA_EXTRACT_', got: {ENV_VAR_PREFIX}"

    def test_env_var_mappings_exist(self):
        """
        RED: Verify environment variable mappings are defined.

        Given: The CLI config module
        When: We import ENV_VAR_MAPPINGS
        Then: It should map env var suffixes to config field paths

        Expected RED failure: ImportError or missing mappings
        """
        # Given/When
        try:
            from data_extract.cli.config import ENV_VAR_MAPPINGS
        except ImportError as e:
            pytest.fail(f"Cannot import ENV_VAR_MAPPINGS: {e}")

        # Then - check required mappings exist
        required_mappings = [
            "OUTPUT_DIR",
            "FORMAT",
            "TFIDF_MAX_FEATURES",
            "CHUNK_SIZE",
            "CACHE_ENABLED",
        ]

        for mapping in required_mappings:
            assert mapping in ENV_VAR_MAPPINGS, f"ENV_VAR_MAPPINGS should include '{mapping}'"


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.env_vars
class TestEnvVarParsing:
    """AC-5.2-2: Test environment variable parsing and mapping."""

    def test_output_dir_env_var_parsed(self, env_vars_fixture):
        """
        RED: Test DATA_EXTRACT_OUTPUT_DIR is parsed correctly.

        Given: DATA_EXTRACT_OUTPUT_DIR is set
        When: load_env_config is called
        Then: output_dir should be in result

        Expected RED failure: Env var not recognized
        """
        # Given
        env_vars_fixture.set("OUTPUT_DIR", "/custom/output")

        # When
        try:
            from data_extract.cli.config import load_env_config

            config = load_env_config()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert (
            config.get("output_dir") == "/custom/output"
        ), f"output_dir should be /custom/output, got: {config.get('output_dir')}"

    def test_format_env_var_parsed(self, env_vars_fixture):
        """
        RED: Test DATA_EXTRACT_FORMAT is parsed correctly.

        Given: DATA_EXTRACT_FORMAT is set
        When: load_env_config is called
        Then: format should be in result

        Expected RED failure: Env var not recognized
        """
        # Given
        env_vars_fixture.set("FORMAT", "csv")

        # When
        try:
            from data_extract.cli.config import load_env_config

            config = load_env_config()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert config.get("format") == "csv", f"format should be 'csv', got: {config.get('format')}"

    def test_tfidf_max_features_env_var_parsed(self, env_vars_fixture):
        """
        RED: Test DATA_EXTRACT_TFIDF_MAX_FEATURES is parsed to nested config.

        Given: DATA_EXTRACT_TFIDF_MAX_FEATURES is set
        When: load_env_config is called
        Then: semantic.tfidf.max_features should be set

        Expected RED failure: Nested mapping not working
        """
        # Given
        env_vars_fixture.set("TFIDF_MAX_FEATURES", "7500")

        # When
        try:
            from data_extract.cli.config import load_env_config

            config = load_env_config()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then - check nested structure
        semantic = config.get("semantic", {})
        tfidf = semantic.get("tfidf", {})
        assert (
            tfidf.get("max_features") == 7500
        ), f"tfidf.max_features should be 7500, got: {tfidf.get('max_features')}"

    def test_chunk_size_env_var_parsed(self, env_vars_fixture):
        """
        RED: Test DATA_EXTRACT_CHUNK_SIZE is parsed correctly.

        Given: DATA_EXTRACT_CHUNK_SIZE is set
        When: load_env_config is called
        Then: chunk.size should be set

        Expected RED failure: Env var not recognized
        """
        # Given
        env_vars_fixture.set("CHUNK_SIZE", "256")

        # When
        try:
            from data_extract.cli.config import load_env_config

            config = load_env_config()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        chunk = config.get("chunk", {})
        assert chunk.get("size") == 256, f"chunk.size should be 256, got: {chunk.get('size')}"

    def test_cache_enabled_env_var_parsed(self, env_vars_fixture):
        """
        RED: Test DATA_EXTRACT_CACHE_ENABLED is parsed as boolean.

        Given: DATA_EXTRACT_CACHE_ENABLED is set to "false"
        When: load_env_config is called
        Then: cache.enabled should be False (boolean)

        Expected RED failure: String not converted to boolean
        """
        # Given
        env_vars_fixture.set("CACHE_ENABLED", "false")

        # When
        try:
            from data_extract.cli.config import load_env_config

            config = load_env_config()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        cache = config.get("cache", {})
        assert (
            cache.get("enabled") is False
        ), f"cache.enabled should be False, got: {cache.get('enabled')}"


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.env_vars
class TestEnvVarTypeCoercion:
    """AC-5.2-2: Test type coercion from string env vars."""

    @pytest.mark.parametrize(
        "env_var,value,expected_type",
        [
            ("TFIDF_MAX_FEATURES", "5000", int),
            ("TFIDF_MIN_DF", "2", int),
            ("TFIDF_MAX_DF", "0.95", float),
            ("SIMILARITY_DUPLICATE_THRESHOLD", "0.85", float),
            ("LSA_N_COMPONENTS", "100", int),
            ("CACHE_MAX_SIZE_MB", "512", int),
            ("QUALITY_MIN_SCORE", "0.3", float),
        ],
    )
    def test_numeric_env_var_type_coercion(
        self,
        env_vars_fixture,
        env_var: str,
        value: str,
        expected_type: type,
    ):
        """
        RED: Test numeric env vars are coerced to correct types.

        Given: A numeric environment variable is set as string
        When: load_env_config is called
        Then: Value should be coerced to correct numeric type

        Expected RED failure: String not converted to number
        """
        # Given
        env_vars_fixture.set(env_var, value)

        # When
        try:
            from data_extract.cli.config import load_env_config

            config = load_env_config()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then - find the value in nested structure
        # Flatten config for checking
        actual_value = self._find_value_by_env_var(config, env_var)
        assert actual_value is not None, f"Value for {env_var} not found in config"
        assert isinstance(actual_value, expected_type), (
            f"{env_var} should be {expected_type.__name__}, "
            f"got {type(actual_value).__name__}: {actual_value}"
        )

    def _find_value_by_env_var(self, config: dict, env_var: str):
        """Helper to find value in nested config by env var name."""
        # Map env var names to config paths
        paths = {
            "TFIDF_MAX_FEATURES": ["semantic", "tfidf", "max_features"],
            "TFIDF_MIN_DF": ["semantic", "tfidf", "min_df"],
            "TFIDF_MAX_DF": ["semantic", "tfidf", "max_df"],
            "SIMILARITY_DUPLICATE_THRESHOLD": ["semantic", "similarity", "duplicate_threshold"],
            "LSA_N_COMPONENTS": ["semantic", "lsa", "n_components"],
            "CACHE_MAX_SIZE_MB": ["cache", "max_size_mb"],
            "QUALITY_MIN_SCORE": ["quality", "min_score"],
        }

        path = paths.get(env_var)
        if not path:
            return None

        current = config
        for key in path:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
        return current

    @pytest.mark.parametrize(
        "env_var,value,expected",
        [
            ("CACHE_ENABLED", "true", True),
            ("CACHE_ENABLED", "True", True),
            ("CACHE_ENABLED", "TRUE", True),
            ("CACHE_ENABLED", "1", True),
            ("CACHE_ENABLED", "yes", True),
            ("CACHE_ENABLED", "false", False),
            ("CACHE_ENABLED", "False", False),
            ("CACHE_ENABLED", "FALSE", False),
            ("CACHE_ENABLED", "0", False),
            ("CACHE_ENABLED", "no", False),
        ],
    )
    def test_boolean_env_var_coercion(
        self,
        env_vars_fixture,
        env_var: str,
        value: str,
        expected: bool,
    ):
        """
        RED: Test boolean env vars handle various true/false strings.

        Given: A boolean env var with various string representations
        When: load_env_config is called
        Then: Value should be coerced to correct boolean

        Expected RED failure: Boolean coercion not implemented
        """
        # Given
        env_vars_fixture.set(env_var, value)

        # When
        try:
            from data_extract.cli.config import load_env_config

            config = load_env_config()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        cache = config.get("cache", {})
        assert (
            cache.get("enabled") is expected
        ), f"'{value}' should coerce to {expected}, got: {cache.get('enabled')}"


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.env_vars
class TestEnvVarIntegration:
    """AC-5.2-2: Test env vars integrate with configuration cascade."""

    def test_env_var_overrides_file_config(
        self,
        six_layer_full_setup,
        env_vars_fixture,
    ):
        """
        RED: Test env var overrides project/user config files.

        Given: Project config has output_dir = "/from/project"
        And: DATA_EXTRACT_OUTPUT_DIR = "/from/env"
        When: Configuration is loaded
        Then: /from/env should be used

        Expected RED failure: Env var doesn't override file config
        """
        # Given
        setup = six_layer_full_setup
        setup.setup_single_layer("project")
        env_vars_fixture.set("OUTPUT_DIR", "/from/env")

        # When
        try:
            from data_extract.cli.config import load_merged_config

            config = load_merged_config()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert config.output_dir == "/from/env", (
            f"Env var should override file config. "
            f"Expected: /from/env, got: {config.output_dir}"
        )

    def test_cli_overrides_env_var(
        self,
        six_layer_full_setup,
        env_vars_fixture,
    ):
        """
        RED: Test CLI args override env vars.

        Given: DATA_EXTRACT_OUTPUT_DIR = "/from/env"
        When: CLI is called with --output-dir=/from/cli
        Then: /from/cli should be used

        Expected RED failure: CLI doesn't override env var
        """
        # Given
        env_vars_fixture.set("OUTPUT_DIR", "/from/env")
        cli_args = {"output_dir": "/from/cli"}

        # When
        try:
            from data_extract.cli.config import load_merged_config

            config = load_merged_config(cli_overrides=cli_args)
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert config.output_dir == "/from/cli", (
            f"CLI should override env var. " f"Expected: /from/cli, got: {config.output_dir}"
        )

    def test_multiple_env_vars_combined(self, env_vars_fixture):
        """
        RED: Test multiple env vars are all loaded.

        Given: Multiple DATA_EXTRACT_* vars are set
        When: load_env_config is called
        Then: All values should be present

        Expected RED failure: Only some env vars loaded
        """
        # Given
        env_vars_fixture.set("OUTPUT_DIR", "/custom/output")
        env_vars_fixture.set("FORMAT", "json")
        env_vars_fixture.set("TFIDF_MAX_FEATURES", "8000")
        env_vars_fixture.set("CACHE_ENABLED", "true")

        # When
        try:
            from data_extract.cli.config import load_env_config

            config = load_env_config()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then - all values should be present
        assert config.get("output_dir") == "/custom/output"
        assert config.get("format") == "json"

        semantic = config.get("semantic", {})
        tfidf = semantic.get("tfidf", {})
        assert tfidf.get("max_features") == 8000

        cache = config.get("cache", {})
        assert cache.get("enabled") is True


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.env_vars
class TestEnvVarEdgeCases:
    """AC-5.2-2: Test edge cases in environment variable handling."""

    def test_unset_env_vars_not_included(self, env_vars_fixture):
        """
        RED: Test unset env vars don't appear in config.

        Given: No DATA_EXTRACT_* env vars are set
        When: load_env_config is called
        Then: Result should be empty or contain only defaults

        Expected RED failure: Spurious values in config
        """
        # Given
        env_vars_fixture.reset()  # Ensure clean state

        # When
        try:
            from data_extract.cli.config import load_env_config

            config = load_env_config()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then - should be empty or minimal
        # Note: might contain empty nested dicts, that's ok
        flat_values = self._count_leaf_values(config)
        assert flat_values == 0, f"Expected no env values, got {flat_values}"

    def _count_leaf_values(self, d: dict) -> int:
        """Count non-dict leaf values in nested dict."""
        count = 0
        for value in d.values():
            if isinstance(value, dict):
                count += self._count_leaf_values(value)
            elif value is not None:
                count += 1
        return count

    def test_empty_env_var_value_handled(self, env_vars_fixture):
        """
        RED: Test empty string env var is handled gracefully.

        Given: DATA_EXTRACT_OUTPUT_DIR is set to empty string
        When: load_env_config is called
        Then: Should either skip or use empty string consistently

        Expected RED failure: Exception or unexpected behavior
        """
        # Given
        env_vars_fixture.set("OUTPUT_DIR", "")

        # When
        try:
            from data_extract.cli.config import load_env_config

            config = load_env_config()
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")
        except Exception as e:
            pytest.fail(f"Empty env var caused exception: {e}")

        # Then - empty string or not included, both are valid
        output_dir = config.get("output_dir")
        assert (
            output_dir == "" or output_dir is None
        ), f"Empty env var should be empty or None, got: {output_dir}"

    def test_non_prefixed_env_vars_ignored(self, env_vars_fixture):
        """
        RED: Test non-DATA_EXTRACT_* env vars are ignored.

        Given: OTHER_PREFIX_OUTPUT_DIR is set
        When: load_env_config is called
        Then: Value should not be included

        Expected RED failure: Non-prefixed vars incorrectly included
        """
        # Given
        import os

        os.environ["OTHER_PREFIX_OUTPUT_DIR"] = "/other/path"

        try:
            # When
            try:
                from data_extract.cli.config import load_env_config

                config = load_env_config()
            except ImportError as e:
                pytest.fail(f"Cannot import: {e}")

            # Then
            assert (
                config.get("output_dir") != "/other/path"
            ), "Non-prefixed env var should be ignored"
        finally:
            # Cleanup
            os.environ.pop("OTHER_PREFIX_OUTPUT_DIR", None)

    def test_invalid_numeric_env_var_handled(self, env_vars_fixture):
        """
        RED: Test invalid numeric env var raises clear error.

        Given: DATA_EXTRACT_TFIDF_MAX_FEATURES is set to non-numeric
        When: load_env_config is called
        Then: Should raise ValidationError or handle gracefully

        Expected RED failure: Cryptic error or crash
        """
        # Given
        env_vars_fixture.set("TFIDF_MAX_FEATURES", "not_a_number")

        # When/Then
        try:
            from data_extract.cli.config import load_env_config

            # Either raises clear error or skips invalid value
            try:
                config = load_env_config()
                # If no error, value should be skipped or defaulted
                semantic = config.get("semantic", {})
                tfidf = semantic.get("tfidf", {})
                max_features = tfidf.get("max_features")
                assert (
                    max_features != "not_a_number"
                ), "Invalid value should not be passed through as string"
            except ValueError as e:
                # Clear error is acceptable
                assert (
                    "TFIDF_MAX_FEATURES" in str(e) or "integer" in str(e).lower()
                ), f"Error should be clear about which var failed: {e}"
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")
