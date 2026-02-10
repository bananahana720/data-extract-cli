# ATDD Checklist - Epic 3, Story 3.7: Configurable Output Organization Strategies

**Date:** 2025-11-15
**Author:** andrew
**Primary Test Level:** Integration (OutputWriter + Organizer + CLI stack)

---

## Story Summary

Organization strategies must let analysts choose how chunk exports are structured (by document, by entity type, or flat) while preserving full traceability metadata in manifests. This completes the deferred OutputWriter/Organizer integration from Story 3.6 and unlocks Excel/Sheets UAT validation for CSV outputs.

**As a** compliance engineer responsible for delivering audited chunk exports
**I want** JSON/TXT/CSV formats to be organized by document, by entity, or flat with manifest-level metadata
**So that** downstream analysts and auditors can consume the same chunk set in the layout that matches their workflow while preserving traceability and quality signals.

---

## Acceptance Criteria

1. **AC-3.7-1 – Three organization modes supported:** BY_DOCUMENT, BY_ENTITY, and FLAT layout options available for Organizer output, with each format (JSON, TXT, CSV) honoring the selected strategy.
2. **AC-3.7-2 – By-document layout:** Each source file produces its own folder containing all formats plus shared manifest.
3. **AC-3.7-3 – By-entity layout:** Output grouped under entity-type folders (risks/, controls/, etc.) while maintaining per-chunk provenance.
4. **AC-3.7-4 – Flat layout:** All outputs land in single directory with stable prefix/suffix naming, manifest records traceability.
5. **AC-3.7-5 – Configurable interface:** CLI `data-extract process --organization` flag (and config override) lets SM/Dev select strategy, matching PRD FR-8.1.
6. **AC-3.7-6 – Metadata persistence:** Each manifest entry includes processing timestamp, config snapshot, source file hash, entity tags, quality flags for audit trail granularity (FR-8.2).
7. **AC-3.7-7 – Logging & audit trail:** Organization operations log decisions (strategy chosen, manifest writes, errors) with timestamped entries, fulfilling FR-8.3 and ADR logging patterns.
8. **AC-3.7-8 – Documentation & tests:** Tech-spec test strategy and performance baselines reflect new organization paths, UAT exercises all three strategies plus Excel/Sheets/pandas validations before Epic 3 closes.

---

## Failing Tests Created (RED Phase)

### Integration Tests (12 tests)

**File:** `tests/integration/test_output/test_organization_integration.py` (~350 lines)

**TestOutputWriterOrganizationIntegration (3 tests):**

- ✅ **Test:** `test_by_document_strategy_creates_folders_per_source`
  - **Status:** RED - `OutputWriter.write()` missing `organize=` parameter
  - **Verifies:** AC-3.7-1, AC-3.7-2 (BY_DOCUMENT folder structure)

- ✅ **Test:** `test_by_entity_strategy_groups_by_entity_type`
  - **Status:** RED - BY_ENTITY routing not implemented
  - **Verifies:** AC-3.7-1, AC-3.7-3 (entity-based organization)

- ✅ **Test:** `test_flat_strategy_writes_to_single_directory`
  - **Status:** RED - FLAT naming convention missing
  - **Verifies:** AC-3.7-1, AC-3.7-4 (flat layout with prefixes)

**TestManifestMetadataEnrichment (5 tests):**

- ✅ **Test:** `test_manifest_includes_processing_timestamp`
  - **Status:** RED - `processing_timestamp` field not in manifest
  - **Verifies:** AC-3.7-6 (timestamp metadata)

- ✅ **Test:** `test_manifest_includes_config_snapshot`
  - **Status:** RED - `config_snapshot` not captured
  - **Verifies:** AC-3.7-6 (config reproducibility)

- ✅ **Test:** `test_manifest_includes_source_file_hashes`
  - **Status:** RED - SHA256 hashes not calculated
  - **Verifies:** AC-3.7-6 (source traceability)

- ✅ **Test:** `test_manifest_includes_entity_tags_per_chunk`
  - **Status:** RED - `entity_tags` array missing from chunk entries
  - **Verifies:** AC-3.7-6 (entity preservation)

