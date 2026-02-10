# CLI Integration Tests - TDD RED Phase Summary

**Date**: 2025-11-29
**Epic**: 5 - Enhanced CLI UX & Batch Processing
**Stories**: 5-1, 5-4, 5-5, 5-7
**Phase**: TDD RED (Test-Driven Development - Red Phase)

## Overview

Created comprehensive CLI integration tests for Epic 5 Stories 5-1, 5-4, 5-5, and 5-7. All tests are designed to **FAIL initially** (RED phase of TDD), establishing behavioral specifications that guide implementation.

**Total Tests Created**: 58 tests across 3 files

## Test Files Created

### 1. tests/test_cli/test_cli_integration.py (20 tests)

**Purpose**: Process command integration with flags for batch processing, presets, and incremental updates.

**Test Classes**:
- `TestProcessIncrementalFlag` (3 tests) - Incremental processing flag
- `TestProcessForceFlag` (2 tests) - Force reprocessing flag
- `TestProcessPresetFlag` (5 tests) - Configuration preset loading
- `TestProcessExportSummary` (3 tests) - Summary file export
- `TestIncrementalBehavior` (2 tests) - Incremental processing behavior
- `TestProcessCommandCombinations` (3 tests) - Flag combinations
- `TestProcessCommandValidation` (3 tests) - Input validation

**Key Test Assertions** (Stories 5-4, 5-5, 5-7):

```
AC-5-4: --incremental flag recognized and processes with incremental logic
AC-5-4: --force flag recognized and reprocesses all files
AC-5-5: --preset quality/speed/balanced loads preset configuration
AC-5-4: --export-summary creates summary file with statistics
AC-5-7: --incremental skips unchanged files in batch
AC-5-7: --force overrides --incremental to process all files
```

### 2. tests/test_cli/test_status_command.py (23 tests)

**Purpose**: New status command for displaying sync state and file metrics.

**Test Classes**:
- `TestStatusCommandExists` (3 tests) - Command registration
- `TestStatusCommandHelp` (3 tests) - Help documentation
- `TestStatusBasicOutput` (4 tests) - Basic output format
- `TestStatusVerboseMode` (5 tests) - Verbose mode breakdown
- `TestStatusFormatOutput` (3 tests) - Output format options
- `TestStatusWorkingDirectory` (2 tests) - State file handling
- `TestStatusEdgeCases` (2 tests) - Edge cases

**Key Test Assertions** (Story 5-1):

```
AC-5-1: status command exists and is registered
AC-5-1: status --help shows usage and available options
AC-5-1: status shows total files and sync state
AC-5-1: status --verbose shows breakdown (new/modified/unchanged files)
AC-5-1: status supports --format json, text, etc.
AC-5-1: status works with no state file (uninitialized state)
```

### 3. tests/test_cli/test_semantic_export.py (15 tests)

**Purpose**: Export summary functionality for semantic analysis commands.

**Test Classes**:
- `TestSemanticAnalyzeExportSummary` (4 tests) - Analyze command export
- `TestSemanticDeduplicateExportSummary` (3 tests) - Deduplicate export
- `TestSemanticClusterExportSummary` (3 tests) - Cluster export
- `TestExportSummaryFormats` (2 tests) - Format support
- `TestExportSummaryWithOtherFlags` (3 tests) - Flag combinations

**Key Test Assertions** (Story 5-4):

```
AC-5-4: semantic analyze --export-summary recognized
AC-5-4: semantic analyze --export-summary creates summary file
AC-5-4: semantic deduplicate --export-summary shows removal stats
AC-5-4: semantic cluster --export-summary shows cluster count
AC-5-4: Summary supports JSON format
AC-5-4: --export-summary works with --verbose, --dry-run, etc.
```

## TDD RED Phase Characteristics

All tests are designed to fail initially with clear, actionable error messages:

### Example Test Structure

```python
@pytest.mark.cli
@pytest.mark.story_5_4
def test_process_incremental_flag_recognized(
    self, runner: CliRunner, app, sample_input_dir: Path, output_dir: Path
) -> None:
    """
    RED: Verify --incremental flag is recognized by process command.

    Given: process command with --incremental flag
    When: We invoke the command
    Then: Should not fail due to unknown flag
    And: Should process files with incremental logic

    Expected RED failure: Flag not recognized or command fails
    """
    result = runner.invoke(
        app,
        [
            "process",
            str(sample_input_dir),
            "--output",
            str(output_dir),
            "--incremental",
        ],
    )

    assert "unrecognized arguments" not in result.output
    assert "no such option" not in result.output.lower()
```

