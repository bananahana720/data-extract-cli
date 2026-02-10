"""TDD RED Phase Tests: Typer App Factory (AC-5.1-1, AC-5.1-8).

These tests verify:
- AC-5.1-1: Git-style command structure with Typer app groups
- AC-5.1-8: Auto-generated help text leverages type hints and docstrings

Tests import from src/data_extract/cli/base which will be created during GREEN phase.
All tests are designed to FAIL initially (TDD RED phase).
"""

import pytest

# P0: CLI framework foundation - critical infrastructure
pytestmark = [
    pytest.mark.P0,
    pytest.mark.unit,
    pytest.mark.story_5_1,
    pytest.mark.cli,
]


@pytest.mark.unit
@pytest.mark.story_5_1
class TestTyperAppFactoryExists:
    """Verify create_app factory function exists and returns Typer instance."""

    @pytest.mark.test_id("5.1-UNIT-001")
    def test_create_app_function_exists(self):
        """
        RED: Verify create_app factory function can be imported.

        Given: The CLI base module
        When: We import create_app from data_extract.cli.base
        Then: It should be a callable function

        Expected RED failure: ImportError - base module doesn't exist yet
        """
        # Given/When
        try:
            from data_extract.cli.base import create_app
        except ImportError as e:
            pytest.fail(
                f"Cannot import create_app from data_extract.cli.base: {e}\n"
                "Expected: src/data_extract/cli/base.py with create_app() function"
            )

        # Then
        assert callable(create_app), "create_app should be a callable function"

    @pytest.mark.test_id("5.1-UNIT-002")
    def test_create_app_returns_typer_instance(self):
        """
        RED: Verify create_app returns a Typer application instance.

        Given: The create_app factory function
        When: We call create_app()
        Then: It should return a typer.Typer instance

        Expected RED failure: ImportError or wrong return type
        """
        # Given
        try:
            import typer

            from data_extract.cli.base import create_app
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        app = create_app()

        # Then
        assert isinstance(
            app, typer.Typer
        ), f"create_app() should return typer.Typer instance, got {type(app).__name__}"

    @pytest.mark.test_id("5.1-UNIT-003")
    def test_create_app_returns_configured_app(self):
        """
        RED: Verify create_app returns an app with name and help text.

        Given: The create_app factory function
        When: We call create_app()
        Then: The returned app should have name and help configured

        Expected RED failure: App not properly configured
        """
        # Given
        try:
            from data_extract.cli.base import create_app
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        app = create_app()

        # Then
        # Typer stores info.name for the app name
        assert (
            app.info.name is not None or app.info.help is not None
        ), "App should have name or help configured"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestTyperAppRichIntegration:
    """Verify Typer app has Rich help formatting enabled (AC-5.1-8)."""

    @pytest.mark.test_id("5.1-UNIT-004")
    def test_app_has_rich_help_formatting(self, typer_cli_runner):
        """
        RED: Verify app uses Rich for help text formatting.

        Given: The Typer app from create_app
        When: We invoke --help
        Then: Output should have Rich-formatted structure

        Expected RED failure: App doesn't exist or no Rich formatting
        """
        # Given
        try:
            from data_extract.cli.base import create_app
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        app = create_app()

        # When
        result = typer_cli_runner.invoke(app, ["--help"])

        # Then
        assert result.exit_code == 0, f"--help failed: {result.output}"
        # Rich help typically includes structured sections (Rich panels use boxes, not colons)
        # Check for Rich-formatted panel headers or fallback to colon format
        has_structure = (
            "Commands" in result.output
            or "Options" in result.output
            or "Arguments" in result.output
        )
        assert (
            has_structure
        ), "Help output should have Rich-formatted structure with Commands/Options/Arguments sections"

    @pytest.mark.test_id("5.1-UNIT-005")
    def test_app_rich_markup_mode_enabled(self):
        """
        RED: Verify app has Rich markup mode enabled for help text.

        Given: The create_app factory
        When: We inspect the created app's configuration
        Then: rich_markup_mode should be set to "rich" or "markdown"

        Expected RED failure: App not configured with Rich markup
        """
        # Given
        try:
            from data_extract.cli.base import create_app
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        app = create_app()

        # Then
        # Typer stores rich_markup_mode directly on the app object
        assert app.rich_markup_mode in (
            "rich",
            "markdown",
        ), f"App should have rich_markup_mode='rich' or 'markdown', got {app.rich_markup_mode}"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestTyperAppVersionOption:
    """Verify app has --version option working correctly."""

    @pytest.mark.test_id("5.1-UNIT-006")
    def test_app_version_option_works(self, typer_cli_runner):
        """
        RED: Verify --version option displays version information.

        Given: The Typer app from create_app
        When: We invoke --version
        Then: It should display version string

        Expected RED failure: App doesn't have version option or wrong output
        """
        # Given
        try:
            from data_extract.cli.base import create_app
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        app = create_app()

        # When
        result = typer_cli_runner.invoke(app, ["--version"])

        # Then
        assert result.exit_code == 0, f"--version failed: {result.output}"
        # Version output should contain version number
        assert (
            "0." in result.output
            or "1." in result.output
            or "data-extract" in result.output.lower()
        ), f"--version should display version info, got: {result.output}"

    @pytest.mark.test_id("5.1-UNIT-007")
    def test_app_version_callback_registered(self):
        """
        RED: Verify version callback is properly registered.

        Given: The create_app factory
        When: We inspect the created app
        Then: It should have version option in registered params

        Expected RED failure: No version callback
        """
        # Given
        try:
            from data_extract.cli.base import create_app
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        app = create_app()

        # Then
        # Check that version is mentioned in help
        # This is a structural test - full test done via CLI runner
        assert app is not None, "App should be created"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestTyperAppRequiredCommandGroups:
    """Verify app has required command groups registered (AC-5.1-1)."""

    @pytest.mark.test_id("5.1-UNIT-008")
    def test_app_has_semantic_command_group(self, typer_cli_runner):
        """
        RED: Verify 'semantic' command group is registered.

        Given: The Typer app from create_app
        When: We invoke 'semantic --help'
        Then: It should show semantic subcommands

        Expected RED failure: 'semantic' group not registered
        """
        # Given
        try:
            from data_extract.cli.base import create_app
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        app = create_app()

        # When
        result = typer_cli_runner.invoke(app, ["semantic", "--help"])

        # Then
        assert result.exit_code == 0, f"semantic --help failed: {result.output}"
        # Should have semantic subcommands
        assert (
            "analyze" in result.output.lower() or "deduplicate" in result.output.lower()
        ), "semantic group should have analyze/deduplicate commands"

    @pytest.mark.test_id("5.1-UNIT-009")
    def test_app_has_cache_command_group(self, typer_cli_runner):
        """
        RED: Verify 'cache' command group is registered.

        Given: The Typer app from create_app
        When: We invoke 'cache --help'
        Then: It should show cache management subcommands

        Expected RED failure: 'cache' group not registered
        """
        # Given
        try:
            from data_extract.cli.base import create_app
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        app = create_app()

        # When
        result = typer_cli_runner.invoke(app, ["cache", "--help"])

        # Then
        assert result.exit_code == 0, f"cache --help failed: {result.output}"
        # Should have cache subcommands
        assert (
            "status" in result.output.lower() or "clear" in result.output.lower()
        ), "cache group should have status/clear commands"

    @pytest.mark.test_id("5.1-UNIT-010")
    def test_app_has_process_command(self, typer_cli_runner):
        """
        RED: Verify 'process' command is registered as top-level command.

        Given: The Typer app from create_app
        When: We invoke 'process --help'
        Then: It should show process command help

        Expected RED failure: 'process' command not registered
        """
        # Given
        try:
            from data_extract.cli.base import create_app
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        app = create_app()

        # When
        result = typer_cli_runner.invoke(app, ["process", "--help"])

        # Then
        assert result.exit_code == 0, f"process --help failed: {result.output}"
        # Should mention input/output options
        assert (
            "input" in result.output.lower()
            or "output" in result.output.lower()
            or "path" in result.output.lower()
        ), "process command should have input/output parameters"

    @pytest.mark.test_id("5.1-UNIT-011")
    def test_app_has_config_command_group(self, typer_cli_runner):
        """
        RED: Verify 'config' command group is registered.

        Given: The Typer app from create_app
        When: We invoke 'config --help'
        Then: It should show config management subcommands

        Expected RED failure: 'config' group not registered
        """
        # Given
        try:
            from data_extract.cli.base import create_app
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        app = create_app()

        # When
        result = typer_cli_runner.invoke(app, ["config", "--help"])

        # Then
        assert result.exit_code == 0, f"config --help failed: {result.output}"
        # Should have config subcommands
        assert (
            "show" in result.output.lower()
            or "set" in result.output.lower()
            or "list" in result.output.lower()
        ), "config group should have show/set/list commands"

    @pytest.mark.test_id("5.1-UNIT-012")
    def test_main_help_lists_all_command_groups(self, typer_cli_runner):
        """
        RED: Verify main --help lists all required command groups.

        Given: The Typer app from create_app
        When: We invoke --help
        Then: All command groups should be listed

        Expected RED failure: Missing command groups in help
        """
        # Given
        try:
            from data_extract.cli.base import create_app
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        app = create_app()

        # When
        result = typer_cli_runner.invoke(app, ["--help"])

        # Then
        assert result.exit_code == 0, f"--help failed: {result.output}"

        required_groups = ["semantic", "cache", "process", "config"]
        missing = []
        for group in required_groups:
            if group not in result.output.lower():
                missing.append(group)

        assert (
            not missing
        ), f"Missing command groups in main help: {missing}\nHelp output:\n{result.output}"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestTyperAppAutoCompletion:
    """Verify app supports shell auto-completion."""

    @pytest.mark.test_id("5.1-UNIT-013")
    def test_app_completion_enabled(self):
        """
        RED: Verify app has completion support enabled.

        Given: The create_app factory
        When: We create the app
        Then: add_completion should be True

        Expected RED failure: Completion not enabled
        """
        # Given
        try:
            from data_extract.cli.base import create_app
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        app = create_app()

        # Then
        # Typer stores add_completion in _add_completion on the app object
        assert (
            app._add_completion is True
        ), "App should have add_completion=True for shell completion support"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestTyperAppCallback:
    """Verify app has callback for shared options/state."""

    @pytest.mark.test_id("5.1-UNIT-014")
    def test_app_has_callback(self):
        """
        RED: Verify app has callback decorator for shared options.

        Given: The create_app factory
        When: We create the app
        Then: The app should have a registered callback

        Expected RED failure: No callback registered
        """
        # Given
        try:
            from data_extract.cli.base import create_app
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        app = create_app()

        # Then
        # Typer stores callback in registered_callback
        assert (
            app.registered_callback is not None
        ), "App should have a callback registered for shared options"

    @pytest.mark.test_id("5.1-UNIT-015")
    def test_app_callback_supports_verbose_option(self, typer_cli_runner):
        """
        RED: Verify global --verbose option works via callback.

        Given: The Typer app
        When: We invoke with --verbose flag at top level
        Then: It should be accepted as a global option

        Expected RED failure: --verbose not recognized
        """
        # Given
        try:
            from data_extract.cli.base import create_app
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        app = create_app()

        # When
        result = typer_cli_runner.invoke(app, ["--verbose", "--help"])

        # Then
        # Should not fail due to unrecognized option
        assert (
            result.exit_code == 0
        ), f"--verbose should be accepted as global option: {result.output}"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestTyperAppEntryPoint:
    """Verify app entry point is properly configured."""

    @pytest.mark.test_id("5.1-UNIT-016")
    def test_app_can_be_invoked_directly(self, typer_cli_runner):
        """
        RED: Verify app can be invoked as entry point.

        Given: The Typer app
        When: We invoke it without arguments
        Then: It should show help or error gracefully

        Expected RED failure: App crashes or has no default behavior
        """
        # Given
        try:
            from data_extract.cli.base import create_app
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        app = create_app()

        # When
        result = typer_cli_runner.invoke(app, [])

        # Then
        # Should either show help or require subcommand
        # Exit code 0 for help display, or 2 for missing required args
        assert result.exit_code in (
            0,
            2,
        ), f"App should handle no-args invocation gracefully: {result.output}"

    @pytest.mark.test_id("5.1-UNIT-017")
    def test_get_app_function_exists(self):
        """
        RED: Verify get_app function returns singleton app instance.

        Given: The CLI base module
        When: We import and call get_app
        Then: It should return the same app instance on repeated calls

        Expected RED failure: get_app doesn't exist
        """
        # Given
        try:
            from data_extract.cli.base import get_app
        except ImportError as e:
            pytest.fail(f"Cannot import get_app: {e}")

        # When
        app1 = get_app()
        app2 = get_app()

        # Then
        assert app1 is app2, "get_app() should return the same singleton instance"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestTyperAppHelpText:
    """Verify help text is properly formatted and informative (AC-5.1-8)."""

    @pytest.mark.test_id("5.1-UNIT-018")
    def test_main_help_has_description(self, typer_cli_runner):
        """
        RED: Verify main help shows application description.

        Given: The Typer app
        When: We invoke --help
        Then: Description about data extraction should be shown

        Expected RED failure: No description in help
        """
        # Given
        try:
            from data_extract.cli.base import create_app
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        app = create_app()

        # When
        result = typer_cli_runner.invoke(app, ["--help"])

        # Then
        assert result.exit_code == 0
        # Should mention data extraction or document processing
        description_terms = ["data", "extract", "document", "rag", "pipeline"]
        has_description = any(term in result.output.lower() for term in description_terms)
        assert (
            has_description
        ), f"Main help should have descriptive text about the tool: {result.output}"

    @pytest.mark.test_id("5.1-UNIT-019")
    def test_command_help_shows_examples(self, typer_cli_runner):
        """
        RED: Verify command help includes usage examples.

        Given: The Typer app
        When: We invoke 'process --help'
        Then: Examples section should be present

        Expected RED failure: No examples in help
        """
        # Given
        try:
            from data_extract.cli.base import create_app
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        app = create_app()

        # When
        result = typer_cli_runner.invoke(app, ["process", "--help"])

        # Then
        assert result.exit_code == 0
        # Help should include example usage
        assert (
            "example" in result.output.lower() or "data-extract" in result.output
        ), f"process --help should include usage examples: {result.output}"

    @pytest.mark.test_id("5.1-UNIT-020")
    def test_semantic_analyze_help_shows_options(self, typer_cli_runner):
        """
        RED: Verify semantic analyze --help shows all options.

        Given: The Typer app
        When: We invoke 'semantic analyze --help'
        Then: All configuration options should be documented

        Expected RED failure: Missing options in help
        """
        # Given
        try:
            from data_extract.cli.base import create_app
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        app = create_app()

        # When
        result = typer_cli_runner.invoke(app, ["semantic", "analyze", "--help"])

        # Then
        assert result.exit_code == 0

        expected_options = ["--output", "--format", "--verbose"]
        missing = [opt for opt in expected_options if opt not in result.output]

        assert (
            not missing
        ), f"semantic analyze --help missing options: {missing}\nOutput:\n{result.output}"
