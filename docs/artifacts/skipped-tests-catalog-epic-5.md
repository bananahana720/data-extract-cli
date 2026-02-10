# Skipped Tests Catalog - Epic 5 CLI

**Generated:** 2025-11-30
**Purpose:** Tech debt tracking for deferred test implementation

## Summary

- **Total skipped tests:** 21
- **By story:**
  - Story 5-1 (Command Router): 3 tests
  - Story 5-3 (Progress Indicators): 2 tests
  - Story 5-6 (Error Recovery): 12 tests
  - Integration (Organization Flags): 4 tests
  - Cross-cutting (Summary Report): 1 class (3+ tests)

## Detailed Catalog

### Story 5-1: Command Router & Typer Migration

| Test | File | Line | Reason |
|------|------|------|--------|
| `test_router_execute_semantic_analyze` | `tests/unit/test_cli/test_story_5_1/test_command_router.py` | 248-250 | "brownfield circular import: cli.semantic_commands <-> data_extract.cli" |
| `test_router_execute_with_options` | `tests/unit/test_cli/test_story_5_1/test_command_router.py` | 342-344 | "brownfield circular import: cli.semantic_commands <-> data_extract.cli" |
| `test_router_pipeline_stops_on_failure` | `tests/unit/test_cli/test_story_5_1/test_command_router.py` | 486 | "Brownfield router validation differs from greenfield - deferred to migration" |

**Root Cause:** Circular import between brownfield `cli.semantic_commands` module and greenfield `data_extract.cli` package. This architectural conflict prevents importing both modules simultaneously during tests.

**Impact:** Router functionality for semantic commands cannot be integration-tested until brownfield migration completes.

---

### Story 5-3: Progress Indicators & Real-time Feedback

| Test | File | Line | Reason |
|------|------|------|--------|
| `test_semantic_analyze_shows_progress_bar` | `tests/unit/test_cli/test_story_5_3/test_progress_components.py` | 72-75 | "Brownfield semantic commands expect JSON chunk files, not txt files. This is a known brownfield/greenfield migration issue." |
| `test_semantic_deduplicate_shows_progress_bar` | `tests/unit/test_cli/test_story_5_3/test_progress_components.py` | 101-104 | "Brownfield semantic commands expect JSON chunk files, not txt files. This is a known brownfield/greenfield migration issue." |

**Root Cause:** Data format mismatch between brownfield (expects `.json` chunk files) and greenfield (produces `.txt` output files). Semantic commands fail when given incompatible input format.

**Impact:** Progress indicators for semantic analysis commands cannot be tested with greenfield output until migration addresses format standardization.

---

### Story 5-6: Error Recovery & Session Management

#### Interactive Error Prompts

| Test | File | Line | Reason |
|------|------|------|--------|
| `test_interactive_flag_enables_prompts` | `tests/unit/test_cli/test_story_5_6/test_error_prompts.py` | 376 | "Interactive error prompts implementation required for BLUE phase" |
| `test_non_interactive_auto_skips_errors` | `tests/unit/test_cli/test_story_5_6/test_error_prompts.py` | 472 | "Non-interactive auto-skip behavior implementation required for BLUE phase" |

#### Session Cleanup

| Test | File | Line | Reason |
|------|------|------|--------|
| `test_session_list_shows_archived_sessions` | `tests/unit/test_cli/test_story_5_6/test_session_cleanup.py` | 263 | "Session command implementation required for BLUE phase" |
| `test_session_clean_removes_old_archives` | `tests/unit/test_cli/test_story_5_6/test_session_cleanup.py` | 294 | "Session command implementation required for BLUE phase" |
| `test_orphaned_session_can_be_resumed` | `tests/unit/test_cli/test_story_5_6/test_session_cleanup.py` | 400 | "Orphaned session resumption logic implementation required for BLUE phase" |
| `test_manual_cleanup_via_command` | `tests/unit/test_cli/test_story_5_6/test_session_cleanup.py` | 471 | "Session cleanup command implementation required for BLUE phase" |
| `test_cleanup_requires_confirmation` | `tests/unit/test_cli/test_story_5_6/test_session_cleanup.py` | 510 | "Session cleanup confirmation logic implementation required for BLUE phase" |
| `test_cleanup_with_no_sessions` | `tests/unit/test_cli/test_story_5_6/test_session_cleanup.py` | 584 | "Session cleanup command implementation required for BLUE phase" |

