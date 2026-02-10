# Test Skip Marker Audit Report
**Date**: 2025-10-30
**Auditor**: npl-validator
**Project**: data-extractor-tool
**Total Tests**: 562 collected

---

## Executive Summary

This audit examined all test skip markers in the data-extractor-tool test suite to identify obsolete, unclear, or unnecessary skips. The audit found **39 skip markers** across the test suite, categorized into 4 types: valid permanent (3 OCR-related), valid conditional (2 platform-specific), temporary development (30 implementation-pending), and 4 unclear defensive/infrastructure skips.

### Key Findings

- **Total Skip Markers Found**: 39
- **Valid Permanent Skips**: 3 (OCR functionality, post-MVP)
- **Valid Conditional Skips**: 2 (Windows platform-specific)
- **Temporary Development Skips**: 30 (pending implementation)
- **Unclear/Defensive Skips**: 4 (need clarification)

### Recommendations Priority

1. **HIGH**: Clarify 4 unclear skips (infrastructure/defensive code)
2. **MEDIUM**: Review 30 "not yet implemented" skips - some may be obsolete
3. **LOW**: Document OCR skip tracking (link to issue/sprint planning)

---

## Detailed Inventory

### Category 1: Valid Permanent Skips ✓
**Count**: 3
**Action**: Keep with improved documentation

These skips are for post-MVP OCR functionality. They are appropriately documented and should remain skipped until OCR is prioritized.

#### OCR-Related Skips (3)

**File**: `tests/test_extractors/test_pdf_extractor.py`

1. **Line 269**: `test_detect_image_based_pdf`
   - **Reason**: "OCR dependencies (pdf2image, pytesseract) not required for MVP"
   - **Status**: ✓ VALID - Clear reason, post-MVP feature
   - **Recommendation**: Add issue tracking link
   - **Improved Reason**: "OCR dependencies (pdf2image, pytesseract) deferred to post-MVP (Sprint 5+)"

2. **Line 286**: `test_extract_with_ocr_fallback`
   - **Reason**: "OCR dependencies (pdf2image, pytesseract) not required for MVP"
   - **Status**: ✓ VALID - Clear reason, post-MVP feature
   - **Recommendation**: Add issue tracking link
   - **Improved Reason**: "OCR dependencies (pdf2image, pytesseract) deferred to post-MVP (Sprint 5+)"

3. **Line 310**: `test_ocr_can_be_disabled`
   - **Reason**: "OCR dependencies (pdf2image, pytesseract) not required for MVP"
   - **Status**: ✓ VALID - Clear reason, post-MVP feature
   - **Recommendation**: Add issue tracking link
   - **Improved Reason**: "OCR dependencies (pdf2image, pytesseract) deferred to post-MVP (Sprint 5+)"

---

### Category 2: Valid Conditional Skips ✓
**Count**: 2
**Action**: Keep as-is (well-documented)

These skips are platform-specific and correctly implemented with `@pytest.mark.skipif`.

#### Windows Platform Skips (2)

1. **File**: `tests/test_infrastructure/test_config_manager.py`
   - **Line 593**: `test_permission_error_handling`
   - **Condition**: `sys.platform == "win32"`
   - **Reason**: "File permission test not supported on Windows"
   - **Status**: ✓ VALID - Correct use of conditional skip
   - **Recommendation**: None needed

2. **File**: `tests/test_extractors/test_docx_extractor_integration.py`
   - **Line 511**: `test_file_permissions_error`
   - **Condition**: `sys.platform == "win32"`
   - **Reason**: "Permission tests unreliable on Windows"
   - **Status**: ✓ VALID - Correct use of conditional skip
   - **Recommendation**: None needed

---

### Category 3: Temporary Development Skips ⚠️
**Count**: 30
**Action**: Review and validate necessity

These skips are marked "not yet implemented" or similar. Given that **Wave 4 is complete and MVP is delivered**, some of these may be obsolete.

#### DocxExtractor Skips (14)

**File**: `tests/test_extractors/test_docx_extractor.py`

All 14 tests have skip reason: `"DocxExtractor not yet implemented"`

**Lines**: 75, 104, 135, 172, 202, 228, 255, 275, 298, 324, 345, 372, 390, 411

**Status**: ⚠️ **LIKELY OBSOLETE** - DocxExtractor was completed in Wave 1

**Tests Affected**:
- `test_extract_returns_result_object` (line 75)
- `test_extract_paragraphs_and_headings` (line 104)
- `test_content_types_classified` (line 135)
- `test_metadata_extracted` (line 172)
- `test_handles_empty_document` (line 202)
- `test_handles_missing_file` (line 228)
- `test_handles_corrupted_file` (line 255)
- `test_invalid_file_type` (line 275)
- `test_lists_detected` (line 298)
- `test_tables_detected` (line 324)
- `test_images_detected` (line 345)
- `test_hyperlinks_captured` (line 372)
- `test_styles_preserved` (line 390)
- `test_nested_structures` (line 411)