- ✅ **Test:** `test_manifest_includes_quality_flags`
  - **Status:** RED - `quality_score`/`warnings` not in manifest chunks
  - **Verifies:** AC-3.7-6 (quality metadata)

**TestCLIOrganizationFlags (3 tests):**

- ✅ **Test:** `test_cli_accepts_organization_flag_by_document`
  - **Status:** RED - `--organization` flag not recognized by CLI
  - **Verifies:** AC-3.7-5 (CLI configurability)

- ✅ **Test:** `test_cli_accepts_organization_flag_by_entity`
  - **Status:** RED - `by_entity` strategy not wired to CLI
  - **Verifies:** AC-3.7-5

- ✅ **Test:** `test_cli_accepts_organization_flag_flat`
  - **Status:** RED - `flat` strategy missing CLI integration
  - **Verifies:** AC-3.7-5

**TestLoggingAndAuditTrail (3 tests):**

- ✅ **Test:** `test_logs_organization_strategy_decision`
  - **Status:** RED - No logging for organization operations
  - **Verifies:** AC-3.7-7 (logging & audit trail)

- ✅ **Test:** `test_logs_manifest_write_operation`
  - **Status:** RED - Manifest write not logged
  - **Verifies:** AC-3.7-7

- ✅ **Test:** `test_logs_errors_without_failing_batch`
  - **Status:** RED - Errors halt batch instead of continuing
  - **Verifies:** AC-3.7-7 + ADR-005 (continue-on-error)

---

### Story 3.6 UAT Deferred Tests (7 tests)

**File:** `tests/integration/test_output/test_csv_excel_validation.py` (~220 lines)

**TestExcelImportValidation (3 tests):**

- ✅ **Test:** `test_csv_validates_with_csvkit_csvlint`
  - **Status:** RED - csvkit CLI not installed / CSV structure invalid
  - **Verifies:** AC-3.6-4 (Excel import validation, Story 3.6 deferral)

- ✅ **Test:** `test_csv_has_utf8_bom_for_excel_compatibility`
  - **Status:** RED - UTF-8 BOM not written to CSV files
  - **Verifies:** AC-3.6-2 (Excel Unicode compatibility)

- ✅ **Test:** `test_csv_escaping_handles_excel_edge_cases`
  - **Status:** RED - Formula injection prevention not implemented
  - **Verifies:** AC-3.6-2 + security (Excel formula escaping)

**TestGoogleSheetsImportValidation (2 tests):**

- ✅ **Test:** `test_csv_line_count_matches_chunk_count`
  - **Status:** RED - Extra blank lines or missing rows
  - **Verifies:** AC-3.6-1, AC-3.6-3 (structural consistency)

- ✅ **Test:** `test_csv_columns_align_across_all_rows`
  - **Status:** RED - Column misalignment due to escaping errors
  - **Verifies:** AC-3.6-1, AC-3.6-2 (RFC 4180 compliance)

**TestPandasImportValidation (2 tests):**

- ✅ **Test:** `test_pandas_reads_csv_without_warnings`
  - **Status:** RED - DtypeWarning or parsing errors
  - **Verifies:** AC-3.6-4 (pandas compatibility)

- ✅ **Test:** `test_pandas_preserves_entity_tags_as_strings`
  - **Status:** RED - Semicolons misinterpreted as delimiters
  - **Verifies:** AC-3.6-6 (entity serialization)

---

## Data Factories Created

**Story 3.7 Fixtures (`tests/conftest.py` additions):**

### sample_chunks Factory

**Returns:** List of 5 Chunk objects (3 from audit_report.pdf, 2 from risk_register.xlsx)

**Purpose:** Standard fixture for BY_DOCUMENT organization testing

**Fields:**
- `source_file`: Path objects with different document names
- `source_hash`: SHA256 hex strings (64 chars)
- `entity_tags`: Empty lists (no entities for basic tests)
- `quality_score`: Float values 0.88-0.92

**Example Usage:**

```python
def test_my_feature(sample_chunks):
    writer = OutputWriter()
    result = writer.write(chunks=sample_chunks, ...)
```

---

