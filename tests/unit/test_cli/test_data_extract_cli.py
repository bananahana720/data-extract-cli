"""Unit tests for greenfield CLI (src/data_extract/cli.py).

This test module covers the Typer-based CLI.
Tests focus on command logic, argument validation, and error handling.

Note: Epic 5 adds enhanced UX features to the CLI.
"""

from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("typer", reason="Typer is required for unit CLI tests")
from typer.testing import CliRunner  # noqa: E402

from data_extract.cli import app  # noqa: E402
from data_extract.output.organization import OrganizationStrategy  # noqa: E402

# P0: CLI entry point - critical path testing
pytestmark = [
    pytest.mark.P0,
    pytest.mark.unit,
    pytest.mark.cli,
]


@pytest.fixture
def cli_runner():
    """Create Typer test runner for CLI invocation."""
    return CliRunner()


@pytest.fixture
def sample_input_file(tmp_path):
    """Create sample input file for testing."""
    input_file = tmp_path / "sample.pdf"
    input_file.write_text("Sample PDF content")
    return input_file


@pytest.fixture
def mock_output_writer():
    """Mock OutputWriter for unit testing (no actual file I/O)."""
    with patch("data_extract.cli.OutputWriter") as mock:
        # Configure mock to return realistic FormatResult
        mock_result = MagicMock()
        mock_result.chunk_count = 3
        mock_result.file_size_bytes = 1024
        mock_result.duration_seconds = 0.15
        mock_result.errors = []

        mock_instance = MagicMock()
        mock_instance.write.return_value = mock_result
        mock.return_value = mock_instance

        yield mock


class TestCLIGroup:
    """Test main CLI group and version option."""

    def test_app_group_exists(self, cli_runner):
        """Should have main app group."""
        # WHEN: Invoking CLI with --help
        result = cli_runner.invoke(app, ["--help"])

        # THEN: Should display help text
        assert result.exit_code == 0
        assert (
            "Enterprise document processing" in result.output
            or "Data Extraction Tool" in result.output
        )
        assert "process" in result.output
        assert "version" in result.output or "--version" in result.output

    def test_app_version_option(self, cli_runner):
        """Should display version with --version flag."""
        # WHEN: Invoking CLI with --version
        result = cli_runner.invoke(app, ["--version"])

        # THEN: Should display version number (v0.2.0 in Epic 5)
        assert result.exit_code == 0
        assert "0.2.0" in result.output or "v0.2.0" in result.output

    def test_no_command_shows_help(self, cli_runner):
        """Should show help when no command provided."""
        # WHEN: Invoking CLI with no arguments
        result = cli_runner.invoke(app, [])

        # THEN: Should display usage information (Click returns 0 for groups without required commands)
        # Note: Click may return 0 or 2 depending on group configuration
        assert result.exit_code in [0, 2]
        assert "Usage:" in result.output or "Commands:" in result.output


class TestVersionCommand:
    """Test version command."""

    @pytest.mark.skip(reason="Brownfield migration - version command output format pending")
    def test_version_command_output(self, cli_runner):
        """Should display detailed version information."""
        # WHEN: Invoking version command
        result = cli_runner.invoke(app, ["version"])

        # THEN: Should display version details
        assert result.exit_code == 0
        assert "Data Extraction Tool v0.1.0" in result.output
        assert "Epic 3, Story 3.5" in result.output
        assert "Epic 5" in result.output


class TestProcessCommandHelp:
    """Test process command help and documentation."""

    @pytest.mark.skip(reason="Brownfield migration - help output format pending")
    def test_process_help(self, cli_runner):
        """Should display process command help."""
        # WHEN: Invoking process with --help
        result = cli_runner.invoke(app, ["process", "--help"])

        # THEN: Should display comprehensive help
        assert result.exit_code == 0
        assert "Process a document" in result.output
        assert "--format" in result.output
        assert "--output" in result.output
        assert "--per-chunk" in result.output
        assert "--include-metadata" in result.output
        assert "--organize" in result.output
        assert "--strategy" in result.output
        assert "--delimiter" in result.output

    def test_process_shows_examples(self, cli_runner):
        """Should show usage examples in help text."""
        # WHEN: Invoking process with --help
        result = cli_runner.invoke(app, ["process", "--help"])

        # THEN: Should include examples
        assert result.exit_code == 0
        assert "Example usage:" in result.output or "data-extract process" in result.output


