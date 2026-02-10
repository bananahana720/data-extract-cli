# PRD: CSV Extractor Feature

**Feature ID**: CSV-EXTRACT-001
**Version**: 1.0.6-alpha
**Status**: SPECIFICATION
**Created**: 2025-11-06
**Target**: v1.0.6 release

---

## Feature Overview

### Context
**Dependencies**:
- BaseExtractor interface - `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\src\core\interfaces.py`
- Excel extractor pattern - `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\src\extractors\excel_extractor.py`
- TableMetadata model - `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\src\core\models.py`

**New Component**: `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\src\extractors\csv_extractor.py` (create new file)

**Reference Files**:
- Pattern source: `src/extractors/excel_extractor.py` (table extraction pattern)
- Test template: `tests/test_extractors/test_excel_extractor.py` (table test cases)
- Model definition: `src/core/models.py` (TableMetadata dataclass)
- Pipeline registration: `src/pipeline/extraction_pipeline.py` (extractor registry)

**Current State**: Excel table extraction complete, CSV format NOT supported

---

## Acceptance Criteria

```
[ ] CSVExtractor class created at src/extractors/csv_extractor.py
[ ] Implements BaseExtractor interface completely
[ ] File extensions supported: .csv, .tsv
[ ] Delimiter auto-detection: comma, tab, semicolon, pipe
[ ] Encoding detection: UTF-8 primary, Latin-1 fallback, CP1252 fallback
[ ] Header detection heuristic: first row analysis
[ ] CSV data mapped to TableMetadata structure
[ ] Configuration options: max_rows, delimiter, encoding, has_header
[ ] Error handling: encoding errors, malformed rows, empty files
[ ] Test coverage ≥85% for csv_extractor.py
[ ] Pipeline registration complete: CSV files routed to CSVExtractor
[ ] CLI accepts CSV files: data-extract extract sample.csv --format json
[ ] Zero regressions: pytest tests/ -q → all 778 existing tests pass
[ ] Integration test: CSV data appears in JSON/Markdown output
```

---

## Task Breakdown

### Task CSV-T1: Design Analysis & Data Model Decision
**Agent**: Explore (general-purpose analysis)
**Duration**: 20 minutes
**Dependencies**: None

**Input Files**:
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\src\extractors\excel_extractor.py`
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\src\core\models.py`

**Output Deliverable**: `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\docs\planning\CSV_DESIGN_DECISION.md`

**Success Criteria**:
```
[ ] Data model options analyzed: Option A (single table), Option B (multiple tables), Option C (content blocks)
[ ] Recommendation provided with rationale: preferred option + justification
[ ] Excel pattern comparison: how CSV differs from multi-sheet Excel
[ ] Edge cases enumerated: no header, single column, single row, empty file, encoding issues
[ ] Delimiter detection approach specified: csv.Sniffer or custom heuristic
[ ] Encoding detection approach specified: chardet library or encoding trial-and-error
[ ] Header detection heuristic specified: data type analysis, unique value count
[ ] Configuration parameters defined: max_rows, delimiter, encoding, has_header
[ ] Decision matrix included: pros/cons of each option
```

**Command to Validate**: `ls "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\docs\planning\CSV_DESIGN_DECISION.md"`

---

### Task CSV-T2: Technical Specification
**Agent**: npl-technical-writer
**Duration**: 25 minutes
**Dependencies**: CSV-T1 (design decision approved)

**Input Files**:
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\docs\planning\CSV_DESIGN_DECISION.md`
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\src\core\interfaces.py`

**Output Deliverable**: `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\docs\planning\CSV_TECHNICAL_SPECIFICATION.md`

**Success Criteria**:
```
[ ] Class structure defined: CSVExtractor(BaseExtractor)
[ ] Method signatures specified: __init__, validate_file, extract, _detect_delimiter, _detect_encoding, _detect_header
[ ] Configuration schema specified: default values for all parameters
[ ] Error handling strategy specified: which errors to catch, which to propagate
[ ] TableMetadata mapping specified: how CSV rows/columns map to table structure
[ ] File extension registration specified: .csv, .tsv in supported_formats
[ ] Dependencies listed: csv module (stdlib), chardet (optional), typing
[ ] Integration points identified: pipeline registration, CLI command routing
[ ] Test scenarios enumerated: at least 30 test cases
```

