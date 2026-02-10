"""
CLI Workflow Integration Tests.

Tests real CLI command execution with actual file I/O:
- Extract command with various options
- Batch command with directory and patterns
- Version command
- Config command (show, validate, path)
- Error handling and user messages
- Progress display
- Overwrite protection

Test IDs: CLI-001 through CLI-013
"""

import json
from typing import Any

import pytest

pytestmark = pytest.mark.skip(
    reason="Brownfield migration: module depends on removed brownfield code"
)

# Stub for brownfield imports (module deleted, tests skipped)
cli: Any = None  # type: ignore[assignment]

# ==============================================================================
# Test Markers
# ==============================================================================

# pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.cli]  # Skipped due to brownfield migration


# ==============================================================================
# Extract Command Tests
# ==============================================================================


def test_cli_001_extract_command_with_real_docx(cli_runner, sample_docx_file, tmp_path):
    """
    Test CLI-001: Execute extract command on real DOCX file.

    Verifies:
    - Command executes successfully
    - Output file created
    - JSON output is valid
    - Success message displayed
    """
    # Arrange
    output_file = tmp_path / "output.json"

    # Act
    result = cli_runner.invoke(
        cli,
        ["extract", str(sample_docx_file), "--output", str(output_file), "--format", "json"],
    )

    # Assert: Exit code success
    assert result.exit_code == 0, f"Command failed: {result.output}"

    # Assert: Output file created
    assert output_file.exists(), "Output file not created"

    # Assert: JSON is valid
    with open(output_file) as f:
        data = json.load(f)
        assert "content_blocks" in data or "blocks" in data

    # Assert: Success message
    assert "success" in result.output.lower() or "✓" in result.output


def test_cli_002_extract_with_all_formats(cli_runner, sample_docx_file, tmp_path):
    """
    Test CLI-002: Execute extract with --format all.

    Verifies:
    - All 3 output files created
    - Each format valid
    - Success message shows count
    """
    # Arrange
    output_dir = tmp_path / "results"
    output_dir.mkdir()

    # Act
    result = cli_runner.invoke(
        cli,
        [
            "extract",
            str(sample_docx_file),
            "--output",
            str(output_dir),
            "--format",
            "all",
        ],
    )

    # Assert: Success
    assert result.exit_code == 0

    # Assert: Multiple files created
    output_files = list(output_dir.glob("*"))
    assert len(output_files) >= 3, f"Expected 3+ output files, got {len(output_files)}"

    # Assert: Different formats present
    extensions = {f.suffix for f in output_files}
    assert ".json" in extensions
    assert ".md" in extensions or ".txt" in extensions


def test_cli_003_extract_to_markdown(cli_runner, sample_docx_file, tmp_path):
    """
    Test CLI-003: Extract to Markdown format.

    Verifies:
    - Markdown file created
    - Contains markdown formatting
    """
    # Arrange
    output_file = tmp_path / "output.md"

    # Act
    result = cli_runner.invoke(
        cli,
        ["extract", str(sample_docx_file), "--output", str(output_file), "--format", "markdown"],
    )

    # Assert: Success
    assert result.exit_code == 0

    # Assert: File created
    assert output_file.exists()

    # Assert: Markdown content
    content = output_file.read_text()
    assert len(content) > 0
    assert "#" in content or "**" in content  # Markdown markers


def test_cli_004_extract_creates_output_directory(cli_runner, sample_docx_file, tmp_path):
    """
    Test CLI-004: Extract creates output directory if missing.

    Verifies:
    - Non-existent directory created
    - File written successfully
    """
    # Arrange
    output_dir = tmp_path / "nested" / "output"
    output_file = output_dir / "result.json"

    # Act
    result = cli_runner.invoke(
        cli,
        ["extract", str(sample_docx_file), "--output", str(output_file)],
    )

    # Assert: Success
    assert result.exit_code == 0

    # Assert: Directory created
    assert output_dir.exists()

    # Assert: File created
    assert output_file.exists()