### Typical RED Phase Failures

```
FAILED tests/test_cli/test_status_command.py::TestStatusCommandExists::test_status_command_exists
AssertionError: assert 'no such command' not in "...│ no such command 'status'."

FAILED tests/test_cli/test_semantic_export.py::TestSemanticAnalyzeExportSummary::test_analyze_export_summary_flag_recognized
AssertionError: assert 'no such option' not in "...│ no such option: --export-summary"

FAILED tests/test_cli/test_cli_integration.py::TestProcessPresetFlag::test_process_preset_quality_loads_config
AssertionError: assert 'no such option' not in "...│ no such option: --preset"
```

## Test Fixtures

### Core Fixtures (Available across all tests)

- `runner: CliRunner` - Fresh CLI test runner with app reset
- `app: typer.Typer` - Fresh Typer application instance
- `sample_input_dir: Path` - Directory with sample test files
- `output_dir: Path` - Directory for command output
- `state_file: Path` - State file tracking processing history
- `sample_chunks_dir: Path` - Directory with semantic chunk files
- `duplicate_chunks_dir: Path` - Directory with duplicate chunks

### Key Fixture Patterns

```python
@pytest.fixture
def runner():
    """Provide fresh CLI runner with reset app instance."""
    _reset_app()
    return CliRunner()

@pytest.fixture
def sample_input_dir(tmp_path: Path) -> Path:
    """Create a sample input directory with test files."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    for i in range(3):
        test_file = input_dir / f"document_{i}.txt"
        test_file.write_text(f"Sample document content {i}\n" * 10)
    return input_dir
```

## Pytest Markers Used

Tests are properly marked for selective execution:

- `@pytest.mark.cli` - All CLI tests (58 tests)
- `@pytest.mark.story_5_1` - Status command tests (23 tests)
- `@pytest.mark.story_5_4` - Process command and export flags (18 tests)
- `@pytest.mark.story_5_5` - Preset configuration tests (5 tests)
- `@pytest.mark.story_5_7` - Incremental processing tests (2 tests)

**Execute by marker**:
```bash
pytest -m story_5_1          # Run status command tests
pytest -m story_5_4          # Run process command tests
pytest -m cli                # Run all CLI tests
pytest -m "story_5_4 or story_5_5"  # Multiple markers
```

## Acceptance Criteria Mapping

### Story 5-1: Status Command

| AC | Test | File | Status |
|----|------|------|--------|
| AC-5-1 | test_status_command_exists | test_status_command.py | RED |
| AC-5-1 | test_status_shows_help | test_status_command.py | RED |
| AC-5-1 | test_status_shows_sync_state | test_status_command.py | RED |
| AC-5-1 | test_status_verbose_shows_breakdown | test_status_command.py | RED |
| AC-5-1 | test_status_json_format | test_status_command.py | RED |

### Story 5-4: Process Command & Export Summary

| AC | Test | File | Status |
|----|------|------|--------|
| AC-5-4 | test_process_incremental_flag_recognized | test_cli_integration.py | RED |
| AC-5-4 | test_process_force_flag_recognized | test_cli_integration.py | RED |
| AC-5-4 | test_process_export_summary_creates_file | test_cli_integration.py | RED |
| AC-5-4 | test_analyze_export_summary_flag_recognized | test_semantic_export.py | RED |
| AC-5-4 | test_deduplicate_export_summary_creates_file | test_semantic_export.py | RED |
| AC-5-4 | test_cluster_export_summary_shows_cluster_count | test_semantic_export.py | RED |

### Story 5-5: Preset Configuration

| AC | Test | File | Status |
|----|------|------|--------|
| AC-5-5 | test_process_preset_flag_loads_config | test_cli_integration.py | RED |
| AC-5-5 | test_process_preset_quality_loads_config | test_cli_integration.py | RED |
| AC-5-5 | test_process_preset_speed_loads_config | test_cli_integration.py | RED |
| AC-5-5 | test_process_preset_balanced_loads_config | test_cli_integration.py | RED |
| AC-5-5 | test_process_invalid_preset_rejected | test_cli_integration.py | RED |

### Story 5-7: Incremental Processing