class TestProcessCommandValidation:
    """Test process command argument validation."""

    def test_missing_input_file_error(self, cli_runner, tmp_path):
        """Should error when input file doesn't exist."""
        # GIVEN: Non-existent input file
        nonexistent = tmp_path / "missing.pdf"
        output_file = tmp_path / "output.txt"

        # WHEN: Invoking process with missing file
        result = cli_runner.invoke(
            app, ["process", str(nonexistent), "--format", "txt", "--output", str(output_file)]
        )

        # THEN: Should exit with error
        assert result.exit_code != 0
        # Click automatically validates file existence

    @pytest.mark.skip(reason="Brownfield migration - argument validation pending")
    def test_missing_output_argument_error(self, cli_runner, sample_input_file):
        """Should error when --output is not provided."""
        # WHEN: Invoking process without --output
        result = cli_runner.invoke(app, ["process", str(sample_input_file), "--format", "txt"])

        # THEN: Should exit with error
        assert result.exit_code != 0
        assert "Missing option" in result.output or "--output" in result.output

    def test_invalid_format_type_error(self, cli_runner, sample_input_file, tmp_path):
        """Should error when invalid format type is provided."""
        # GIVEN: Invalid format type
        output_file = tmp_path / "output.xml"

        # WHEN: Invoking process with invalid format
        result = cli_runner.invoke(
            app,
            [
                "process",
                str(sample_input_file),
                "--format",
                "xml",  # Invalid - only json/txt supported
                "--output",
                str(output_file),
            ],
        )

        # THEN: Should exit with error
        assert result.exit_code != 0
        assert "Invalid value" in result.output or "xml" in result.output

    @pytest.mark.skip(reason="Brownfield migration - OutputWriter mock needs update")
    def test_organize_without_strategy_error(
        self, cli_runner, sample_input_file, tmp_path, mock_output_writer
    ):
        """Should error when --organize is set without --strategy."""
        # GIVEN: Organize flag without strategy
        output_dir = tmp_path / "output"

        # WHEN: Invoking process with --organize but no --strategy
        result = cli_runner.invoke(
            app,
            [
                "process",
                str(sample_input_file),
                "--format",
                "txt",
                "--output",
                str(output_dir),
                "--organize",
            ],
        )

        # THEN: Should exit with validation error
        assert result.exit_code == 1
        assert "Error" in result.output
        assert "organize" in result.output.lower()
        assert "strategy" in result.output.lower()

    @pytest.mark.skip(reason="Brownfield migration - OutputWriter mock needs update")
    def test_strategy_without_organize_error(
        self, cli_runner, sample_input_file, tmp_path, mock_output_writer
    ):
        """Should error when --strategy is set without --organize."""
        # GIVEN: Strategy without organize flag
        output_dir = tmp_path / "output"

        # WHEN: Invoking process with --strategy but no --organize
        result = cli_runner.invoke(
            app,
            [
                "process",
                str(sample_input_file),
                "--format",
                "txt",
                "--output",
                str(output_dir),
                "--strategy",
                "by_document",
            ],
        )

        # THEN: Should exit with validation error
        assert result.exit_code == 1
        assert "Error" in result.output
        assert "strategy" in result.output.lower()
        assert "organize" in result.output.lower()

    @pytest.mark.skip(reason="Brownfield migration - strategy validation pending")
    def test_invalid_strategy_value_error(self, cli_runner, sample_input_file, tmp_path):
        """Should error when invalid strategy value is provided."""
        # GIVEN: Invalid strategy value
        output_dir = tmp_path / "output"

        # WHEN: Invoking process with invalid strategy
        result = cli_runner.invoke(
            app,
            [
                "process",
                str(sample_input_file),
                "--format",
                "txt",
                "--output",
                str(output_dir),
                "--organize",
                "--strategy",
                "invalid_strategy",
            ],
        )

        # THEN: Should exit with error
        assert result.exit_code != 0
        assert "Invalid value" in result.output or "invalid_strategy" in result.output