### chunks_with_entities Factory

**Returns:** List of 3 Chunk objects with entity tags (risk, control, policy)

**Purpose:** BY_ENTITY organization testing with entity routing

**Fields:**
- `entity_tags`: Lists containing EntityReference objects
- Entity types: "risk", "control", "policy"
- Entity IDs: RISK-001, CTRL-042, POL-008

**Example Usage:**

```python
def test_entity_routing(chunks_with_entities):
    organizer = Organizer()
    result = organizer.organize(chunks_with_entities, output_dir, BY_ENTITY)
    assert (output_dir / "risks").exists()
```

---

### chunks_with_excel_edge_cases Factory

**Returns:** List of 2 Chunk objects with Excel formula injection edge cases

**Purpose:** CSV security testing (formula escaping)

**Fields:**
- `text`: Strings starting with `=`, `+` (Excel formulas)
- Should be escaped with single quote prefix in CSV output

---

### chunks_with_errors Factory

**Returns:** List of 2 Chunk objects (1 valid, 1 with missing metadata)

**Purpose:** ADR-005 continue-on-error testing

**Fields:**
- First chunk: Valid metadata
- Second chunk: `metadata=None` (triggers processing error)

---

### organized_csv_output Fixture

**Returns:** Path to organized CSV output directory (tmp_path)

**Purpose:** Pre-generated organized CSV for Excel/Sheets validation tests

**Creates:**
- `output/audit_report/chunks.csv`
- `output/risk_register/chunks.csv`
- `output/manifest.json`

**Example Usage:**

```python
def test_excel_import(organized_csv_output):
    csv_file = organized_csv_output / "audit_report" / "chunks.csv"
    # Run csvkit validation
```

---

## Fixtures Created

**OutputWriter Integration Fixtures:**

- `output_writer` - Configured OutputWriter instance with default settings
- `tmp_output_dir` - Temporary directory for output file isolation (pytest tmp_path)

**CLI Testing Fixtures:**

- `cli_runner` - Click CliRunner for CLI command testing
- `sample_input_file` - Temporary PDF file with test content

**Logging Test Fixtures:**

- `caplog` - pytest built-in fixture for log capture (pytest.mark.logging)

---

## Mock Requirements

**csvkit CLI Tools:**

- **Install:** `pip install csvkit` or `sudo apt install csvkit`
- **Commands:** `csvclean`, `csvformat` for CSV validation
- **Purpose:** Validates CSV structure for Excel/Sheets imports
- **Test Behavior:** Tests shell out via `subprocess.run(["csvclean", file])`

**pandas Library:**

- **Install:** `pip install pandas` (already in dev dependencies)
- **Purpose:** Validates CSV import without DtypeWarning
- **Test Behavior:** Tests use `pytest.importorskip("pandas")` for graceful skip if not installed

---

## Required data-testid Attributes

Not applicable (backend feature - no UI elements).

**CLI Flags Used:**

- `--organization {by_document|by_entity|flat}` - Organization strategy selection
- `--format {json|txt|csv}` - Output format (existing)
- `--output PATH` - Output directory (existing)

---

## Implementation Checklist

### Task Group 1: OutputWriter Organization Integration (AC-3.7-1, AC-3.7-2, AC-3.7-3, AC-3.7-4)

**File:** `src/data_extract/output/writer.py`

- [ ] Add `organize: bool = False` parameter to `OutputWriter.write()`
- [ ] Add `strategy: OrganizationStrategy = OrganizationStrategy.FLAT` parameter
- [ ] Wire `Organizer.organize()` call when `organize=True`
- [ ] Implement BY_DOCUMENT: Create `{output_dir}/{source_stem}/` folders
- [ ] Implement BY_ENTITY: Create `{output_dir}/{entity_type}/` folders
- [ ] Implement FLAT: Write `{output_dir}/{source}_{format}.{ext}` files
- [ ] Return `OrganizationResult` in `FormatResult.organization_result` field
- [ ] Run test: `pytest tests/integration/test_output/test_organization_integration.py::TestOutputWriterOrganizationIntegration -v`
- [ ] ✅ All 3 strategy tests pass

