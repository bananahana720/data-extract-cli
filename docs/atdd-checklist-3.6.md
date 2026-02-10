# ATDD Checklist - Epic 3, Story 3.6: CSV Output Format for Analysis and Tracking

**Date:** 2025-11-15
**Author:** andrew
**Primary Test Level:** Integration (CLI + formatter stack)

---

## Story Summary

CSV formatter must let analysts export normalized chunks (text + provenance) into spreadsheet-ready artifacts without re-running the pipeline. The CLI should expose `--format csv` and produce schema-stable files that downstream Excel/pandas flows can ingest with zero manual cleanup.

**As a** data quality analyst
**I want** canonical CSV output with provenance metadata and parser validation
**So that** I can review coverage in spreadsheets and trace each row back to its source confidently.

---

## Acceptance Criteria

1. **AC-3.6-1 – Canonical column schema:** Columns appear in fixed order: chunk_id, source_file, section_context, chunk_text, entity_tags, quality_score, word_count, token_count, processing_version, warnings.
2. **AC-3.6-2 – RFC 4180 escaping:** Quotes, commas, and multiline chunks follow RFC 4180 quoting so Excel/Sheets stay aligned.
3. **AC-3.6-3 – Clear header row:** First row labels columns with readable names and remains stable between runs.
4. **AC-3.6-4 – Import validation:** CSV loads into Excel/Sheets/pandas without warnings.
5. **AC-3.6-5 – Optional truncation indicator:** `max_text_length` truncates chunk_text and appends `…` plus warning.
6. **AC-3.6-6 – Entity list serialization:** Entity tags serialize as `;`-delimited tokens (e.g., `Risk-001;Control-003`).
7. **AC-3.6-7 – Parser sanity checks:** Python `csv`, pandas, and csvkit (CLI) validations run pre-output; failures block publishing.

---

## Failing Tests Created (RED Phase)

### E2E Tests (0 tests)

**File:** `tests/e2e/` (not yet created)

- ✅ **Test:** _None yet_
  - **Status:** RED - Requires Playwright CLI wiring once CSV formatter exists
  - **Verifies:** Future CLI smoke test for `data-extract --format csv`

### API / Integration Tests (5 tests)

**File:** `tests/integration/test_output/test_csv_pipeline.py` (221 lines)

- ✅ **Test:** `test_chunking_pipeline_generates_csv_with_header`
  - **Status:** RED - ImportError (`CsvFormatter` missing)
  - **Verifies:** AC-3.6-1 canonical header end-to-end
- ✅ **Test:** `test_formatter_truncation_indicator_surfaces_in_pipeline`
  - **Status:** RED - CsvFormatter not implemented
  - **Verifies:** AC-3.6-5 ellipsis + warning propagation
- ✅ **Test:** `test_pandas_can_import_csv_output`
  - **Status:** RED - CsvFormatter missing / pandas skip guard
  - **Verifies:** AC-3.6-4 pandas.read_csv compatibility
- ✅ **Test:** `test_output_writer_emits_csv_format`
  - **Status:** RED - OutputWriter lacks csv registry
  - **Verifies:** Writer returns FormatResult(format_type="csv")
- ✅ **Test:** `test_output_writer_honors_per_chunk_option`
  - **Status:** RED - OutputWriter missing csv support
  - **Verifies:** Organizer creates per-chunk CSV artifacts

### Component / Unit Tests (13 tests)

**File:** `tests/unit/test_output/test_csv_formatter.py` (313 lines)

- ✅ **Test:** `test_formatter_writes_canonical_header_once`
  - **Status:** RED - CsvFormatter missing
  - **Verifies:** AC-3.6-1 header order stability
- ✅ **Test:** `test_formatter_populates_required_columns`
  - **Status:** RED
  - **Verifies:** Columns filled with provenance metadata
- ✅ **Test:** `test_formatter_escapes_commas_quotes_and_newlines`
  - **Status:** RED
  - **Verifies:** AC-3.6-2 RFC 4180 escaping
- ✅ **Test:** `test_formatter_serializes_entities_as_semicolon_list`
  - **Status:** RED
  - **Verifies:** AC-3.6-6 entity tag serialization