class TestProcessCommandHappyPaths:
    """Test process command successful execution paths."""

    @pytest.mark.skip(reason="Brownfield migration - OutputWriter mock needs update")
    def test_process_txt_concatenated_basic(
        self, cli_runner, sample_input_file, tmp_path, mock_output_writer
    ):
        """Should process file and create TXT output (concatenated mode)."""
        # GIVEN: Input file and output path
        output_file = tmp_path / "output.txt"

        # WHEN: Invoking process with basic TXT format
        result = cli_runner.invoke(
            app,
            ["process", str(sample_input_file), "--format", "txt", "--output", str(output_file)],
        )

        # THEN: Should succeed and display results
        assert result.exit_code == 0
        assert "Processing:" in result.output
        assert str(sample_input_file) in result.output
        assert "Output format: TXT" in result.output
        assert "Processing complete!" in result.output
        assert "Chunks written: 3" in result.output

        # Verify OutputWriter.write was called
        mock_output_writer.return_value.write.assert_called_once()
        call_kwargs = mock_output_writer.return_value.write.call_args[1]
        assert call_kwargs["format_type"] == "txt"
        assert call_kwargs["output_path"] == output_file
        assert call_kwargs["organize"] is False
        assert call_kwargs["per_chunk"] is False
        assert call_kwargs["include_metadata"] is False

    @pytest.mark.skip(reason="Brownfield migration - OutputWriter mock needs update")
    def test_process_json_format(self, cli_runner, sample_input_file, tmp_path, mock_output_writer):
        """Should process file and create JSON output."""
        # GIVEN: Input file and output path
        output_file = tmp_path / "output.json"

        # WHEN: Invoking process with JSON format
        result = cli_runner.invoke(
            app,
            ["process", str(sample_input_file), "--format", "json", "--output", str(output_file)],
        )

        # THEN: Should succeed
        assert result.exit_code == 0
        assert "Output format: JSON" in result.output
        assert "Processing complete!" in result.output

        # Verify OutputWriter.write called with json format
        call_kwargs = mock_output_writer.return_value.write.call_args[1]
        assert call_kwargs["format_type"] == "json"

    @pytest.mark.skip(reason="Brownfield migration - OutputWriter mock needs update")
    def test_process_txt_per_chunk_mode(
        self, cli_runner, sample_input_file, tmp_path, mock_output_writer
    ):
        """Should process with --per-chunk flag for individual files."""
        # GIVEN: Output directory for per-chunk files
        output_dir = tmp_path / "chunks"

        # WHEN: Invoking process with --per-chunk
        result = cli_runner.invoke(
            app,
            [
                "process",
                str(sample_input_file),
                "--format",
                "txt",
                "--output",
                str(output_dir),
                "--per-chunk",
            ],
        )

        # THEN: Should succeed with per_chunk=True
        assert result.exit_code == 0
        call_kwargs = mock_output_writer.return_value.write.call_args[1]
        assert call_kwargs["per_chunk"] is True

    @pytest.mark.skip(reason="Brownfield migration - OutputWriter mock needs update")
    def test_process_with_metadata_headers(
        self, cli_runner, sample_input_file, tmp_path, mock_output_writer
    ):
        """Should process with --include-metadata flag."""
        # GIVEN: Output file
        output_file = tmp_path / "output.txt"

        # WHEN: Invoking process with --include-metadata
        result = cli_runner.invoke(
            app,
            [
                "process",
                str(sample_input_file),
                "--format",
                "txt",
                "--output",
                str(output_file),
                "--include-metadata",
            ],
        )

        # THEN: Should succeed with include_metadata=True
        assert result.exit_code == 0
        call_kwargs = mock_output_writer.return_value.write.call_args[1]
        assert call_kwargs["include_metadata"] is True

    @pytest.mark.skip(reason="Brownfield migration - OutputWriter mock needs update")
    def test_process_custom_delimiter(
        self, cli_runner, sample_input_file, tmp_path, mock_output_writer
    ):
        """Should process with custom delimiter pattern."""
        # GIVEN: Custom delimiter
        custom_delimiter = "--- CHUNK {{n}} ---"
        output_file = tmp_path / "output.txt"

        # WHEN: Invoking process with --delimiter
        result = cli_runner.invoke(
            app,
            [
                "process",
                str(sample_input_file),
                "--format",
                "txt",
                "--output",
                str(output_file),
                "--delimiter",
                custom_delimiter,
            ],
        )

        # THEN: Should succeed with custom delimiter
        assert result.exit_code == 0
        call_kwargs = mock_output_writer.return_value.write.call_args[1]
        assert call_kwargs["delimiter"] == custom_delimiter

    @pytest.mark.skip(reason="Brownfield migration - OutputWriter mock needs update")
    def test_process_with_by_document_strategy(
        self, cli_runner, sample_input_file, tmp_path, mock_output_writer
    ):
        """Should process with --organize and --strategy by_document."""
        # GIVEN: Output directory and by_document strategy
        output_dir = tmp_path / "organized"

        # WHEN: Invoking process with organization
        result = cli_runner.invoke(
            app,
            [
                "process",
                str(sample_input_file),
                "--format",
                "txt",
                "--output",
                str(output_dir),
                "--per-chunk",
                "--organize",
                "--strategy",
                "by_document",
            ],
        )

        # THEN: Should succeed with organization enabled
        assert result.exit_code == 0
        call_kwargs = mock_output_writer.return_value.write.call_args[1]
        assert call_kwargs["organize"] is True
        assert call_kwargs["strategy"] == OrganizationStrategy.BY_DOCUMENT

    @pytest.mark.skip(reason="Brownfield migration - OutputWriter mock needs update")
    def test_process_with_by_entity_strategy(
        self, cli_runner, sample_input_file, tmp_path, mock_output_writer
    ):
        """Should process with --strategy by_entity."""
        # GIVEN: Output directory and by_entity strategy
        output_dir = tmp_path / "organized"

        # WHEN: Invoking process with by_entity
        result = cli_runner.invoke(
            app,
            [
                "process",
                str(sample_input_file),
                "--format",
                "txt",
                "--output",
                str(output_dir),
                "--per-chunk",
                "--organize",
                "--strategy",
                "by_entity",
            ],
        )

        # THEN: Should succeed with BY_ENTITY strategy
        assert result.exit_code == 0
        call_kwargs = mock_output_writer.return_value.write.call_args[1]
        assert call_kwargs["strategy"] == OrganizationStrategy.BY_ENTITY

    @pytest.mark.skip(reason="Brownfield migration - OutputWriter mock needs update")
    def test_process_with_flat_strategy(
        self, cli_runner, sample_input_file, tmp_path, mock_output_writer
    ):
        """Should process with --strategy flat."""
        # GIVEN: Output directory and flat strategy
        output_dir = tmp_path / "organized"

        # WHEN: Invoking process with flat
        result = cli_runner.invoke(
            app,
            [
                "process",
                str(sample_input_file),
                "--format",
                "txt",
                "--output",
                str(output_dir),
                "--per-chunk",
                "--organize",
                "--strategy",
                "flat",
            ],
        )

        # THEN: Should succeed with FLAT strategy
        assert result.exit_code == 0
        call_kwargs = mock_output_writer.return_value.write.call_args[1]
        assert call_kwargs["strategy"] == OrganizationStrategy.FLAT

    @pytest.mark.skip(reason="Brownfield migration - OutputWriter mock needs update")
    def test_process_combined_flags(
        self, cli_runner, sample_input_file, tmp_path, mock_output_writer
    ):
        """Should process with multiple flags combined."""
        # GIVEN: All optional flags
        output_dir = tmp_path / "output"

        # WHEN: Invoking process with all flags
        result = cli_runner.invoke(
            app,
            [
                "process",
                str(sample_input_file),
                "--format",
                "txt",
                "--output",
                str(output_dir),
                "--per-chunk",
                "--include-metadata",
                "--organize",
                "--strategy",
                "by_document",
                "--delimiter",
                "=== CHUNK {{n}} ===",
            ],
        )

        # THEN: Should succeed with all options
        assert result.exit_code == 0
        call_kwargs = mock_output_writer.return_value.write.call_args[1]
        assert call_kwargs["per_chunk"] is True
        assert call_kwargs["include_metadata"] is True
        assert call_kwargs["organize"] is True
        assert call_kwargs["strategy"] == OrganizationStrategy.BY_DOCUMENT
        assert call_kwargs["delimiter"] == "=== CHUNK {{n}} ==="