**Recommendation**:
- **REMOVE SKIPS** - DocxExtractor is complete and functional
- Tests should either:
  - Be un-skipped and verified to pass
  - Be updated if implementation differs from original TDD plan
  - Be deleted if truly obsolete

**Action Required**: Review each test against actual DocxExtractor implementation

---

#### ExcelExtractor Skips (6)

**File**: `tests/test_extractors/test_excel_extractor.py`

1. **Lines 52, 60**: Basic extraction tests
   - **Reason**: "ExcelExtractor not yet implemented"
   - **Status**: ⚠️ **LIKELY OBSOLETE** - ExcelExtractor completed in Wave 3

2. **Lines 378, 391**: Integration tests
   - **Reason**: "ExcelExtractor not yet implemented"
   - **Status**: ⚠️ **LIKELY OBSOLETE**

3. **Lines 386, 402**: Infrastructure tests
   - **Reason**: "Infrastructure not available"
   - **Status**: ⚠️ **LIKELY OBSOLETE** - Infrastructure completed in Wave 2

4. **Line 421**: Logging integration
   - **Reason**: "Logging not yet integrated"
   - **Status**: ⚠️ **LIKELY OBSOLETE** - Logging framework completed in Wave 2

5. **Lines 443, 449**: Chart detection
   - **Reason**: "Chart fixture not yet created"
   - **Status**: ⚠️ **NEEDS REVIEW** - Is chart detection implemented? If not, skip is valid.

6. **Line 603**: Large file test
   - **Reason**: "Large fixture not yet created"
   - **Status**: ⚠️ **NEEDS REVIEW** - Is large file testing needed?

**Recommendation**:
- Lines 52, 60, 378, 391, 386, 402, 421: **REMOVE SKIPS** or **DELETE TESTS** if obsolete
- Lines 443, 449: Keep skip if chart detection is post-MVP, otherwise create fixture
- Line 603: Keep skip if large file testing is post-MVP, otherwise create fixture

---

#### PptxExtractor Skips (6)

**File**: `tests/test_extractors/test_pptx_extractor.py`

1. **Lines 252, 282, 299**: Dependency checks
   - **Reason**: "python-pptx not installed"
   - **Status**: ⚠️ **CONDITIONAL SKIP INSIDE TEST** - Uses `pytest.skip()` at runtime
   - **Issue**: Should use `@pytest.mark.skipif` decorator instead

2. **Lines 327, 350, 390, 415**: Infrastructure tests
   - **Reason**: "Infrastructure not available"
   - **Status**: ⚠️ **LIKELY OBSOLETE** - Infrastructure completed in Wave 2

**Recommendation**:
- Lines 252, 282, 299: Convert to proper conditional skips using decorator
- Lines 327, 350, 390, 415: **REMOVE SKIPS** - Infrastructure is available

---

#### PDF Extractor Dependency Skip (1)

**File**: `tests/test_extractors/test_pdf_extractor.py`

1. **Line 738**: Encryption test
   - **Reason**: "pypdf not available for encryption test"
   - **Status**: ⚠️ **CONDITIONAL SKIP INSIDE TEST** - Should use decorator
   - **Recommendation**: Convert to `@pytest.mark.skipif(not HAS_PYPDF, reason="...")`

---

#### Integration Test Dependency Skips (4)

**File**: `tests/integration/conftest.py`

These are conditional skips inside fixture functions:

1. **Line 45**: `docx_with_tables` fixture
   - **Reason**: "python-docx not installed"
   - **Status**: ✓ VALID - Proper dependency check in fixture

2. **Line 120**: `sample_pdf` fixture
   - **Reason**: "reportlab not installed"
   - **Status**: ✓ VALID - Proper dependency check in fixture

3. **Line 196**: `complex_docx` fixture
   - **Reason**: "python-docx not installed"
   - **Status**: ✓ VALID - Proper dependency check in fixture

4. **Line 269**: `docx_with_metadata` fixture
   - **Reason**: "python-docx not installed"
   - **Status**: ✓ VALID - Proper dependency check in fixture

**Recommendation**: Keep as-is (proper pattern for optional dependencies)

---

#### Test Fixture Dependency Skip (1)

**File**: `tests/test_extractors/conftest.py`

1. **Line 28**: `sample_pdf` fixture
   - **Reason**: "reportlab not installed"
   - **Status**: ✓ VALID - Proper dependency check in fixture

**Recommendation**: Keep as-is

---

### Category 4: Unclear/Defensive Skips ❓
**Count**: 1
**Action**: Clarify purpose or remove