- ✅ **Test:** `test_formatter_combines_quality_flags_into_warnings_column`
  - **Status:** RED
  - **Verifies:** warnings column aggregates quality flags
- ✅ **Test:** `test_formatter_truncates_text_with_ellipsis_indicator`
  - **Status:** RED
  - **Verifies:** AC-3.6-5 truncation indicator + warning
- ✅ **Test:** `test_format_chunks_returns_format_result`
  - **Status:** RED
  - **Verifies:** FormatResult metadata for csv format
- ✅ **Test:** `test_formatter_invokes_parser_validator_when_enabled`
  - **Status:** RED
  - **Verifies:** AC-3.6-7 parser hook executes
- ✅ **Test:** `test_formatter_allows_disabling_validation`
  - **Status:** RED
  - **Verifies:** Validation toggle for offline runs

**File:** `tests/unit/test_output/test_csv_parser_validator.py` (119 lines)

- ✅ **Test:** `test_validate_returns_report_for_valid_csv`
  - **Status:** RED - Validator not implemented
  - **Verifies:** AC-3.6-4/7 python + pandas + CLI success
- ✅ **Test:** `test_validator_invokes_cli_runner`
  - **Status:** RED
  - **Verifies:** csvkit command executed (AC-3.6-7)
- ✅ **Test:** `test_invalid_csv_raises_error`
  - **Status:** RED
  - **Verifies:** Parser failure blocks output
- ✅ **Test:** `test_cli_failure_surfaces_in_error_message`
  - **Status:** RED
  - **Verifies:** CLI failure bubbled via CsvParserError

---

## Data Factories Created

- `enriched_chunk` fixture (tests/unit/test_output/test_csv_formatter.py) – builds Chunk with full metadata, two entities, and quality flags for schema + warning tests.
- `chunk_with_long_text` fixture – clones enriched chunk with verbose text to trigger truncation indicator.
- `pipeline_chunks` fixture (tests/integration/test_output/test_csv_pipeline.py) – produces iterator resembling ChunkingEngine output for integration tests.
- CSV parser fixtures (`valid_csv_path`, `invalid_csv_path`) – generate clean/malformed CSV files for validator coverage.

---

## Fixtures Created

- `csv_formatter`, `csv_formatter_with_truncation` – configure CsvFormatter with default + max_text_length options.
- `DummyParserValidator` spy – asserts parser hook is invoked.
- `csv_formatter` (integration) – used for pipeline + pandas compatibility tests.
- `output_writer` – ensures writer registry includes CSV.

---

## Mock Requirements

- csvkit CLI (`csvformat` or `csvclean`) must be available on PATH for AC-3.6-7. Tests inject a fake runner but production must shell out via subprocess with deterministic flags.
- Pandas is optional dependency; integration tests call `pd.read_csv` when installed, else skip with clear marker.

---

## Required data-testid Attributes

Not applicable (CLI / formatter story). CLI switches relied upon:

- `--format csv`
- `--max-text-length {int}`
- `--validate/--no-validate`

---

## Mock / External Service Notes

- Parser validator should fail fast if csvkit CLI missing—surface actionable error instructing engineers to run `pip install csvkit` or install OS package before rerunning tests.
- Excel/Google Sheets validation steps remain manual but will use same sample CSV built by `tests/integration/test_output/test_csv_pipeline.py`.

---

## Implementation Checklist

### Formatter + Validator

- [ ] Implement `CsvFormatter` under `src/data_extract/output/formatters/csv_formatter.py`
  - [ ] Enforce canonical column order constant
  - [ ] Use `csv.writer` with `QUOTE_ALL` for RFC 4180 compliance
  - [ ] Inject `parser_validator` dependency; default to `CsvParserValidator`
  - [ ] Support `max_text_length` + ellipsis indicator with warnings
  - [ ] Serialize entity tags as `;`-delimited list (EntityReference.entity_id)
  - [ ] Populate FormatResult (format_type, chunk_count, bytes, duration, errors)