class TestProcessCommandStatisticsDisplay:
    """Test process command statistics and output display."""

    @pytest.mark.skip(reason="Brownfield migration - OutputWriter mock needs update")
    def test_displays_processing_statistics(
        self, cli_runner, sample_input_file, tmp_path, mock_output_writer
    ):
        """Should display processing statistics after completion."""
        # GIVEN: Output file
        output_file = tmp_path / "output.txt"

        # WHEN: Invoking process
        result = cli_runner.invoke(
            app,
            ["process", str(sample_input_file), "--format", "txt", "--output", str(output_file)],
        )

        # THEN: Should display statistics
        assert result.exit_code == 0
        assert "Processing complete!" in result.output
        assert "Chunks written: 3" in result.output
        assert "Output size:" in result.output
        assert "1,024 bytes" in result.output
        assert "Duration:" in result.output
        assert "0.15s" in result.output

    @pytest.mark.skip(reason="Brownfield migration - OutputWriter mock needs update")
    def test_displays_warnings_when_errors_exist(self, cli_runner, sample_input_file, tmp_path):
        """Should display warnings when FormatResult contains errors."""
        # GIVEN: Mock OutputWriter that returns errors
        with patch("data_extract.cli.OutputWriter") as mock:
            mock_result = MagicMock()
            mock_result.chunk_count = 2
            mock_result.file_size_bytes = 512
            mock_result.duration_seconds = 0.10
            mock_result.errors = ["Warning: Some chunks had low quality scores"]

            mock_instance = MagicMock()
            mock_instance.write.return_value = mock_result
            mock.return_value = mock_instance

            output_file = tmp_path / "output.txt"

            # WHEN: Invoking process
            result = cli_runner.invoke(
                app,
                [
                    "process",
                    str(sample_input_file),
                    "--format",
                    "txt",
                    "--output",
                    str(output_file),
                ],
            )

            # THEN: Should display warnings
            assert result.exit_code == 0  # Still succeeds despite warnings
            assert "Warnings (1):" in result.output
            assert "low quality scores" in result.output

    @pytest.mark.skip(reason="Brownfield migration - OutputWriter mock needs update")
    def test_no_warnings_section_when_no_errors(
        self, cli_runner, sample_input_file, tmp_path, mock_output_writer
    ):
        """Should not display warnings section when no errors."""
        # GIVEN: Mock OutputWriter with empty errors
        output_file = tmp_path / "output.txt"

        # WHEN: Invoking process
        result = cli_runner.invoke(
            app,
            ["process", str(sample_input_file), "--format", "txt", "--output", str(output_file)],
        )

        # THEN: Should not display warnings
        assert result.exit_code == 0
        assert "Warnings" not in result.output