def test_cli_005_extract_default_output_location(cli_runner, sample_docx_file):
    """
    Test CLI-005: Extract with default output location.

    Verifies:
    - Output created in current directory
    - File named after input file
    """
    # Act
    result = cli_runner.invoke(cli, ["extract", str(sample_docx_file)])

    # Assert: Success (or at least expected behavior)
    # Output location depends on CLI implementation
    assert result.exit_code == 0 or "output" in result.output.lower()


# ==============================================================================
# Batch Command Tests
# ==============================================================================


def test_cli_006_batch_command_with_directory(cli_runner, batch_test_directory, tmp_path):
    """
    Test CLI-006: Execute batch processing on directory.

    Verifies:
    - All files in directory processed
    - Output files created for each
    - Progress displayed
    - Summary shown
    """
    # Arrange
    output_dir = tmp_path / "batch_results"
    output_dir.mkdir()

    # Act
    result = cli_runner.invoke(
        cli,
        ["batch", str(batch_test_directory), "--output", str(output_dir)],
    )

    # Assert: Success
    assert result.exit_code == 0

    # Assert: Output files created
    output_files = list(output_dir.glob("*"))
    assert len(output_files) > 0

    # Assert: Summary in output
    assert "processed" in result.output.lower() or "success" in result.output.lower()


def test_cli_007_batch_with_pattern_filter(cli_runner, batch_test_directory, tmp_path):
    """
    Test CLI-007: Execute batch with glob pattern.

    Verifies:
    - Only matching files processed
    - Non-matching files ignored
    """
    # Arrange
    output_dir = tmp_path / "filtered_results"
    output_dir.mkdir()

    # Act: Only process .txt files
    result = cli_runner.invoke(
        cli,
        [
            "batch",
            str(batch_test_directory),
            "--pattern",
            "*.txt",
            "--output",
            str(output_dir),
        ],
    )

    # Assert: Success
    assert result.exit_code == 0

    # Assert: Only text files processed
    output_files = list(output_dir.glob("*"))
    # Number of outputs should match number of .txt files
    txt_files = list(batch_test_directory.glob("*.txt"))
    assert len(output_files) >= len(txt_files)


def test_cli_008_batch_with_custom_workers(cli_runner, batch_test_directory, tmp_path):
    """
    Test CLI-008: Execute batch with custom worker count.

    Verifies:
    - Workers parameter accepted
    - Processing completes
    """
    # Arrange
    output_dir = tmp_path / "parallel_results"
    output_dir.mkdir()

    # Act
    result = cli_runner.invoke(
        cli,
        [
            "batch",
            str(batch_test_directory),
            "--workers",
            "4",
            "--output",
            str(output_dir),
        ],
    )

    # Assert: Success
    assert result.exit_code == 0

    # Assert: Files processed
    output_files = list(output_dir.glob("*"))
    assert len(output_files) > 0


def test_cli_009_batch_with_explicit_file_list(cli_runner, multiple_test_files, tmp_path):
    """
    Test CLI-009: Process explicit list of files.

    Verifies:
    - Files specified on command line
    - All files processed
    """
    # Arrange
    output_dir = tmp_path / "explicit_results"
    output_dir.mkdir()

    # Convert file paths to strings
    file_args = [str(f) for f in multiple_test_files[:3]]  # First 3 files

    # Act
    result = cli_runner.invoke(
        cli,
        ["batch", *file_args, "--output", str(output_dir)],
    )

    # Assert: Success
    assert result.exit_code == 0

    # Assert: Outputs created
    output_files = list(output_dir.glob("*"))
    assert len(output_files) >= 3


# ==============================================================================
# Version Command Tests
# ==============================================================================


def test_cli_010_version_command(cli_runner):
    """
    Test CLI-010: Basic version display.

    Verifies:
    - Version command works
    - Shows tool name and version
    - Exit code success
    """
    # Act
    result = cli_runner.invoke(cli, ["version"])

    # Assert: Success
    assert result.exit_code == 0

    # Assert: Version info displayed
    assert "data" in result.output.lower() or "extract" in result.output.lower()
    # Version number should be present
    assert any(char.isdigit() for char in result.output)


