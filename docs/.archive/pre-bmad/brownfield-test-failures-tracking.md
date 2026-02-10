# Brownfield Test Failures Tracking

**Created:** 2025-11-12
**Status:** Needs Triage
**Total Failures:** 25 (pre-existing, not introduced by Story 2.5.3)

## Summary

Pre-existing brownfield integration test failures identified during Story 2.5.3 code review. These failures exist in the legacy codebase (`src/{cli,extractors,processors,formatters,infrastructure,pipeline}/`) and are NOT caused by greenfield changes in `src/data_extract/`.

**Impact:** Brownfield tests currently fail but greenfield tests pass. This is expected during migration (Epic 1-2) as brownfield code is being assessed and consolidated.

## Failure Breakdown

### test_processor_formatter_integration.py (11 failures)
- **Location:** `tests/integration/test_processor_formatter_integration.py`
- **Scope:** Brownfield processor → formatter integration
- **Count:** 11 test failures
- **Triage Status:** Pending
- **Notes:** Integration tests for legacy pipeline components

### test_cli_workflows.py (4 failures)
- **Location:** `tests/integration/test_cli_workflows.py`
- **Scope:** Brownfield CLI workflows
- **Count:** 4 test failures
- **Triage Status:** Pending
- **Notes:** CLI command integration tests

### test_cross_format_validation.py (4 failures)
- **Location:** `tests/integration/test_cross_format_validation.py`
- **Scope:** Cross-format validation in brownfield
- **Count:** 4 test failures
- **Triage Status:** Pending
- **Notes:** Multi-format processing workflows

### test_extractor_processor_integration.py (6 failures)
- **Location:** `tests/integration/test_extractor_processor_integration.py`
- **Scope:** Brownfield extractor → processor integration
- **Count:** 6 test failures
- **Triage Status:** Pending
- **Notes:** Legacy extraction pipeline integration

## Triage Plan

1. **Epic 1 Story 1.2 (Brownfield Assessment):** Document which tests map to deprecated vs. migrate-worthy code
2. **Epic 1 Story 1.4 (Architecture Consolidation):** Decide migration strategy:
   - Fix and migrate tests to greenfield patterns
   - Mark as deprecated if feature is replaced
   - Archive if no longer relevant to product vision
3. **Epic 2.5/3 Bridge:** Keep brownfield failures isolated from greenfield quality gates during migration

## Quality Gate Strategy

**Current Approach (Epic 2.5):**
- ✅ Greenfield quality gates enforced: `mypy src/data_extract/`, greenfield integration tests
- ⚠️ Brownfield tests isolated: Failures tracked but don't block greenfield stories
- 📋 Migration decision deferred to Epic 1 Story 1.4

**Future State (Post-Migration):**
- All tests passing OR explicitly deprecated with documentation
- Single quality gate covering entire codebase
- No brownfield/greenfield distinction

## References

- **Story 2.5.3 Review:** Code review identified these failures (2025-11-12)
- **Epic 1 Story 1.2:** Brownfield codebase assessment (in progress)
- **Epic 1 Story 1.4:** Core pipeline architecture consolidation (planned)
- **CLAUDE.md:** Dual codebase structure section explains migration approach

## Actions Required

- [ ] Run full integration test suite and capture detailed failure output
- [ ] Map each failing test to brownfield modules it exercises
- [ ] Cross-reference with Story 1.2 brownfield assessment
- [ ] Prioritize fixes based on migration strategy (Story 1.4)
- [ ] Consider creating sub-issues per test file if failures persist beyond Epic 2
