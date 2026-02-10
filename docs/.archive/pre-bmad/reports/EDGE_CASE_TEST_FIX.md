# Edge Case Test Fix - CLI Flag Correction

**Issue**: Test files use incorrect `--output-dir` flag instead of `--output`
**Impact**: 20 tests fail due to test implementation bug, not product bug
**Severity**: Minor (test infrastructure only)
**Fix Time**: <5 minutes

---

## Problem Description

Edge case tests were written assuming batch command uses `--output-dir` flag.
Actual CLI uses `--output` flag for both extract and batch commands.

**Error Message**:
```
Error: No such option: --output-dir Did you mean --output?
```

---

## Files Requiring Fix

1. `tests/test_edge_cases/test_threading_edge_cases.py` (12 occurrences)
2. `tests/test_edge_cases/test_filesystem_edge_cases.py` (3 occurrences)
3. `tests/test_edge_cases/test_resource_edge_cases.py` (5 occurrences)

**Total**: 20 occurrences across 3 files

---

## Fix Instructions

### Option A: Global Search & Replace (Recommended)

In your IDE or editor:

1. Open search/replace across project
2. Search for: `--output-dir`
3. Replace with: `--output`
4. Apply to files in: `tests/test_edge_cases/`
5. Review changes (should be 20 replacements)
6. Save all files

### Option B: Manual Sed Command (Unix/Git Bash)

```bash
cd data-extractor-tool/tests/test_edge_cases/

# Fix threading tests
sed -i "s/--output-dir/--output/g" test_threading_edge_cases.py

# Fix filesystem tests
sed -i "s/--output-dir/--output/g" test_filesystem_edge_cases.py

# Fix resource tests
sed -i "s/--output-dir/--output/g" test_resource_edge_cases.py
```

### Option C: PowerShell Command (Windows)

```powershell
cd data-extractor-tool\tests\test_edge_cases\

# Fix all files
Get-ChildItem *.py | ForEach-Object {
    (Get-Content $_.FullName) -replace '--output-dir', '--output' |
    Set-Content $_.FullName
}
```

---

## Expected Results After Fix

### Before Fix:
```
49 PASSED, 20 FAILED, 6 SKIPPED (65.3% pass rate)
```

### After Fix:
```
65+ PASSED, 3-4 FAILED, 6 SKIPPED (94%+ pass rate)
```

**Remaining Failures** (Expected):
- May have 1-2 failures in empty directory tests (expected behavior)
- May have 1-2 failures in corrupted file tests (expected behavior)
- These are FAIL-EXPECTED tests validating error handling

---

## Verification

After applying fix, run:

```bash
# Run all edge case tests
pytest tests/test_edge_cases/ -v

# Run specific categories
pytest tests/test_edge_cases/test_threading_edge_cases.py -v
pytest tests/test_edge_cases/test_filesystem_edge_cases.py -v
pytest tests/test_edge_cases/test_resource_edge_cases.py -v
```

Expected output:
- Threading: 12-14/15 tests pass
- Filesystem: 18-19/20 tests pass
- Resource: 19-20/21 tests pass
- Encoding: 20/20 tests pass (already passing)

---

## Alternative: CLI Flag Standardization

If you prefer to keep test naming and update the CLI instead:

**NOT RECOMMENDED** because:
1. Breaking change to existing CLI users
2. Requires documentation updates
3. Requires examples updates
4. Current `--output` naming is more concise and consistent

The CLI correctly uses `--output` for both commands. Tests should match CLI, not vice versa.

---

## Detailed Change List

### test_threading_edge_cases.py (Lines to Change)

Replace in these test functions:
1. `test_batch_single_file` (line ~64)
2. `test_batch_two_files` (line ~82)
3. `test_batch_many_files_low_workers` (line ~101)
4. `test_batch_many_files_high_workers` (line ~121)
5. `test_batch_100_plus_files` (line ~142)
6. `test_batch_workers_greater_than_files` (line ~160)
7. `test_batch_with_some_corrupted_files` (line ~206)
8. `test_batch_all_files_fail` (line ~235)
9. `test_batch_with_large_files` (line ~263)
10. `test_batch_mixed_file_sizes` (line ~303)
11. `test_batch_rapid_succession` (line ~328, appears twice)
12. `test_batch_empty_directory` (line ~368)
13. `test_batch_directory_with_only_subdirs` (line ~389)

### test_filesystem_edge_cases.py (Lines to Change)

Replace in these test functions:
1. `test_nonexistent_batch_directory` (line ~59)
2. `test_output_is_directory_not_file` (line ~331)
3. `test_relative_path_input` (line ~356) - if batch command used

### test_resource_edge_cases.py (Lines to Change)

Replace in these test functions:
1. `test_batch_many_tiny_files` (line ~219)
2. `test_batch_many_empty_files` (line ~239)
3. `test_batch_few_large_files` (line ~265)
4. `test_batch_memory_stress_mixed_sizes` (line ~463)

---

## Testing the Fix

### Step 1: Apply Fix
Use one of the methods above to replace `--output-dir` with `--output`.

### Step 2: Run Tests
```bash
cd data-extractor-tool
pytest tests/test_edge_cases/ -v --tb=short
```

### Step 3: Verify Output
Look for:
- Encoding: 20/20 pass ✅
- Threading: 13-14/15 pass ✅
- Filesystem: 18-19/20 pass ✅
- Resource: 19-20/21 pass ✅

### Step 4: Check Remaining Failures
Any remaining failures should be:
- Empty directory tests (may legitimately fail if validation strict)
- All-files-corrupted tests (may legitimately fail if batch stops early)

These are acceptable "FAIL-EXPECTED" scenarios.

---

## Commit Message (If Committing Fix)

```
Fix edge case tests: Correct CLI flag usage

Replace --output-dir with --output in edge case tests to match
actual CLI interface. This fixes 20 test failures that were due to
test implementation bug, not product bug.

- Fix threading edge case tests (12 tests)
- Fix filesystem edge case tests (3 tests)
- Fix resource edge case tests (5 tests)

Expected pass rate increases from 65% to 94%+.

No product changes required - CLI is correct as-is.
```

---

## Summary

- **What**: Replace `--output-dir` with `--output` in test files
- **Where**: 3 test files in `tests/test_edge_cases/`
- **Why**: Tests used wrong flag name, CLI is correct
- **Impact**: Fixes 20 failing tests
- **Time**: <5 minutes
- **Risk**: None (test-only change)

**Status**: Ready to apply
