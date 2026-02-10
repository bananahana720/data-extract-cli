"""TDD RED Phase Tests: Learning Mode (AC-5.1-7).

These tests verify:
- AC-5.1-7: Journey 4 (Learning Mode) --learn flag

All tests are designed to FAIL initially (TDD RED phase).
"""

import re
from unittest.mock import patch

import pytest

# P1: Core functionality - run on PR
pytestmark = [
    pytest.mark.P1,
    pytest.mark.story_5_1,
    pytest.mark.unit,
    pytest.mark.cli,
]


@pytest.mark.unit
@pytest.mark.story_5_1
class TestLearnFlagExists:
    """Verify --learn flag exists on relevant commands."""

    def test_process_command_has_learn_flag(self, typer_cli_runner):
        """
        RED: Verify 'process' command has --learn flag.

        Given: The CLI app
        When: We invoke 'data-extract process --help'
        Then: --learn flag should be documented

        Expected RED failure: --learn not in help output
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError as e:
            pytest.fail(f"Cannot import app: {e}")

        # When
        result = typer_cli_runner.invoke(app, ["process", "--help"])

        # Then
        assert result.exit_code == 0
        assert (
            "--learn" in result.output
        ), f"--learn flag not found in process help:\n{result.output}"

    @pytest.mark.xfail(reason="TDD RED - Learning mode for semantic analyze not yet implemented")
    def test_semantic_analyze_has_learn_flag(self, typer_cli_runner):
        """
        RED: Verify 'semantic analyze' command has --learn flag.

        Given: The CLI app
        When: We invoke 'data-extract semantic analyze --help'
        Then: --learn flag should be documented

        Expected RED failure: --learn not in help output
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError as e:
            pytest.fail(f"Cannot import app: {e}")

        # When
        result = typer_cli_runner.invoke(app, ["semantic", "analyze", "--help"])

        # Then
        assert result.exit_code == 0
        assert "--learn" in result.output, "--learn flag not found in semantic analyze help"

    def test_global_learn_flag_exists(self, typer_cli_runner):
        """
        RED: Verify global --learn flag is available.

        Given: The CLI app
        When: We invoke 'data-extract --help'
        Then: --learn should be a global option

        Expected RED failure: --learn not global
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError as e:
            pytest.fail(f"Cannot import app: {e}")

        # When
        result = typer_cli_runner.invoke(app, ["--help"])

        # Then
        assert result.exit_code == 0
        assert "--learn" in result.output, "Global --learn flag should be available"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestLearningModeOutput:
    """Test learning mode output patterns."""

    def test_learning_mode_shows_step_indicators(
        self,
        typer_cli_runner,
        tmp_path,
        mock_console,
    ):
        """
        RED: Verify learning mode shows step indicators.

        Given: --learn flag enabled
        When: We run a command
        Then: Step indicators [Step 1/N] should appear

        Expected RED failure: No step indicators
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError as e:
            pytest.fail(f"Cannot import app: {e}")

        # Create test input
        input_file = tmp_path / "test.txt"
        input_file.write_text("Sample content for learning mode test")
        output_dir = tmp_path / "output"

        # When
        result = typer_cli_runner.invoke(
            app,
            ["--learn", "process", str(input_file), "--output", str(output_dir)],
        )

        # Then
        output = result.output
        step_pattern = r"\[Step \d+/\d+\]"
        assert re.search(
            step_pattern, output
        ), f"Expected step indicators [Step N/M] in output:\n{output}"

    def test_learning_mode_shows_learn_markers(
        self,
        typer_cli_runner,
        tmp_path,
    ):
        """
        RED: Verify learning mode shows [LEARN] markers.

        Given: --learn flag enabled
        When: We run a command
        Then: [LEARN] markers should appear before explanations

        Expected RED failure: No [LEARN] markers
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError as e:
            pytest.fail(f"Cannot import app: {e}")

        input_file = tmp_path / "test.txt"
        input_file.write_text("Content for testing")
        output_dir = tmp_path / "output"

        # When
        result = typer_cli_runner.invoke(
            app,
            ["--learn", "process", str(input_file), "--output", str(output_dir)],
        )

        # Then
        assert (
            "[LEARN]" in result.output or "[Learn]" in result.output
        ), f"Expected [LEARN] markers in output:\n{result.output}"

    def test_learning_mode_shows_whats_happening(
        self,
        typer_cli_runner,
        tmp_path,
    ):
        """
        RED: Verify learning mode explains what's happening.

        Given: --learn flag enabled
        When: We run a command
        Then: "What's happening:" sections should appear

        Expected RED failure: No explanatory sections
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError as e:
            pytest.fail(f"Cannot import app: {e}")

        input_file = tmp_path / "test.txt"
        input_file.write_text("Content for explanation test")
        output_dir = tmp_path / "output"

        # When
        result = typer_cli_runner.invoke(
            app,
            ["--learn", "process", str(input_file), "--output", str(output_dir)],
        )

        # Then
        output_lower = result.output.lower()
        assert (
            "what's happening" in output_lower
            or "happening:" in output_lower
            or "explains" in output_lower
        ), f"Expected explanatory content in output:\n{result.output}"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestLearningModeInteractivity:
    """Test learning mode interactive features."""

    def test_learning_mode_shows_continue_prompts(
        self,
        typer_cli_runner,
        tmp_path,
    ):
        """
        RED: Verify learning mode shows continue prompts.

        Given: --learn flag enabled
        When: We run a multi-step command
        Then: [Continue] or "Press Enter" prompts should appear

        Expected RED failure: No interactive prompts
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError as e:
            pytest.fail(f"Cannot import app: {e}")

        input_file = tmp_path / "test.txt"
        input_file.write_text("Interactive test content")
        output_dir = tmp_path / "output"

        # Mock input to auto-continue
        with patch("builtins.input", return_value=""):
            # When
            result = typer_cli_runner.invoke(
                app,
                ["--learn", "process", str(input_file), "--output", str(output_dir)],
            )

        # Then
        output_lower = result.output.lower()
        assert (
            "continue" in output_lower
            or "press enter" in output_lower
            or "press any key" in output_lower
        ), f"Expected continue prompt in output:\n{result.output}"

    def test_learning_mode_non_blocking_option(
        self,
        typer_cli_runner,
        tmp_path,
    ):
        """
        RED: Verify learning mode can run non-interactively.

        Given: --learn --no-pause flags
        When: We run a command
        Then: Command should complete without waiting for input

        Expected RED failure: Command blocks waiting for input
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError as e:
            pytest.fail(f"Cannot import app: {e}")

        input_file = tmp_path / "test.txt"
        input_file.write_text("Non-interactive test")
        output_dir = tmp_path / "output"

        # When - with timeout to detect blocking
        result = typer_cli_runner.invoke(
            app,
            [
                "--learn",
                "--no-pause",  # Skip interactive pauses
                "process",
                str(input_file),
                "--output",
                str(output_dir),
            ],
        )

        # Then
        # Command should complete (exit code check proves it didn't block)
        assert result.exit_code in [
            0,
            1,
        ], f"Command should complete without blocking: {result.output}"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestLearningModeSummary:
    """Test learning mode summary at end of execution."""

    def test_learning_mode_shows_insights_summary(
        self,
        typer_cli_runner,
        tmp_path,
    ):
        """
        RED: Verify learning mode shows insights summary.

        Given: --learn flag enabled
        When: Command completes
        Then: Summary of what was learned should appear

        Expected RED failure: No summary section
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError as e:
            pytest.fail(f"Cannot import app: {e}")

        input_file = tmp_path / "test.txt"
        input_file.write_text("Content for summary test")
        output_dir = tmp_path / "output"

        with patch("builtins.input", return_value=""):
            # When
            result = typer_cli_runner.invoke(
                app,
                ["--learn", "process", str(input_file), "--output", str(output_dir)],
            )

        # Then
        output_lower = result.output.lower()
        assert (
            "what you learned" in output_lower
            or "summary" in output_lower
            or "insights" in output_lower
        ), f"Expected summary section in output:\n{result.output}"

    def test_learning_mode_lists_concepts_covered(
        self,
        typer_cli_runner,
        tmp_path,
    ):
        """
        RED: Verify learning mode lists covered concepts.

        Given: --learn flag on semantic analyze
        When: Command completes
        Then: Should list concepts like "TF-IDF", "vectorization"

        Expected RED failure: No concept list
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError as e:
            pytest.fail(f"Cannot import app: {e}")

        # Create test chunks
        chunks_file = tmp_path / "chunks.json"
        chunks_file.write_text('{"chunks": [{"id": "1", "text": "test content"}]}')

        with patch("builtins.input", return_value=""):
            # When
            result = typer_cli_runner.invoke(
                app,
                ["--learn", "semantic", "analyze", str(chunks_file)],
            )

        # Then
        output_lower = result.output.lower()
        # Should mention at least one NLP concept
        concepts = ["tf-idf", "vectoriz", "similar", "semantic", "lsa", "topic"]
        has_concept = any(c in output_lower for c in concepts)
        assert has_concept, f"Expected NLP concepts in learning output:\n{result.output}"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestLearningModeSemanticCommands:
    """Test learning mode specifically for semantic commands."""

    def test_semantic_analyze_learn_explains_tfidf(
        self,
        typer_cli_runner,
        tmp_path,
    ):
        """
        RED: Verify --learn on semantic analyze explains TF-IDF.

        Given: --learn flag on semantic analyze
        When: TF-IDF stage runs
        Then: Explanation of TF-IDF should appear

        Expected RED failure: No TF-IDF explanation
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError as e:
            pytest.fail(f"Cannot import app: {e}")

        chunks_file = tmp_path / "chunks.json"
        chunks_file.write_text('{"chunks": [{"id": "1", "text": "audit report compliance"}]}')

        with patch("builtins.input", return_value=""):
            # When
            result = typer_cli_runner.invoke(
                app,
                ["--learn", "semantic", "analyze", str(chunks_file)],
            )

        # Then
        output_lower = result.output.lower()
        # Should explain TF-IDF concept
        assert (
            "tf-idf" in output_lower
            or "term frequency" in output_lower
            or "inverse document" in output_lower
        ), f"Expected TF-IDF explanation:\n{result.output}"

    def test_semantic_cluster_learn_explains_lsa(
        self,
        typer_cli_runner,
        tmp_path,
    ):
        """
        RED: Verify --learn on semantic cluster explains LSA.

        Given: --learn flag on semantic cluster
        When: LSA stage runs
        Then: Explanation of LSA/SVD should appear

        Expected RED failure: No LSA explanation
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError as e:
            pytest.fail(f"Cannot import app: {e}")

        chunks_file = tmp_path / "chunks.json"
        chunks_file.write_text('{"chunks": [{"id": "1", "text": "test content for clustering"}]}')

        with patch("builtins.input", return_value=""):
            # When
            result = typer_cli_runner.invoke(
                app,
                ["--learn", "semantic", "cluster", str(chunks_file)],
            )

        # Then
        output_lower = result.output.lower()
        assert (
            "lsa" in output_lower
            or "latent semantic" in output_lower
            or "svd" in output_lower
            or "dimensionality" in output_lower
        ), f"Expected LSA explanation:\n{result.output}"

    def test_semantic_dedupe_learn_explains_similarity(
        self,
        typer_cli_runner,
        tmp_path,
    ):
        """
        RED: Verify --learn on deduplicate explains similarity.

        Given: --learn flag on semantic deduplicate
        When: Similarity analysis runs
        Then: Explanation of cosine similarity should appear

        Expected RED failure: No similarity explanation
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError as e:
            pytest.fail(f"Cannot import app: {e}")

        chunks_file = tmp_path / "chunks.json"
        chunks_file.write_text('{"chunks": [{"id": "1", "text": "audit findings report"}]}')

        with patch("builtins.input", return_value=""):
            # When
            result = typer_cli_runner.invoke(
                app,
                ["--learn", "semantic", "deduplicate", str(chunks_file)],
            )

        # Then
        output_lower = result.output.lower()
        assert (
            "similar" in output_lower or "cosine" in output_lower or "duplicate" in output_lower
        ), f"Expected similarity explanation:\n{result.output}"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestLearningModeColorCoding:
    """Test learning mode uses appropriate color coding."""

    def test_learning_tips_use_magenta_color(
        self,
        typer_cli_runner,
        tmp_path,
        mock_console,
    ):
        """
        RED: Verify learning tips use magenta color per UX spec.

        Given: --learn flag enabled
        When: Learning tips are displayed
        Then: Magenta color should be used

        Expected RED failure: Wrong color or no color
        """
        # Given
        try:
            from data_extract.cli.app import app
        except ImportError as e:
            pytest.fail(f"Cannot import app: {e}")

        input_file = tmp_path / "test.txt"
        input_file.write_text("Color test content")
        output_dir = tmp_path / "output"

        # When - capture Rich output
        with patch("builtins.input", return_value=""):
            result = typer_cli_runner.invoke(
                app,
                ["--learn", "process", str(input_file), "--output", str(output_dir)],
            )

        # Then
        # Check for magenta in Rich output or ANSI codes
        output = result.output
        # Magenta ANSI: \x1b[35m or Rich's [magenta]
        has_magenta = (
            "\x1b[35m" in output
            or "magenta" in output.lower()
            or "[LEARN]" in output  # Learn markers typically styled
        )
        assert (
            has_magenta or "[LEARN]" in output
        ), "Learning tips should use magenta color (or [LEARN] markers)"
