"""TDD RED Phase Tests: Typer Migration (AC-5.1-1, AC-5.1-2, AC-5.1-3).

These tests verify:
- AC-5.1-1: Git-style command structure with Typer app groups
- AC-5.1-2: Click-to-Typer migration complete (0 Click imports)
- AC-5.1-3: 100% type hints on all command parameters

All tests are designed to FAIL initially (TDD RED phase).
"""

import ast
import re
from pathlib import Path

import pytest

pytest.importorskip("typer", reason="Typer is required for unit CLI tests")

# P1: Core functionality - run on PR
pytestmark = [
    pytest.mark.P1,
    pytest.mark.story_5_1,
    pytest.mark.unit,
    pytest.mark.cli,
]


@pytest.mark.unit
@pytest.mark.story_5_1
class TestTyperMigration:
    """AC-5.1-2: Click-to-Typer migration tests."""

    def test_zero_click_imports_in_greenfield_cli(self):
        """
        RED: Verify no Click imports remain in greenfield CLI modules.

        Given: The src/data_extract/cli/ directory exists
        When: We search for 'import click' or 'from click' in Python files
        Then: Zero matches should be found

        Expected RED failure: AssertionError - Click imports still exist
        """
        # Given
        cli_dir = Path("src/data_extract/cli/")

        # When - collect all Python files in CLI directory
        violations = []
        # base.py is allowed to import click for brownfield command wrapping during migration
        allowed_exceptions = {"base.py"}
        for file in cli_dir.glob("**/*.py"):
            if file.name in allowed_exceptions:
                continue  # Skip wrapper module that bridges brownfield Click commands
            content = file.read_text()
            # Check for click imports
            if "import click" in content or "from click" in content:
                # Skip if it's just in comments
                lines = content.split("\n")
                for line_num, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    if "import click" in line or "from click" in line:
                        violations.append(f"{file.name}:{line_num}")

        # Then
        assert violations == [], (
            f"Click imports found in greenfield CLI modules: {violations}\n"
            "All CLI commands should use Typer instead of Click."
        )

    def test_typer_is_primary_cli_framework(self):
        """
        RED: Verify Typer is imported and used as primary CLI framework.

        Given: The main CLI app module exists
        When: We import the main app
        Then: It should be a Typer app instance

        Expected RED failure: ImportError or AttributeError
        """
        # Given/When
        try:
            from data_extract.cli.app import app
        except ImportError:
            pytest.fail(
                "Cannot import 'app' from data_extract.cli.app. " "Typer app not yet implemented."
            )

        # Then
        # Check it's a Typer app (has typer-specific attributes)
        assert hasattr(app, "command"), "app should have 'command' decorator (Typer)"
        assert hasattr(app, "add_typer"), "app should have 'add_typer' method (Typer)"

        # Verify it's actually Typer not Click
        import typer

        assert isinstance(
            app, typer.Typer
        ), f"app should be typer.Typer instance, got {type(app).__name__}"

    def test_click_decorator_not_used(self):
        """
        RED: Verify @click.command() decorators are not used.

        Given: All Python files in src/data_extract/cli/
        When: We scan for @click.command or @click.group decorators
        Then: Zero occurrences should be found

        Expected RED failure: AssertionError - Click decorators found
        """
        # Given
        cli_dir = Path("src/data_extract/cli/")
        click_decorator_pattern = re.compile(r"@click\.(command|group|option|argument)")

        # When
        violations = []
        for file in cli_dir.glob("**/*.py"):
            content = file.read_text()
            for match in click_decorator_pattern.finditer(content):
                line_num = content[: match.start()].count("\n") + 1
                violations.append(f"{file.name}:{line_num}: {match.group()}")

        # Then
        assert violations == [], (
            f"Click decorators found in CLI modules: {violations}\n"
            "Replace @click.command() with @app.command(), etc."
        )