**Command to Validate**: `ls "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\docs\planning\CSV_TECHNICAL_SPECIFICATION.md"`

---

### Task CSV-T3: Test-Driven Development (RED Phase)
**Agent**: npl-tdd-builder
**Duration**: 45 minutes
**Dependencies**: CSV-T2 (technical specification complete)

**Input Files**:
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\docs\planning\CSV_TECHNICAL_SPECIFICATION.md`
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\tests\test_extractors\test_excel_extractor.py` (test pattern reference)

**Output Deliverable**: Test suite at `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\tests\test_extractors\test_csv_extractor.py` (new file)

**Success Criteria**:
```
[ ] Test fixtures created: simple.csv, with_header.csv, no_header.csv, tsv_file.tsv, semicolon_delimited.csv, empty.csv, single_column.csv, single_row.csv, encoding_utf8.csv, encoding_latin1.csv, malformed.csv
[ ] Test case: test_extract_simple_csv → validates basic CSV parsing
[ ] Test case: test_detect_comma_delimiter → validates delimiter detection
[ ] Test case: test_detect_tab_delimiter → validates TSV support
[ ] Test case: test_detect_semicolon_delimiter → validates alternate delimiter
[ ] Test case: test_detect_header_present → validates header detection
[ ] Test case: test_detect_no_header → validates data-only files
[ ] Test case: test_encoding_utf8 → validates UTF-8 files
[ ] Test case: test_encoding_latin1_fallback → validates encoding fallback
[ ] Test case: test_table_metadata_mapping → validates TableMetadata structure
[ ] Test case: test_max_rows_limit → validates row limit configuration
[ ] Test case: test_empty_file_handling → validates empty file behavior
[ ] Test case: test_single_column → validates single-column CSV
[ ] Test case: test_single_row → validates single-row CSV
[ ] Test case: test_malformed_row_handling → validates error recovery
[ ] Test case: test_config_delimiter_override → validates manual delimiter
[ ] Test case: test_config_encoding_override → validates manual encoding
[ ] Test case: test_config_has_header_override → validates manual header flag
[ ] Test case: test_unsupported_file_type → validates .xlsx rejection
[ ] Test case: test_file_not_found → validates missing file handling
[ ] Test case: test_file_permissions → validates access error handling
[ ] Test count ≥30: pytest tests/test_extractors/test_csv_extractor.py --collect-only | grep "test_" | wc -l → ≥30
[ ] All tests FAIL (RED state): pytest tests/test_extractors/test_csv_extractor.py --tb=short → FAILED count = total
[ ] Fixtures directory created: ls tests/fixtures/csv/ → directory exists
[ ] Fixture count ≥5: ls tests/fixtures/csv/ | grep ".csv" | wc -l → ≥5
```

**Command to Validate**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
pytest tests/test_extractors/test_csv_extractor.py --collect-only | grep "test_"
pytest tests/test_extractors/test_csv_extractor.py --tb=short
ls tests/fixtures/csv/
```
**Expected Output**: 30+ tests collected, all FAILED, 5+ fixtures

---

### Task CSV-T4: Implementation (GREEN Phase)
**Agent**: General-purpose implementation
**Duration**: 60 minutes
**Dependencies**: CSV-T3 (tests written, RED state confirmed)

**Input Files**:
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\tests\test_extractors\test_csv_extractor.py` (failing tests)
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\docs\planning\CSV_TECHNICAL_SPECIFICATION.md` (implementation spec)
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\src\extractors\excel_extractor.py` (pattern reference)

**Output Deliverable**: New file `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\src\extractors\csv_extractor.py`

