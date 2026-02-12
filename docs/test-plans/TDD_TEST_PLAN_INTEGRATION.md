# Integration Test Plan - Wave 4 Agent 3

**Agent**: TDD-Builder Specialist
**Date**: 2025-10-29
**Mission**: Comprehensive integration testing for data extraction tool
**Working Directory**: `<project-root>`

---

## Test Plan Overview

This document outlines the comprehensive integration test strategy for validating that all components (extractors, processors, formatters, pipeline, CLI) work cohesively to meet requirements.

### Test Categories

1. **End-to-End Pipeline Tests** - Full extraction workflow validation
2. **CLI Workflow Tests** - Real command execution with file I/O
3. **Performance Benchmark Tests** - Performance requirements validation
4. **Error Scenario Tests** - Error handling and recovery validation

### Success Criteria

- All integration tests passing
- End-to-end tests cover all format combinations (4 extractors × 3 formatters = 12 combinations)
- CLI workflow tests cover all commands (extract, batch, version, config)
- Performance benchmarks meet or exceed requirements
- Error scenarios properly handled and logged
- No regressions in existing unit tests
- Overall test coverage >85%

---

## Test Category 1: End-to-End Pipeline Tests

**File**: `tests/integration/test_end_to_end.py`
**Purpose**: Validate complete extraction pipeline for all format combinations

### Test Matrix

| Extractor | Formatter | Priority | Test ID |
|-----------|-----------|----------|---------|
| DOCX | JSON | High | E2E-001 |
| DOCX | Markdown | High | E2E-002 |
| DOCX | ChunkedText | Medium | E2E-003 |
| PDF | JSON | High | E2E-004 |
| PDF | Markdown | High | E2E-005 |
| PDF | ChunkedText | Medium | E2E-006 |
| PPTX | JSON | Medium | E2E-007 |
| PPTX | Markdown | Medium | E2E-008 |
| PPTX | ChunkedText | Low | E2E-009 |
| XLSX | JSON | Medium | E2E-010 |
| XLSX | Markdown | Low | E2E-011 |
| XLSX | ChunkedText | Low | E2E-012 |

### Test Cases

#### TC-E2E-001: DOCX → JSON Pipeline
**Description**: Extract DOCX document, process through full pipeline, output to JSON
**Prerequisites**: Sample DOCX file with headings, paragraphs, tables
**Steps**:
1. Create ExtractionPipeline
2. Register DocxExtractor
3. Add ContextLinker, MetadataAggregator processors
4. Add JsonFormatter
5. Process test DOCX file
6. Validate PipelineResult structure
7. Verify JSON output contains all expected blocks
8. Verify metadata aggregation occurred
9. Verify quality score computed

**Expected Results**:
- `result.success == True`
- `result.extraction_result` contains ContentBlocks
- `result.processing_result.quality_score > 85.0`
- `result.formatted_outputs[0].format_type == "json"`
- JSON parsable and contains all content