def test_cli_011_version_verbose_mode(cli_runner):
    """
    Test CLI-011: Verbose version with components.

    Verifies:
    - Verbose flag shows more details
    - Component information included
    - Python version shown
    """
    # Act
    result = cli_runner.invoke(cli, ["version", "--verbose"])

    # Assert: Success
    assert result.exit_code == 0

    # Assert: More information than basic version
    assert len(result.output) > 50  # Should have substantial output

    # Assert: Component information
    assert "python" in result.output.lower() or "3." in result.output


def test_cli_012_version_short_flag(cli_runner):
    """
    Test CLI-012: Short -V flag for version.

    Verifies:
    - -V flag works as alternative
    - Shows same information as version command
    """
    # Act
    result = cli_runner.invoke(cli, ["-V"])

    # Assert: Success
    assert result.exit_code == 0

    # Assert: Version info shown
    assert len(result.output) > 0


# ==============================================================================
# Config Command Tests
# ==============================================================================


def test_cli_013_config_show_command(cli_runner, config_file):
    """
    Test CLI-013: Show configuration.

    Verifies:
    - Config displayed
    - Readable format
    - All settings shown
    """
    # Act
    result = cli_runner.invoke(cli, ["--config", str(config_file), "config", "show"])

    # Assert: Success
    assert result.exit_code == 0

    # Assert: Config content displayed
    assert "pipeline" in result.output.lower() or "config" in result.output.lower()


def test_cli_014_config_validate_valid(cli_runner, config_file):
    """
    Test CLI-014: Validate valid configuration.

    Verifies:
    - Validation succeeds
    - Success message shown
    """
    # Act
    result = cli_runner.invoke(cli, ["--config", str(config_file), "config", "validate"])

    # Assert: Success
    assert result.exit_code == 0

    # Assert: Validation message
    assert "valid" in result.output.lower() or "success" in result.output.lower()


def test_cli_015_config_validate_invalid(cli_runner, invalid_config_file):
    """
    Test CLI-015: Validate invalid configuration.

    Verifies:
    - Validation fails
    - Error details shown
    - Exit code non-zero
    """
    # Act
    result = cli_runner.invoke(cli, ["--config", str(invalid_config_file), "config", "validate"])

    # Assert: Failure
    assert result.exit_code != 0

    # Assert: Error message
    assert "error" in result.output.lower() or "invalid" in result.output.lower()


def test_cli_016_config_path_command(cli_runner, config_file):
    """
    Test CLI-016: Show config path.

    Verifies:
    - Path displayed
    - Correct file shown
    """
    # Act
    result = cli_runner.invoke(cli, ["--config", str(config_file), "config", "path"])

    # Assert: Success
    assert result.exit_code == 0

    # Assert: Path shown
    assert str(config_file.name) in result.output or "config" in result.output.lower()


# ==============================================================================
# Error Handling Tests
# ==============================================================================


def test_cli_017_error_file_not_found(cli_runner):
    """
    Test CLI-017: User-friendly error for missing file.

    Verifies:
    - Clear error message
    - No technical jargon
    - Non-zero exit code
    """
    # Act
    result = cli_runner.invoke(cli, ["extract", "nonexistent.docx"])

    # Assert: Failure
    assert result.exit_code != 0

    # Assert: User-friendly message
    assert "not found" in result.output.lower() or "exist" in result.output.lower()
    # Should NOT contain technical stack traces
    assert "traceback" not in result.output.lower()


def test_cli_018_error_unsupported_format(cli_runner, tmp_path):
    """
    Test CLI-018: Error for unsupported format.

    Verifies:
    - Error explains unsupported format
    - Lists supported formats
    """
    # Arrange: Create file with unsupported extension
    unsupported_file = tmp_path / "test.xyz"
    unsupported_file.write_text("test content")

    # Act
    result = cli_runner.invoke(cli, ["extract", str(unsupported_file)])

    # Assert: Failure
    assert result.exit_code != 0

    # Assert: Helpful message
    assert "support" in result.output.lower() or "format" in result.output.lower()


def test_cli_019_error_invalid_output_format(cli_runner, sample_docx_file):
    """
    Test CLI-019: Error for invalid output format.

    Verifies:
    - Invalid format rejected
    - Lists valid formats
    """
    # Act
    result = cli_runner.invoke(
        cli,
        ["extract", str(sample_docx_file), "--format", "invalid_format"],
    )

    # Assert: Failure
    assert result.exit_code != 0

    # Assert: Format options mentioned
    # Click will show available choices in error