**Success Criteria**:
```
[ ] File created: src/extractors/csv_extractor.py exists
[ ] Class implemented: CSVExtractor(BaseExtractor)
[ ] Method: __init__(self, config: Optional[Dict[str, Any]] = None)
[ ] Method: validate_file(self, file_path: Path) -> Tuple[bool, List[str]]
[ ] Method: extract(self, file_path: Path) -> ExtractionResult
[ ] Method: _detect_delimiter(self, file_path: Path, sample_size: int = 1024) -> str
[ ] Method: _detect_encoding(self, file_path: Path, sample_size: int = 4096) -> str
[ ] Method: _detect_header(self, rows: List[List[str]]) -> bool
[ ] Import: from src.core.interfaces import BaseExtractor
[ ] Import: from src.core.models import ExtractionResult, TableMetadata, Position
[ ] Import: import csv, from pathlib import Path, from typing import Dict, List, Tuple, Optional, Any
[ ] Supported formats: ["csv", "tsv"] in class attribute
[ ] Configuration: max_rows, delimiter, encoding, has_header with defaults
[ ] Delimiter detection: uses csv.Sniffer or fallback logic
[ ] Encoding detection: try UTF-8, Latin-1, CP1252 in order
[ ] Header detection: checks first row data types vs subsequent rows
[ ] Error handling: try/except for encoding errors, malformed rows (log warning, skip row)
[ ] TableMetadata creation: maps CSV to table structure with headers, rows, columns
[ ] Type hints: all parameters and return types annotated
[ ] Docstrings: class and all methods documented
[ ] All tests PASS: pytest tests/test_extractors/test_csv_extractor.py -v → PASSED count = total
[ ] Coverage ≥85%: pytest --cov=src/extractors/csv_extractor.py --cov-report=term | grep "csv_extractor" | awk '{print $4}' | sed 's/%//' → ≥85
```

**Command to Validate**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
ls src/extractors/csv_extractor.py
python -c "from src.extractors.csv_extractor import CSVExtractor; print('Import OK')"
pytest tests/test_extractors/test_csv_extractor.py -v
pytest --cov=src/extractors/csv_extractor.py --cov-report=term-missing
```
**Expected Output**: File exists, import succeeds, all tests PASSED, coverage ≥85%

---

### Task CSV-T5: Code Review
**Agent**: npl-code-reviewer
**Duration**: 25 minutes
**Dependencies**: CSV-T4 (implementation complete, tests passing)

**Input Files**:
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\src\extractors\csv_extractor.py` (implementation)
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\docs\architecture\FOUNDATION.md` (architecture reference)

**Output Deliverable**: `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\docs\reviews\CSV_EXTRACTOR_CODE_REVIEW.md`

**Success Criteria**:
```
[ ] Zero critical issues (security, data corruption, crashes)
[ ] Zero major issues (performance, memory leaks, incorrect behavior)
[ ] Minor issues ≤5 (style, documentation, optimization suggestions)
[ ] BaseExtractor interface verified: all required methods implemented
[ ] Immutability verified: TableMetadata objects are frozen dataclasses
[ ] Error handling verified: try/except blocks present, appropriate logging
[ ] Type hints verified: all functions annotated
[ ] Documentation verified: docstrings present for class and all methods
[ ] Configuration verified: uses ConfigManager pattern (self.config.get)
[ ] Dependencies verified: only stdlib + approved libraries (csv, pathlib, typing)
[ ] Performance verified: no obvious bottlenecks (no quadratic algorithms)
```

**Command to Validate**: `ls "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\docs\reviews\CSV_EXTRACTOR_CODE_REVIEW.md"`

---

### Task CSV-T6: Pipeline Integration
**Agent**: General-purpose integration
**Duration**: 30 minutes
**Dependencies**: CSV-T5 (code review approved)

**Input Files**:
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\src\pipeline\extraction_pipeline.py` (pipeline registry)
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\src\extractors\csv_extractor.py` (new extractor)

**Output Deliverable**: Updated `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\src\pipeline\extraction_pipeline.py`

**Success Criteria**:
```
[ ] Import added: from src.extractors.csv_extractor import CSVExtractor
[ ] Extractor registered: pipeline._register_extractor(CSVExtractor) or equivalent
[ ] File extension mapping: .csv → CSVExtractor, .tsv → CSVExtractor
[ ] CLI accepts CSV: python -m cli extract sample.csv --format json → success
[ ] CLI output valid: python -m cli extract sample.csv --format json && python -m json.tool output.json → valid JSON
[ ] CLI output contains table: grep "table" output.json → match found
[ ] Integration test created: tests/integration/test_new_features_integration.py::TestCsvPipeline
[ ] Integration test: test_csv_through_pipeline → validates CSV → ProcessingResult → JSON
[ ] Integration test: test_csv_cli_workflow → validates CLI command end-to-end
[ ] Integration test: test_csv_batch_processing → validates batch with CSV files
[ ] All integration tests PASS: pytest tests/integration/test_new_features_integration.py::TestCsvPipeline -v → 100% PASSED
```

**Command to Validate**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
grep -i "CSVExtractor" src/pipeline/extraction_pipeline.py
python -m cli extract tests/fixtures/csv/simple.csv --format json
pytest tests/integration/test_new_features_integration.py::TestCsvPipeline -v
```
**Expected Output**: Import found, CLI succeeds, integration tests PASSED