These skips have unclear rationale or appear to be defensive programming.

#### Defensive Exception Handling Skip (1)

**File**: `tests/test_extractors/test_docx_extractor_integration.py`

1. **Line 562**: `test_internal_exception_handling`
   - **Reason**: "Exception handler is defensive code - difficult to test without breaking isolation"
   - **Status**: ❓ **UNCLEAR** - Why skip if it's defensive code?
   - **Issue**: If code is untestable, consider refactoring. If skip is intentional, clarify.
   - **Recommendation**: Either:
     - Remove skip and add focused test using mocking
     - Document why testing is deferred (e.g., "Low priority, difficult to isolate")
     - Remove test entirely if truly untestable

---

## pytest.ini Marker Registration

### Current Registered Markers

From `pytest.ini`:
```ini
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (slower, multiple components)
    slow: Tests that may take more than 1 second
    performance: Performance and benchmarking tests
    extraction: Tests for extractor modules
    processing: Tests for processor modules
    formatting: Tests for formatter modules
    pipeline: Tests for pipeline orchestration
    cli: Command-line interface tests
```

### Missing Markers

No custom skip markers are used in the codebase. All skips use standard pytest decorators:
- `@pytest.mark.skip(reason="...")`
- `@pytest.mark.skipif(condition, reason="...")`

### Recommendation

Consider adding a custom marker for post-MVP features:

```ini
markers =
    ...
    post_mvp: Features deferred to post-MVP (OCR, charts, etc.)
```

Usage:
```python
@pytest.mark.skip(reason="OCR deferred to post-MVP")
@pytest.mark.post_mvp
def test_ocr_feature():
    pass
```

Benefits:
- Easy to run all post-MVP tests: `pytest -m post_mvp`
- Easy to skip post-MVP tests: `pytest -m "not post_mvp"`
- Clear categorization of future work

---

## Risk Assessment

### High Risk Issues

None identified. All skips are documented with reasons.

### Medium Risk Issues

1. **30 Temporary Skips May Be Obsolete**
   - **Impact**: Reduced test coverage, false sense of completeness
   - **Risk**: Unknown whether features are actually implemented and working
   - **Mitigation**: Review each skip against actual implementation

2. **Inconsistent Skip Patterns**
   - **Impact**: Some skips use decorators, others use runtime `pytest.skip()`
   - **Risk**: Runtime skips are harder to track and filter
   - **Mitigation**: Standardize on decorator-based skips where possible

### Low Risk Issues

1. **OCR Skips Lack Issue Tracking Links**
   - **Impact**: Difficult to track when OCR work is scheduled
   - **Risk**: Skips may be forgotten
   - **Mitigation**: Add issue numbers to skip reasons

---

## Detailed Recommendations

### Priority 1: HIGH - Immediate Action Required

**Task 1.1**: Review DocxExtractor skips (14 tests)
- **File**: `tests/test_extractors/test_docx_extractor.py`
- **Action**: For each skipped test:
  - Remove `@pytest.mark.skip` decorator
  - Run test to see if it passes
  - If fails, update test to match actual implementation
  - If obsolete, delete test entirely
- **Estimated Time**: 60 minutes
- **Impact**: Potential +14 test coverage

**Task 1.2**: Review ExcelExtractor skips (6 tests)
- **File**: `tests/test_extractors/test_excel_extractor.py`
- **Action**: Same as Task 1.1
- **Estimated Time**: 30 minutes
- **Impact**: Potential +6 test coverage

**Task 1.3**: Review PptxExtractor skips (6 tests)
- **File**: `tests/test_extractors/test_pptx_extractor.py`
- **Action**: Same as Task 1.1, plus convert runtime skips to decorators
- **Estimated Time**: 30 minutes
- **Impact**: Potential +6 test coverage

### Priority 2: MEDIUM - Important but Not Urgent

**Task 2.1**: Clarify unclear skip
- **File**: `tests/test_extractors/test_docx_extractor_integration.py:562`
- **Action**: Either remove skip and add test, or document why skip is necessary
- **Estimated Time**: 15 minutes

**Task 2.2**: Standardize skip patterns
- **Action**: Convert runtime `pytest.skip()` calls to decorators where possible
- **Files**: `test_pptx_extractor.py`, `test_pdf_extractor.py`
- **Estimated Time**: 20 minutes

**Task 2.3**: Add issue tracking to OCR skips
- **Action**: Update OCR skip reasons to include sprint/issue references
- **Estimated Time**: 10 minutes

### Priority 3: LOW - Nice to Have

**Task 3.1**: Add `post_mvp` marker to pytest.ini
- **Action**: Register new marker for future work
- **Estimated Time**: 5 minutes