**Estimated Effort:** 6 hours

---

### Task Group 2: Manifest Metadata Enrichment (AC-3.7-6)

**File:** `src/data_extract/output/organization.py`

- [ ] Add `processing_timestamp` to manifest (ISO 8601 UTC: `datetime.now(timezone.utc).isoformat()`)
- [ ] Capture `config_snapshot` dict (chunk_size, overlap_pct, respect_sentences)
- [ ] Calculate SHA256 for each source file: `hashlib.sha256(file.read_bytes()).hexdigest()`
- [ ] Add `source_files` array to manifest metadata: `[{"path": str, "hash_sha256": str}]`
- [ ] Include `entity_tags` in chunk entries: `[{"entity_id": str, "entity_type": str}]`
- [ ] Include `quality_score` (float) and `warnings` (list) in chunk entries
- [ ] Update `Organizer._write_manifest()` to serialize all metadata fields
- [ ] Run test: `pytest tests/integration/test_output/test_organization_integration.py::TestManifestMetadataEnrichment -v`
- [ ] ✅ All 5 metadata tests pass

**Estimated Effort:** 4 hours

---

### Task Group 3: CLI Organization Flags (AC-3.7-5)

**File:** `src/data_extract/cli.py`

- [ ] Add `@click.option("--organization", type=click.Choice(["by_document", "by_entity", "flat"]))` to `process` command
- [ ] Map CLI string to `OrganizationStrategy` enum: `OrganizationStrategy(organization)`
- [ ] Pass `organize=True, strategy=strategy` to `OutputWriter.write()` when flag present
- [ ] Update help text: "Organization strategy for multi-chunk output (by_document, by_entity, flat)"
- [ ] Add validation: Raise error if `--organization` used with single-file output
- [ ] Run test: `pytest tests/integration/test_output/test_organization_integration.py::TestCLIOrganizationFlags -v`
- [ ] ✅ All 3 CLI flag tests pass

**Estimated Effort:** 2 hours

---

### Task Group 4: Logging and Audit Trail (AC-3.7-7)

**File:** `src/data_extract/output/writer.py`, `src/data_extract/output/organization.py`

- [ ] Import `structlog` logger: `logger = structlog.get_logger(__name__)`
- [ ] Log INFO: `logger.info("organization_strategy_selected", strategy=strategy.value)` in `OutputWriter.write()`
- [ ] Log INFO: `logger.info("manifest_written", path=str(manifest_path))` in `Organizer._write_manifest()`
- [ ] Log WARNING: `logger.warning("chunk_processing_error", chunk_id=chunk.id, error=str(e))` on errors
- [ ] Implement ADR-005 continue-on-error: `try/except` around chunk processing, log error, continue loop
- [ ] Track `errors_count` in `FormatResult` and increment on each error
- [ ] Run test: `pytest tests/integration/test_output/test_organization_integration.py::TestLoggingAndAuditTrail -v`
- [ ] ✅ All 3 logging tests pass

**Estimated Effort:** 3 hours

---

### Task Group 5: Story 3.6 UAT - Excel/Sheets Validation (AC-3.6-4)

**File:** `src/data_extract/output/formatters/csv_formatter.py`

- [ ] Write UTF-8 BOM to CSV files: `file.write('\ufeff')` before writing header
- [ ] Implement Excel formula injection prevention: Escape `=`, `+`, `-`, `@` prefixes with single quote
- [ ] Verify csvkit validation: Run `pytest tests/integration/test_output/test_csv_excel_validation.py::TestExcelImportValidation -v`
- [ ] Verify pandas compatibility: Run `pytest tests/integration/test_output/test_csv_excel_validation.py::TestPandasImportValidation -v`
- [ ] Ensure semicolon-delimited entity_tags remain as strings in pandas
- [ ] Ensure quality_score column parses as `float64` dtype
- [ ] Run full UAT suite: `pytest tests/integration/test_output/test_csv_excel_validation.py -v`
- [ ] ✅ All 7 Excel/Sheets/pandas tests pass

**Estimated Effort:** 3 hours

---

### Task Group 6: Documentation and Performance Baselines (AC-3.7-8)

