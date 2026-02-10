# PRD: Integration & Deployment (v1.0.6)

**Feature ID**: INTEGRATION-001
**Version**: 1.0.6
**Status**: SPECIFICATION
**Created**: 2025-11-06
**Target**: Production deployment

---

## Integration Scope

### Features to Integrate
1. **DOCX Image Extraction** (DOCX-IMAGE-001)
   - Status: Complete per PRD_DOCX_IMAGE_EXTRACTION.md
   - Integration point: src/extractors/docx_extractor.py
   - Deliverable: Images in ExtractionResult → ProcessingResult → FormattedOutput

2. **CSV Extractor** (CSV-EXTRACT-001)
   - Status: Complete per PRD_CSV_EXTRACTOR.md
   - Integration point: src/extractors/csv_extractor.py
   - Deliverable: CSV files supported in pipeline and CLI

### Integration Requirements
```
[ ] Both features independently validated (all unit tests pass)
[ ] Pipeline preserves DOCX images through 3-stage processing
[ ] Pipeline routes CSV files to CSVExtractor
[ ] CLI commands work: extract, batch, validate for both features
[ ] Formatters serialize images and CSV tables correctly
[ ] Configuration supports both features (extract_images, csv_delimiter, etc.)
[ ] Error handling works for both features
[ ] No feature interaction conflicts
```

---

## Acceptance Criteria

```
[ ] Full test suite passes: pytest tests/ -q → 778 + new tests (≥850 total) all pass
[ ] Integration tests pass: pytest tests/integration/test_new_features_integration.py -v → 100% PASSED
[ ] CLI extract with CSV: python -m cli extract sample.csv --format json → success
[ ] CLI extract with DOCX images: python -m cli extract doc_with_images.docx --format json → images present
[ ] CLI batch mixed formats: python -m cli batch mixed_formats/ output/ → 100% success
[ ] Smoke tests: python scripts/run_smoke_tests.py → 100% pass rate
[ ] Documentation updated: PROJECT_STATE.md reflects v1.0.6
[ ] Documentation updated: CLAUDE.md includes new features
[ ] Documentation updated: USER_GUIDE.md includes usage examples
[ ] Package builds: python -m build → dist/ai_data_extractor-1.0.6-py3-none-any.whl
[ ] Clean install works: pip install dist/*.whl && python -m cli --help
[ ] Version updated: python -m cli --version → 1.0.6
```

---

## Task Breakdown

### Task INT-T1: Feature Integration (Pipeline)
**Agent**: General-purpose integration
**Duration**: 30 minutes
**Dependencies**: DOCX-IMAGE-001 complete, CSV-EXTRACT-001 complete