**Task 3.2**: Create skip policy documentation
- **Action**: Document when and how to skip tests
- **File**: `docs/test-plans/TEST_SKIP_POLICY.md`
- **Estimated Time**: 30 minutes

---

## Cleanup Action Plan

### Step 1: Validate Extractor Implementations (90 minutes)

For each extractor with skipped tests:

1. **Check if extractor exists and is functional**
   ```bash
   python -c "from extractors.docx_extractor import DocxExtractor; print('OK')"
   python -c "from extractors.excel_extractor import ExcelExtractor; print('OK')"
   python -c "from extractors.pptx_extractor import PptxExtractor; print('OK')"
   ```

2. **Run actual extraction to verify functionality**
   ```bash
   cd tests/fixtures/real-world-files
   # Test each extractor with real files
   ```

3. **For each skipped test**:
   - Remove skip decorator
   - Run test: `pytest tests/test_extractors/test_<name>.py::test_<name> -v`
   - If passes: ✓ Skip removed successfully
   - If fails: Update test or re-skip with clearer reason
   - If obsolete: Delete test

### Step 2: Update Skip Reasons (20 minutes)

For remaining valid skips:

1. **OCR skips**: Add sprint/issue references
2. **Chart skips**: Verify if charts are implemented
3. **Infrastructure skips**: Remove (infrastructure complete)
4. **Defensive code skip**: Clarify or remove

### Step 3: Standardize Skip Patterns (20 minutes)

Convert runtime skips to decorators:

```python
# BEFORE (runtime skip)
def test_something():
    if not HAS_DEPENDENCY:
        pytest.skip("dependency not available")
    # test code

# AFTER (decorator skip)
@pytest.mark.skipif(not HAS_DEPENDENCY, reason="dependency not available")
def test_something():
    # test code
```

### Step 4: Update pytest.ini (5 minutes)

Add `post_mvp` marker if desired.

### Step 5: Verify Test Suite Health (15 minutes)

```bash
# Run full test suite
pytest tests/ -v

# Check skip summary
pytest tests/ -v | grep -E "passed|failed|skipped"

# Verify no new failures
pytest tests/ -x  # Stop on first failure
```

### Step 6: Document Changes (30 minutes)

Create `docs/test-plans/TEST_SKIP_POLICY.md` with:
- When to skip tests
- How to document skips
- Skip review process
- Examples of good/bad skips

---

## Expected Outcomes

### Before Cleanup
- 562 tests collected
- ~30-35 tests skipped (estimate)
- Unclear if skips are valid
- Mix of skip patterns

### After Cleanup
- 562 tests collected (or slightly fewer if tests deleted)
- ~5-10 tests skipped (OCR, charts, platform-specific)
- All skips documented with clear reasons
- Consistent skip patterns (decorators)
- Potential +20-26 tests in active suite

### Success Metrics

- ✓ All obsolete skips removed
- ✓ All temporary skips reviewed and validated
- ✓ All skips have clear, specific reasons
- ✓ Consistent skip patterns across suite
- ✓ Test suite still passes (no regressions)
- ✓ Documentation updated with skip policy

---

## Appendix: Skip Pattern Reference

### Good Skip Examples

```python
# Post-MVP feature with clear timeline
@pytest.mark.skip(reason="OCR functionality deferred to Sprint 5+ (issue #123)")
def test_ocr_extraction():
    pass

# Platform-specific with clear condition
@pytest.mark.skipif(sys.platform == "win32", reason="Unix-specific file permissions")
def test_file_permissions():
    pass

# Optional dependency with clear requirement
import sys
HAS_OPTIONAL_LIB = importlib.util.find_spec("optional_lib") is not None

@pytest.mark.skipif(not HAS_OPTIONAL_LIB, reason="Requires optional_lib package")
def test_optional_feature():
    pass
```

### Bad Skip Examples

```python
# BAD: No reason
@pytest.mark.skip
def test_something():
    pass

# BAD: Vague reason
@pytest.mark.skip(reason="broken")
def test_something():
    pass

# BAD: Runtime skip (should use decorator)
def test_something():
    pytest.skip("not implemented")
    pass

# BAD: Unclear condition
@pytest.mark.skipif(SOME_FLAG, reason="skip if flag")
def test_something():
    pass
```

---

## Next Steps

1. **Review this audit report**
2. **Prioritize cleanup tasks** (recommend starting with Priority 1)
3. **Execute cleanup in phases** (Step 1-6 above)
4. **Verify test suite health** after each phase
5. **Document skip policy** for future development
6. **Schedule regular skip reviews** (quarterly or at milestone boundaries)

---

**Audit Complete**: 2025-10-30
**Estimated Cleanup Time**: 2-3 hours
**Estimated Coverage Improvement**: +20-26 tests potentially activated