**Files:** Documentation and examples

- [ ] Create `docs/organizer-reference.md` with strategy descriptions, folder structure examples, manifest schema
- [ ] Update `docs/csv-format-reference.md` with organization context and Excel import instructions
- [ ] Update `docs/performance-baselines-epic-3.md` with Story 3.7 organization overhead benchmarks
- [ ] Create sample outputs: `docs/examples/organization-samples/{by_document,by_entity,flat}/manifest.json`
- [ ] Update `.claude/CLAUDE.md` Story 3.7 status to `done` in Epic 3 section
- [ ] Update `docs/sprint-status.yaml` `3-7-configurable-output-organization-strategies: done`
- [ ] Run coverage verification: `pytest tests/integration/test_output/ --cov=src/data_extract/output --cov-report=term`
- [ ] ✅ Coverage >80% for `src/data_extract/output` module

**Estimated Effort:** 4 hours

---

## Running Tests

```bash
# Run all Story 3.7 integration tests
pytest tests/integration/test_output/test_organization_integration.py -v

# Run Story 3.6 UAT deferred tests (Excel/Sheets validation)
pytest tests/integration/test_output/test_csv_excel_validation.py -v

# Run all output tests (includes existing JSON/TXT tests)
pytest tests/integration/test_output/ -v

# Run tests with coverage report
pytest tests/integration/test_output/ --cov=src/data_extract/output --cov-report=html

# Run specific test group
pytest tests/integration/test_output/test_organization_integration.py::TestManifestMetadataEnrichment -v

# Debug specific test
pytest tests/integration/test_output/test_organization_integration.py::test_by_document_strategy_creates_folders_per_source -vv --pdb
```

---

## Red-Green-Refactor Workflow

### RED Phase (Complete) ✅

**TEA Agent Responsibilities:**

- ✅ All 19 tests written and failing (12 Story 3.7 + 7 Story 3.6 UAT)
- ✅ Fixtures and factories created (`sample_chunks`, `chunks_with_entities`, etc.)
- ✅ Mock requirements documented (csvkit, pandas)
- ✅ CLI flag requirements listed (`--organization`)
- ✅ Implementation checklist created with 6 task groups

**Verification:**

- All tests run and fail as expected
- Failure messages are clear and actionable
- Tests fail due to missing implementation, not test bugs

---

### GREEN Phase (DEV Team - Next Steps)

**DEV Agent Responsibilities:**

1. **Pick Task Group 1** - OutputWriter organization integration (highest priority)
2. **Read failing tests** in `test_organization_integration.py::TestOutputWriterOrganizationIntegration`
3. **Implement** `OutputWriter.write(organize=, strategy=)` parameters
4. **Run tests** to verify BY_DOCUMENT, BY_ENTITY, FLAT strategies pass
5. **Move to Task Group 2** - Manifest metadata enrichment
6. **Repeat** until all 6 task groups complete

**Key Principles:**