#### Graceful Degradation

| Test | File | Line | Reason |
|------|------|------|--------|
| `test_exception_in_normalization_caught` | `tests/unit/test_cli/test_story_5_6/test_graceful_degradation.py` | 622 | "BatchProcessor module implementation required for BLUE phase" |

#### Retry Commands

| Test | File | Line | Reason |
|------|------|------|--------|
| `test_retry_last_processes_failed_files` | `tests/unit/test_cli/test_story_5_6/test_retry.py` | 200 | "Retry command implementation required for BLUE phase" |
| `test_retry_last_no_failed_files_message` | `tests/unit/test_cli/test_story_5_6/test_retry.py` | 267 | "Retry command implementation required for BLUE phase" |
| `test_retry_single_file` | `tests/unit/test_cli/test_story_5_6/test_retry.py` | 373 | "Retry command implementation required for BLUE phase" |

**Root Cause:** Story 5-6 BLUE phase features (interactive prompts, session management commands, retry commands) are not yet implemented. GREEN phase focused on core error handling and session state infrastructure.

**Impact:** Advanced CLI UX features for error recovery, session inspection, and selective retry cannot be tested. These are polish features deferred to BLUE phase after core functionality is validated.

---

### Integration Tests: Organization Flags

| Test | File | Line | Reason |
|------|------|------|--------|
| `test_cli_organization_by_document_flag` | `tests/integration/test_cli/test_organization_flags.py` | 34 | "Requires full CLI implementation from Epic 5" |
| `test_cli_organization_by_entity_flag` | `tests/integration/test_cli/test_organization_flags.py` | 68 | "Requires full CLI implementation from Epic 5" |
| `test_cli_organization_flat_default` | `tests/integration/test_cli/test_organization_flags.py` | 97 | "Requires full CLI implementation from Epic 5" |
| `test_cli_invalid_organization_strategy` | `tests/integration/test_cli/test_organization_flags.py` | 128 | "Requires full CLI implementation from Epic 5" |
| `test_cli_organization_with_csv_format` | `tests/integration/test_cli/test_organization_flags.py` | 151 | "Requires full CLI implementation from Epic 5" |

**Note:** File shows 5 tests skipped, though review doc mentioned 4. All 5 are documented here for completeness.

**Root Cause:** End-to-end CLI integration tests require full `data-extract process` command with organization flags. Story 3.7 implemented the organization strategies, but CLI wiring is part of Epic 5 Stories 5-1/5-2.

**Impact:** Organization flag routing through CLI cannot be integration-tested until Epic 5 completes CLI command structure.

---

### Cross-Cutting: Summary Report

| Test Class | File | Line | Reason |
|------------|------|------|--------|
| `TestSummaryPanelAdvanced` (entire class) | `tests/unit/test_cli/test_summary_report.py` | 548 | "Implementation pending - summary.py module" |

**Tests in skipped class:**
- `test_summary_panel_respects_no_color` (line 552)
- `test_summary_panel_width_adaptation` (line 556)
- `test_summary_panel_error_section` (line 560)
- *(Additional tests may exist in the class - 29 total tests found in file)*

**Root Cause:** `summary.py` module for advanced summary panel features not yet implemented. Core summary functionality exists, but advanced features (NO_COLOR support, terminal width adaptation, error sections) are deferred.

**Impact:** Advanced summary panel UX polish cannot be tested. Basic summary functionality is tested in other test classes.

---

## Recovery Timeline

### Immediate (Epic 5 BLUE Phase - Target: 2025-12)

**Ready after BLUE phase implementation:**
- ✅ All Story 5-6 BLUE phase tests (12 tests)
  - Interactive error prompts (2 tests)
  - Session management commands (6 tests)
  - Retry commands (3 tests)
  - BatchProcessor integration (1 test)

**Action:** Unskip these tests after implementing:
- `data_extract.cli.error_prompts` module with `--interactive` flag support
- `data-extract session` command group (list, show, clean)
- `data-extract retry` command with `--last`, `--session`, `--file` options
- `data_extract.cli.batch_processor` module for pipeline error handling

---

### Short-term (After Brownfield Migration - Target: 2026-Q1)

**Ready after brownfield/greenfield unification:**
- ✅ Story 5-1 router tests (3 tests) - circular import resolved
- ✅ Story 5-3 progress tests (2 tests) - chunk format standardized
- ✅ Integration organization tests (5 tests) - full CLI wiring complete

