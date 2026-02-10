# Test Skip Cleanup Implementation Plan
**Date**: 2025-10-30
**Based On**: TEST_SKIP_AUDIT_REPORT.md
**Status**: READY FOR EXECUTION

---

## Executive Decision: Delete vs. Fix

### Analysis Summary

After auditing the test suite, I discovered:

1. **DocxExtractor**: 14 skipped placeholder tests vs. 35 passing integration tests
2. **ExcelExtractor**: Similar pattern - skipped TDD scaffolds vs. working integration tests
3. **PptxExtractor**: Similar pattern - skipped TDD scaffolds vs. working integration tests
4. **PDF Extractor**: 3 valid OCR skips (post-MVP)

### Recommendation: DELETE Obsolete TDD Scaffolds

**Rationale**:
- The skipped tests are empty TDD placeholders (all code is commented out)
- Each extractor has comprehensive integration tests that actually test functionality
- Keeping empty placeholder tests creates confusion and maintenance burden
- Test count inflation (562 collected, but 30+ are empty shells)

**Benefits**:
- Cleaner test suite (true test count visible)
- No ambiguity about what's tested
- Easier maintenance
- Accurate coverage metrics

**Risk**: Minimal - Integration tests cover all real functionality

---

## Cleanup Actions

### Action 1: Delete Obsolete TDD Placeholder Files ✓ RECOMMENDED

**Files to Delete**:
1. `tests/test_extractors/test_docx_extractor.py` (14 empty placeholder tests)
2. `tests/test_extractors/test_excel_extractor.py` (partial - only placeholder sections)
3. `tests/test_extractors/test_pptx_extractor.py` (partial - only placeholder sections)

**Replacement**: Integration test files exist and are comprehensive:
- `tests/test_extractors/test_docx_extractor_integration.py` (35 passing tests)
- `tests/test_extractors/test_excel_extractor_integration.py` (if exists)
- `tests/test_extractors/test_pptx_extractor_integration.py` (if exists)

**Before Deletion - Verify**:
```bash
# Check integration test coverage
pytest tests/test_extractors/test_docx_extractor_integration.py -v
pytest tests/test_extractors/test_excel_extractor_integration.py -v
pytest tests/test_extractors/test_pptx_extractor_integration.py -v

# Verify no unique tests in placeholder files
# (All code is commented out, so nothing unique)
```

### Action 2: Fix OCR Skip Documentation ✓ REQUIRED

**File**: `tests/test_extractors/test_pdf_extractor.py`
**Lines**: 269, 286, 310

**Current**:
```python
@pytest.mark.skip(reason="OCR dependencies (pdf2image, pytesseract) not required for MVP")
```

**Updated**:
```python
@pytest.mark.skip(reason="OCR functionality deferred to post-MVP (Sprint 5+, no issue tracking yet)")
```

### Action 3: Remove Infrastructure Skips ✓ REQUIRED

Several tests are skipped for "Infrastructure not available" but infrastructure was completed in Wave 2.

**Files to Check**:
- `tests/test_extractors/test_excel_extractor.py` (lines 386, 402)
- `tests/test_extractors/test_pptx_extractor.py` (lines 327, 350, 390, 415)

**Action**:
1. Remove skip decorator
2. Run test to verify it passes
3. If fails, fix test or clarify skip reason

### Action 4: Standardize Runtime Skips to Decorators ✓ RECOMMENDED

**Pattern to Fix**:
```python
# BEFORE (runtime skip - hard to track)
def test_something(self):
    if not HAS_DEPENDENCY:
        pytest.skip("dependency not installed")
    # test code

# AFTER (decorator - easy to track)
HAS_DEPENDENCY = importlib.util.find_spec("dependency") is not None

@pytest.mark.skipif(not HAS_DEPENDENCY, reason="Requires dependency package")
def test_something(self):
    # test code
```

**Files with Runtime Skips**:
- `tests/test_extractors/test_pptx_extractor.py` (lines 252, 282, 299)
- `tests/test_extractors/test_pdf_extractor.py` (line 738)
- `tests/integration/conftest.py` (lines 45, 120, 196, 269) - ✓ Valid in fixtures
- `tests/test_extractors/conftest.py` (line 28) - ✓ Valid in fixtures

**Note**: Runtime skips in fixtures are acceptable and correct pattern.

### Action 5: Clarify or Remove Defensive Code Skip ⚠️ REQUIRES DECISION

**File**: `tests/test_extractors/test_docx_extractor_integration.py`
**Line**: 562
**Test**: `test_internal_exception_handling`
**Skip Reason**: "Exception handler is defensive code - difficult to test without breaking isolation"

**Options**:
1. **Remove skip and add focused test** using mocking to inject exception
2. **Update skip reason** to be clearer: "Low priority - requires breaking encapsulation to test defensive exception handling"
3. **Delete test** if truly untestable and low value

**Recommendation**: Option 2 (update reason) - defensive code testing is low priority

### Action 6: Add `post_mvp` Marker to pytest.ini ✓ OPTIONAL

**File**: `pytest.ini`

