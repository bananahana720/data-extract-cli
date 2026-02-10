# Story: Refactor Large Test Files for DoD Compliance

**Epic:** Epic 3 - Chunk & Output (Technical Debt)
**Story ID:** 3.9 (Quality Improvement)
**Priority:** P1 (HIGH)
**Status:** done

## Overview

Refactor 5 test files that exceed TEA DoD <300 line requirement to improve maintainability, reviewability, and test discovery performance. Current 71% non-compliance rate impacts code quality and violates Test Architect best practices.

## Problem Statement

Epic 3 has excellent test coverage (94%) and sound architecture, but 5 out of 7 sampled test files exceed the 300-line limit from TEA DoD. This reduces maintainability (harder to find specific tests), slows IDE/test discovery performance, and makes code reviews more difficult. The worst offender (`test_txt_formatter.py` at 677 lines) is 126% over the limit.

## User Story

**As a** test maintainer
**I want** all test files to comply with <300 line DoD requirement
**So that** tests are easy to navigate, review, and maintain over time

## Acceptance Criteria

### AC-3.9-1 (P1 - Critical): test_txt_formatter.py Split into 3 Files
- **Given:** test_txt_formatter.py with 677 lines
- **When:** Refactored into logical modules
- **Then:** 3 new files created:
  - `test_txt_formatter_basic.py` (~200 lines) - Creation, delimiters, sequential numbering
  - `test_txt_formatter_cleaning.py` (~250 lines) - Text cleaning, artifact removal (markdown, HTML, JSON, ANSI)
  - `test_txt_formatter_metadata.py` (~200 lines) - Metadata headers, encoding (UTF-8-sig), output contract
- **And:** All tests pass after refactoring
- **And:** Each file <300 lines

### AC-3.9-2 (P1): test_json_formatter.py Split into 2-3 Files
- **Given:** test_json_formatter.py with 561 lines
- **When:** Refactored
- **Then:** 2-3 new files created:
  - `test_json_formatter_structure.py` - JSON structure, root metadata
  - `test_json_formatter_serialization.py` - Metadata serialization, ISO 8601, Path stringification
  - `test_json_formatter_validation.py` (optional) - Pretty-printing, field ordering
- **And:** All tests pass
- **And:** Each file <300 lines

### AC-3.9-3 (P1): test_json_output_pipeline.py Split into 2-3 Files
- **Given:** test_json_output_pipeline.py with 463 lines
- **When:** Refactored
- **Then:** 2-3 new files created:
  - `test_json_pipeline_basic.py` - End-to-end pipeline, metadata accuracy
  - `test_json_pipeline_compatibility.py` - Cross-library compatibility (Python json, pandas, jq, Node.js)
  - `test_json_pipeline_queryability.py` - Queryability tests (jq filtering, pandas DataFrame, JavaScript)
- **And:** All tests pass
- **And:** Each file <300 lines

### AC-3.9-4 (P1): test_entity_preserver.py Split into 2-3 Files
- **Given:** test_entity_preserver.py with 446 lines
- **When:** Refactored
- **Then:** 2-3 new files created:
  - `test_entity_preserver_analysis.py` - Entity sorting, context snippets, boundary detection
  - `test_entity_preserver_gaps.py` - Gap finding between entities
  - `test_entity_preserver_relationships.py` - Relationship detection ("mitigated by" patterns)
- **And:** All tests pass
- **And:** Each file <300 lines

### AC-3.9-5 (P2): test_engine.py Minor Cleanup
- **Given:** test_engine.py with 309 lines (only 9 lines over)
- **When:** Minor refactoring
- **Then:** Extract 1-2 helper functions OR split one test class
- **And:** File reduced to <300 lines
- **And:** All tests pass

## Technical Approach

**Refactoring Pattern:**
1. Identify logical test groupings within large file (by test class or functionality)
2. Create new test files with descriptive names
3. Move test classes/functions to new files
4. Ensure fixtures remain accessible (import from conftest.py or duplicate if needed)
5. Run tests to verify all pass after split
6. Delete original large file
7. Update any import references in other test files

