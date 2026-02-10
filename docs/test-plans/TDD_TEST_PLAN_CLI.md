# TDD Test Plan: CLI Implementation (Wave 4 Agent 2)

## Test Plan for CLI Module

**Agent**: TDD-Builder Specialist
**Date**: 2025-10-29
**Target Coverage**: >85%
**Working Directory**: `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool`

---

## Requirements Coverage

### Requirement 1: Extract Command - Single File Processing
**Description**: Process a single file with format selection
**Test Cases**:
- `test_extract_command_docx_to_json` - Extract DOCX to JSON format
- `test_extract_command_pdf_to_markdown` - Extract PDF to Markdown format
- `test_extract_command_all_formats` - Extract to all formats simultaneously
- `test_extract_command_missing_file` - Handle file not found error
- `test_extract_command_unsupported_format` - Handle unsupported file format
- `test_extract_command_output_directory_created` - Create output directory if missing
- `test_extract_command_overwrite_protection` - Prompt before overwriting
- `test_extract_command_exit_code_success` - Exit code 0 on success
- `test_extract_command_exit_code_failure` - Exit code non-zero on failure

**Integration Points**: ExtractionPipeline, ConfigManager, ErrorHandler

---

### Requirement 2: Batch Command - Multiple File Processing
**Description**: Process multiple files in parallel with progress display
**Test Cases**:
- `test_batch_command_multiple_files` - Process list of files
- `test_batch_command_glob_pattern` - Filter files by pattern (*.pdf)
- `test_batch_command_custom_workers` - Configure worker thread count
- `test_batch_command_all_formats` - Generate all output formats
- `test_batch_command_partial_failure` - Continue on individual file errors
- `test_batch_command_progress_display` - Show progress bar
- `test_batch_command_summary_stats` - Display success/failure summary
- `test_batch_command_output_directory` - Create output directory structure
- `test_batch_command_exit_code` - Exit codes for success/partial/complete failure

**Integration Points**: BatchProcessor, ProgressTracker

---

### Requirement 3: Version Command - Version Information
**Description**: Display version and component information
**Test Cases**:
- `test_version_command_basic` - Show basic version info
- `test_version_command_verbose` - Show all component versions
- `test_version_command_exit_code` - Exit code 0

**Integration Points**: None (simple command)

---

### Requirement 4: Config Command - Configuration Management
**Description**: Show and validate configuration
**Test Cases**:
- `test_config_show_command` - Display current configuration
- `test_config_validate_command_valid` - Validate valid configuration
- `test_config_validate_command_invalid` - Report invalid configuration
- `test_config_path_command` - Show config file location
- `test_config_missing_file` - Handle missing config file gracefully

**Integration Points**: ConfigManager

---

### Requirement 5: User Experience - Non-Technical Error Messages
**Description**: Clear, actionable error messages for auditors
**Test Cases**:
- `test_error_message_file_not_found` - Plain language file error
- `test_error_message_corrupted_file` - Suggest fix for corrupted files
- `test_error_message_unsupported_format` - List supported formats
- `test_error_message_permission_denied` - Explain permission issues
- `test_error_message_output_write_failure` - Suggest output directory fix

**Integration Points**: ErrorHandler

---

### Requirement 6: Progress Display
**Description**: Visual progress indicators for long operations
**Test Cases**:
- `test_progress_bar_single_file` - Show progress during extraction
- `test_progress_bar_batch_processing` - Show batch progress
- `test_progress_percentage_calculation` - Accurate percentage display
- `test_progress_time_estimation` - Show estimated time remaining

**Integration Points**: ProgressTracker, rich/tqdm library

---

### Requirement 7: Input Validation
**Description**: Validate all user inputs before processing
**Test Cases**:
- `test_validate_file_exists` - Check file existence
- `test_validate_format_supported` - Check format support
- `test_validate_output_path` - Validate output path
- `test_validate_workers_positive` - Workers must be > 0
- `test_validate_pattern_syntax` - Glob pattern validation

**Integration Points**: Pipeline validation methods

---

## Implementation Strategy

### Phase 1: Test Infrastructure Setup (RED)
1. Create test directory structure
2. Set up Click test runner fixtures
3. Create sample test files in fixtures
4. Write all failing tests first
5. Verify import errors before implementation

### Phase 2: Extract Command (RED-GREEN-REFACTOR)
**Red Phase**:
- Write failing tests for extract command
- Test all format combinations
- Test error scenarios
- Test exit codes

**Green Phase**:
- Implement minimal CLI entry point
- Implement extract command handler
- Integrate with ExtractionPipeline
- Make all tests pass

**Refactor Phase**:
- Extract common error handling patterns
- Improve user message formatting
- Add input validation helpers

### Phase 3: Batch Command (RED-GREEN-REFACTOR)
**Red Phase**:
- Write failing tests for batch command
- Test parallel processing
- Test progress display
- Test summary statistics

**Green Phase**:
- Implement batch command handler
- Integrate with BatchProcessor
- Add progress bar integration
- Make all tests pass

**Refactor Phase**:
- Extract file discovery logic
- Improve progress reporting
- Optimize worker management

### Phase 4: Version & Config Commands (RED-GREEN-REFACTOR)
**Red Phase**:
- Write failing tests for version command
- Write failing tests for config commands
- Test validation scenarios