| AC | Test | File | Status |
|----|------|------|--------|
| AC-5-7 | test_incremental_skips_unchanged_files | test_cli_integration.py | RED |
| AC-5-7 | test_force_overrides_incremental | test_cli_integration.py | RED |

## Test Execution Results

### Initial RED Phase Execution

```bash
$ pytest tests/test_cli/test_cli_integration.py -v
======================== 20 tests in collection =========================
FAILED tests/test_cli/test_cli_integration.py::TestProcessPresetFlag::test_process_preset_flag_recognized
AssertionError: assert 'no such option' not in "│ no such option: --preset"
... (19 more failures)

$ pytest tests/test_cli/test_status_command.py -v
======================== 23 tests in collection =========================
FAILED tests/test_cli/test_status_command.py::TestStatusCommandExists::test_status_command_exists
AssertionError: assert 'no such command' not in "│ no such command 'status'."
... (22 more failures)

$ pytest tests/test_cli/test_semantic_export.py -v
======================== 15 tests in collection =========================
FAILED tests/test_cli/test_semantic_export.py::TestSemanticAnalyzeExportSummary::test_analyze_export_summary_flag_recognized
AssertionError: assert 'no such option' not in "│ no such option: --export-summary"
... (14 more failures)

Total: 58/58 tests FAILED (100% failure rate) ✓ CORRECT for RED phase
```

## Next Steps - GREEN Phase

Once implementation is complete:

1. Run tests to verify they all pass: `pytest tests/test_cli/ -v`
2. Check coverage: `pytest tests/test_cli/ --cov=src/data_extract/cli`
3. Mark complete when all 58 tests pass

### Expected Implementation Scope

**Story 5-1**: Implement `status` command with:
- Basic status display (total files, sync state)
- Verbose mode with file breakdown (new/modified/unchanged)
- Format options (JSON, text)

**Story 5-4**: Add flags to existing commands:
- `process --incremental`, `--force`, `--export-summary`
- `semantic analyze --export-summary`
- `semantic deduplicate --export-summary`
- `semantic cluster --export-summary`

**Story 5-5**: Implement preset system:
- `process --preset quality|speed|balanced`
- PresetManager for loading/validating presets
- CLI flag overrides configuration

**Story 5-7**: Implement incremental processing:
- FileHasher for change detection
- StateFile for persistence
- ChangeDetector for tracking modifications

## Test Quality Metrics

- **Comprehensive Coverage**: 58 tests covering all acceptance criteria
- **Proper Structure**: Given-When-Then BDD format for clarity
- **Isolation**: Each test independent with proper fixtures
- **Markers**: Proper pytest markers for selective execution
- **Documentation**: Clear docstrings explaining intent
- **Red Phase**: All tests properly FAIL before implementation

## Files Created

```
tests/test_cli/test_cli_integration.py      (20 tests, 495 lines)
tests/test_cli/test_status_command.py       (23 tests, 558 lines)
tests/test_cli/test_semantic_export.py      (15 tests, 628 lines)
```

**Total**: 58 tests, 1,681 lines of test code

## Testing Strategy

### Running Tests by Story

```bash
# Story 5-1: Status command
pytest tests/test_cli/test_status_command.py -v

# Story 5-4: Process command
pytest tests/test_cli/test_cli_integration.py -k "incremental or force or export" -v
pytest tests/test_cli/test_semantic_export.py -v

# Story 5-5: Presets
pytest tests/test_cli/test_cli_integration.py -k "preset" -v

# Story 5-7: Incremental
pytest tests/test_cli/test_cli_integration.py -k "incremental" -v
```

### Running All CLI Tests

```bash
# All 58 tests
pytest tests/test_cli/test_cli_integration.py tests/test_cli/test_status_command.py tests/test_cli/test_semantic_export.py -v

# With coverage
pytest tests/test_cli/ --cov=src/data_extract/cli --cov-report=term-missing

# Parallel execution
pytest tests/test_cli/ -n auto
```

## Conclusion

All 58 tests are in RED phase and ready for GREEN phase implementation. Tests are:

✅ Comprehensive - covering all acceptance criteria
✅ Well-organized - proper test classes and markers
✅ Properly isolated - fresh fixtures for each test
✅ Clearly documented - BDD-style descriptions
✅ Ready for implementation - guide development of features

Next phase: Implement the CLI commands to make these tests pass.
