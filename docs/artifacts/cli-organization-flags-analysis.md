# CLI Organization Flags Test Analysis

**Date:** 2025-11-30
**Task:** Analyze and update skip decorators for CLI organization flag tests
**File:** `tests/integration/test_cli/test_organization_flags.py`

## Summary

The CLI organization flag tests in `test_organization_flags.py` were originally skipped with the reason "Requires full CLI implementation from Epic 5". Investigation revealed that while Epic 5 CLI implementation is complete, the **`--organization` flag is not yet implemented** in the CLI interface.

## Findings

### Test Suite Status

**Total Tests:** 7
- **Passing:** 2 (unit-level tests)
- **Skipped:** 5 (integration tests requiring --organization flag)

### Integration Tests Requiring Implementation

All 5 tests in `TestCLIOrganizationFlags` class require the `--organization` flag to be implemented:

1. **test_cli_organization_by_document_flag** (Line 34)
   - Tests: `data-extract process ... --organization by_document`
   - Validates BY_DOCUMENT folder structure in manifest

2. **test_cli_organization_by_entity_flag** (Line 68)
   - Tests: `data-extract process ... --organization by_entity`
   - Validates BY_ENTITY organization strategy

3. **test_cli_organization_flat_default** (Line 97)
   - Tests: Default organization behavior (no flag specified)
   - Validates FLAT organization strategy is default

4. **test_cli_invalid_organization_strategy** (Line 128)
   - Tests: Error handling for invalid strategies
   - Validates proper error messages for invalid input

5. **test_cli_organization_with_csv_format** (Line 151)
   - Tests: Organization flag combined with CSV format
   - Validates multi-format organization support

### Unit Tests (Passing)

Two unit-level tests in `TestCLIOrganizationUnit` class **pass** without needing CLI implementation:

1. **test_organization_flag_accepts_valid_strategies** (Line 187)
   - Validates enum contains correct strategy values
   - Tests: `by_document`, `by_entity`, `flat`

2. **test_organization_strategy_enum_complete** (Line 197)
   - Validates enum has exactly 3 strategies defined

## Root Cause Analysis

### Why Tests Fail When Unskipped

The CLI `process` command does not support the `--organization` flag:

```bash
$ data-extract process --help
# Output shows: --format, --output, --chunk-size, --recursive, --verbose,
#               --quiet, --learn, --resume, --interactive, --non-interactive,
#               --incremental, --force, --preset
# Missing: --organization flag
```

When tests run with `--organization` flag:
- **Error:** "No such option: --organization"
- **Exit Code:** 2 (argument parsing failure)
- **Manifest:** Not created (command fails before processing)

### Current CLI Options

The Epic 5 CLI implementation includes:
- `--format` (json, csv, txt)
- `--output` (output directory)
- `--chunk-size` (maximum tokens)
- `--recursive` (process subdirectories)
- `--verbose` (logging levels)
- `--quiet` (suppress output)
- `--learn` (learning mode)
- `--resume` (session resumption)
- `--interactive` / `--non-interactive` (error prompts)
- `--incremental` (skip unchanged files)
- `--force` (reprocess all)
- `--preset` (configuration presets)

**Missing:** `--organization` flag to control output organization strategy

## Updated Skip Decorators

All 5 tests have been updated with accurate skip reasons:

```python
@pytest.mark.skip(reason="Organization flag not yet implemented in CLI (Story 5.x)")
```

This reason:
- Accurately reflects the implementation gap
- Points to which Epic/Story needs to address it
- Is more specific than "Requires full CLI implementation"
- Can be tracked for future implementation

## Implementation Plan

### Phase: Story 5.x (Future)

To unskip these tests, implement:

1. **Add `--organization` flag to CLI**
   - Location: `src/data_extract/cli/base.py` (process command)
   - Options: `by_document`, `by_entity`, `flat`
   - Default: `flat`

2. **Wire flag to output pipeline**
   - Pass organization strategy to output writers
   - Ensure manifest includes `organization_strategy` field

3. **Update manifest generation**
   - Include organization strategy in manifest JSON
   - Include folder structure in manifest for organizational strategies

4. **Add validation**
   - Reject invalid strategy values
   - Return clear error messages

### Test Verification Steps

Once implemented:

```bash
# Remove skip decorators
pytest tests/integration/test_cli/test_organization_flags.py -v

# All 7 tests should pass (5 integration + 2 unit)
# Expected: 7 passed in 0.10s
```

## Current Test Results

```
tests/integration/test_cli/test_organization_flags.py
===================================================
SKIPPED [1] ...::test_cli_organization_by_document_flag
SKIPPED [1] ...::test_cli_organization_by_entity_flag
SKIPPED [1] ...::test_cli_organization_flat_default
SKIPPED [1] ...::test_cli_invalid_organization_strategy
SKIPPED [1] ...::test_cli_organization_with_csv_format
PASSED [1] ...::test_organization_flag_accepts_valid_strategies
PASSED [1] ...::test_organization_strategy_enum_complete

Result: 2 passed, 5 skipped in 0.05s
```

## Files Modified

- `<project-root>/tests/integration/test_cli/test_organization_flags.py`
  - Updated 5 skip decorators with accurate reason
  - No test logic changed
  - All skip reasons now point to Story 5.x implementation gap

## Key Takeaway

The tests are **correctly written and comprehensive**. They are **appropriately skipped** because the `--organization` flag feature has not been implemented in the CLI yet. The enum and infrastructure for organization strategies exist in the codebase, but the CLI integration is missing.

**Next Action:** Implement `--organization` flag in CLI as part of Story 5.x, then unskip these tests.