---

## Validation Checkpoints

### Checkpoint A: Design Decision
**When**: After Task CSV-T1
**Decision Point**: APPROVE design → proceed to CSV-T2 | REJECT → reevaluate

**Validation**:
```
[ ] Data model choice documented: Option A/B/C selected
[ ] Rationale provided: why this approach is best
[ ] Excel pattern comparison done: similarities/differences noted
[ ] Edge cases identified: at least 5 scenarios enumerated
[ ] Decision matrix present: pros/cons table for each option
[ ] Recommendation clear: unambiguous choice stated
[ ] Design file exists: ls docs/planning/CSV_DESIGN_DECISION.md → file found
```

**Command**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
ls docs/planning/CSV_DESIGN_DECISION.md
grep -i "recommendation" docs/planning/CSV_DESIGN_DECISION.md
```

**IF REJECT**:
1. Identify unclear design points
2. Request specific analysis: delimiter detection, encoding handling, data model
3. Re-assign Task CSV-T1 with clarifications
4. Re-run Checkpoint A

---

### Checkpoint B: Test Suite Validation (RED State)
**When**: After Task CSV-T3
**Decision Point**: APPROVE → proceed to CSV-T4 | REJECT → add tests

**Validation**:
```
[ ] Test count ≥30: pytest tests/test_extractors/test_csv_extractor.py --collect-only | grep "test_" | wc -l → ≥30
[ ] All tests FAIL (RED state): pytest tests/test_extractors/test_csv_extractor.py --tb=short → FAILED count = total
[ ] Fixtures ≥5: ls tests/fixtures/csv/ | grep ".csv" | wc -l → ≥5
[ ] Coverage check possible: pytest --cov=src/extractors/csv_extractor.py --cov-report=term → generates report (even if file doesn't exist yet)
[ ] Test variety: grep -c "test_detect" tests/test_extractors/test_csv_extractor.py → ≥4 (delimiter, encoding, header tests)
```

**Command**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
pytest tests/test_extractors/test_csv_extractor.py --collect-only | grep "test_" | wc -l
pytest tests/test_extractors/test_csv_extractor.py --tb=short
ls tests/fixtures/csv/ | grep -E "\.(csv|tsv)$"
```

**Expected Output**:
- Test count ≥30
- All tests FAILED
- At least 5 fixtures

**IF REJECT**:
1. Check: Are delimiter/encoding/header tests present?
2. Check: Are edge case tests present (empty, single column, malformed)?
3. Check: Do fixtures cover test scenarios?
4. Review test specifications in CSV_TECHNICAL_SPECIFICATION.md
5. Re-assign Task CSV-T3 with missing test categories
6. Re-run Checkpoint B

---

### Checkpoint C: Implementation Validation (GREEN State)
**When**: After Task CSV-T4
**Decision Point**: APPROVE → proceed to CSV-T5 | REJECT → debug

**Validation**:
```
[ ] File exists: ls src/extractors/csv_extractor.py → file found
[ ] Import succeeds: python -c "from src.extractors.csv_extractor import CSVExtractor; print('OK')" → OK
[ ] BaseExtractor implemented: python -c "from src.extractors.csv_extractor import CSVExtractor; from src.core.interfaces import BaseExtractor; assert issubclass(CSVExtractor, BaseExtractor); print('OK')" → OK
[ ] All tests PASS: pytest tests/test_extractors/test_csv_extractor.py -v → FAILED count = 0
[ ] Coverage ≥85%: pytest --cov=src/extractors/csv_extractor.py --cov-report=term | grep "csv_extractor" | awk '{print $4}' | sed 's/%//' → ≥85
[ ] No syntax errors: python -m py_compile src/extractors/csv_extractor.py → no errors
```

**Command**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
ls src/extractors/csv_extractor.py
python -c "from src.extractors.csv_extractor import CSVExtractor; print('Import OK')"
pytest tests/test_extractors/test_csv_extractor.py -v
pytest --cov=src/extractors/csv_extractor.py --cov-report=term-missing
```

**Expected Output**:
- File exists
- Import succeeds
- Tests: 100% PASSED
- Coverage: ≥85%

**IF REJECT**:
1. Check: Does file exist?
2. Check: Does it import without errors?
3. Analyze failures: pytest ... -vv --tb=long
4. Check: Are required methods present (validate_file, extract)?
5. Check: Is BaseExtractor interface fully implemented?
6. Debug with: pytest ... --pdb
7. Re-assign Task CSV-T4 with specific fixes
8. Re-run Checkpoint C

---

### Checkpoint D: Pipeline Integration
**When**: After Task CSV-T6
**Decision Point**: APPROVE → Phase 5 (integration testing) | REJECT → fix integration

**Validation**:
```
[ ] Import present: grep "CSVExtractor" src/pipeline/extraction_pipeline.py → match found
[ ] CLI accepts CSV: python -m cli extract tests/fixtures/csv/simple.csv --format json → exit code 0
[ ] Output valid JSON: python -m cli extract tests/fixtures/csv/simple.csv --format json && python -m json.tool output.json → valid JSON
[ ] Output contains table: python -m cli extract tests/fixtures/csv/simple.csv --format json && grep "table" output.json → match found
[ ] Integration tests pass: pytest tests/integration/test_new_features_integration.py::TestCsvPipeline -v → 100% PASSED
[ ] No regressions: pytest tests/test_pipeline/ -q → all pass
```

**Command**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
grep "CSVExtractor" src/pipeline/extraction_pipeline.py
python -m cli extract tests/fixtures/csv/simple.csv --format json
pytest tests/integration/test_new_features_integration.py::TestCsvPipeline -v
```

**Expected Output**:
- Import found
- CLI exit code 0
- Integration tests PASSED

**IF REJECT**:
1. Check: Is CSVExtractor imported in pipeline?
2. Check: Is it registered with the pipeline?
3. Check: Does CLI recognize .csv extension?
4. Run: python -m cli extract tests/fixtures/csv/simple.csv --format json -v (verbose mode)
5. Check pipeline logs for errors
6. Fix registration issues
7. Re-run Checkpoint D

---

## Context Passing Rules

### Task CSV-T1 → Task CSV-T2
**Required Context**:
- File path: `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\docs\planning\CSV_DESIGN_DECISION.md`
- Key section: Recommendation (which data model option selected)
- Key section: Rationale (why this option)

**Command to Extract Context**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
grep -A 10 "Recommendation" docs/planning/CSV_DESIGN_DECISION.md
```

---

### Task CSV-T2 → Task CSV-T3
**Required Context**:
- File path: `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\docs\planning\CSV_TECHNICAL_SPECIFICATION.md`
- Key sections: Class structure, method signatures, test scenarios

**Command to Validate Spec Exists**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
ls docs/planning/CSV_TECHNICAL_SPECIFICATION.md
```

---

### Task CSV-T3 → Task CSV-T4
**Required Context**:
- Test file path: `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\tests\test_extractors\test_csv_extractor.py`
- Test failure output: capture from `pytest tests/test_extractors/test_csv_extractor.py --tb=short`
- Fixture directory: `tests/fixtures/csv/`

**Command to Capture Context**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
pytest tests/test_extractors/test_csv_extractor.py --tb=short
ls tests/fixtures/csv/
```

**Expected**: All tests FAILED (RED state)

---

### Task CSV-T4 → Task CSV-T5
**Required Context**:
- Implementation file path: `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\src\extractors\csv_extractor.py`
- Test results: capture from `pytest tests/test_extractors/test_csv_extractor.py -v`

**Command to Capture Context**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
pytest tests/test_extractors/test_csv_extractor.py -v
pytest --cov=src/extractors/csv_extractor.py --cov-report=term-missing
```

**Expected**: All tests PASSED, coverage ≥85%

---

### Task CSV-T5 → Task CSV-T6
**Required Context**:
- Code review document: `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\docs\reviews\CSV_EXTRACTOR_CODE_REVIEW.md`
- Issue count: critical=0, major=0

**Command to Validate**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
grep -c "CRITICAL" docs/reviews/CSV_EXTRACTOR_CODE_REVIEW.md
grep -c "MAJOR" docs/reviews/CSV_EXTRACTOR_CODE_REVIEW.md
```

**Expected**: Both commands return 0

---

## Quality Metrics

### Test Coverage Target
**Requirement**: ≥85% for `src/extractors/csv_extractor.py`

**Measurement Command**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
pytest --cov=src/extractors/csv_extractor.py --cov-report=term-missing
```

**Expected Output**: Coverage percentage ≥85%

**IF BELOW TARGET**:
1. Identify uncovered lines: review --cov-report=term-missing output
2. Add tests for uncovered paths
3. Re-run coverage measurement

---

### Performance Target
**Requirement**: <1s for 1000 rows

**Measurement Command**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
time python -m cli extract tests/fixtures/csv/large_1000_rows.csv --format json
```

**Expected Output**: real time <1.0s

**IF ABOVE TARGET**:
1. Profile code: python -m cProfile -o profile.stats src/extractors/csv_extractor.py
2. Identify bottlenecks
3. Optimize: use csv.reader instead of manual parsing, avoid list copies

---

### Delimiter Detection Accuracy
**Requirement**: >95% accuracy

**Measurement**: Test with 20 diverse CSV files (comma, tab, semicolon, pipe)

**Test Set**: Collect 20 CSV files from various sources

**Command**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
python scripts/test_delimiter_detection.py --input-dir test_files/csv_diverse/ --output-report delimiter_accuracy.json
```

**Expected**: Accuracy ≥95% (19/20 correct)

---

### Encoding Detection Accuracy
**Requirement**: >90% accuracy

**Measurement**: Test with 20 files (UTF-8, Latin-1, CP1252)

**Command**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
python scripts/test_encoding_detection.py --input-dir test_files/csv_encodings/ --output-report encoding_accuracy.json
```

**Expected**: Accuracy ≥90% (18/20 correct)

---

## Rollback Procedure

### IF Implementation Fails Validation
**Condition**: Checkpoint C fails after implementation attempt

**Steps**:
1. Check: Does csv_extractor.py exist? `ls src/extractors/csv_extractor.py`
2. Check: Does it implement BaseExtractor? `python -c "from src.extractors.csv_extractor import CSVExtractor; from src.core.interfaces import BaseExtractor; print(issubclass(CSVExtractor, BaseExtractor))"`
3. Check: Can it import? `python -c "from src.extractors.csv_extractor import CSVExtractor; print('OK')"`
4. IF import fails: Review import errors, fix dependencies
5. IF tests fail: Debug with `pytest tests/test_extractors/test_csv_extractor.py -vv --tb=long --pdb`
6. Analyze specific test failures
7. Re-assign Task CSV-T4 with specific fixes
8. Re-run Checkpoint C

---

### IF Code Review Identifies Critical Issues
**Condition**: Checkpoint D finds critical or major issues

**Steps**:
1. Extract issue list from `docs/reviews/CSV_EXTRACTOR_CODE_REVIEW.md`
2. Prioritize: critical first, then major
3. Create fix plan: one issue per fix cycle
4. Re-assign Task CSV-T4 with specific fix instructions
5. Re-run Checkpoint C
6. Re-run code review (Task CSV-T5)
7. Repeat until zero critical/major issues

---

### IF Pipeline Integration Fails
**Condition**: Checkpoint D fails (CLI doesn't accept CSV)

**Steps**:
1. Check: Is CSVExtractor imported? `grep "CSVExtractor" src/pipeline/extraction_pipeline.py`
2. Check: Is it registered? `grep "register.*CSVExtractor" src/pipeline/extraction_pipeline.py`
3. Check: File extension mapping? `grep "csv" src/pipeline/extraction_pipeline.py`
4. Run CLI in verbose mode: `python -m cli extract sample.csv --format json -v`
5. Review pipeline logs for errors
6. Fix registration code
7. Re-run Checkpoint D

---

## Success Metrics

**Feature Complete When**:
```
✓ All 6 tasks completed
✓ All 4 checkpoints passed
✓ Test coverage ≥85%
✓ CSVExtractor registered in pipeline
✓ CLI accepts CSV files
✓ Integration tests pass
✓ Code review approved (zero critical/major issues)
✓ CSV data appears in JSON/Markdown output
```

**Deployment Ready When**:
```
✓ Success metrics achieved
✓ Manual testing: 10 diverse CSV files extract successfully
✓ Performance: <1s for 1000 rows
✓ Delimiter detection: >95% accuracy
✓ Encoding detection: >90% accuracy
✓ Zero regressions: all 778 existing tests still pass
✓ Documentation updated: USER_GUIDE.md includes CSV support
```

---

**Version**: 1.0
**Last Updated**: 2025-11-06
**Orchestrator**: Claude Code
