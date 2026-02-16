"""TDD RED Phase Tests: Config CLI Commands (AC-5.2-6, AC-5.2-7, AC-5.2-8).

These tests verify:
- AC-5.2-6: `config init` creates default configuration
- AC-5.2-7: `config show` displays merged configuration with source indicators
- AC-5.2-8: `config validate` checks configuration for errors

All tests are designed to FAIL initially (TDD RED phase).
"""

import pytest

# P1: Core functionality - run on PR
pytestmark = [
    pytest.mark.P1,
    pytest.mark.config_commands,
    pytest.mark.story_5_2,
    pytest.mark.unit,
    pytest.mark.cli,
]


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.config_commands
class TestConfigInitCommand:
    """AC-5.2-6: Test 'data-extract config init' command."""

    def test_config_init_command_exists(self, typer_cli_runner):
        """
        RED: Verify 'config init' command exists.

        Given: The CLI app
        When: We invoke 'config init'
        Then: Command should execute without unknown command error

        Expected RED failure: Command not found
        """
        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "init"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then - should not fail with "No such command"
        assert (
            "No such command" not in result.output
        ), f"'config init' command should exist: {result.output}"

    def test_config_init_creates_file(self, typer_cli_runner, mock_home_directory):
        """
        RED: Verify 'config init' creates config file.

        Given: No config file exists
        When: 'config init' is executed
        Then: .data-extract.yaml should be created in cwd

        Expected RED failure: File not created
        """
        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "init"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code == 0, f"Command failed: {result.output}"

        config_file = mock_home_directory.work_dir / ".data-extract.yaml"
        assert config_file.exists(), f"Config file should be created at {config_file}"

    def test_config_init_file_has_comments(self, typer_cli_runner, mock_home_directory):
        """
        RED: Verify 'config init' creates file with documentation comments.

        Given: 'config init' has been run
        When: We read the created file
        Then: It should contain helpful comments

        Expected RED failure: No comments in generated file
        """
        # Given
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "init"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        assert result.exit_code == 0

        # When
        config_file = mock_home_directory.work_dir / ".data-extract.yaml"
        content = config_file.read_text()

        # Then - should have documentation comments
        assert "#" in content, "File should contain comments"
        assert any(
            keyword in content.lower() for keyword in ["configuration", "settings", "options"]
        ), f"File should have documentation: {content[:200]}"

    def test_config_init_has_example_values(self, typer_cli_runner, mock_home_directory):
        """
        RED: Verify 'config init' file has commented example values.

        Given: 'config init' has been run
        When: We read the created file
        Then: It should contain example configuration values

        Expected RED failure: No example values
        """
        # Given
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "init"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        assert result.exit_code == 0

        # When
        config_file = mock_home_directory.work_dir / ".data-extract.yaml"
        content = config_file.read_text()

        # Then - should have key config sections
        expected_sections = ["semantic", "tfidf", "cache"]
        found_sections = [s for s in expected_sections if s in content.lower()]
        assert len(found_sections) >= 2, (
            f"Expected config sections {expected_sections}, " f"found: {found_sections}"
        )

    def test_config_init_confirms_creation(self, typer_cli_runner, mock_home_directory):
        """
        RED: Verify 'config init' outputs confirmation message.

        Given: The CLI app
        When: 'config init' is executed
        Then: Should output confirmation of file creation

        Expected RED failure: No confirmation message
        """
        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "init"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code == 0
        assert any(
            word in result.output.lower() for word in ["created", "initialized", "generated"]
        ), f"Should confirm creation: {result.output}"

    def test_config_init_warns_if_exists(self, typer_cli_runner, mock_home_directory):
        """
        RED: Verify 'config init' warns if config already exists.

        Given: Config file already exists
        When: 'config init' is executed
        Then: Should warn about existing file

        Expected RED failure: No warning, overwrites silently
        """
        # Given
        mock_home_directory.create_project_config({"semantic": {"tfidf": {"max_features": 5000}}})

        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "init"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then - should warn or ask for confirmation
        assert any(
            word in result.output.lower() for word in ["exists", "already", "overwrite", "warning"]
        ), f"Should warn about existing file: {result.output}"

    def test_config_init_force_flag_overwrites(self, typer_cli_runner, mock_home_directory):
        """
        RED: Verify 'config init --force' overwrites existing file.

        Given: Config file already exists
        When: 'config init --force' is executed
        Then: File should be overwritten

        Expected RED failure: --force flag not implemented
        """
        # Given
        mock_home_directory.create_project_config({"old_key": "old_value"})

        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "init", "--force"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code == 0, f"Command failed: {result.output}"

        config_file = mock_home_directory.work_dir / ".data-extract.yaml"
        content = config_file.read_text()
        assert "old_key" not in content, "Old config should be overwritten"


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.config_commands
class TestConfigShowCommand:
    """AC-5.2-7: Test 'data-extract config show' command."""

    def test_config_show_command_exists(self, typer_cli_runner):
        """
        RED: Verify 'config show' command exists.

        Given: The CLI app
        When: We invoke 'config show'
        Then: Command should execute and show configuration

        Expected RED failure: Command not found
        """
        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "show"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert (
            "No such command" not in result.output
        ), f"'config show' should exist: {result.output}"
        assert result.exit_code == 0, f"Command failed: {result.output}"

    def test_config_show_displays_merged_config(self, typer_cli_runner):
        """
        RED: Verify 'config show' displays merged configuration.

        Given: The CLI app
        When: 'config show' is executed
        Then: Should display current configuration values

        Expected RED failure: No config displayed
        """
        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "show"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code == 0
        # Should show some config values
        assert any(
            keyword in result.output.lower()
            for keyword in ["max_features", "tfidf", "cache", "semantic"]
        ), f"Should show config values: {result.output}"

    def test_config_show_includes_source_indicators(self, typer_cli_runner):
        """
        RED: Verify 'config show' includes source indicators.

        Given: The CLI app
        When: 'config show' is executed
        Then: Each value should show its source [cli], [env], [file], etc.

        Expected RED failure: No source indicators
        """
        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "show"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code == 0
        # Should include source indicators
        has_source = any(
            indicator in result.output
            for indicator in ["[default]", "[env]", "[cli]", "[file]", "[preset]"]
        )
        assert has_source, f"Should include source indicators: {result.output}"

    def test_config_show_source_indicator_for_cli_override(
        self, typer_cli_runner, env_vars_fixture
    ):
        """
        RED: Verify CLI overrides show [cli] source indicator.

        Given: CLI arg is provided
        When: 'config show --tfidf-max-features 9999'
        Then: tfidf_max_features should show [cli] source

        Expected RED failure: Source not tracked for CLI args
        """
        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(
                app, ["config", "show", "--tfidf-max-features", "9999"]
            )
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code == 0
        assert "9999" in result.output, "CLI value should be shown"
        # Source should indicate CLI
        assert (
            "[cli]" in result.output.lower()
        ), f"CLI override should show [cli] source: {result.output}"

    def test_config_show_source_indicator_for_env_var(self, typer_cli_runner, env_vars_fixture):
        """
        RED: Verify env var overrides show [env] source indicator.

        Given: Environment variable is set
        When: 'config show' is executed
        Then: Value should show [env] source

        Expected RED failure: Source not tracked for env vars
        """
        # Given
        env_vars_fixture.set("TFIDF_MAX_FEATURES", "7777")

        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "show"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code == 0
        assert "7777" in result.output, "Env value should be shown"
        assert (
            "[env]" in result.output.lower()
        ), f"Env override should show [env] source: {result.output}"

    def test_config_show_reports_invalid_project_config_without_traceback(
        self, typer_cli_runner, mock_home_directory
    ):
        """
        RED: Verify invalid project YAML is surfaced as a clear config error.

        Given: .data-extract.yaml contains malformed YAML
        When: 'config show' is executed
        Then: Command should fail with a clear message and no traceback dump

        Expected RED failure: Silent fallback or raw exception
        """
        config_file = mock_home_directory.work_dir / ".data-extract.yaml"
        config_file.write_text(
            """
semantic
  tfidf:
    max_features: 5000
""",
            encoding="utf-8",
        )

        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "show"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        assert result.exit_code != 0
        assert "invalid yaml" in result.output.lower()
        assert "config file" in result.output.lower()
        assert "traceback" not in result.output.lower()

    def test_config_show_reports_invalid_numeric_env_var_without_traceback(
        self, typer_cli_runner, env_vars_fixture
    ):
        """
        RED: Verify malformed numeric env vars fail cleanly in config commands.

        Given: DATA_EXTRACT_TFIDF_MAX_FEATURES has non-numeric value
        When: 'config show' is executed
        Then: Command should show clear env-var error without traceback

        Expected RED failure: Raw uncaught ValueError
        """
        env_vars_fixture.set("TFIDF_MAX_FEATURES", "not_a_number")

        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "show"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        assert result.exit_code != 0
        assert "DATA_EXTRACT_TFIDF_MAX_FEATURES" in result.output
        assert "integer or float" in result.output.lower()
        assert "traceback" not in result.output.lower()

    def test_config_show_formats_output_nicely(self, typer_cli_runner):
        """
        RED: Verify 'config show' has well-formatted output.

        Given: The CLI app
        When: 'config show' is executed
        Then: Output should be formatted (not raw dict dump)

        Expected RED failure: Ugly raw output
        """
        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "show"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code == 0
        # Should have some structure (indentation, colons, etc.)
        has_structure = "\n" in result.output and (":" in result.output or "=" in result.output)
        assert has_structure, f"Output should be formatted: {result.output[:200]}"

    def test_config_show_json_format_option(self, typer_cli_runner):
        """
        RED: Verify 'config show --format json' outputs JSON.

        Given: The CLI app
        When: 'config show --format json' is executed
        Then: Should output valid JSON

        Expected RED failure: --format option not implemented
        """
        # When
        try:
            import json

            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "show", "--format", "json"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code == 0
        # Should be valid JSON
        try:
            parsed = json.loads(result.output)
            assert isinstance(parsed, dict)
        except json.JSONDecodeError:
            pytest.fail(f"Output should be valid JSON: {result.output}")


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.config_commands
class TestConfigValidateCommand:
    """AC-5.2-8: Test 'data-extract config validate' command."""

    def test_config_validate_command_exists(self, typer_cli_runner):
        """
        RED: Verify 'config validate' command exists.

        Given: The CLI app
        When: We invoke 'config validate'
        Then: Command should execute

        Expected RED failure: Command not found
        """
        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "validate"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert (
            "No such command" not in result.output
        ), f"'config validate' should exist: {result.output}"

    def test_config_validate_success_message(self, typer_cli_runner, mock_home_directory):
        """
        RED: Verify 'config validate' shows success for valid config.

        Given: Valid configuration exists
        When: 'config validate' is executed
        Then: Should show success message

        Expected RED failure: No success indication
        """
        # Given
        mock_home_directory.create_project_config(
            {
                "semantic": {
                    "tfidf": {"max_features": 5000},
                },
            }
        )

        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "validate"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code == 0
        assert any(
            word in result.output.lower() for word in ["valid", "ok", "success", "pass"]
        ), f"Should indicate success: {result.output}"

    def test_config_validate_detects_yaml_syntax_error(
        self, typer_cli_runner, config_file_factory, mock_home_directory
    ):
        """
        RED: Verify 'config validate' detects YAML syntax errors.

        Given: Config file with invalid YAML syntax
        When: 'config validate' is executed
        Then: Should report YAML syntax error

        Expected RED failure: YAML error not detected
        """
        # Given
        config_file = mock_home_directory.work_dir / ".data-extract.yaml"
        config_file.write_text(
            """
semantic
  tfidf:
    max_features 5000  # Missing colon
"""
        )

        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "validate"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code != 0, "Should fail for invalid YAML"
        assert any(
            word in result.output.lower() for word in ["yaml", "syntax", "parse", "error"]
        ), f"Should report YAML error: {result.output}"

    def test_config_validate_detects_type_mismatch(self, typer_cli_runner, mock_home_directory):
        """
        RED: Verify 'config validate' detects type mismatches.

        Given: Config file with wrong types
        When: 'config validate' is executed
        Then: Should report type mismatch error

        Expected RED failure: Type error not detected
        """
        # Given
        mock_home_directory.create_project_config(
            {
                "semantic": {
                    "tfidf": {
                        "max_features": "not_a_number",  # Should be int
                    },
                },
            }
        )

        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "validate"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code != 0, "Should fail for type mismatch"
        assert any(
            word in result.output.lower()
            for word in ["type", "int", "integer", "number", "validation"]
        ), f"Should report type error: {result.output}"

    def test_config_validate_detects_range_violation(self, typer_cli_runner, mock_home_directory):
        """
        RED: Verify 'config validate' detects range violations.

        Given: Config file with out-of-range values
        When: 'config validate' is executed
        Then: Should report range violation

        Expected RED failure: Range error not detected
        """
        # Given
        mock_home_directory.create_project_config(
            {
                "semantic": {
                    "tfidf": {
                        "max_features": -100,  # Must be positive
                        "max_df": 1.5,  # Must be <= 1.0
                    },
                },
            }
        )

        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "validate"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code != 0, "Should fail for range violation"
        assert any(
            word in result.output.lower()
            for word in ["range", "greater", "less", "must be", "invalid"]
        ), f"Should report range error: {result.output}"

    def test_config_validate_provides_fix_suggestions(self, typer_cli_runner, mock_home_directory):
        """
        RED: Verify 'config validate' provides fix suggestions.

        Given: Config file with validation errors
        When: 'config validate' is executed
        Then: Should include suggestions for fixing issues

        Expected RED failure: No fix suggestions
        """
        # Given
        mock_home_directory.create_project_config(
            {
                "semantic": {
                    "tfidf": {
                        "max_features": -100,
                    },
                },
            }
        )

        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "validate"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code != 0
        # Should have helpful suggestions
        has_suggestion = any(
            word in result.output.lower()
            for word in ["should be", "expected", "try", "fix", "suggestion", "hint"]
        )
        assert has_suggestion, f"Should provide fix suggestions: {result.output}"

    def test_config_validate_reports_multiple_errors(self, typer_cli_runner, mock_home_directory):
        """
        RED: Verify 'config validate' reports all errors, not just first.

        Given: Config file with multiple errors
        When: 'config validate' is executed
        Then: Should report all validation errors

        Expected RED failure: Only first error reported
        """
        # Given
        mock_home_directory.create_project_config(
            {
                "semantic": {
                    "tfidf": {
                        "max_features": -100,  # Error 1
                        "max_df": 2.0,  # Error 2
                        "ngram_range": [3, 1],  # Error 3
                    },
                },
            }
        )

        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "validate"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code != 0
        # Count error indicators
        error_count = result.output.lower().count("error")
        # Or count by lines with error indicators
        error_lines = [
            line
            for line in result.output.split("\n")
            if any(word in line.lower() for word in ["error", "invalid", "must be"])
        ]
        assert len(error_lines) >= 2, f"Should report multiple errors: {result.output}"

    def test_config_validate_checks_specific_file(self, typer_cli_runner, mock_home_directory):
        """
        RED: Verify 'config validate --file <path>' validates specific file.

        Given: A specific config file path
        When: 'config validate --file <path>' is executed
        Then: Should validate that specific file

        Expected RED failure: --file option not implemented
        """
        # Given
        custom_config = mock_home_directory.work_dir / "custom-config.yaml"
        custom_config.write_text(
            """
semantic:
  tfidf:
    max_features: -999
"""
        )

        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(
                app, ["config", "validate", "--file", str(custom_config)]
            )
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code != 0, "Should fail for invalid config"
        assert (
            "-999" in result.output or "max_features" in result.output.lower()
        ), f"Should validate specified file: {result.output}"