**Add to markers section**:
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
    post_mvp: Features deferred to post-MVP sprints
```

**Usage**:
```python
@pytest.mark.skip(reason="OCR deferred to post-MVP (Sprint 5+)")
@pytest.mark.post_mvp
def test_ocr_extraction():
    pass
```

**Benefits**:
- Run all post-MVP tests: `pytest -m post_mvp`
- Skip post-MVP tests: `pytest -m "not post_mvp"`

---

## Step-by-Step Execution Plan

### Phase 1: Verification (15 minutes)

**Verify extractors exist and work**:
```bash
cd "data-extractor-tool"

# Test each extractor works
python -c "import sys; sys.path.insert(0, 'src'); from extractors.docx_extractor import DocxExtractor; print('OK')"
python -c "import sys; sys.path.insert(0, 'src'); from extractors.excel_extractor import ExcelExtractor; print('OK')"
python -c "import sys; sys.path.insert(0, 'src'); from extractors.pptx_extractor import PptxExtractor; print('OK')"
python -c "import sys; sys.path.insert(0, 'src'); from extractors.pdf_extractor import PdfExtractor; print('OK')"
```

**Verify integration tests exist and pass**:
```bash
pytest tests/test_extractors/test_docx_extractor_integration.py -v
pytest tests/test_extractors/ -k "integration" -v
```

**Check for unique tests in placeholder files**:
```bash
# All placeholder tests have commented-out code, so nothing unique
grep -A 20 "def test_" tests/test_extractors/test_docx_extractor.py | grep -v "^\s*#"
```

### Phase 2: Delete Obsolete TDD Scaffolds (10 minutes)

**Backup first** (optional):
```bash
mkdir -p tests/obsolete_scaffolds_backup
cp tests/test_extractors/test_docx_extractor.py tests/obsolete_scaffolds_backup/
```

**Delete obsolete placeholder file**:
```bash
git rm tests/test_extractors/test_docx_extractor.py
```

**Verify test count reduction**:
```bash
pytest tests/ --co -q  # Should show ~548 tests (562 - 14)
```

**Check for similar patterns in other files**:
```bash
# Review test_excel_extractor.py for placeholder sections
# Review test_pptx_extractor.py for placeholder sections
```

### Phase 3: Fix OCR Skip Reasons (5 minutes)

**File**: `tests/test_extractors/test_pdf_extractor.py`

**Edit lines 269, 286, 310**:
```bash
# Use Edit tool to update skip reasons
# From: "OCR dependencies (pdf2image, pytesseract) not required for MVP"
# To: "OCR functionality deferred to post-MVP (Sprint 5+, no issue tracking yet)"
```

### Phase 4: Remove Infrastructure Skips (30 minutes)

**For each infrastructure skip**:

1. **Identify skip**:
   ```bash
   grep -n "Infrastructure not available" tests/test_extractors/*.py
   ```

2. **For each match**:
   - Remove `@pytest.mark.skip(reason="Infrastructure not available")`
   - Or remove `pytest.skip("Infrastructure not available")` line
   - Run test: `pytest tests/test_extractors/test_<file>.py::test_<name> -v`
   - If passes: ✓ Skip removed successfully
   - If fails: Investigate and either fix test or re-skip with clearer reason

**Expected Files**:
- `tests/test_extractors/test_excel_extractor.py`
- `tests/test_extractors/test_pptx_extractor.py`

### Phase 5: Standardize Skip Patterns (20 minutes)

**For each runtime skip in test methods** (not fixtures):

**File**: `tests/test_extractors/test_pptx_extractor.py`

**Example - Line 252**:
```python
# BEFORE
def test_pptx_integration_sanity(self):
    """Test basic PPTX integration with real file."""
    try:
        import pptx
    except ImportError:
        pytest.skip("python-pptx not installed")
    # test code

# AFTER
import importlib
HAS_PPTX = importlib.util.find_spec("pptx") is not None

@pytest.mark.skipif(not HAS_PPTX, reason="Requires python-pptx package")
def test_pptx_integration_sanity(self):
    """Test basic PPTX integration with real file."""
    # test code (no skip call)
```

**Repeat for**:
- `test_pptx_extractor.py` lines 252, 282, 299
- `test_pdf_extractor.py` line 738

### Phase 6: Update Defensive Code Skip (5 minutes)

**File**: `tests/test_extractors/test_docx_extractor_integration.py`
**Line**: 562

**Update skip reason**:
```python
# BEFORE
pytest.skip("Exception handler is defensive code - difficult to test without breaking isolation")

# AFTER
pytest.skip("Low priority - testing defensive exception handling requires breaking encapsulation")
```

### Phase 7: Add post_mvp Marker (5 minutes)

**File**: `pytest.ini`

**Add marker** (see Action 6 above for full text)

**Apply to OCR tests**:
```python
@pytest.mark.skip(reason="OCR deferred to post-MVP (Sprint 5+)")
@pytest.mark.post_mvp
def test_detect_image_based_pdf(self, image_pdf):
    # test code
```

### Phase 8: Verification (15 minutes)

**Run full test suite**:
```bash
pytest tests/ -v
```

**Check skip summary**:
```bash
pytest tests/ -v | grep -E "passed|failed|skipped"
```

**Expected Results**:
- Tests collected: ~535-540 (down from 562 after deleting placeholders)
- Tests skipped: ~5-10 (OCR + platform-specific + defensive)
- Tests passed: ~525-535
- Tests failed: 0

**Verify no regressions**:
```bash
pytest tests/ -x  # Stop on first failure (should complete successfully)
```

**Check skip reasons are clear**:
```bash
pytest tests/ -v | grep "SKIPPED"
```

---

## Expected Outcomes

### Before Cleanup
```
562 tests collected
~35-40 tests skipped
- 14 DocxExtractor placeholders (obsolete)
- 6+ ExcelExtractor placeholders (obsolete)
- 6+ PptxExtractor placeholders (obsolete)
- 3 OCR tests (valid)
- 2 platform-specific (valid)
- 4+ infrastructure skips (invalid - infra exists)
```

### After Cleanup
```
~535-540 tests collected (reduced by deleting placeholders)
~5-10 tests skipped
- 3 OCR tests (valid, post-MVP)
- 2 platform-specific (valid)
- 1 defensive code (low priority, clarified)
- 0 infrastructure skips (removed)
- 0 placeholder tests (deleted)
```

### Benefits
- **Accurate test count**: No placeholder inflation
- **Clear skip reasons**: All remaining skips documented
- **Consistent patterns**: All skips use decorators (except fixtures)
- **Maintainability**: No confusion about what's tested vs. what's placeholder
- **Coverage accuracy**: Metrics reflect actual tested code

---

## Risk Assessment

### Low Risk Actions ✓
- Deleting placeholder files (comprehensive integration tests exist)
- Updating skip reasons (no functional change)
- Adding pytest marker (no functional change)

### Medium Risk Actions ⚠️
- Removing infrastructure skips (tests might fail if not properly implemented)
- Converting runtime skips to decorators (could miss edge cases)

### Mitigation Strategy
- Run tests after each phase
- Use `-x` flag to stop on first failure
- Keep git history for rollback if needed
- Verify integration tests cover deleted placeholder functionality

---

## Rollback Plan

If issues arise:

```bash
# Revert specific file
git checkout HEAD -- tests/test_extractors/test_docx_extractor.py

# Revert all changes
git reset --hard HEAD

# Restore from backup
cp tests/obsolete_scaffolds_backup/test_docx_extractor.py tests/test_extractors/
```

---

## Time Estimate

| Phase | Time | Complexity |
|-------|------|------------|
| 1. Verification | 15 min | Low |
| 2. Delete Scaffolds | 10 min | Low |
| 3. Fix OCR Skips | 5 min | Low |
| 4. Remove Infra Skips | 30 min | Medium |
| 5. Standardize Patterns | 20 min | Medium |
| 6. Update Defensive Skip | 5 min | Low |
| 7. Add Marker | 5 min | Low |
| 8. Final Verification | 15 min | Low |
| **TOTAL** | **105 min** | **1.75 hours** |

---

## Post-Cleanup Documentation

After cleanup, create `docs/test-plans/TEST_SKIP_POLICY.md`:

### Content Outline

1. **When to Skip Tests**
   - Post-MVP features
   - Optional dependencies
   - Platform-specific functionality
   - External service dependencies

2. **How to Skip Tests**
   - Use `@pytest.mark.skip(reason="Clear, specific reason")`
   - Use `@pytest.mark.skipif(condition, reason="Why condition matters")`
   - Include issue/sprint references
   - Use `@pytest.mark.post_mvp` for future work

3. **Skip Patterns to Avoid**
   - Runtime `pytest.skip()` in test methods (use decorators)
   - Vague reasons ("broken", "TODO")
   - Skips without reasons
   - Temporary skips without tracking

4. **Skip Review Process**
   - Review quarterly or at milestones
   - Remove skips when conditions change
   - Update reasons if context changes
   - Delete obsolete tests

5. **Examples**
   - Good skip patterns
   - Bad skip patterns
   - Conditional skip patterns

---

## Success Criteria

✓ All obsolete placeholder tests deleted
✓ All infrastructure skips removed (infrastructure exists)
✓ All OCR skips have clear post-MVP documentation
✓ All runtime skips converted to decorators (except fixtures)
✓ Defensive code skip clarified
✓ `post_mvp` marker added to pytest.ini
✓ Full test suite passes (no regressions)
✓ Test count accurately reflects real tests
✓ Skip policy documented for future reference

---

## Next Steps

1. **Review this plan** with stakeholder
2. **Execute phases 1-8** sequentially
3. **Verify outcomes** match expectations
4. **Create skip policy** documentation
5. **Update PROJECT_STATE.md** with cleanup summary
6. **Commit changes** with clear commit message

---

**Ready for Execution**: YES
**Estimated Time**: 1.75 hours
**Risk Level**: LOW
**Prerequisite**: Review and approval of this plan
