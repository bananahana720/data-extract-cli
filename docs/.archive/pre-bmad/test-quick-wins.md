# Test Suite Quick Wins - Story 1.4

**Priority: HIGH** | **Estimated Time: 2 hours** | **Impact: +27 tests passing**

---

## Current State
- **Total Tests:** 1,119
- **Currently Passing:** 610 (81% of runnable tests)
- **Target after fixes:** 637 (85% of runnable tests)

---

## Fix #1: PDF Path Handling (30 minutes)

**Impact:** Unblocks 15 tests
**Files to modify:** `src/extractors/pdf_extractor.py` (or wherever PDF extraction happens)

### Problem
PyMuPDF cannot accept `WindowsPath` objects directly.

### Error
```python
TypeError: Cannot use WindowsPath('C:/Users/.../test.pdf') as a filename or file
```

### Solution
Convert Path objects to strings before passing to PyMuPDF:

```python
# Before (causes error)
doc = fitz.open(file_path)  # file_path is WindowsPath

# After (works)
doc = fitz.open(str(file_path))  # Convert to string
```

### Tests Fixed
All PDF-related integration tests:
- `test_full_pipeline_extraction[pdf-*]` (9 tests)
- `test_ep_004_pdf_to_metadata_aggregator_preserves_page_numbers`
- `test_ep_005_pdf_to_context_linker_handles_sequential_content`
- `test_ep_008_multiple_extractors_same_processor`
- `test_po_002_pipeline_auto_detects_pdf`
- `test_po_007_batch_handles_mixed_formats`
- `test_e2e_pdf_text_extraction`

### Implementation
1. Find PDF extractor initialization (likely in `src/extractors/pdf_extractor.py`)
2. Add `str()` conversion around file path parameter
3. Run tests: `pytest tests/integration/ -k pdf --timeout=30`
4. Verify all 15 tests now pass

---

## Fix #2: Tuple vs. Object Returns (1 hour)

**Impact:** Unblocks 9 tests
**Files to check:** All extractor implementations

### Problem
Some extractors are returning tuples instead of `ExtractionResult` or `ProcessingResult` objects.

### Error
```python
AttributeError: 'tuple' object has no attribute 'content_blocks'
```

### Solution
Ensure all extractors return proper data model instances:

```python
# Before (wrong)
def extract(self, file_path: Path) -> tuple:
    # ... extraction logic ...
    return (content_blocks, metadata)  # ❌ Tuple

# After (correct)
def extract(self, file_path: Path) -> ExtractionResult:
    # ... extraction logic ...
    return ExtractionResult(
        content_blocks=content_blocks,
        document_metadata=metadata,
        success=True
    )  # ✅ Proper object
```

### Tests Fixed
- `test_cf_003_same_content_different_processors_complementary`
- `test_ep_007_xlsx_to_all_processors_handles_tabular_data`
- `test_ep_009_extraction_errors_handled_by_processors`
- `test_ep_010_processor_chain_propagates_enrichments`
- `test_ep_012_processors_handle_empty_input`
- `test_pf_001_processed_to_json_includes_all_metadata`
- `test_pf_003_processed_to_markdown_hierarchy_as_headers`
- `test_pf_004_extensive_processing_to_markdown`
- `test_pf_005_processed_to_chunked_preserves_context`

### Implementation
1. Search for extractor return statements: `rg "return \(" src/extractors/ src/processors/`
2. For each tuple return, refactor to return proper data model
3. Check processor chain outputs too
4. Run tests: `pytest tests/integration/ -k "ep_007 or ep_009 or ep_010 or ep_012 or pf_" --timeout=30`
5. Verify all 9 tests now pass

---

## Fix #3: TxtExtractor Import (5 minutes)

**Impact:** Unblocks 3 tests
**Files to modify:** `tests/test_extractors/test_edge_cases.py`

### Problem
Test file has incorrect import path for `TxtExtractor`.

### Error
```python
ImportError: cannot import name 'TxtExtractor' from 'extractors.txt_extractor'
```

### Solution
Fix the import statement in the test file:

```python
# Before (wrong)
from extractors.txt_extractor import TxtExtractor  # ❌

# After (check actual module structure and use correct import)
from src.extractors.txt_extractor import txt_extractor  # Or whatever is correct
# OR
from extractors.txt_extractor import txt_extractor as TxtExtractor
```

### Tests Fixed
- `test_text_with_utf8_bom`
- `test_text_with_mixed_line_endings`
- `test_text_with_null_bytes`

### Implementation
1. Check actual TxtExtractor location: `rg "class.*TxtExtractor" src/`
2. Or check what's actually exported: `rg "def txt_extractor" src/extractors/txt_extractor.py`
3. Update import in test file
4. Run tests: `pytest tests/test_extractors/test_edge_cases.py::TestEncodingEdgeCases --timeout=30`
5. Verify all 3 tests now pass

---

## Validation Steps

### Step 1: Run All Three Fix Areas
```bash
# From project root
cd C:\Users\Andrew\Projects\data-extraction-tool-1

# Test PDF fixes
pytest tests/integration/ -k pdf --timeout=30 -v

# Test object return fixes
pytest tests/integration/ -k "ep_007 or ep_009 or ep_010 or ep_012 or pf_" --timeout=30 -v

# Test import fixes
pytest tests/test_extractors/test_edge_cases.py::TestEncodingEdgeCases --timeout=30 -v
```

### Step 2: Run Full Integration Suite
```bash
pytest tests/integration/ --timeout=30 -v --tb=short
```

**Expected Results:**
- Before: 105 passed, 25 failed, 2 skipped, 15 errors
- After: 129 passed, 10 failed, 2 skipped, 0 errors

### Step 3: Run Full Test Suite (Excluding Performance)
```bash
pytest -m "not performance" --timeout=30 -v --tb=short
```

**Expected Results:**
- Before: ~610 passing (81%)
- After: ~637 passing (85%)

---

## Post-Fix Documentation

After completing fixes, update:

1. **docs/test-triage-analysis.md** - Mark fixed issues as resolved
2. **Story 1.4 completion criteria** - Check off "Critical path tests passing"
3. **Git commit message:**
   ```
   fix: Resolve 27 critical test failures

   - Fix PDF WindowsPath handling in extractor (15 tests)
   - Ensure all extractors return proper data models (9 tests)
   - Fix TxtExtractor import in edge case tests (3 tests)

   Test coverage: 81% → 85% (+27 passing tests)

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>
   ```

---

## Risk Assessment

### Low Risk
- **PDF Path fix** - Isolated change, well-understood issue
- **Import fix** - Test-only change, no production code impact

### Medium Risk
- **Tuple returns** - Touches multiple extractors, requires careful validation
- **Mitigation:** Test each extractor individually after changes

### Rollback Plan
If any fix breaks other tests:
1. Revert specific commit
2. Re-run test suite to confirm baseline restored
3. Debug issue in isolation
4. Re-apply fix with additional safeguards

---

## Success Criteria

✅ All 27 target tests passing
✅ No regressions in previously passing tests
✅ Test coverage reaches 85%
✅ All fixes documented in commit messages
✅ Ready to proceed with remaining Story 1.4 work

---

## Timeline

| Task | Duration | Cumulative |
|------|----------|-----------|
| PDF Path fix | 30 min | 30 min |
| Tuple returns fix | 60 min | 1h 30min |
| Import fix | 5 min | 1h 35min |
| Validation & docs | 25 min | 2h 0min |

**Total: 2 hours** to unlock 27 tests and reach 85% coverage baseline.