- [ ] Implement `CsvParserValidator` (`src/data_extract/output/validation/csv_parser.py`)
  - [ ] Run python `csv.reader` streaming validation
  - [ ] Run `pandas.read_csv` to assert schema compatibility
  - [ ] Run csvkit CLI (`csvformat --out csv file.csv`) capturing stderr/stdout
  - [ ] Raise `CsvParserError` when any engine fails; include error context
  - [ ] Return `CsvParserValidationReport` for logging (python/pandas/cli booleans)

### OutputWriter / CLI

- [ ] Register CsvFormatter in OutputWriter formatter registry (format_type `"csv"`)
- [ ] Wire CLI `data-extract process --format csv` option with validation toggle + truncation kwargs
- [ ] Extend Organizer strategies to handle CSV artifacts (BY_DOCUMENT, BY_ENTITY, FLAT manifests)
- [ ] Update `data_extract.cli` help text + docs to describe CSV usage.

### Documentation & Samples

- [ ] Create `docs/csv-format-reference.md` with schema, examples, and import steps.
- [ ] Publish sample CSV outputs (full + truncated) under `docs/examples/csv-output-samples/`.
- [ ] Update `docs/performance-baselines-epic-3.md` with Story 3.6 throughput.
- [ ] Refresh `.claude/CLAUDE.md` status + ADR-012 (OrganizationStrategy) referencing CSV addition.

---

## Test Execution Plan

```bash
pytest tests/unit/test_output/test_csv_formatter.py \
       tests/unit/test_output/test_csv_parser_validator.py \
       tests/integration/test_output/test_csv_pipeline.py -v
```

Expected RED-phase failure signature:

```
ImportError: No module named 'data_extract.output.formatters.csv_formatter'
```

Once formatter stub exists, failures should shift to assertion mismatches until all ACs satisfied.

---

## Knowledge Base References Applied

- `fixture-architecture.md` – fixture purity and auto-cleanup patterns for chunk factories.
- `data-factories.md` – faker-style factories mirrored via Python fixtures creating canonical chunk metadata.
- `component-tdd.md` – enforced single-assertion tests and Given-When-Then comments.
- `network-first.md` – ensured data dependencies (parser validation) occur before exposing output.
- `test-quality.md` – deterministic tests, one assertion per behavior, <100 LOC sections.
- `test-healing-patterns.md` – warnings column surfaces readability flags for healing visibility.
- `selector-resilience.md` – n/a (documented rationale for CLI flags vs selectors).
- `timing-debugging.md` – validated asynchronous parser steps happen deterministically; no sleeps.
- `test-levels-framework.md` – selected Integration as primary level (formatter/CLI) with supporting unit suites.

Official references:

- Python csv docs (RFC 4180 compliance for `csv.writer` QUOTE_ALL).
- pandas `read_csv` documentation – ensures dtype inference stays stable.
- csvkit documentation – command usage for `csvformat`/`csvclean`.
- Playwright/Cypress/Pact docs reviewed: no UI/contract dependencies for this story; recorded as not applicable.

---

## Test Execution Evidence

Tests intentionally left in RED state; sample failure when running `pytest -k csv_formatter`:

```
ImportError: No module named 'data_extract.output.formatters.csv_formatter'
```

This confirms formatter code is missing and needs implementation.

---

## Notes

- CSV formatter work depends on pending Story 3.5 artifacts (OutputWriter/Organizer). Ensure those land or stub for Story 3.6 to progress.
- csvkit dependency should be added to `[project.optional-dependencies.dev]` or docs instruct installing via pipx.
- For Excel/Sheets validation, capture screenshots + csvlint logs for UAT once formatter passes tests.

---

## Next Steps

1. Implement CsvFormatter + CsvParserValidator per checklist.
2. Register CSV format in OutputWriter and CLI.
3. Re-run RED tests until they pass (GREEN), then refactor for maintainability.
4. Execute manual Excel/Google Sheets imports, attach artifacts to UAT report.
5. Update `bmm-workflow-status.md` once Story 3.6 transitions to GREEN.

---

**Generated by BMad TEA Agent** - 2025-11-15
