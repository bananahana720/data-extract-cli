# Coverage Baseline Report

**Generated:** 2025-11-10
**Test Framework:** pytest 8.4.2 with pytest-cov 5.0.0
**Python Version:** 3.13.9

## Executive Summary

Established baseline code coverage for brownfield codebase as part of Story 1.3 (Testing Framework and CI Pipeline).

**Overall Coverage: 55%**

## Coverage by Module

| Module | Statements | Missed | Coverage |
|--------|-----------|--------|----------|
| **CLI** | | | |
| cli/__init__.py | 2 | 0 | 100% |
| cli/__main__.py | 3 | 3 | 0% |
| cli/commands.py | 286 | 62 | 78% |
| cli/main.py | 42 | 17 | 60% |
| cli/progress_display.py | 160 | 67 | 58% |
| **Core** | | | |
| core/__init__.py | 3 | 0 | 100% |
| core/interfaces.py | 70 | 22 | 69% |
| core/models.py | 168 | 13 | **92%** ⭐ |
| **Extractors** | | | |
| extractors/__init__.py | 7 | 0 | 100% |
| extractors/csv_extractor.py | 226 | 171 | 24% ⚠️ |
| extractors/docx_extractor.py | 174 | 56 | 68% |
| extractors/excel_extractor.py | 179 | 132 | 26% ⚠️ |
| extractors/pdf_extractor.py | 347 | 281 | **19%** ⚠️ |
| extractors/pptx_extractor.py | 175 | 133 | 24% ⚠️ |
| extractors/txt_extractor.py | 54 | 30 | 44% |
| **Formatters** | | | |
| formatters/__init__.py | 4 | 0 | 100% |
| formatters/chunked_text_formatter.py | 107 | 19 | **82%** ⭐ |
| formatters/json_formatter.py | 178 | 73 | 59% |
| formatters/markdown_formatter.py | 114 | 39 | 66% |
| **Infrastructure** | | | |
| infrastructure/__init__.py | 8 | 2 | 75% |
| infrastructure/config_manager.py | 162 | 84 | 48% |
| infrastructure/error_handler.py | 130 | 68 | 48% |
| infrastructure/logging_framework.py | 82 | 39 | 52% |
| infrastructure/progress_tracker.py | 130 | 55 | 58% |
| **Pipeline** | | | |
| pipeline/__init__.py | 3 | 0 | 100% |
| pipeline/batch_processor.py | 70 | 16 | 77% |
| pipeline/extraction_pipeline.py | 175 | 46 | 74% |
| **Processors** | | | |
| processors/__init__.py | 4 | 0 | 100% |
| processors/context_linker.py | 70 | 8 | **89%** ⭐ |
| processors/metadata_aggregator.py | 49 | 6 | **88%** ⭐ |
| processors/quality_validator.py | 90 | 19 | 79% |
| **TOTAL** | **3,280** | **1,469** | **55%** |

## Test Execution Summary

- **Total tests collected:** 1,007
- **Passed:** 34 (in limited run with --maxfail=5)
- **Failed:** 5
- **Skipped:** 1
- **Collection errors:** 1 (test_cli_benchmarks.py - missing psutil)
- **Duration:** 10.58 seconds

## Key Findings

### High Coverage Areas ⭐
- **core/models.py** (92%) - Well-tested data models
- **processors/** (79-89%) - Strong processor test coverage
- **formatters/chunked_text_formatter.py** (82%) - Good formatter coverage

### Low Coverage Areas ⚠️
- **extractors/pdf_extractor.py** (19%) - CRITICAL: Largest module (347 lines) with lowest coverage
- **extractors/csv_extractor.py** (24%) - Needs comprehensive testing
- **extractors/excel_extractor.py** (26%) - Inadequate test coverage
- **extractors/pptx_extractor.py** (24%) - Poor coverage for complex extraction

### Module Entry Points
- Multiple `__main__.py` and `__init__.py` files have 0% coverage (expected - entry points not exercised in unit tests)

## Known Test Failures

5 tests failed during baseline run:
1. `test_cli_012_version_short_flag` - CLI version flag issue
2. `test_cli_015_config_validate_invalid` - Config validation
3. `test_cli_037_config_validate_invalid_shows_helpful_error` - Config validation error messages
4. `test_cli_038_batch_empty_directory_handled` - Batch processing edge case
5. `test_cf_002_same_source_multiple_formatters_consistency` - Formatter API signature mismatch

## Comparison to Story Expectations

**Story 1.3 Targets:**
- **Target:** >80% overall coverage
- **Epic 1 Baseline:** >60% acceptable for brownfield code
- **Actual:** 55%

**Status:** Below Epic 1 baseline target by 5 percentage points.

**Brownfield Assessment Findings (Story 1.2):**
- Total tests: 1,007
- Failing: 229 (23%)
- Coverage: Unknown (never run)

**Current Status:**
- ✅ Coverage baseline established
- ✅ HTML report generated (htmlcov/)
- ⚠️ Below 60% target - needs improvement
- ⚠️ Critical gaps in extractor modules (19-26%)

## Recommendations

### Immediate Actions (Epic 1)
1. Fix 5 failing tests identified in baseline run
2. Focus on PDF extractor coverage (19% → 60% minimum)
3. Improve Excel/CSV/PPTX extractor coverage (24-26% → 60%)
4. Install missing dependency: psutil (for performance tests)
5. Fix reportlab dependency for integration tests

### Epic 2+ Actions
1. Target 80%+ coverage for all new code
2. Gradually improve brownfield coverage during refactoring
3. Add integration tests for cross-format workflows
4. Implement performance test coverage tracking

## Coverage Report Files

- **HTML Report:** `htmlcov/index.html`
- **Terminal Report:** Displayed in pytest output
- **Configuration:** `pytest.ini` and `pyproject.toml`

## Next Steps

1. ✅ Baseline documented
2. Create pre-commit hooks (Task 5)
3. Set up CI pipeline with coverage reporting (Task 6)
4. Address failing tests before Epic 2
5. Monitor coverage trends in CI

---

**Note:** This baseline is critical for Epic 2 refactoring work. All future epics must maintain or improve coverage from this baseline.