@pytest.mark.unit
@pytest.mark.story_5_2
@pytest.mark.config_commands
class TestConfigSubcommandGroup:
    """Test 'config' subcommand group structure."""

    def test_config_subcommand_exists(self, typer_cli_runner):
        """
        RED: Verify 'config' subcommand group exists.

        Given: The CLI app
        When: We invoke 'config --help'
        Then: Should show config subcommands

        Expected RED failure: config group not found
        """
        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "--help"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code == 0
        assert "config" in result.output.lower()

    def test_config_help_lists_subcommands(self, typer_cli_runner):
        """
        RED: Verify 'config --help' lists all subcommands.

        Given: The CLI app
        When: 'config --help' is executed
        Then: Should list init, show, validate, presets, load, save

        Expected RED failure: Subcommands not listed
        """
        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config", "--help"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then
        assert result.exit_code == 0
        expected_commands = ["init", "show", "validate"]
        output_lower = result.output.lower()
        found = [cmd for cmd in expected_commands if cmd in output_lower]
        assert len(found) >= 3, (
            f"Help should list commands {expected_commands}, " f"found: {found} in {result.output}"
        )

    def test_config_without_subcommand_shows_help(self, typer_cli_runner):
        """
        RED: Verify 'config' without subcommand shows help.

        Given: The CLI app
        When: 'config' is executed without subcommand
        Then: Should show help or error with suggestions

        Expected RED failure: Cryptic error or crash
        """
        # When
        try:
            from data_extract.app import app

            result = typer_cli_runner.invoke(app, ["config"])
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Then - should either show help or helpful error
        is_helpful = (
            "usage" in result.output.lower()
            or "help" in result.output.lower()
            or "commands" in result.output.lower()
            or result.exit_code == 0
        )
        assert is_helpful, f"Should be helpful: {result.output}"