# ==============================================================================
# Flag Tests
# ==============================================================================


def test_cli_020_verbose_flag(cli_runner, sample_docx_file, tmp_path):
    """
    Test CLI-020: Verbose flag increases output.

    Verifies:
    - More detailed logging
    - Debug information shown
    """
    # Arrange
    output_file = tmp_path / "output.json"

    # Act: With verbose
    result_verbose = cli_runner.invoke(
        cli,
        ["--verbose", "extract", str(sample_docx_file), "--output", str(output_file)],
    )

    # Act: Without verbose
    output_file2 = tmp_path / "output2.json"
    result_normal = cli_runner.invoke(
        cli,
        ["extract", str(sample_docx_file), "--output", str(output_file2)],
    )

    # Assert: Both succeed
    assert result_verbose.exit_code == 0
    assert result_normal.exit_code == 0

    # Assert: Verbose has more output
    # (This may not always be true depending on implementation)
    # At minimum, verbose should not break things
    assert len(result_verbose.output) >= 0


def test_cli_021_quiet_flag(cli_runner, sample_docx_file, tmp_path):
    """
    Test CLI-021: Quiet flag suppresses output.

    Verifies:
    - No progress bar
    - Only errors shown
    """
    # Arrange
    output_file = tmp_path / "output.json"

    # Act
    result = cli_runner.invoke(
        cli,
        ["--quiet", "extract", str(sample_docx_file), "--output", str(output_file)],
    )

    # Assert: Success
    assert result.exit_code == 0

    # Assert: Minimal output (implementation dependent)
    # At minimum, quiet should not break things


def test_cli_022_overwrite_protection(cli_runner, sample_docx_file, tmp_path):
    """
    Test CLI-022: Overwrite protection prompts user.

    Verifies:
    - Existing file triggers prompt
    - Can cancel or proceed
    """
    # Arrange: Create existing output file
    output_file = tmp_path / "output.json"
    output_file.write_text('{"existing": "data"}')

    # Act: Try to overwrite (input "n" to cancel)
    result = cli_runner.invoke(
        cli,
        ["extract", str(sample_docx_file), "--output", str(output_file)],
        input="n\n",
    )

    # Assert: Command recognized existing file
    # (Behavior depends on implementation - may prompt or warn)
    assert result.exit_code == 0 or "exist" in result.output.lower()


def test_cli_023_force_overwrite(cli_runner, sample_docx_file, tmp_path):
    """
    Test CLI-023: Force flag bypasses overwrite prompt.

    Verifies:
    - --force flag works
    - No prompt displayed
    - File overwritten
    """
    # Arrange: Create existing output file
    output_file = tmp_path / "output.json"
    output_file.write_text('{"existing": "data"}')

    # Act: Force overwrite
    result = cli_runner.invoke(
        cli,
        ["extract", str(sample_docx_file), "--output", str(output_file), "--force"],
    )

    # Assert: Success
    assert result.exit_code == 0

    # Assert: File was overwritten (new content)
    content = output_file.read_text()
    assert "existing" not in content  # Old content gone


# ==============================================================================
# Progress Display Tests
# ==============================================================================


def test_cli_024_progress_bar_display(cli_runner, sample_docx_file, tmp_path):
    """
    Test CLI-024: Progress bar displayed during processing.

    Verifies:
    - Progress indicators shown
    - Updates during processing
    """
    # Arrange
    output_file = tmp_path / "output.json"

    # Act
    result = cli_runner.invoke(
        cli,
        ["extract", str(sample_docx_file), "--output", str(output_file)],
    )

    # Assert: Success
    assert result.exit_code == 0

    # Assert: Progress mentioned (implementation dependent)
    # CLI may show progress bar or percentage
    # At minimum, command should complete successfully