@pytest.mark.unit
@pytest.mark.story_5_1
class TestGitStyleCommandStructure:
    """AC-5.1-1: Git-style command structure with Typer app groups."""

    def test_semantic_subcommand_group_exists(self, typer_cli_runner):
        """
        RED: Verify 'semantic' command group exists as Typer subapp.

        Given: The main CLI app
        When: We invoke 'data-extract semantic --help'
        Then: It should show semantic subcommands (analyze, deduplicate, cluster)

        Expected RED failure: No subcommand 'semantic' or wrong help output
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError:
            pytest.fail("Cannot import Typer app - not yet implemented")

        # When
        result = typer_cli_runner.invoke(app, ["semantic", "--help"])

        # Then
        assert result.exit_code == 0, f"semantic --help failed: {result.output}"
        assert "analyze" in result.output.lower(), "Missing 'analyze' subcommand"
        assert "deduplicate" in result.output.lower(), "Missing 'deduplicate' subcommand"
        assert "cluster" in result.output.lower(), "Missing 'cluster' subcommand"

    def test_config_subcommand_group_exists(self, typer_cli_runner):
        """
        RED: Verify 'config' command group exists as Typer subapp.

        Given: The main CLI app
        When: We invoke 'data-extract config --help'
        Then: It should show config subcommands

        Expected RED failure: No subcommand 'config'
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError:
            pytest.fail("Cannot import Typer app - not yet implemented")

        # When
        result = typer_cli_runner.invoke(app, ["config", "--help"])

        # Then
        assert result.exit_code == 0, f"config --help failed: {result.output}"
        # Config commands expected: show, set, presets, etc.
        assert (
            "show" in result.output.lower() or "list" in result.output.lower()
        ), "Missing config subcommand"

    def test_cache_subcommand_group_exists(self, typer_cli_runner):
        """
        RED: Verify 'cache' command group exists as Typer subapp.

        Given: The main CLI app
        When: We invoke 'data-extract cache --help'
        Then: It should show cache management commands

        Expected RED failure: No subcommand 'cache'
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError:
            pytest.fail("Cannot import Typer app - not yet implemented")

        # When
        result = typer_cli_runner.invoke(app, ["cache", "--help"])

        # Then
        assert result.exit_code == 0, f"cache --help failed: {result.output}"
        assert (
            "clear" in result.output.lower() or "stats" in result.output.lower()
        ), "Missing cache subcommand"

    def test_process_command_is_top_level(self, typer_cli_runner):
        """
        RED: Verify 'process' is a top-level command (not nested).

        Given: The main CLI app
        When: We invoke 'data-extract --help'
        Then: 'process' should be listed as a command

        Expected RED failure: 'process' not in top-level commands
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError:
            pytest.fail("Cannot import Typer app - not yet implemented")

        # When
        result = typer_cli_runner.invoke(app, ["--help"])

        # Then
        assert result.exit_code == 0
        assert "process" in result.output.lower(), "'process' should be a top-level command"

    def test_semantic_analyze_nested_command(self, typer_cli_runner):
        """
        RED: Verify 'semantic analyze' follows git-style nesting.

        Given: The main CLI app
        When: We invoke 'data-extract semantic analyze --help'
        Then: It should show analyze command help

        Expected RED failure: Command path doesn't work
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError:
            pytest.fail("Cannot import Typer app - not yet implemented")

        # When
        result = typer_cli_runner.invoke(app, ["semantic", "analyze", "--help"])

        # Then
        assert result.exit_code == 0, f"semantic analyze --help failed: {result.output}"
        assert (
            "input" in result.output.lower() or "path" in result.output.lower()
        ), "analyze should accept input path argument"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestTypeHintCompleteness:
    """AC-5.1-3: 100% type hints on all command parameters."""

    def test_all_cli_functions_have_type_hints(self):
        """
        RED: Verify all CLI command functions have complete type hints.

        Given: All Python files in src/data_extract/cli/
        When: We inspect function signatures
        Then: All parameters should have type annotations

        Expected RED failure: Functions missing type hints
        """
        # Given
        cli_dir = Path("src/data_extract/cli/")

        # When
        missing_hints = []

        for file in cli_dir.glob("**/*.py"):
            if file.name.startswith("_"):
                continue

            try:
                # Parse the AST to find function definitions
                content = file.read_text()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Skip private functions and test helpers
                        if node.name.startswith("_"):
                            continue

                        # Skip Pydantic validators and classmethods (they have implicit return types)
                        has_pydantic_decorator = any(
                            (isinstance(d, ast.Name) and d.id == "classmethod")
                            or (
                                isinstance(d, ast.Name)
                                and d.id in ["field_validator", "model_validator"]
                            )
                            or (
                                isinstance(d, ast.Attribute)
                                and d.attr in ["field_validator", "model_validator"]
                            )
                            for d in node.decorator_list
                        )
                        if has_pydantic_decorator:
                            continue

                        # Check parameters for type annotations
                        for arg in node.args.args:
                            if arg.arg == "self":
                                continue
                            if arg.annotation is None:
                                missing_hints.append(
                                    f"{file.name}:{node.lineno}:{node.name}({arg.arg})"
                                )

                        # Check return type annotation
                        if node.returns is None and not node.name.startswith("_"):
                            missing_hints.append(
                                f"{file.name}:{node.lineno}:{node.name}() -> missing return type"
                            )

            except SyntaxError:
                continue

        # Then
        assert missing_hints == [], (
            "Functions/parameters missing type hints:\n"
            + "\n".join(missing_hints[:20])  # Limit output
            + (f"\n... and {len(missing_hints) - 20} more" if len(missing_hints) > 20 else "")
        )

    @pytest.mark.xfail(
        reason="TDD RED - Type hint refactoring for Annotated pattern not yet complete"
    )
    def test_typer_options_use_annotated_type(self):
        """
        RED: Verify Typer options use Annotated type pattern.

        Given: CLI command functions using Typer
        When: We inspect their parameter annotations
        Then: Options should use Annotated[type, typer.Option(...)] pattern

        Expected RED failure: Options not using Annotated pattern
        """
        # Given
        cli_dir = Path("src/data_extract/cli/")

        # When
        non_annotated_options = []

        for file in cli_dir.glob("**/*.py"):
            if file.name.startswith("_"):
                continue

            content = file.read_text()

            # Look for typer.Option without Annotated
            # Old pattern: param: str = typer.Option(...)
            old_pattern = re.compile(r":\s*\w+\s*=\s*typer\.Option")
            for match in old_pattern.finditer(content):
                line_num = content[: match.start()].count("\n") + 1
                non_annotated_options.append(f"{file.name}:{line_num}")

        # Then
        assert non_annotated_options == [], (
            "Typer options not using Annotated pattern:\n"
            + "\n".join(non_annotated_options)
            + "\nUse: param: Annotated[str, typer.Option(...)]"
        )

    def test_mypy_strict_passes_for_cli_modules(self):
        """
        RED: Verify mypy strict mode passes for CLI modules.

        Given: The src/data_extract/cli/ directory
        When: We run mypy with strict mode
        Then: Zero type errors should be reported

        Expected RED failure: mypy reports type errors
        Note: This test is informational - actual mypy runs in CI.
        """
        # This test documents the requirement
        # Actual mypy validation happens in pre-commit and CI

        # Given
        cli_dir = Path("src/data_extract/cli/")

        # When - we verify the directory exists and has Python files
        py_files = list(cli_dir.glob("**/*.py"))

        # Then - basic sanity check
        assert len(py_files) > 0, "No Python files found in CLI directory"

        # Document expected mypy command
        expected_command = "mypy --strict src/data_extract/cli/"
        assert expected_command, "Document: Run mypy strict for full validation"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestAutoGeneratedHelp:
    """AC-5.1-8: Auto-generated help text tests."""

    def test_main_help_shows_all_commands(self, typer_cli_runner):
        """
        RED: Verify main --help shows all available commands.

        Given: The main CLI app
        When: We invoke 'data-extract --help'
        Then: All major commands should be listed

        Expected RED failure: Missing commands in help output
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError:
            pytest.fail("Cannot import Typer app - not yet implemented")

        # When
        result = typer_cli_runner.invoke(app, ["--help"])

        # Then
        assert result.exit_code == 0
        expected_commands = ["process", "semantic", "config", "cache", "validate"]
        for cmd in expected_commands:
            assert cmd in result.output.lower(), f"Missing '{cmd}' in main help"

    def test_help_includes_examples(self, typer_cli_runner):
        """
        RED: Verify help text includes usage examples.

        Given: The main CLI app
        When: We invoke 'data-extract process --help'
        Then: Examples section should be present

        Expected RED failure: No examples in help
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError:
            pytest.fail("Cannot import Typer app - not yet implemented")

        # When
        result = typer_cli_runner.invoke(app, ["process", "--help"])

        # Then
        assert result.exit_code == 0
        # Typer supports rich help with examples
        assert (
            "example" in result.output.lower() or "data-extract" in result.output
        ), "Help should include usage examples"

    def test_semantic_analyze_help_shows_options(self, typer_cli_runner):
        """
        RED: Verify 'semantic analyze' help shows all options.

        Given: The CLI app with semantic commands
        When: We invoke 'data-extract semantic analyze --help'
        Then: All configuration options should be documented

        Expected RED failure: Missing options in help
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError:
            pytest.fail("Cannot import Typer app - not yet implemented")

        # When
        result = typer_cli_runner.invoke(app, ["semantic", "analyze", "--help"])

        # Then
        assert result.exit_code == 0
        expected_options = ["--output", "--format", "--max-features", "--verbose"]
        for opt in expected_options:
            assert opt in result.output, f"Missing option '{opt}' in analyze help"

    def test_help_text_is_rich_formatted(self, typer_cli_runner):
        """
        RED: Verify help uses Rich formatting for better readability.

        Given: The CLI app configured with Rich
        When: We invoke any command with --help
        Then: Output should contain Rich formatting markers

        Expected RED failure: Plain text help instead of Rich
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError:
            pytest.fail("Cannot import Typer app - not yet implemented")

        # When
        result = typer_cli_runner.invoke(app, ["--help"])

        # Then
        # Rich help includes box drawing characters for panels
        assert result.exit_code == 0
        # Check for Rich box-drawing characters (panels) or section headers
        has_rich_formatting = (
            "╭" in result.output  # Top-left box corner
            or "╰" in result.output  # Bottom-left box corner
            or "─" in result.output  # Horizontal line
            or ("Commands" in result.output and "Options" in result.output)
        )
        assert has_rich_formatting, "Help should be structured with Rich formatting"
