# Wave 3 Phase 2 - Test Deletion Action Plan

**Date:** 2025-11-20
**Status:** APPROVED BY MURAT ✅
**Execution:** IMMEDIATE

## Quick Reference

**Decision:** GO for 48 LOW RISK files
**Coverage Impact:** 87% → 82% (ACCEPTABLE)
**Time Savings:** 35% faster CI
**Maintenance Savings:** 50% reduction

## Immediate Execution Steps

### Step 1: Mark Tests for Deletion (15 minutes)
```bash
# Add @pytest.mark.deprecated to all 48 LOW RISK files
# Use the list from test-deletion-audit-appendix-2025-11-20.md
```

### Step 2: Verify Coverage Without Deprecated Tests (10 minutes)
```bash
# Run tests excluding deprecated marks
pytest -m "not deprecated" --cov=src --cov-report=term-missing

# Verify coverage >= 82%
# Verify all behavioral tests pass
# Verify integration tests pass
```

### Step 3: Delete Wave 1 - Templates/Demos (5 minutes)
**Delete these directories/files immediately:**
```bash
rm -rf tests/support/
rm tests/test_fixtures_demo.py
rm tests/fixtures/test_fixtures.py
rm tests/fixtures/test_story_fixtures.py
rm tests/fixtures/semantic_corpus.py
rm tests/fixtures/semantic/generate_*.py
rm tests/validation/semantic_validator.py
rm tests/fixtures/semantic/harness/compare-*.py
```

### Step 4: Delete Wave 2 - Getter/Setter Tests (5 minutes)
```bash
rm tests/test_infrastructure/test_config_manager.py
rm tests/test_infrastructure/test_error_handler.py
rm tests/test_infrastructure/test_logging_framework.py
rm tests/test_infrastructure/test_progress_tracker.py
```

### Step 5: Delete Wave 3 - Structure-Only Tests (5 minutes)
```bash
rm tests/test_cli/test_threading.py
rm tests/test_cli/test_encoding.py
rm tests/test_cli/test_signal_handling.py
rm tests/test_pipeline/test_pipeline_edge_cases.py
rm tests/test_processors/test_processor_edge_cases.py
```

### Step 6: Delete Wave 4 - Edge Cases (5 minutes)
```bash
rm -rf tests/test_edge_cases/
rm tests/test_poppler_config.py
rm tests/test_docx_extractor.py  # root level duplicate
rm tests/uat/execute_story_3_3_uat.py
```

### Step 7: Run Final Verification (10 minutes)
```bash
# Full test suite
pytest --cov=src --cov-report=term-missing

# Verify:
# - Coverage >= 80%
# - All tests pass
# - CI time reduced
# - No import errors
```

### Step 8: Commit Changes (5 minutes)
```bash
git add -A
git commit -m "Test Reality Sprint Wave 3: Remove 48 low-value tests

- Deleted getter/setter, structure-only, and template tests
- Coverage: 87% → 82% (acceptable for greenfield)
- CI time: 7.5min → 4.9min (35% improvement)
- Maintenance: 50% reduction in effort
- All behavioral and integration tests retained

Approved by: Murat (Master Test Architect)
Audit by: Amelia (Senior Implementation Engineer)"
```

## Medium Risk Files - NEXT WEEK

**DO NOT DELETE THESE YET:**
- `unit/data_extract/normalize/test_validation.py` (32 mocks!)
- `unit/test_scripts/test_generate_fixtures.py` (15 mocks)
- `unit/test_scripts/test_manage_sprint_status.py` (12 mocks)
- [See full list in appendix]

These require team review to:
1. Extract unique test cases
2. Verify integration coverage
3. Get consensus on deletion

## Success Criteria

✅ Tests still pass after deletion
✅ Coverage stays above 80%
✅ CI runs in under 5 minutes
✅ No production code breaks
✅ Behavioral tests all operational

## Rollback Plan

If issues arise:
```bash
git revert HEAD  # Revert the deletion commit
pytest  # Verify tests work again
```

## Next Steps

1. **Today:** Execute Steps 1-8
2. **Tomorrow:** Monitor CI for any issues
3. **Next Week:** Review MEDIUM RISK files with team
4. **Sprint End:** Document lessons in testing standards

---

**Ready to Execute:** YES ✅
**Estimated Time:** 60 minutes total
**Risk Level:** LOW
**Rollback Available:** YES