#### TC-E2E-002: DOCX → Markdown Pipeline
**Description**: Extract DOCX document, output to Markdown format
**Prerequisites**: Sample DOCX file
**Steps**:
1. Configure pipeline with MarkdownFormatter
2. Process test DOCX file
3. Validate Markdown structure (headings as #, paragraphs as text)

**Expected Results**:
- Markdown output contains proper heading markers
- Paragraphs formatted correctly
- Tables converted to Markdown table syntax

#### TC-E2E-003: Full Processor Chain
**Description**: Validate all processors run in correct order
**Prerequisites**: Sample DOCX file
**Steps**:
1. Add processors: MetadataAggregator, ContextLinker (wrong order)
2. Verify topological sort orders them correctly
3. Verify ContextLinker runs before MetadataAggregator

**Expected Results**:
- Processors execute in dependency order
- Each processor's metadata present in final result

#### TC-E2E-004: PDF with OCR Pipeline
**Description**: Extract PDF document that may require OCR
**Prerequisites**: Sample PDF file (both native text and scanned)
**Steps**:
1. Configure pipeline with PdfExtractor
2. Process PDF with native text
3. Process scanned PDF requiring OCR
4. Compare quality scores

**Expected Results**:
- Native PDF: quality_score > 95
- Scanned PDF: quality_score > 80 (if OCR enabled)
- Both produce valid ContentBlocks

#### TC-E2E-005: Multi-Format Batch Pipeline
**Description**: Process batch of files in different formats
**Prerequisites**: DOCX, PDF, PPTX, XLSX files
**Steps**:
1. Create BatchProcessor with configured pipeline
2. Process batch of mixed files
3. Validate all results

**Expected Results**:
- All files processed successfully
- Results map contains entry for each file
- Summary shows success rate

#### TC-E2E-006: Progress Tracking Integration
**Description**: Validate progress callbacks through full pipeline
**Prerequisites**: Large DOCX file
**Steps**:
1. Register progress callback
2. Process file
3. Collect progress updates

**Expected Results**:
- Progress updates from 0% to 100%
- Updates include stage information
- No duplicate percentages

---

## Test Category 2: CLI Workflow Tests

**File**: `tests/integration/test_cli_workflows.py`
**Purpose**: Test real CLI command execution with actual file I/O

### Test Cases

#### TC-CLI-001: Extract Command with Real DOCX
**Description**: Execute `data-extract extract` command on real DOCX file
**Prerequisites**: Sample DOCX file in fixtures
**Steps**:
1. Create CliRunner isolated filesystem
2. Copy sample DOCX to isolated filesystem
3. Execute: `data-extract extract sample.docx`
4. Verify output file created
5. Load and validate JSON output

**Expected Results**:
- Exit code 0
- Output file exists at expected path
- JSON contains valid ExtractionResult
- Success message displayed

#### TC-CLI-002: Extract Command with All Formats
**Description**: Execute extract with `--format all`
**Prerequisites**: Sample DOCX file
**Steps**:
1. Execute: `data-extract extract sample.docx --format all --output ./results/`
2. Verify 3 output files created (JSON, MD, chunked)

**Expected Results**:
- 3 files created: `sample.json`, `sample.md`, `sample_chunked.txt`
- All files contain valid content
- Success message shows 3 formats generated

#### TC-CLI-003: Batch Command with Directory
**Description**: Execute batch processing on directory
**Prerequisites**: Directory with 5+ mixed format files
**Steps**:
1. Create directory with DOCX, PDF, PPTX, XLSX files
2. Execute: `data-extract batch ./documents/ --output ./results/`
3. Verify all output files created

**Expected Results**:
- Output files created for each input
- Progress bar displayed during processing
- Summary shows success rate

#### TC-CLI-004: Batch Command with Pattern Filter
**Description**: Execute batch with glob pattern
**Prerequisites**: Directory with mixed files
**Steps**:
1. Execute: `data-extract batch ./documents/ --pattern "*.docx" --output ./results/`
2. Verify only DOCX files processed

**Expected Results**:
- Only DOCX files in output
- PDF, PPTX files ignored

#### TC-CLI-005: Batch Command with Workers
**Description**: Execute batch with custom worker count
**Prerequisites**: Directory with 10+ files
**Steps**:
1. Execute: `data-extract batch ./documents/ --workers 4 --output ./results/`
2. Monitor parallel execution

**Expected Results**:
- Multiple files processed simultaneously
- No race conditions or corrupted outputs

#### TC-CLI-006: Config Command Show
**Description**: Display current configuration
**Prerequisites**: Config file with custom settings
**Steps**:
1. Create config file: `config.yaml`
2. Execute: `data-extract --config config.yaml config show`

**Expected Results**:
- Configuration displayed in readable format
- All settings shown

#### TC-CLI-007: Config Command Validate
**Description**: Validate configuration file
**Prerequisites**: Valid and invalid config files
**Steps**:
1. Execute: `data-extract --config valid.yaml config validate`
2. Execute: `data-extract --config invalid.yaml config validate`

**Expected Results**:
- Valid config: Success message, exit code 0
- Invalid config: Error message with details, exit code 1

#### TC-CLI-008: Error Handling - File Not Found
**Description**: Verify user-friendly error for missing file
**Prerequisites**: None
**Steps**:
1. Execute: `data-extract extract nonexistent.docx`

**Expected Results**:
- Error message: "The file you specified could not be found..."
- No technical jargon
- Exit code 1

#### TC-CLI-009: Error Handling - Unsupported Format
**Description**: Verify error for unsupported format
**Prerequisites**: File with unsupported extension
**Steps**:
1. Execute: `data-extract extract file.xyz`

**Expected Results**:
- Error message lists supported formats
- User-friendly language
- Exit code 1

#### TC-CLI-010: Verbose Mode
**Description**: Verify verbose flag increases output
**Prerequisites**: Sample DOCX file
**Steps**:
1. Execute: `data-extract --verbose extract sample.docx`
2. Compare output to non-verbose

**Expected Results**:
- More detailed logging output
- Debug information displayed

#### TC-CLI-011: Quiet Mode
**Description**: Verify quiet flag suppresses output
**Prerequisites**: Sample DOCX file
**Steps**:
1. Execute: `data-extract --quiet extract sample.docx`

**Expected Results**:
- No progress bar displayed
- Only errors shown (if any)

#### TC-CLI-012: Overwrite Protection
**Description**: Verify confirmation prompt for existing files
**Prerequisites**: Existing output file
**Steps**:
1. Create: `output.json`
2. Execute: `data-extract extract sample.docx --output output.json`
3. Respond to prompt

**Expected Results**:
- Prompt: "File exists. Overwrite? [y/N]"
- File only overwritten if confirmed

#### TC-CLI-013: Force Overwrite
**Description**: Verify --force flag bypasses prompt
**Prerequisites**: Existing output file
**Steps**:
1. Create: `output.json`
2. Execute: `data-extract extract sample.docx --output output.json --force`

**Expected Results**:
- No prompt displayed
- File overwritten immediately

---

## Test Category 3: Performance Benchmark Tests

**File**: `tests/integration/test_performance.py`
**Purpose**: Validate performance meets requirements

### Performance Requirements

| Operation | Requirement | Test ID |
|-----------|-------------|---------|
| Text extraction | <2s/MB | PERF-001 |
| OCR extraction | <15s/page | PERF-002 |
| Memory (single file) | <500MB | PERF-003 |
| Memory (batch) | <2GB total | PERF-004 |
| Quality (native) | >98% completeness | PERF-005 |
| Quality (OCR) | >85% completeness | PERF-006 |

### Test Cases

#### TC-PERF-001: Text Extraction Speed
**Description**: Verify text extraction meets <2s/MB requirement
**Prerequisites**: Large DOCX file (10MB+)
**Steps**:
1. Create DocxExtractor
2. Load 10MB DOCX file
3. Time extraction using pytest-benchmark
4. Calculate duration per MB

**Expected Results**:
- `duration_per_mb < 2.0 seconds`
- Benchmark repeatable across runs

#### TC-PERF-002: OCR Extraction Speed
**Description**: Verify OCR meets <15s/page requirement
**Prerequisites**: Scanned PDF (5+ pages)
**Steps**:
1. Create PdfExtractor with OCR enabled
2. Process scanned PDF
3. Time extraction per page

**Expected Results**:
- `duration_per_page < 15.0 seconds`
- All pages processed

#### TC-PERF-003: Single File Memory Usage
**Description**: Verify single file memory usage <500MB
**Prerequisites**: Large file (50MB+)
**Steps**:
1. Monitor memory using `tracemalloc`
2. Extract large file
3. Measure peak memory usage

**Expected Results**:
- `peak_memory_mb < 500`
- No memory leaks after completion

#### TC-PERF-004: Batch Memory Usage
**Description**: Verify batch processing memory <2GB
**Prerequisites**: 50+ files totaling 100MB+
**Steps**:
1. Create BatchProcessor
2. Monitor memory during batch processing
3. Measure peak memory

**Expected Results**:
- `peak_memory_gb < 2.0`
- Memory released after each file

#### TC-PERF-005: Native Format Quality
**Description**: Verify >98% completeness for native formats
**Prerequisites**: DOCX with known content (100 paragraphs)
**Steps**:
1. Extract DOCX with known structure
2. Count extracted blocks
3. Compare to expected count

**Expected Results**:
- `extracted_blocks / expected_blocks > 0.98`
- Quality score reflects completeness

#### TC-PERF-006: OCR Quality
**Description**: Verify >85% completeness for OCR
**Prerequisites**: Scanned PDF with known text
**Steps**:
1. Extract scanned PDF
2. Compare extracted text to ground truth
3. Calculate accuracy

**Expected Results**:
- `text_accuracy > 0.85`
- Quality score reflects OCR limitations

#### TC-PERF-007: Batch Processing Throughput
**Description**: Measure batch processing throughput
**Prerequisites**: 100 files
**Steps**:
1. Process batch with 4 workers
2. Measure total time
3. Calculate files per second

**Expected Results**:
- Throughput > sequential processing / 3
- All files processed successfully

#### TC-PERF-008: Parallel Scaling
**Description**: Verify parallel processing scales with workers
**Prerequisites**: 20 files
**Steps**:
1. Process with 1, 2, 4, 8 workers
2. Measure time for each
3. Calculate scaling efficiency

**Expected Results**:
- 4 workers: ~3x faster than 1 worker
- 8 workers: ~5-6x faster than 1 worker

---

## Test Category 4: Error Scenario Tests

**File**: `tests/integration/test_error_scenarios.py`
**Purpose**: Validate error handling and recovery

### Error Categories

1. **File Errors** - Missing, corrupted, encrypted files
2. **Format Errors** - Unknown formats, malformed content
3. **System Errors** - Disk space, permissions, timeouts
4. **Configuration Errors** - Invalid settings, missing dependencies

### Test Cases

#### TC-ERR-001: Missing File
**Description**: Verify graceful handling of missing file
**Prerequisites**: None
**Steps**:
1. Create pipeline
2. Process non-existent file
3. Verify error handling

**Expected Results**:
- `result.success == False`
- `result.failed_stage == ProcessingStage.VALIDATION`
- Error message: "File not found"

#### TC-ERR-002: Corrupted DOCX File
**Description**: Verify handling of corrupted DOCX
**Prerequisites**: Corrupted DOCX file
**Steps**:
1. Create corrupted DOCX (invalid ZIP)
2. Process with DocxExtractor
3. Verify error handling

**Expected Results**:
- `result.success == False`
- Error code: "E103" (extraction failed)
- User message mentions corrupted file

#### TC-ERR-003: Corrupted PDF File
**Description**: Verify handling of corrupted PDF
**Prerequisites**: Corrupted PDF file
**Steps**:
1. Create corrupted PDF
2. Process with PdfExtractor
3. Verify error handling

**Expected Results**:
- `result.success == False`
- Partial extraction if possible
- Warning about corruption

#### TC-ERR-004: Encrypted PDF
**Description**: Verify handling of password-protected PDF
**Prerequisites**: Encrypted PDF file
**Steps**:
1. Process encrypted PDF without password
2. Verify error handling

**Expected Results**:
- Error message indicates encryption
- Suggests password required

#### TC-ERR-005: Unknown File Format
**Description**: Verify handling of unsupported format
**Prerequisites**: File with unknown extension
**Steps**:
1. Create file: `test.xyz`
2. Process with pipeline
3. Verify format detection failure

**Expected Results**:
- `result.success == False`
- Error lists supported formats
- No exception raised

#### TC-ERR-006: Empty File
**Description**: Verify handling of empty file
**Prerequisites**: 0-byte file
**Steps**:
1. Create empty DOCX
2. Process file
3. Verify handling

**Expected Results**:
- `result.success == True` (valid but empty)
- Zero content blocks
- Warning about empty file

#### TC-ERR-007: Invalid Configuration
**Description**: Verify handling of invalid config
**Prerequisites**: Invalid config.yaml
**Steps**:
1. Create config with invalid values
2. Load with ConfigManager
3. Verify validation errors

**Expected Results**:
- Exception raised with clear message
- Indicates which setting is invalid

#### TC-ERR-008: Missing Required Dependency
**Description**: Verify error when extractor unavailable
**Prerequisites**: Unregister extractor
**Steps**:
1. Create pipeline without PdfExtractor
2. Attempt to process PDF
3. Verify error

**Expected Results**:
- Clear error: "No extractor for PDF format"
- Suggests installing dependency

#### TC-ERR-009: Disk Space Error
**Description**: Verify handling of insufficient disk space
**Prerequisites**: Mock disk full condition
**Steps**:
1. Mock disk space error
2. Attempt to write output
3. Verify error handling

**Expected Results**:
- Error caught and reported
- Suggests freeing disk space

#### TC-ERR-010: Permission Error
**Description**: Verify handling of permission denied
**Prerequisites**: Read-only directory
**Steps**:
1. Create read-only output directory
2. Attempt to write output
3. Verify error handling

**Expected Results**:
- Permission error caught
- Clear message about permissions

#### TC-ERR-011: Timeout Error
**Description**: Verify timeout handling for long operations
**Prerequisites**: Very large file
**Steps**:
1. Set short timeout on BatchProcessor
2. Process large file
3. Verify timeout handling

**Expected Results**:
- File marked as failed due to timeout
- Other files continue processing

#### TC-ERR-012: Processor Exception
**Description**: Verify pipeline continues despite processor failure
**Prerequisites**: Mock failing processor
**Steps**:
1. Add processor that raises exception
2. Process file
3. Verify partial success

**Expected Results**:
- Extraction succeeds
- Processor failure logged
- Other processors still run

#### TC-ERR-013: Formatter Exception
**Description**: Verify pipeline handles formatter failures
**Prerequisites**: Mock failing formatter
**Steps**:
1. Add formatter that raises exception
2. Process file
3. Verify other formatters succeed

**Expected Results**:
- Extraction and processing succeed
- Failed formatter logged
- Other formatters produce output

#### TC-ERR-014: Batch Partial Failure
**Description**: Verify batch continues despite individual failures
**Prerequisites**: Mix of valid and corrupted files
**Steps**:
1. Create batch: 5 valid, 2 corrupted files
2. Process batch
3. Verify partial success

**Expected Results**:
- 5 files succeed
- 2 files fail with errors
- Summary shows 5/7 success rate

#### TC-ERR-015: Circular Dependency Detection
**Description**: Verify processor circular dependency caught
**Prerequisites**: Mock processors with circular deps
**Steps**:
1. Create processors A→B, B→A
2. Attempt to add to pipeline
3. Verify error

**Expected Results**:
- ValueError raised
- Message indicates circular dependency

---

## Test Fixtures

### Required Test Files

#### fixtures/documents/
- `test_document.docx` - Valid Word document (2-3 pages)
  - Headings (levels 1-3)
  - Paragraphs with formatting
  - Table (2x3)
  - Image (embedded)
  - Metadata (author, title, dates)

- `test_presentation.pptx` - Valid PowerPoint (5 slides)
  - Title slide
  - Content slides with bullet points
  - Slide with table
  - Slide with image
  - Speaker notes

- `test_spreadsheet.xlsx` - Valid Excel workbook (3 sheets)
  - Sheet 1: Data table with headers
  - Sheet 2: Formulas
  - Sheet 3: Charts and mixed content

- `test_document.pdf` - Valid PDF (native text)
  - Multi-page document
  - Mixed fonts
  - Tables and images

#### fixtures/corrupted/
- `corrupted.docx` - Invalid ZIP structure
- `corrupted.pdf` - Truncated PDF
- `encrypted.pdf` - Password-protected PDF
- `empty.docx` - 0-byte file

#### fixtures/large/
- `large_document.pdf` - 10MB+ PDF for performance testing
- `large_batch/` - Directory with 50+ files for batch testing

### Fixture Generation

Use pytest fixtures to generate files programmatically:

```python
@pytest.fixture
def sample_docx_file(tmp_path):
    """Generate valid DOCX file for testing."""
    from docx import Document

    doc = Document()
    doc.add_heading('Test Document', 0)
    doc.add_paragraph('This is a test paragraph.')
    # ... more content

    file_path = tmp_path / 'test.docx'
    doc.save(file_path)
    return file_path
```

---

## Test Execution Strategy

### Phase 1: RED - Write Failing Tests (Week 1, Days 1-2)
1. Create integration test directory structure
2. Implement conftest.py with fixtures
3. Write all test cases (failing initially)
4. Verify tests import correctly and fail as expected

### Phase 2: GREEN - Fix Issues (Week 1, Days 3-4)
1. Run tests and identify failures
2. Fix issues in pipeline, CLI, or tests themselves
3. Iteratively fix one test at a time
4. Verify no regressions in existing unit tests

### Phase 3: REFACTOR - Improve Quality (Week 1, Day 5)
1. Refactor test code for clarity
2. Extract common patterns to fixtures
3. Optimize slow tests
4. Document findings

### Test Execution Commands

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific category
pytest tests/integration/test_end_to_end.py -v
pytest tests/integration/test_cli_workflows.py -v
pytest tests/integration/test_performance.py -v
pytest tests/integration/test_error_scenarios.py -v

# Run with markers
pytest -m integration -v
pytest -m slow -v
pytest -m benchmark -v

# Run with coverage
pytest tests/integration/ --cov=src --cov-report=html

# Run performance benchmarks
pytest tests/integration/test_performance.py --benchmark-only
```

---

## Coverage Targets

### Overall Coverage
- **Target**: >85% for entire codebase
- **Critical**: >90% for pipeline and CLI modules

### Module-Specific Targets
- `src/pipeline/extraction_pipeline.py`: >90%
- `src/pipeline/batch_processor.py`: >90%
- `src/cli/main.py`: >85%
- `src/cli/commands.py`: >85%
- Integration of all components: 100% (all combinations tested)

### Coverage Measurement

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html --cov-report=term

# View detailed report
open htmlcov/index.html

# Check coverage threshold
pytest tests/ --cov=src --cov-fail-under=85
```

---

## Success Metrics

### Quantitative Metrics
- [ ] All 61+ integration tests passing
- [ ] Overall test coverage >85%
- [ ] All format combinations tested (12 tests)
- [ ] All CLI commands tested (13 tests)
- [ ] Performance benchmarks meet requirements (8 tests)
- [ ] Error scenarios handled gracefully (15 tests)

### Qualitative Metrics
- [ ] No regressions in existing unit tests
- [ ] Error messages are user-friendly
- [ ] Performance meets enterprise requirements
- [ ] System resilient to failures
- [ ] Code maintainable and well-documented

---

## Risk Assessment

### High Risk Areas
1. **Performance Testing** - May need larger test files than available
   - *Mitigation*: Generate synthetic files programmatically

2. **OCR Testing** - Tesseract installation may be unavailable
   - *Mitigation*: Skip OCR tests if not installed, mark as optional

3. **File Corruption Testing** - Creating realistic corrupted files is hard
   - *Mitigation*: Use known corruption patterns (truncate, invalid headers)

4. **Memory Testing** - Memory limits may not trigger in test environment
   - *Mitigation*: Use `tracemalloc` for accurate measurement

### Medium Risk Areas
1. **CLI Testing** - Click testing utilities may have quirks
   - *Mitigation*: Use Click's CliRunner in isolated filesystem

2. **Progress Tracking** - Progress callbacks hard to test deterministically
   - *Mitigation*: Test callback invocation, not exact percentages

3. **Batch Processing** - Parallelism makes tests non-deterministic
   - *Mitigation*: Use synchronous mode for tests, test async separately

---

## Handoff Deliverables

Upon completion, create `WAVE4_AGENT3_HANDOFF.md` containing:

1. **Test Results Summary**
   - Total tests created and passing
   - Coverage report with percentages
   - Performance benchmark results

2. **Integration Findings**
   - Issues discovered during integration
   - Component interactions validated
   - Error scenarios tested

3. **Performance Analysis**
   - Actual vs. required performance
   - Bottlenecks identified
   - Optimization recommendations

4. **Known Issues**
   - Bugs found but not fixed
   - Limitations discovered
   - Technical debt identified

5. **Deployment Readiness**
   - Recommendation for production deployment
   - Remaining work needed
   - Risk assessment

6. **Test Execution Guide**
   - How to run integration tests
   - How to interpret results
   - How to add new integration tests

---

**Test Plan Status**: Draft Complete
**Next Action**: Create integration test directory structure
**Estimated Effort**: 40-60 hours (5-8 days)