class TestProcessCommandErrorHandling:
    """Test process command error handling."""

    @pytest.mark.skip(reason="Brownfield migration - OutputWriter mock needs update")
    def test_handles_output_writer_exception(self, cli_runner, sample_input_file, tmp_path):
        """Should handle exceptions from OutputWriter gracefully."""
        # GIVEN: Mock OutputWriter that raises exception
        with patch("data_extract.cli.OutputWriter") as mock:
            mock_instance = MagicMock()
            mock_instance.write.side_effect = ValueError("Invalid chunk data")
            mock.return_value = mock_instance

            output_file = tmp_path / "output.txt"

            # WHEN: Invoking process (exception raised)
            result = cli_runner.invoke(
                app,
                [
                    "process",
                    str(sample_input_file),
                    "--format",
                    "txt",
                    "--output",
                    str(output_file),
                ],
            )

            # THEN: Should exit with error
            assert result.exit_code == 1
            assert "Error:" in result.output
            assert "Invalid chunk data" in result.output

    @pytest.mark.skip(reason="Brownfield migration - OutputWriter mock needs update")
    def test_exits_with_code_1_on_error(self, cli_runner, sample_input_file, tmp_path):
        """Should exit with code 1 when error occurs."""
        # GIVEN: Mock that raises exception
        with patch("data_extract.cli.OutputWriter") as mock:
            mock.side_effect = RuntimeError("Unexpected error")

            output_file = tmp_path / "output.txt"

            # WHEN: Invoking process
            result = cli_runner.invoke(
                app,
                [
                    "process",
                    str(sample_input_file),
                    "--format",
                    "txt",
                    "--output",
                    str(output_file),
                ],
            )

            # THEN: Should exit with code 1
            assert result.exit_code == 1


