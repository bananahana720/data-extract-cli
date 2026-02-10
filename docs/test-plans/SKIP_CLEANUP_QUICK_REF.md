# Test Skip Cleanup - Quick Reference Card
**Mission**: P3-T2 - Clean Up Test Skip Markers
**Date**: 2025-10-30
**Estimated Time**: 1.75 hours

---

## Pre-Flight Checklist

```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"

# Verify current state
pytest tests/ --co -q | tail -1  # Should show "562 tests collected"
pytest tests/ -v --tb=no | grep -i "skip" | wc -l  # Count skips

# Create backup branch (optional)
git checkout -b cleanup/test-skip-markers
```

---

## 8-Phase Execution Plan

### Phase 1: Verification (15 min)

```bash
# Verify extractors exist
python -c "import sys; sys.path.insert(0, 'src'); from extractors.docx_extractor import DocxExtractor; print('✓ DocxExtractor')"
python -c "import sys; sys.path.insert(0, 'src'); from extractors.excel_extractor import ExcelExtractor; print('✓ ExcelExtractor')"
python -c "import sys; sys.path.insert(0, 'src'); from extractors.pptx_extractor import PptxExtractor; print('✓ PptxExtractor')"

# Verify integration tests pass
pytest tests/test_extractors/test_docx_extractor_integration.py -v --tb=line
pytest tests/test_extractors/ -k "integration" -q
```

**Expected**: All extractors import successfully, integration tests pass

---

### Phase 2: Delete Obsolete Scaffolds (10 min)

```bash
# Review placeholder file (all code commented out)
cat tests/test_extractors/test_docx_extractor.py | grep -v "^\s*#" | grep "def test"

# Backup (optional)
mkdir -p tests/obsolete_scaffolds_backup
cp tests/test_extractors/test_docx_extractor.py tests/obsolete_scaffolds_backup/

# Delete placeholder file
git rm tests/test_extractors/test_docx_extractor.py

# Verify test count reduction
pytest tests/ --co -q | tail -1  # Should show ~548 tests (562 - 14)

# Run tests to ensure no breakage
pytest tests/ -x -q
```

**Expected**: 14 fewer tests collected, all tests still pass

---

### Phase 3: Fix OCR Skip Reasons (5 min)

**File**: `tests/test_extractors/test_pdf_extractor.py`

**Lines to Edit**: 269, 286, 310

**Change**:
```python
# FROM:
@pytest.mark.skip(reason="OCR dependencies (pdf2image, pytesseract) not required for MVP")

# TO:
@pytest.mark.skip(reason="OCR functionality deferred to post-MVP (Sprint 5+, no issue tracking yet)")
```

**Command**:
```bash
# Use Edit tool or manually edit file
```

---

### Phase 4: Remove Infrastructure Skips (30 min)

```bash
# Find infrastructure skips
grep -n "Infrastructure not available" tests/test_extractors/*.py

# For each match:
# 1. Remove skip line
# 2. Run test
# 3. If passes: ✓ Done
# 4. If fails: Investigate and either fix or re-skip with clearer reason

# Example workflow for each skip:
# Remove skip from file
# Run test:
pytest tests/test_extractors/test_excel_extractor.py::test_excel_integration_with_logging -v

# If passes: Continue to next skip
# If fails: Re-add skip with updated reason
```

**Files to Check**:
- `tests/test_extractors/test_excel_extractor.py` (lines 386, 402)
- `tests/test_extractors/test_pptx_extractor.py` (lines 327, 350, 390, 415)

---

### Phase 5: Standardize Skip Patterns (20 min)

**Pattern**: Convert runtime skips to decorators

**Files**:
- `tests/test_extractors/test_pptx_extractor.py` (lines 252, 282, 299)
- `tests/test_extractors/test_pdf_extractor.py` (line 738)

**Example**:
```python
# BEFORE (runtime skip)
def test_pptx_integration_sanity(self):
    try:
        import pptx
    except ImportError:
        pytest.skip("python-pptx not installed")
    # test code

# AFTER (decorator skip)
import importlib
HAS_PPTX = importlib.util.find_spec("pptx") is not None

@pytest.mark.skipif(not HAS_PPTX, reason="Requires python-pptx package")
def test_pptx_integration_sanity(self):
    # test code
```

---

### Phase 6: Update Defensive Code Skip (5 min)

**File**: `tests/test_extractors/test_docx_extractor_integration.py`
**Line**: 562

**Change**:
```python
# FROM:
pytest.skip("Exception handler is defensive code - difficult to test without breaking isolation")

# TO:
pytest.skip("Low priority - testing defensive exception handling requires breaking encapsulation")
```

---

### Phase 7: Add post_mvp Marker (5 min)

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

**Apply to OCR tests**:
```python
@pytest.mark.skip(reason="OCR functionality deferred to post-MVP (Sprint 5+)")
@pytest.mark.post_mvp
def test_detect_image_based_pdf(self, image_pdf):
    pass
```

---

### Phase 8: Final Verification (15 min)