**Green Phase**:
- Implement version command
- Implement config commands
- Make all tests pass

**Refactor Phase**:
- Clean up command structure
- Standardize output formatting

### Phase 5: User Experience Polish (RED-GREEN-REFACTOR)
**Red Phase**:
- Write tests for error message formatting
- Write tests for progress display
- Write tests for overwrite protection

**Green Phase**:
- Implement ErrorHandler integration
- Implement progress bar display
- Add user prompts for overwrites

**Refactor Phase**:
- Create reusable message templates
- Standardize error formatting
- Polish progress display

---

## Test File Organization

```
tests/test_cli/
├── __init__.py
├── conftest.py                    # CLI test fixtures
├── test_main.py                   # CLI entry point tests
├── test_commands.py               # Command handler tests
├── test_extract_command.py        # Extract command detailed tests
├── test_batch_command.py          # Batch command detailed tests
├── test_version_command.py        # Version command tests
├── test_config_command.py         # Config command tests
├── test_error_messages.py         # User-friendly error message tests
├── test_progress_display.py       # Progress display tests
└── test_input_validation.py       # Input validation tests
```

---

## Testing Tools & Patterns

### Click Testing Utilities
```python
from click.testing import CliRunner

def test_extract_command_success():
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test file
        Path("test.docx").write_text("content")

        # Run command
        result = runner.invoke(cli, ['extract', 'test.docx', '--format', 'json'])

        # Assertions
        assert result.exit_code == 0
        assert 'Successfully extracted' in result.output
        assert Path("output.json").exists()
```

### Fixture Pattern for Sample Files
```python
@pytest.fixture
def sample_docx_file(tmp_path):
    """Create a sample DOCX file for testing."""
    file_path = tmp_path / "sample.docx"
    # Create actual DOCX file with python-docx
    doc = Document()
    doc.add_paragraph("Test content")
    doc.save(file_path)
    return file_path
```

### Progress Display Testing
```python
def test_progress_bar_display():
    runner = CliRunner()
    result = runner.invoke(cli, ['batch', 'files/*.pdf'])

    # Check for progress indicators in output
    assert '[' in result.output  # Progress bar brackets
    assert '%' in result.output  # Percentage display
```

### Error Message Testing
```python
def test_user_friendly_error_missing_file():
    runner = CliRunner()
    result = runner.invoke(cli, ['extract', 'nonexistent.pdf'])

    # Should NOT contain technical jargon
    assert 'exception' not in result.output.lower()
    assert 'traceback' not in result.output.lower()

    # Should contain helpful message
    assert 'file' in result.output.lower()
    assert 'found' in result.output.lower()
    assert result.exit_code != 0
```

---

## Coverage Targets

**Overall Target**: >85%

**Per-Module Targets**:
- `src/cli/main.py` - 90% (entry point, straightforward)
- `src/cli/commands.py` - 85% (command handlers)
- Error paths - 100% (critical for user experience)

**Excluded from Coverage**:
- Debug logging statements
- Unreachable defensive code

---

## Success Criteria

Implementation is complete when:

1. All specification requirements have corresponding passing tests
2. Code coverage meets or exceeds 85% for new functionality
3. All CLI commands work with sample files
4. Error messages are clear and non-technical
5. Progress bars display correctly
6. No regressions in Wave 1-3 test suites
7. User guide documentation complete with examples

---

## Dependencies

**Required Packages**:
- `click` - CLI framework (recommended over argparse)
- `rich` or `tqdm` - Progress bar display
- Existing infrastructure (ConfigManager, ErrorHandler, ProgressTracker)
- Wave 4 Agent 1 deliverables (ExtractionPipeline, BatchProcessor)

**Test Dependencies**:
- `pytest` (already available)
- `pytest-cov` (for coverage)
- Click's testing utilities (`click.testing.CliRunner`)

---

## Integration Testing Notes

**End-to-End Workflow Tests**:
1. Extract single DOCX → Verify JSON output
2. Batch process directory → Verify all outputs created
3. Handle errors gracefully → Verify user-friendly messages
4. Progress display → Verify visual feedback
5. Config validation → Verify error detection

**Integration with Wave 4 Agent 1**:
- Use ExtractionPipeline for single file processing
- Use BatchProcessor for multi-file processing
- Pass progress callbacks through to ProgressTracker
- Format errors using ErrorHandler

---

## Risk Mitigation

**Potential Issues**:
1. **Progress bar rendering in tests** - Use Click's isolated filesystem and capture output
2. **File system operations** - Use tmp_path fixture for isolation
3. **Thread pool in tests** - Use small worker counts, ensure cleanup
4. **Platform differences** - Test path handling on Windows (primary platform)

**Mitigation Strategies**:
- Isolated test environments (Click's CliRunner)
- Temporary file fixtures (pytest tmp_path)
- Mocked components where appropriate
- Platform-specific path handling tests

---

## Next Steps After Test Creation

1. Run tests - verify all fail (RED phase)
2. Implement minimal CLI entry point
3. Implement one command at a time (GREEN phase)
4. Refactor for quality (REFACTOR phase)
5. Repeat for each command
6. Final integration testing
7. Documentation and handoff

---

**TDD Cycle Reminder**: Red → Green → Refactor → Repeat

Always write the failing test first, implement minimal code to pass, then refactor for quality.