**Example (test_txt_formatter.py):**
```bash
# Step 1: Create new files
touch tests/unit/test_output/test_txt_formatter_basic.py
touch tests/unit/test_output/test_txt_formatter_cleaning.py
touch tests/unit/test_output/test_txt_formatter_metadata.py

# Step 2: Move test classes
# - TestTxtFormatterCreation → test_txt_formatter_basic.py
# - TestTxtFormatterDelimiters → test_txt_formatter_basic.py
# - TestTxtFormatterArtifactRemoval → test_txt_formatter_cleaning.py
# - TestTxtFormatterMetadataHeaders → test_txt_formatter_metadata.py
# - TestTxtFormatterEncoding → test_txt_formatter_metadata.py

# Step 3: Verify tests pass
pytest tests/unit/test_output/test_txt_formatter_*.py -v

# Step 4: Delete original
rm tests/unit/test_output/test_txt_formatter.py

# Step 5: Run full test suite
pytest tests/unit/test_output/ -v
```yaml

**Fixture Handling:**
- Shared fixtures in `tests/conftest.py` remain accessible (no changes needed)
- File-specific fixtures can be duplicated in new files OR moved to conftest.py

**Import Updates:**
- Check for any imports of test classes from large files in other test files
- Update imports to reference new file locations

## Definition of Done

- [ ] All 5 files refactored (test_txt_formatter.py, test_json_formatter.py, test_json_output_pipeline.py, test_entity_preserver.py, test_engine.py)
- [ ] Each new file <300 lines (100% DoD compliance)
- [ ] All tests pass after refactoring (348 tests still passing)
- [ ] No test coverage regression (maintain 94% coverage)
- [ ] Fixtures remain accessible (no broken imports)
- [ ] Pre-commit checks pass (black, ruff, mypy)
- [ ] CI/CD pipeline passes
- [ ] Traceability matrix updated (test quality: GOOD → EXCELLENT)

## Test Execution

```bash
# Verify all tests pass after refactoring
pytest tests/unit/test_output/ tests/integration/test_output/ tests/unit/test_chunk/ -v

# Check coverage maintained
pytest --cov=src/data_extract --cov-report=html

# Count lines per file (validation)
wc -l tests/unit/test_output/test_txt_formatter_*.py
wc -l tests/unit/test_output/test_json_formatter_*.py
wc -l tests/integration/test_output/test_json_pipeline_*.py
wc -l tests/unit/test_chunk/test_entity_preserver_*.py
wc -l tests/unit/test_chunk/test_engine.py

# All should be <300 lines
```bash

## Dependencies

- Epic 3 test suite (348 tests) - EXISTS
- pytest fixtures in tests/conftest.py - EXISTS

## Risk Mitigation

**Risk:** Breaking tests during refactoring
**Mitigation:**
1. Run tests after each file split (incremental validation)
2. Keep original files until new files verified working
3. Use git branches for incremental commits

**Risk:** Fixture import issues
**Mitigation:**
1. Test new files immediately after creation
2. Duplicate file-specific fixtures if needed (temporary redundancy acceptable)

## Related Artifacts

- Traceability Matrix: `docs/traceability-matrix-epic-3.md` (Test Quality Assessment)
- TEA Knowledge Base: `bmad/bmm/testarch/knowledge/test-quality.md` (DoD <300 lines requirement)
- Test Files: `tests/unit/test_output/`, `tests/integration/test_output/`, `tests/unit/test_chunk/`

## Implementation Order

**Priority Order (by severity):**
1. **AC-3.9-1:** test_txt_formatter.py (SEVERE - 677 lines)
2. **AC-3.9-2:** test_json_formatter.py (HIGH - 561 lines)
3. **AC-3.9-3:** test_json_output_pipeline.py (MEDIUM - 463 lines)
4. **AC-3.9-4:** test_entity_preserver.py (MEDIUM - 446 lines)
5. **AC-3.9-5:** test_engine.py (LOW - 309 lines)

**Can be parallelized:** Files are independent, multiple developers can work simultaneously.

## Notes

This is a technical debt story to bring Epic 3 test suite to 100% DoD compliance. No functionality changes - pure refactoring. Test architecture is fundamentally sound; only file organization needs improvement.

**Impact:**
- Improves maintainability (easier to find specific tests)
- Improves reviewability (smaller diffs in PRs)
- Improves IDE/test discovery performance
- Brings Epic 3 to 100% TEA DoD compliance

## Dev Agent Record

**Context Reference:**
- docs/stories/follow-up-3.9-refactor-large-test-files.context.xml (generated 2025-11-17)

---

**Created:** 2025-11-17
**Workflow:** testarch-trace Phase 1 follow-up
**Agent:** Murat (TEA)