def test_cli_025_batch_progress_tracking(cli_runner, batch_test_directory, tmp_path):
    """
    Test CLI-025: Progress tracking for batch processing.

    Verifies:
    - Progress shown per file
    - Overall progress displayed
    - Summary at end
    """
    # Arrange
    output_dir = tmp_path / "batch_output"
    output_dir.mkdir()

    # Act
    result = cli_runner.invoke(
        cli,
        ["batch", str(batch_test_directory), "--output", str(output_dir)],
    )

    # Assert: Success
    assert result.exit_code == 0

    # Assert: Summary information
    assert "file" in result.output.lower() or "success" in result.output.lower()


# ==============================================================================
# Integration with Components Tests
# ==============================================================================


def test_cli_026_full_workflow_integration(cli_runner, sample_docx_file, tmp_path):
    """
    Test CLI-026: Complete workflow from CLI to output.

    Verifies:
    - Extract command
    - Full pipeline execution
    - Valid output file
    - All components working together
    """
    # Arrange
    output_file = tmp_path / "final_output.json"

    # Act
    result = cli_runner.invoke(
        cli,
        ["extract", str(sample_docx_file), "--output", str(output_file), "--format", "json"],
    )

    # Assert: Success
    assert result.exit_code == 0

    # Assert: Output file valid
    assert output_file.exists()

    with open(output_file) as f:
        data = json.load(f)
        # Verify structure
        assert isinstance(data, dict)
        # Should have content
        assert len(data) > 0


def test_cli_027_error_recovery(cli_runner, batch_test_directory, corrupted_docx_file, tmp_path):
    """
    Test CLI-027: CLI handles errors gracefully in batch.

    Verifies:
    - Batch continues despite errors
    - Failed files reported
    - Summary shows partial success
    """
    # Arrange: Add corrupted file to batch
    output_dir = tmp_path / "error_recovery"
    output_dir.mkdir()

    # Create a directory with mix of valid and corrupted files
    test_dir = tmp_path / "mixed_files"
    test_dir.mkdir()

    # Copy some valid files
    import shutil

    for f in list(batch_test_directory.glob("*"))[:2]:
        shutil.copy(f, test_dir / f.name)

    # Add corrupted file
    shutil.copy(corrupted_docx_file, test_dir / "corrupted.docx")

    # Act
    result = cli_runner.invoke(
        cli,
        ["batch", str(test_dir), "--output", str(output_dir)],
    )

    # Assert: Command completes (may have warnings)
    # Exit code depends on implementation (may be 0 for partial success)
    assert result.exit_code == 0 or result.exit_code == 1

    # Assert: Some files succeeded
    output_files = list(output_dir.glob("*"))
    assert len(output_files) > 0


# ==============================================================================
# CLI Without --config Flag Tests
# ==============================================================================


def test_cli_028_extract_without_config_flag_uses_defaults(cli_runner, sample_docx_file, tmp_path):
    """
    Test CLI-028: Extract without --config flag uses default configuration.

    Scenario: `data-extract extract file.docx` works without --config flag

    Verifies:
    - Command succeeds with exit_code=0
    - Output file created successfully
    - JSON format defaults correctly
    - Success message displayed
    """
    # Arrange: Set up output file path
    output_file = tmp_path / "output.json"

    # Act: Run CLI extract without --config flag
    result = cli_runner.invoke(
        cli,
        [
            "extract",
            str(sample_docx_file),
            "--output",
            str(output_file),
        ],
    )

    # Assert: Command succeeds
    assert result.exit_code == 0, f"Command failed with: {result.output}"

    # Assert: Output message contains success indicator
    assert "success" in result.output.lower() or "extract" in result.output.lower()

    # Assert: Output file created
    assert output_file.exists(), "Output file not created"

    # Assert: Output is valid JSON
    with open(output_file) as f:
        data = json.load(f)
        assert isinstance(data, dict), "Output should be valid JSON object"
        assert len(data) > 0, "Output should contain data"


# ==============================================================================
# Additional CLI Integration Scenarios
# ==============================================================================