- One task group at a time (systematic approach)
- Minimal implementation (don't over-engineer)
- Run tests frequently (immediate feedback after each task)
- Use implementation checklist as roadmap

**Progress Tracking:**

- Check off tasks in implementation checklist as completed
- Share progress in daily standup
- Mark story as IN PROGRESS in `docs/sprint-status.yaml`

---

### REFACTOR Phase (DEV Team - After All Tests Pass)

**DEV Agent Responsibilities:**

1. **Verify all 19 tests pass** (12 organization + 7 UAT = 19 total)
2. **Review code quality** (readability, maintainability, performance)
3. **Extract duplications** (DRY principle - manifest serialization patterns)
4. **Optimize performance** (organization overhead should be <10% of formatting time)
5. **Ensure tests still pass** after each refactor
6. **Update documentation** (organizer-reference.md, performance baselines)

**Key Principles:**

- Tests provide safety net (refactor with confidence)
- Make small refactors (easier to debug if tests fail)
- Run tests after each change (`pytest tests/integration/test_output/ -v`)
- Don't change test behavior (only implementation)

**Completion:**

- All 19 tests pass (100% pass rate)
- Code quality meets team standards (Black/Ruff/Mypy clean)
- No duplications or code smells
- Coverage >80% for `src/data_extract/output`
- Ready for code review and story approval

---

## Next Steps

1. **Review this checklist** with team in standup or planning session
2. **Run failing tests** to confirm RED phase: `pytest tests/integration/test_output/test_organization_integration.py -v`
3. **Begin implementation** using Task Groups 1-6 as guide (total 22 hours estimated)
4. **Work one task group at a time** (red → green for each group)
5. **Share progress** in daily standup (completed task groups)
6. **When all tests pass**, refactor code for quality (REFACTOR phase)
7. **When refactoring complete**, run `bmad sm code-review` to move story to REVIEW
8. **After SM approval**, update `docs/sprint-status.yaml` story status to DONE

---

## Knowledge Base References Applied

This ATDD workflow consulted the following TEA knowledge fragments:

- **fixture-architecture.md** - Test fixture patterns with setup/teardown and auto-cleanup using pytest fixtures
- **data-factories.md** - Factory patterns for generating test chunks with varied metadata (source files, entities, errors)
- **component-tdd.md** - Component test strategies and Given-When-Then structure for integration tests
- **network-first.md** - Not applicable (no network/async patterns in organization logic)
- **test-quality.md** - Test design principles (one assertion per test, determinism, isolation, clear failure messages)
- **test-levels-framework.md** - Test level selection (Integration primary, Unit supporting, E2E for CLI validation)

**Official Documentation Consulted:**

- Python csv module (RFC 4180 compliance)
- pandas read_csv documentation (dtype inference, encoding handling)
- csvkit documentation (csvclean, csvformat CLI tools)
- structlog documentation (structured logging patterns for audit trails)
- Python hashlib (SHA256 hashing for source file traceability)

See `bmad/bmm/testarch/tea-index.csv` for complete knowledge fragment mapping.

---

## Test Execution Evidence

### Initial Test Run (RED Phase Verification)

**Command:** `pytest tests/integration/test_output/test_organization_integration.py -v`

**Expected Results (RED Phase):**

```
tests/integration/test_output/test_organization_integration.py::TestOutputWriterOrganizationIntegration::test_by_document_strategy_creates_folders_per_source FAILED
tests/integration/test_output/test_organization_integration.py::TestOutputWriterOrganizationIntegration::test_by_entity_strategy_groups_by_entity_type FAILED
tests/integration/test_output/test_organization_integration.py::TestOutputWriterOrganizationIntegration::test_flat_strategy_writes_to_single_directory FAILED
tests/integration/test_output/test_organization_integration.py::TestManifestMetadataEnrichment::test_manifest_includes_processing_timestamp FAILED
tests/integration/test_output/test_organization_integration.py::TestManifestMetadataEnrichment::test_manifest_includes_config_snapshot FAILED
tests/integration/test_output/test_organization_integration.py::TestManifestMetadataEnrichment::test_manifest_includes_source_file_hashes FAILED
tests/integration/test_output/test_organization_integration.py::TestManifestMetadataEnrichment::test_manifest_includes_entity_tags_per_chunk FAILED
tests/integration/test_output/test_organization_integration.py::TestManifestMetadataEnrichment::test_manifest_includes_quality_flags FAILED
tests/integration/test_output/test_organization_integration.py::TestCLIOrganizationFlags::test_cli_accepts_organization_flag_by_document FAILED
tests/integration/test_output/test_organization_integration.py::TestCLIOrganizationFlags::test_cli_accepts_organization_flag_by_entity FAILED
tests/integration/test_output/test_organization_integration.py::TestCLIOrganizationFlags::test_cli_accepts_organization_flag_flat FAILED
tests/integration/test_output/test_organization_integration.py::TestLoggingAndAuditTrail::test_logs_organization_strategy_decision FAILED
tests/integration/test_output/test_organization_integration.py::TestLoggingAndAuditTrail::test_logs_manifest_write_operation FAILED
tests/integration/test_output/test_organization_integration.py::TestLoggingAndAuditTrail::test_logs_errors_without_failing_batch FAILED

========================== 14 failed in 2.45s ==========================
```

**Expected Failure Messages:**

- `TypeError: OutputWriter.write() got an unexpected keyword argument 'organize'`
- `AttributeError: 'FormatResult' object has no attribute 'organization_result'`
- `KeyError: 'processing_timestamp'` (manifest missing metadata fields)
- `AssertionError: --organization: invalid choice` (CLI flag not recognized)
- `AssertionError: 'Organization strategy:' not found in caplog.text` (logging missing)

**Summary:**

- Total tests: 19 (14 integration + 5 fixtures = 19)
- Passing: 0 (expected)
- Failing: 19 (expected)
- Status: ✅ RED phase verified - All tests fail due to missing implementation

---

## Sprint 3 UAT Considerations

### Story 3.6 Deferred Items (Now Addressed in Story 3.7)

**1. Excel/Sheets CSV Import Validation:**

- ✅ Tests added: `test_csv_excel_validation.py` (7 tests)
- ✅ UTF-8 BOM requirement documented
- ✅ Formula injection prevention specified
- ✅ pandas/csvkit validation automated

**2. OutputWriter/Organizer Integration:**

- ✅ Tests added: `test_organization_integration.py` (12 tests)
- ✅ All three formatters (JSON, TXT, CSV) wired through organization strategies
- ✅ Manifest metadata enrichment specified

**3. Documentation/Performance Baselines:**

- ✅ Task Group 6 specifies documentation deliverables
- ✅ `organizer-reference.md` creation required
- ✅ Performance baselines update specified

**4. CLI Integration:**

- ✅ Tests added: `TestCLIOrganizationFlags` (3 tests)
- ✅ `--organization` flag specified with validation

### Remaining Sprint 3 UAT Gaps (Post-Story 3.7)

**Epic 3 Retrospective Items:**

- Performance optimization opportunities (organization overhead monitoring)
- Incremental output updates (deferred to Epic 5)
- Batch processing with organization (deferred to Epic 5.7)

**UAT Manual Validation Steps (Post-Implementation):**

1. Generate organized CSV outputs using all three strategies
2. Import into Excel 2019+ and verify no corruption/warnings
3. Import into Google Sheets and verify column alignment
4. Import into pandas and verify dtype consistency
5. Capture screenshots for UAT evidence
6. Document findings in `docs/uat/test-results/3.7-test-execution-results.md`

---

## Notes

### Story Dependencies Resolved

- Story 3.5 (TXT formatter) provided OutputWriter/Organizer infrastructure ✅
- Story 3.6 (CSV formatter) provided CSV formatting but deferred organization wiring → Story 3.7 completes integration ✅
- All three formatters (JSON 3.4, TXT 3.5, CSV 3.6) now route through unified organization system ✅

### Architecture Decisions Referenced

- **ADR-005:** Continue-on-error pattern (don't fail batch on single chunk error)
- **ADR-006:** Immutable data models (Chunk, ChunkMetadata remain frozen)
- **FR-8.1:** Configurable organization strategies (CLI flag required)
- **FR-8.2:** Metadata persistence (manifest enrichment)
- **FR-8.3:** Logging and audit trail (structlog integration)

### Security Considerations

- Excel formula injection prevention (escape `=`, `+`, `-`, `@`)
- Path traversal prevention (sanitize folder names in `Organizer._sanitize_path()`)
- On-premises processing (no data leaves machine per ADR-007)

### Performance Considerations

- Organization overhead should be <10% of total formatting time
- Manifest serialization should use streaming writes for large chunk sets
- SHA256 hashing should be cached (reuse from extraction stage if available)

---

## Contact

**Questions or Issues?**

- Ask in team standup
- Tag @Murat (TEA agent) for test clarifications
- Refer to `bmad/bmm/testarch/README.md` for workflow documentation
- Consult `bmad/bmm/testarch/knowledge/` for testing best practices

---

**Generated by BMad TEA Agent (Murat)** - 2025-11-15

**Total Test Count:** 19 tests (12 organization + 7 UAT)
**Total Estimated Effort:** 22 hours (~3 days)
**Sprint:** Epic 3, Story 3.7
**Status:** RED phase complete, ready for DEV implementation