**Input Files**:
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\src\pipeline\extraction_pipeline.py`
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\src\extractors\docx_extractor.py`
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\src\extractors\csv_extractor.py`

**Output Deliverable**: Updated pipeline registration in `src/pipeline/extraction_pipeline.py`

**Success Criteria**:
```
[ ] CSVExtractor imported: grep "from src.extractors.csv_extractor import CSVExtractor" src/pipeline/extraction_pipeline.py → match found
[ ] CSVExtractor registered: grep "CSVExtractor" src/pipeline/extraction_pipeline.py | grep -i "register" → match found
[ ] File extension mapping: .csv → CSVExtractor, .tsv → CSVExtractor
[ ] DOCX images preserved: verify src/processors/*.py preserve images field
[ ] Pipeline test: pytest tests/test_pipeline/ -v → all pass
```

**Command to Validate**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
grep "CSVExtractor" src/pipeline/extraction_pipeline.py
pytest tests/test_pipeline/test_extraction_pipeline.py -v
```

**Expected Output**: Import found, all pipeline tests PASSED

---

### Task INT-T2: Integration Test Suite
**Agent**: npl-tdd-builder
**Duration**: 45 minutes
**Dependencies**: INT-T1 (pipeline integration complete)

**Input Files**:
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\tests\integration\` (directory)

**Output Deliverable**: Enhanced `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\tests\integration\test_new_features_integration.py`

**Success Criteria**:
```
[ ] Test class: TestDocxImages with 5+ test cases
[ ] Test class: TestCsvExtractor with 5+ test cases
[ ] Test class: TestCrossFeature with 3+ test cases
[ ] Test: test_docx_images_through_pipeline → DOCX with images → JSON output
[ ] Test: test_docx_images_markdown_output → DOCX with images → Markdown output
[ ] Test: test_csv_through_pipeline → CSV file → JSON output
[ ] Test: test_csv_batch_processing → multiple CSV files → batch output
[ ] Test: test_mixed_format_batch → DOCX + CSV + PDF in batch → all succeed
[ ] Test: test_docx_with_images_and_tables → both features together
[ ] Test: test_csv_delimiter_detection → various delimiters auto-detected
[ ] Test: test_configuration_inheritance → config applies to both features
[ ] All integration tests PASS: pytest tests/integration/test_new_features_integration.py -v → 100% PASSED
[ ] Test count ≥13: pytest tests/integration/test_new_features_integration.py --collect-only | grep "test_" | wc -l → ≥13
```

**Command to Validate**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
pytest tests/integration/test_new_features_integration.py -v
pytest tests/integration/test_new_features_integration.py --collect-only | grep "test_"
```

**Expected Output**: 13+ tests collected, 100% PASSED

---

### Task INT-T3: CLI Validation
**Agent**: General-purpose validation
**Duration**: 20 minutes
**Dependencies**: INT-T2 (integration tests passing)

**Input Files**:
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\src\cli\main.py`
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\src\cli\commands.py`

**Output Deliverable**: CLI validation report (console output)

**Success Criteria**:
```
[ ] CLI help works: python -m cli --help → displays commands
[ ] CLI version correct: python -m cli --version → 1.0.6
[ ] CSV extract works: python -m cli extract tests/fixtures/csv/simple.csv --format json → success
[ ] CSV output valid: python -m cli extract tests/fixtures/csv/simple.csv --format json && python -m json.tool output.json → valid JSON
[ ] DOCX extract works: python -m cli extract tests/fixtures/docx/with_images.docx --format json → success
[ ] DOCX images present: python -m cli extract tests/fixtures/docx/with_images.docx --format json && grep "images" output.json → match found
[ ] Batch mixed formats: python -m cli batch tests/fixtures/mixed/ output_batch/ → all files processed
[ ] Batch CSV included: ls output_batch/*.json | wc -l → count includes CSV files
[ ] Batch DOCX included: ls output_batch/*.json | wc -l → count includes DOCX files
[ ] Error handling: python -m cli extract nonexistent.csv --format json → graceful error (exit code ≠0)
```

**Command to Validate**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
python -m cli --version
python -m cli extract tests/fixtures/csv/simple.csv --format json
python -m cli extract tests/fixtures/docx/with_images.docx --format json
python -m cli batch tests/fixtures/mixed/ output_batch/
```

**Expected Output**: All commands succeed, version = 1.0.6

---

### Task INT-T4: Smoke Test Suite
**Agent**: General-purpose testing
**Duration**: 30 minutes
**Dependencies**: INT-T3 (CLI validated)

**Input Files**:
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\scripts\run_smoke_tests.py` (create if not exists)

**Output Deliverable**: Smoke test script + test files at `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\test_files\`

**Success Criteria**:
```
[ ] Test files created: ls test_files/ | wc -l → ≥8 (variety of formats)
[ ] Test files include: sample.csv, sample.tsv, doc_with_images.docx, doc_with_tables.docx, sample.pdf, sample.xlsx, sample.pptx, sample.txt
[ ] Smoke test script exists: ls scripts/run_smoke_tests.py → file found
[ ] Smoke test runs: python scripts/run_smoke_tests.py → completes without crash
[ ] Success rate 100%: python scripts/run_smoke_tests.py | grep "Success rate" | awk '{print $3}' → 100%
[ ] CSV smoke test: extract sample.csv → success
[ ] DOCX images smoke test: extract doc_with_images.docx → images present
[ ] DOCX tables smoke test: extract doc_with_tables.docx → tables present
[ ] TSV smoke test: extract sample.tsv → success
[ ] Mixed batch smoke test: batch test_files/ output_smoke/ → 100% success
```

**Command to Validate**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
ls test_files/
python scripts/run_smoke_tests.py
```

**Expected Output**: 8+ test files, 100% success rate

---

### Task INT-T5: Documentation Update
**Agent**: npl-technical-writer
**Duration**: 40 minutes
**Dependencies**: INT-T4 (smoke tests passing)

**Input Files**:
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\PROJECT_STATE.md`
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\CLAUDE.md`
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\docs\USER_GUIDE.md`

**Output Deliverable**: Updated documentation files

**Success Criteria**:
```
[ ] PROJECT_STATE.md updated: version = v1.0.6
[ ] PROJECT_STATE.md updated: new features listed (DOCX images, CSV extractor)
[ ] PROJECT_STATE.md updated: test count = 850+ (or actual count)
[ ] CLAUDE.md updated: recent deployment section includes v1.0.6
[ ] CLAUDE.md updated: module status includes CSVExtractor
[ ] CLAUDE.md updated: extraction capabilities include CSV
[ ] USER_GUIDE.md updated: CSV extraction section added
[ ] USER_GUIDE.md updated: DOCX image extraction section added
[ ] USER_GUIDE.md updated: usage examples for both features
[ ] USER_GUIDE.md updated: configuration options documented (extract_images, csv_delimiter, etc.)
[ ] CHANGELOG.md created/updated: v1.0.6 entry with feature list
```

**Command to Validate**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
grep "1.0.6" PROJECT_STATE.md
grep "CSV" docs/USER_GUIDE.md
grep "image extraction" docs/USER_GUIDE.md
```

**Expected Output**: Version found, CSV and image extraction documented

---

### Task INT-T6: Package Build & Validation
**Agent**: General-purpose build
**Duration**: 25 minutes
**Dependencies**: INT-T5 (documentation complete)

**Input Files**:
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\pyproject.toml`
- `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\setup.py` (if exists)

**Output Deliverable**: Wheel file at `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\dist\ai_data_extractor-1.0.6-py3-none-any.whl`

**Success Criteria**:
```
[ ] Version updated in pyproject.toml: grep "version" pyproject.toml | grep "1.0.6" → match found
[ ] Build succeeds: python -m build → no errors
[ ] Wheel created: ls dist/ai_data_extractor-1.0.6-py3-none-any.whl → file exists
[ ] Clean install: python -m venv test-env && test-env\Scripts\activate && pip install dist/ai_data_extractor-1.0.6-py3-none-any.whl → success
[ ] CLI available: test-env\Scripts\activate && data-extract --help → displays help
[ ] CLI version: test-env\Scripts\activate && data-extract --version → 1.0.6
[ ] CLI extract CSV: test-env\Scripts\activate && data-extract extract tests/fixtures/csv/simple.csv --format json → success
[ ] CLI extract DOCX images: test-env\Scripts\activate && data-extract extract tests/fixtures/docx/with_images.docx --format json → success
```

**Command to Validate**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
grep "version" pyproject.toml
python -m build
ls dist/ai_data_extractor-1.0.6-py3-none-any.whl
```

**Expected Output**: Version = 1.0.6, wheel file exists

---

## Validation Checkpoints

### Checkpoint E: Integration Complete
**When**: After Task INT-T1
**Decision Point**: APPROVE → proceed to INT-T2 | REJECT → debug integration

**Validation**:
```
[ ] CSVExtractor in pipeline: grep -r "CSVExtractor" src/pipeline/extraction_pipeline.py → match found
[ ] CSVExtractor imported: grep "from src.extractors.csv_extractor import" src/pipeline/extraction_pipeline.py → match found
[ ] Pipeline tests passing: pytest tests/test_pipeline/ --maxfail=5 -q → 0 failures
[ ] CLI recognizes CSV: python -m cli extract tests/fixtures/csv/simple.csv --format json && echo $? → 0
[ ] Images preserved: grep -r "images" src/processors/*.py | wc -l → ≥3 (3 processors)
```

**Command**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
grep "CSVExtractor" src/pipeline/extraction_pipeline.py
pytest tests/test_pipeline/ -q
python -m cli extract tests/fixtures/csv/simple.csv --format json
```

**Expected Output**: Import found, tests passed, CLI succeeds

**IF REJECT**:
1. Check: Is CSVExtractor imported?
2. Check: Is it registered in pipeline?
3. Run pipeline tests: pytest tests/test_pipeline/ -vv --tb=long
4. Analyze failures
5. Fix registration issues
6. Re-run Checkpoint E

---

### Checkpoint F: Smoke Tests
**When**: After Task INT-T4
**Decision Point**: APPROVE → proceed to INT-T5 | REJECT → investigate failures

**Validation**:
```
[ ] Test files exist: ls test_files/ | wc -l → ≥8
[ ] Smoke test script exists: ls scripts/run_smoke_tests.py → file found
[ ] Smoke test runs: python scripts/run_smoke_tests.py → exit code 0
[ ] Success rate 100%: python scripts/run_smoke_tests.py | grep "Success rate" | grep "100%" → match found
[ ] CSV tested: python scripts/run_smoke_tests.py | grep "sample.csv" | grep "PASS" → match found
[ ] DOCX images tested: python scripts/run_smoke_tests.py | grep "doc_with_images.docx" | grep "PASS" → match found
```

**Command**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
ls test_files/ | wc -l
python scripts/run_smoke_tests.py
```

**Expected Output**: 8+ test files, 100% success rate

**IF REJECT**:
1. Identify failed test: python scripts/run_smoke_tests.py | grep "FAIL"
2. Run failed test manually: python -m cli extract test_files/[failed_file] --format json -v
3. Analyze error: check logs, stack trace
4. Fix issue: update extractor/pipeline/formatter
5. Re-run smoke tests
6. Re-run Checkpoint F

---

### Checkpoint G: Package Validation
**When**: After Task INT-T6
**Decision Point**: APPROVE → DEPLOY | REJECT → fix package

**Validation**:
```
[ ] Build succeeds: python -m build && echo $? → 0
[ ] Wheel exists: ls dist/ai_data_extractor-1.0.6-py3-none-any.whl → file found
[ ] Clean install: python -m venv test-env && test-env\Scripts\activate && pip install dist/*.whl && echo $? → 0
[ ] CLI works: test-env\Scripts\activate && data-extract --help && echo $? → 0
[ ] Version correct: test-env\Scripts\activate && data-extract --version | grep "1.0.6" → match found
[ ] CSV extract works: test-env\Scripts\activate && data-extract extract tests/fixtures/csv/simple.csv --format json && echo $? → 0
[ ] DOCX images work: test-env\Scripts\activate && data-extract extract tests/fixtures/docx/with_images.docx --format json && grep "images" output.json → match found
```

**Command**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
python -m build
ls dist/ai_data_extractor-1.0.6-py3-none-any.whl
python -m venv test-env
test-env\Scripts\activate
pip install dist/ai_data_extractor-1.0.6-py3-none-any.whl
data-extract --version
```

**Expected Output**: Build succeeds, wheel exists, version = 1.0.6

**IF REJECT**:
1. Check: Does build command succeed?
2. Check: Is version in pyproject.toml correct?
3. Check: Does wheel file exist?
4. IF install fails: check dependencies in pyproject.toml
5. IF CLI fails: check entry point in pyproject.toml
6. Fix issues
7. Rebuild: rm -rf dist/ && python -m build
8. Re-run Checkpoint G

---

## Context Passing Rules

### Task INT-T1 → Task INT-T2
**Required Context**:
- Pipeline file path: `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\src\pipeline\extraction_pipeline.py`
- Registration verification: `grep "CSVExtractor" src/pipeline/extraction_pipeline.py`

**Command to Validate Integration**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
grep "CSVExtractor" src/pipeline/extraction_pipeline.py
pytest tests/test_pipeline/ -v
```

**Expected**: Import found, tests pass

---

### Task INT-T2 → Task INT-T3
**Required Context**:
- Integration test results: `pytest tests/integration/test_new_features_integration.py -v`
- Test count: `pytest tests/integration/test_new_features_integration.py --collect-only | grep "test_" | wc -l`

**Command to Capture Context**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
pytest tests/integration/test_new_features_integration.py -v
```

**Expected**: 13+ tests, 100% PASSED

---

### Task INT-T3 → Task INT-T4
**Required Context**:
- CLI validation results: capture output from CLI commands
- Test fixtures used: list of files tested

**Command to Capture Context**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
python -m cli --version
python -m cli extract tests/fixtures/csv/simple.csv --format json
python -m cli extract tests/fixtures/docx/with_images.docx --format json
```

**Expected**: All commands succeed, version = 1.0.6

---

### Task INT-T4 → Task INT-T5
**Required Context**:
- Smoke test results: `python scripts/run_smoke_tests.py`
- Success rate: extract from output

**Command to Capture Context**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
python scripts/run_smoke_tests.py
```

**Expected**: 100% success rate

---

### Task INT-T5 → Task INT-T6
**Required Context**:
- Documentation files updated: list of modified files
- Version references: grep "1.0.6" across documentation

**Command to Validate Documentation**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
grep "1.0.6" PROJECT_STATE.md CLAUDE.md docs/USER_GUIDE.md
```

**Expected**: Version found in all files

---

## Quality Metrics

### Full Test Suite Coverage
**Requirement**: All tests pass (778 existing + new tests)

**Measurement Command**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
pytest tests/ -q
```

**Expected Output**: 850+ tests, 0 failures

**IF FAILURES**:
1. Count failures: pytest tests/ -q | grep "failed"
2. Identify failing tests: pytest tests/ --tb=short | grep "FAILED"
3. Run failing tests individually: pytest tests/path/to/test.py::test_name -vv
4. Debug and fix
5. Re-run full suite

---

### Integration Test Coverage
**Requirement**: All integration tests pass

**Measurement Command**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
pytest tests/integration/test_new_features_integration.py -v
```

**Expected Output**: 13+ tests, 100% PASSED

---

### CLI Functional Coverage
**Requirement**: All CLI commands work for both features

**Test Matrix**:
| Command | Format | Feature | Status |
|---------|--------|---------|--------|
| extract | CSV | CSV extractor | Must pass |
| extract | DOCX | DOCX images | Must pass |
| batch | Mixed | Both features | Must pass |
| validate | CSV | CSV extractor | Must pass |
| validate | DOCX | DOCX images | Must pass |

**Measurement**: Manual testing + smoke test script

---

### Smoke Test Coverage
**Requirement**: 100% success rate

**Measurement Command**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
python scripts/run_smoke_tests.py
```

**Expected Output**: "Success rate: 100%"

---

### Package Installation Test
**Requirement**: Clean install works in fresh environment

**Measurement Command**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
python -m venv test-env
test-env\Scripts\activate
pip install dist/ai_data_extractor-1.0.6-py3-none-any.whl
data-extract --version
data-extract extract tests/fixtures/csv/simple.csv --format json
```

**Expected Output**: Version = 1.0.6, extract succeeds

---

## Rollback Procedure

### IF Integration Tests Fail
**Condition**: Checkpoint F smoke tests fail

**Steps**:
1. Identify failed test: `python scripts/run_smoke_tests.py | grep "FAIL"`
2. Categorize failure: CSV issue OR DOCX images issue OR both
3. IF CSV fails: revert CSV extractor changes, re-test
4. IF DOCX images fail: revert DOCX extractor changes, re-test
5. IF both fail: check pipeline integration, processors
6. Debug: run failed test manually with verbose output
7. Fix issue: update relevant component
8. Re-run smoke tests
9. Re-run Checkpoint F

---

### IF Package Build Fails
**Condition**: Checkpoint G build fails

**Steps**:
1. Check: Does `python -m build` produce errors?
2. Review error message
3. Common issues:
   - Version syntax error in pyproject.toml
   - Missing files in MANIFEST.in
   - Import errors in __init__.py
   - Dependency version conflicts
4. Fix issue
5. Clean: `rm -rf dist/ build/ *.egg-info`
6. Rebuild: `python -m build`
7. Re-run Checkpoint G

---

### IF Package Install Fails
**Condition**: Checkpoint G install fails

**Steps**:
1. Check: Does `pip install dist/*.whl` produce errors?
2. Review error message
3. Common issues:
   - Dependency conflicts
   - Python version mismatch
   - Missing dependencies in pyproject.toml
4. Fix pyproject.toml dependencies
5. Rebuild: `rm -rf dist/ && python -m build`
6. Create fresh venv: `rm -rf test-env && python -m venv test-env`
7. Retry install
8. Re-run Checkpoint G

---

## Final Deployment Checklist

```
Pre-Deployment Verification:
[ ] All 778 original tests pass: pytest tests/test_extractors/ tests/test_processors/ tests/test_formatters/ tests/test_pipeline/ -q
[ ] All new feature tests pass: pytest tests/test_extractors/test_csv_extractor.py tests/test_extractors/test_docx_extractor.py -k "image" -q
[ ] Integration tests pass: pytest tests/integration/test_new_features_integration.py -v
[ ] Smoke tests 100%: python scripts/run_smoke_tests.py | grep "100%"
[ ] Full test suite: pytest tests/ -q → 850+ tests, 0 failures
[ ] Coverage maintained: pytest --cov=src --cov-report=term | grep "TOTAL" | awk '{print $4}' | sed 's/%//' → ≥85

Documentation Verification:
[ ] PROJECT_STATE.md updated to v1.0.6
[ ] CLAUDE.md includes new features
[ ] USER_GUIDE.md includes usage examples
[ ] CHANGELOG.md includes v1.0.6 entry
[ ] README.md updated (if applicable)

Package Verification:
[ ] Version in pyproject.toml: 1.0.6
[ ] Build succeeds: python -m build
[ ] Wheel exists: ls dist/ai_data_extractor-1.0.6-py3-none-any.whl
[ ] Clean install: pip install dist/*.whl in fresh venv
[ ] CLI works: data-extract --help
[ ] CLI version: data-extract --version → 1.0.6

Functional Verification:
[ ] CSV extraction: data-extract extract sample.csv --format json → success
[ ] DOCX image extraction: data-extract extract doc_with_images.docx --format json → images present
[ ] Batch processing: data-extract batch mixed/ output/ → all formats processed
[ ] Configuration: extract_images=False works, csv_delimiter override works
[ ] Error handling: graceful failures for corrupted files

Git & Release:
[ ] All changes committed: git status → clean
[ ] Git tag created: git tag v1.0.6
[ ] Release notes: docs/releases/v1.0.6.md created
[ ] Wheel file: dist/ai_data_extractor-1.0.6-py3-none-any.whl ready for distribution
```

---

## Success Metrics

**Phase 5 Complete When**:
```
✓ All 6 integration tasks completed
✓ All 3 checkpoints passed (E, F, G)
✓ Test suite: 850+ tests, 100% passing
✓ Smoke tests: 100% success rate
✓ Documentation: complete and accurate
✓ Package: builds and installs cleanly
✓ CLI: all commands functional
✓ Features: CSV and DOCX images working end-to-end
```

**Deployment Ready When**:
```
✓ Success metrics achieved
✓ Final deployment checklist: 100% checked
✓ Manual verification: 5 users test both features successfully
✓ Performance: no degradation vs v1.0.5
✓ Memory: no leaks detected
✓ Stability: 24-hour soak test with diverse files
✓ User documentation: reviewed and approved
✓ Package: signed and ready for distribution
```

---

## Deployment Artifacts

**Package Location**: `C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool\dist\ai_data_extractor-1.0.6-py3-none-any.whl`

**Documentation**:
- `docs/releases/v1.0.6.md` - Release notes
- `docs/USER_GUIDE.md` - Updated user guide
- `CHANGELOG.md` - Version history

**Git Tag**: `v1.0.6`

**Git Commit Message**:
```
Release v1.0.6: CSV Extractor + DOCX Image Extraction

Features:
- NEW: CSV file extraction with auto-detection (delimiter, encoding, header)
- NEW: DOCX image extraction with metadata
- IMPROVED: Pipeline preserves images through processing
- IMPROVED: CLI supports CSV and TSV files

Tests: 850+ tests (778 existing + 72 new), 100% passing
Coverage: 92%+ maintained
Smoke tests: 100% success rate (8 formats)

Fixes:
- None (clean feature additions)

Breaking Changes:
- None (backward compatible)

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

---

**Version**: 1.0
**Last Updated**: 2025-11-06
**Orchestrator**: Claude Code