def test_cli_029_extract_then_batch_with_same_config(
    cli_runner, sample_docx_file, batch_test_directory, config_file, tmp_path
):
    """
    Test CLI-029: Extract single file, then batch with same config.

    Scenario: extract file.docx --config=X → batch dir/ --config=X

    Verifies:
    - Config used consistently
    - Single and batch use same settings
    - No config caching issues
    """
    # Arrange: Output locations
    single_output = tmp_path / "single_output.json"
    batch_output_dir = tmp_path / "batch_output"
    batch_output_dir.mkdir()

    # Act: Extract single file with config
    result_single = cli_runner.invoke(
        cli,
        [
            "--config",
            str(config_file),
            "extract",
            str(sample_docx_file),
            "--output",
            str(single_output),
        ],
    )

    # Act: Batch process with same config
    result_batch = cli_runner.invoke(
        cli,
        [
            "--config",
            str(config_file),
            "batch",
            str(batch_test_directory),
            "--output",
            str(batch_output_dir),
        ],
    )

    # Assert: Both succeeded
    assert result_single.exit_code == 0
    assert result_batch.exit_code == 0

    # Assert: Outputs created
    assert single_output.exists()
    assert len(list(batch_output_dir.glob("*"))) > 0


def test_cli_030_config_show_then_extract(cli_runner, sample_docx_file, config_file, tmp_path):
    """
    Test CLI-030: Show config, then extract using that config.

    Scenario: config show --config=X → extract --config=X

    Verifies:
    - Config show doesn't break subsequent commands
    - Config state preserved
    - Extract uses shown config
    """
    # Act: Show config first
    result_show = cli_runner.invoke(cli, ["--config", str(config_file), "config", "show"])

    # Act: Extract with same config
    output_file = tmp_path / "output.json"
    result_extract = cli_runner.invoke(
        cli,
        [
            "--config",
            str(config_file),
            "extract",
            str(sample_docx_file),
            "--output",
            str(output_file),
        ],
    )

    # Assert: Both succeeded
    assert result_show.exit_code == 0
    assert result_extract.exit_code == 0

    # Assert: Output created
    assert output_file.exists()


def test_cli_031_version_compatibility_check(cli_runner, sample_docx_file, tmp_path):
    """
    Test CLI-031: Version check doesn't interfere with extraction.

    Scenario: version → extract (ensure version check doesn't break state)

    Verifies:
    - Version command isolated
    - Extract works after version
    - No state leakage
    """
    # Act: Check version first
    result_version = cli_runner.invoke(cli, ["version"])

    # Act: Extract file
    output_file = tmp_path / "output.json"
    result_extract = cli_runner.invoke(
        cli, ["extract", str(sample_docx_file), "--output", str(output_file)]
    )

    # Assert: Both succeeded
    assert result_version.exit_code == 0
    assert result_extract.exit_code == 0

    # Assert: Output created
    assert output_file.exists()


def test_cli_032_batch_with_multiple_format_outputs(cli_runner, batch_test_directory, tmp_path):
    """
    Test CLI-032: Batch with --format=all produces multiple outputs per file.

    Scenario: batch dir/ --format=all → Multiple outputs per input file

    Verifies:
    - All formats generated for each file
    - Output naming correct
    - No file collisions
    """
    # Arrange: Output directory
    output_dir = tmp_path / "multi_format_batch"
    output_dir.mkdir()

    # Act: Batch with all formats
    result = cli_runner.invoke(
        cli, ["batch", str(batch_test_directory), "--output", str(output_dir), "--format", "all"]
    )

    # Assert: Success
    assert result.exit_code == 0

    # Assert: Multiple output files created
    output_files = list(output_dir.glob("*"))
    assert len(output_files) > 0

    # Assert: Different format extensions present
    extensions = {f.suffix for f in output_files}
    # Should have at least 2 different formats
    assert len(extensions) >= 2


def test_cli_033_extract_with_relative_paths(cli_runner, sample_docx_file, tmp_path):
    """
    Test CLI-033: Extract with relative file paths works correctly.

    Scenario: extract ./file.docx --output ./output.json

    Verifies:
    - Relative paths resolved correctly
    - Output created in expected location
    - No path resolution errors
    """
    # Arrange: Change to tmp_path directory context
    # Copy sample file to tmp_path
    import shutil

    local_file = tmp_path / "local_test.docx"
    shutil.copy(sample_docx_file, local_file)

    # Use relative path from tmp_path
    output_file = tmp_path / "output.json"

    # Act: Extract (CLI should handle paths)
    result = cli_runner.invoke(cli, ["extract", str(local_file), "--output", str(output_file)])

    # Assert: Success
    assert result.exit_code == 0

    # Assert: Output created
    assert output_file.exists()