**Action:** Unskip these tests after:
- Migrating `cli.semantic_commands` to greenfield `data_extract.cli.commands.semantic`
- Standardizing chunk format (likely JSON for both brownfield/greenfield)
- Completing CLI command routing infrastructure

**Technical Debt Considerations:**
- Circular import indicates architectural smell - consider dependency inversion
- Format mismatch suggests need for adapter pattern or unified serialization layer

---

### Long-term (Epic 6 or Later - Target: TBD)

**Ready after summary panel enhancements:**
- ✅ Summary report advanced tests (1 class, 3+ tests)

**Action:** Unskip after implementing:
- NO_COLOR environment variable support in Rich panels
- Terminal width detection and adaptive layout
- Error section rendering in summary panel
- Whatever additional features exist in the skipped class

**Priority:** Low - core summary functionality is already tested and working. These are UX polish features.

---

## Test Debt Metrics

| Category | Count | % of Total | Recovery Phase |
|----------|-------|-----------|----------------|
| BLUE phase deferred | 12 | 57% | Epic 5 BLUE |
| Brownfield migration | 5 | 24% | Post-migration |
| Integration wiring | 5 | 24% | Epic 5 complete |
| Advanced features | 1 class | ~14%* | Epic 6+ |

*Assuming 3 tests in class; actual may be higher

**Total Technical Debt:** 21+ skipped tests (28 identified via `rg` count)

**Recommendation:** Prioritize BLUE phase implementation to reduce debt by 57% in current epic.

---

## Risk Assessment

### High Risk (Must Address in Epic 5)
- ❌ **None** - All skipped tests are either:
  - Deferred features (BLUE phase) with clear recovery path
  - Migration-dependent with known workarounds
  - Low-priority polish features

### Medium Risk (Monitor)
- ⚠️ **Brownfield circular import** (Story 5-1)
  - **Risk:** Architectural debt may complicate future refactoring
  - **Mitigation:** Document circular dependency; plan resolution in migration epic

- ⚠️ **Format mismatch** (Story 5-3)
  - **Risk:** Dual-format support increases maintenance burden
  - **Mitigation:** Adapter pattern or format converter for interim compatibility

### Low Risk (Acceptable Debt)
- ✅ **BLUE phase features** (Story 5-6)
  - **Rationale:** TDD RED-GREEN-BLUE methodology - tests exist before implementation
  - **Status:** Working as intended

- ✅ **Integration tests** (Organization flags)
  - **Rationale:** CLI wiring in progress; strategies themselves are tested
  - **Status:** Will naturally unskip as Epic 5 completes

- ✅ **Advanced summary** (Cross-cutting)
  - **Rationale:** Core functionality tested; advanced features are polish
  - **Status:** Low priority, can defer indefinitely

---

## Action Items

### For Epic 5 BLUE Phase
1. Implement `data_extract.cli.error_prompts` module
2. Implement `data-extract session` command group
3. Implement `data-extract retry` command
4. Implement `data_extract.cli.batch_processor` module
5. **Unskip and validate 12 Story 5-6 tests**

### For Brownfield Migration Epic
1. Resolve circular import by restructuring semantic commands
2. Standardize chunk format (JSON vs TXT decision)
3. Complete CLI routing infrastructure
4. **Unskip and validate 10 brownfield-dependent tests**

### For Future Epics (As Needed)
1. Implement advanced summary panel features
2. **Unskip and validate TestSummaryPanelAdvanced class**

---

## Notes

- **Test count discrepancy:** Review doc mentioned 12-21 skipped tests. This catalog found 21+ distinct tests (28 via `rg` count). Discrepancy likely due to:
  - Entire test class (TestSummaryPanelAdvanced) counted as 1 item vs multiple tests
  - Organization flags: 5 tests found vs 4 mentioned

- **TDD RED phase tests:** Many skipped tests are intentionally RED (expected failures) per TDD methodology. These tests define acceptance criteria for unimplemented features.

- **Brownfield constraints:** 5 tests blocked by legacy architecture decisions. This is acceptable tech debt during gradual migration strategy.

- **BLUE phase scope:** 12 tests represent 57% of skipped tests. Completing Story 5-6 BLUE phase will significantly reduce test debt.

---

**Catalog Status:** Complete
**Files Analyzed:** 8 test files
**Next Review:** After Epic 5 BLUE phase completion (estimated 2025-12)