```bash
# Run full test suite
pytest tests/ -v

# Check skip summary
pytest tests/ -v | grep -E "passed|failed|skipped"

# Expected output:
# ======================== XXX passed, 5-10 skipped in X.XXs ========================

# Verify no failures
pytest tests/ -x

# Check skip reasons are clear
pytest tests/ -v --tb=no 2>&1 | grep "SKIPPED"

# Verify test count
pytest tests/ --co -q | tail -1
# Expected: ~535-540 tests collected
```

**Success Criteria**:
- Tests collected: ~535-540 (down from 562)
- Tests skipped: 5-10 (down from ~35-40)
- Tests passed: ~525-535
- Tests failed: 0
- All skip reasons clear and specific

---

## Expected Results

### Before Cleanup
```
======================== 562 tests collected ========================
======================== 522 passed, 35-40 skipped ========================
```

### After Cleanup
```
======================== ~535-540 tests collected ========================
======================== ~525-535 passed, 5-10 skipped ========================
```

### Skip Breakdown After Cleanup
- 3 OCR tests (post-MVP)
- 2 platform-specific tests (Windows)
- 1 defensive code test (low priority)
- 0 infrastructure skips
- 0 placeholder tests

---

## Rollback Commands

If issues arise:

```bash
# Revert all changes
git checkout .

# Revert specific file
git checkout HEAD -- tests/test_extractors/test_docx_extractor.py

# Restore from backup
cp tests/obsolete_scaffolds_backup/test_docx_extractor.py tests/test_extractors/

# Reset to start of session
git reset --hard HEAD
```

---

## Post-Cleanup Checklist

- [ ] All phases completed successfully
- [ ] Full test suite passes
- [ ] Test count reduced by ~20-26
- [ ] Skip count reduced to 5-10
- [ ] All skip reasons clear and specific
- [ ] No regressions in test functionality
- [ ] pytest.ini updated with post_mvp marker
- [ ] Skip policy documented in docs/test-plans/

---

## Documentation Updates

After cleanup:

1. **Update PROJECT_STATE.md**:
   - Note skip marker cleanup completion
   - Update test count statistics

2. **Commit Changes**:
   ```bash
   git add .
   git commit -m "Clean up test skip markers

   - Delete 14 obsolete DocxExtractor placeholder tests
   - Update OCR skip reasons with post-MVP timeline
   - Remove obsolete infrastructure skips
   - Standardize skip patterns (decorators over runtime)
   - Add post_mvp marker to pytest.ini
   - Clarify defensive code skip reason

   Result: 562 → ~540 tests, 35 → ~8 skips
   All skip reasons documented and justified
   See TEST_SKIP_VALIDATION_SUMMARY.md for details"
   ```

3. **Move Reports**:
   ```bash
   mkdir -p docs/reports/skip-cleanup
   mv TEST_SKIP_AUDIT_REPORT.md docs/reports/skip-cleanup/
   mv TEST_SKIP_CLEANUP_PLAN.md docs/reports/skip-cleanup/
   mv TEST_SKIP_VALIDATION_SUMMARY.md docs/reports/skip-cleanup/
   mv SKIP_CLEANUP_QUICK_REF.md docs/reports/skip-cleanup/
   ```

---

## Success Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Tests Collected | 562 | ~540 | -22 |
| Tests Skipped | ~35-40 | ~5-10 | -30 |
| Tests Passing | ~522-527 | ~525-535 | +3-8 |
| Placeholder Tests | 30+ | 0 | -30 |
| Clear Skip Reasons | ~20% | 100% | +80% |

---

## Time Tracking

| Phase | Estimated | Actual | Notes |
|-------|-----------|--------|-------|
| 1. Verification | 15 min | | |
| 2. Delete Scaffolds | 10 min | | |
| 3. Fix OCR Skips | 5 min | | |
| 4. Remove Infra Skips | 30 min | | |
| 5. Standardize Patterns | 20 min | | |
| 6. Update Defensive Skip | 5 min | | |
| 7. Add Marker | 5 min | | |
| 8. Final Verification | 15 min | | |
| **TOTAL** | **105 min** | | **1.75 hours** |

---

## Quick Commands Reference

```bash
# Count current skips
pytest tests/ -v --tb=no 2>&1 | grep "SKIPPED" | wc -l

# List skip reasons
pytest tests/ -v --tb=no 2>&1 | grep "SKIPPED"

# Run only skipped tests (shows skip decorators)
pytest tests/ --co -q | grep -i skip

# Check test count
pytest tests/ --co -q | tail -1

# Run tests with stop on first failure
pytest tests/ -x

# Run tests quietly
pytest tests/ -q

# Run tests verbosely
pytest tests/ -v

# Run specific test file
pytest tests/test_extractors/test_pdf_extractor.py -v

# Run tests by marker
pytest -m post_mvp -v

# Skip tests by marker
pytest -m "not post_mvp" -v
```

---

**Status**: ✓ READY FOR EXECUTION
**Risk Level**: LOW
**Time Required**: 1.75 hours
**Expected Outcome**: Cleaner test suite, accurate metrics, clear documentation