class TestDemoChunksHelper:
    """Test _create_demo_chunks helper function."""

    @pytest.mark.skip(reason="Brownfield migration - _create_demo_chunks not yet exposed in CLI")
    def test_creates_three_demo_chunks(self, tmp_path):
        """Should create 3 demo chunks with varied content."""
        # GIVEN: Sample input file
        from data_extract.cli import _create_demo_chunks

        input_file = tmp_path / "sample.pdf"

        # WHEN: Creating demo chunks
        chunks = _create_demo_chunks(input_file)

        # THEN: Should return 3 chunks
        assert len(chunks) == 3
        assert all(hasattr(chunk, "id") for chunk in chunks)
        assert all(hasattr(chunk, "text") for chunk in chunks)
        assert all(hasattr(chunk, "metadata") for chunk in chunks)

    @pytest.mark.skip(reason="Brownfield migration - _create_demo_chunks not yet exposed in CLI")
    def test_demo_chunks_have_entity_tags(self, tmp_path):
        """Should create chunks with entity tags for testing."""
        # GIVEN: Sample input file
        from data_extract.cli import _create_demo_chunks

        input_file = tmp_path / "sample.pdf"

        # WHEN: Creating demo chunks
        chunks = _create_demo_chunks(input_file)

        # THEN: Should have entity tags
        assert chunks[0].metadata.entity_tags  # First chunk has Risk-001
        assert chunks[1].metadata.entity_tags  # Second chunk has Control-042, Risk-001
        assert chunks[2].metadata.entity_tags  # Third chunk has Policy-123

    @pytest.mark.skip(reason="Brownfield migration - _create_demo_chunks not yet exposed in CLI")
    def test_demo_chunks_have_quality_scores(self, tmp_path):
        """Should create chunks with quality scores."""
        # GIVEN: Sample input file
        from data_extract.cli import _create_demo_chunks

        input_file = tmp_path / "sample.pdf"

        # WHEN: Creating demo chunks
        chunks = _create_demo_chunks(input_file)

        # THEN: Should have quality scores
        for chunk in chunks:
            assert chunk.metadata.quality is not None
            assert chunk.metadata.quality.overall == 0.95
            assert chunk.metadata.quality.completeness == 0.98

    @pytest.mark.skip(reason="Brownfield migration - _create_demo_chunks not yet exposed in CLI")
    def test_demo_chunks_use_input_file_path(self, tmp_path):
        """Should use input file path in chunk metadata."""
        # GIVEN: Specific input file path
        from data_extract.cli import _create_demo_chunks

        input_file = tmp_path / "test_document.pdf"

        # WHEN: Creating demo chunks
        chunks = _create_demo_chunks(input_file)

        # THEN: Should reference input file
        for chunk in chunks:
            assert chunk.metadata.source_file == input_file