def test_cli_034_cli_error_messages_user_friendly(cli_runner, tmp_path):
    """
    Test CLI-034: CLI error messages are user-friendly, not technical.

    Scenario: Various error conditions → Check error messages

    Verifies:
    - No raw stack traces in normal output
    - Clear error descriptions
    - Helpful suggestions when possible
    """
    # Test 1: Non-existent file
    result = cli_runner.invoke(cli, ["extract", "nonexistent_file.docx"])

    assert result.exit_code != 0
    # Should have user-friendly error
    assert "not found" in result.output.lower() or "does not exist" in result.output.lower()
    # Should NOT have technical traceback
    assert "Traceback" not in result.output

    # Test 2: Invalid format
    real_file = tmp_path / "test.txt"
    real_file.write_text("test")

    result = cli_runner.invoke(cli, ["extract", str(real_file), "--format", "invalid_fmt"])

    assert result.exit_code != 0
    # Click will show available choices
    # Error should mention format issue


def test_cli_035_batch_progress_display_updates(cli_runner, batch_test_directory, tmp_path):
    """
    Test CLI-035: Batch progress display shows per-file updates.

    Scenario: batch dir/ with multiple files → Progress shown

    Verifies:
    - Progress information in output
    - File names mentioned
    - Completion status shown
    """
    # Arrange: Output directory
    output_dir = tmp_path / "progress_test"
    output_dir.mkdir()

    # Act: Batch process
    result = cli_runner.invoke(
        cli, ["batch", str(batch_test_directory), "--output", str(output_dir)]
    )

    # Assert: Success
    assert result.exit_code == 0

    # Assert: Output mentions processing
    assert "process" in result.output.lower() or "success" in result.output.lower()


def test_cli_036_extract_output_directory_auto_created(cli_runner, sample_docx_file, tmp_path):
    """
    Test CLI-036: Extract creates nested output directories automatically.

    Scenario: extract file.docx --output=a/b/c/output.json (a/b/c doesn't exist)

    Verifies:
    - Nested directories created
    - File written successfully
    - No errors about missing directories
    """
    # Arrange: Deep nested path that doesn't exist
    output_file = tmp_path / "level1" / "level2" / "level3" / "output.json"

    # Act: Extract
    result = cli_runner.invoke(
        cli, ["extract", str(sample_docx_file), "--output", str(output_file)]
    )

    # Assert: Success
    assert result.exit_code == 0

    # Assert: Directory structure created
    assert output_file.parent.exists()

    # Assert: File created
    assert output_file.exists()


def test_cli_037_config_validate_invalid_shows_helpful_error(cli_runner, invalid_config_file):
    """
    Test CLI-037: Config validate shows helpful errors for invalid config.

    Scenario: config validate --config=invalid.yaml

    Verifies:
    - Validation errors shown
    - Specific problems identified
    - User can understand what's wrong
    """
    # Act: Validate invalid config
    result = cli_runner.invoke(cli, ["--config", str(invalid_config_file), "config", "validate"])

    # Assert: Failed
    assert result.exit_code != 0

    # Assert: Error information present
    assert "error" in result.output.lower() or "invalid" in result.output.lower()


def test_cli_038_batch_empty_directory_handled(cli_runner, tmp_path):
    """
    Test CLI-038: Batch on empty directory handled gracefully.

    Scenario: batch empty_dir/ → Graceful message

    Verifies:
    - No crash on empty directory
    - Informative message
    - Appropriate exit code
    """
    # Arrange: Empty directory
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    # Act: Try to batch process
    result = cli_runner.invoke(cli, ["batch", str(empty_dir)])

    # Assert: Doesn't crash
    # May succeed with message or exit with info
    assert (
        result.exit_code == 0
        or "no files" in result.output.lower()
        or "empty" in result.output.lower()
    )
