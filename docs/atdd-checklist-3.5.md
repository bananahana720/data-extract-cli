# ATDD Checklist - Epic 3, Story 3.5: Plain Text Output Format for LLM Upload

**Date:** 2025-11-15
**Author:** andrew (TEA Agent - Murat)
**Primary Test Level:** Unit + Integration

---

## Story Summary

Power users generating audit context for LLM workflows need clean plain text output optimized for direct ChatGPT/Claude upload, enabling copy/paste of predictable, metadata-rich chunks without manual cleanup.

**As a** power user generating audit context for LLM workflows
**I want** clean plain text output optimized for direct ChatGPT/Claude upload
**So that** I can copy/paste predictable, metadata-rich chunks without manual cleanup

---

## Acceptance Criteria

1. **AC-3.5-1: Clean chunk text (P0)**
   - TXT output strips markdown/HTML artifacts, preserves intentional paragraph spacing
   - Guarantees deterministic whitespace across platforms
   - UAT Required: Yes - Manual review sample

2. **AC-3.5-2: Configurable delimiters (P0)**
   - Default delimiter: ━━━ CHUNK {{n}} ━━━
   - Configurable via CLI/config
   - Delimiter always appears between chunks in concatenated mode
   - UAT Required: No - Unit test sufficient

3. **AC-3.5-3: Optional metadata header (P1)**
   - When --include-metadata is set, each chunk emits compact header
   - Header includes: source file, chunk id, entity tags, quality score
   - Header precedes text block
   - UAT Required: Yes - Format validation

4. **AC-3.5-4: Output organization (P0)**
   - Formatter supports concatenated single-file exports
   - Formatter supports individual per-chunk files
   - Honors global organization strategies (by_document, by_entity, flat)
   - UAT Required: Yes

5. **AC-3.5-5: UTF-8 encoding (P0)**
   - TXT files written with UTF-8 (utf-8-sig for Windows compatibility)
   - Documented newline handling (LF default, CRLF optional)
   - UAT Required: No - Encoding test

6. **AC-3.5-6: No formatting artifacts (P1)**
   - Formatter removes BOM duplication, stray JSON braces, CLI color codes
   - QA verifies zipped sample has zero lint-detected anomalies
   - UAT Required: Yes - Manual review

7. **AC-3.5-7: LLM upload readiness (P0 - Critical)**
   - Manual UAT demonstrates copy/paste into ChatGPT and Claude prompts
   - No additional cleanup required
   - References at least one real chunk from integration fixtures
   - UAT Required: Yes - Critical

---

## Failing Tests Created (RED Phase)

### Unit Tests (14 tests)

**File:** `tests/unit/test_output/test_txt_formatter.py` (715 lines)

**Test Class: TestTxtFormatterCreation (3 tests)**
- ✅ **Test:** `test_formatter_creation_default_settings`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-2 - Default delimiter configuration

- ✅ **Test:** `test_formatter_creation_with_metadata_enabled`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-3 - Metadata header toggle

- ✅ **Test:** `test_formatter_creation_with_custom_delimiter`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-2 - Custom delimiter support

**Test Class: TestTextCleaning (5 tests)**
- ✅ **Test:** `test_clean_text_preserves_paragraph_spacing`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-1 - Intentional spacing preservation

- ✅ **Test:** `test_clean_text_removes_markdown_headers`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-1 - Markdown artifact removal

- ✅ **Test:** `test_clean_text_removes_markdown_bold_italic`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-1 - Markdown formatting removal

- ✅ **Test:** `test_clean_text_removes_html_tags`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-1 - HTML tag removal

- ✅ **Test:** `test_clean_text_normalizes_whitespace`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-1 - Whitespace normalization

**Test Class: TestDelimiterRendering (3 tests)**
- ✅ **Test:** `test_default_delimiter_renders_correctly`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-2 - Default delimiter pattern

- ✅ **Test:** `test_custom_delimiter_renders_correctly`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-2 - Custom delimiter rendering

- ✅ **Test:** `test_delimiter_chunk_numbering_sequential`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-2 - Sequential chunk numbering

**Test Class: TestMetadataHeaders (7 tests)**
- ✅ **Test:** `test_metadata_header_omitted_when_disabled`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-3 - Metadata toggle (off)

- ✅ **Test:** `test_metadata_header_included_when_enabled`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-3 - Metadata toggle (on)

- ✅ **Test:** `test_metadata_header_includes_source_file`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-3 - Source file in header

- ✅ **Test:** `test_metadata_header_includes_entity_tags`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-3 - Entity tags in header

- ✅ **Test:** `test_metadata_header_includes_quality_score`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-3 - Quality score in header

- ✅ **Test:** `test_metadata_header_compact_format`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-3 - Compact header (max 5-6 lines)

**Test Class: TestEncodingAndNewlines (2 tests)**
- ✅ **Test:** `test_utf8_sig_encoding_with_bom`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-5 - UTF-8-sig BOM

- ✅ **Test:** `test_unicode_character_preservation`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-5 - Unicode preservation

**Test Class: TestArtifactRemoval (3 tests)**
- ✅ **Test:** `test_no_bom_duplication`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-6 - Single BOM only

- ✅ **Test:** `test_no_json_braces_in_output`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-6 - No JSON syntax

- ✅ **Test:** `test_no_ansi_escape_codes`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-6 - No ANSI codes

**Test Class: TestFormatResultContract (3 tests)**
- ✅ **Test:** `test_format_chunks_returns_format_result`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** BaseFormatter protocol compliance

- ✅ **Test:** `test_format_result_includes_statistics`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** FormatResult statistics

- ✅ **Test:** `test_format_result_errors_empty_on_success`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** Error handling

**Test Class: TestDeterministicOutput (1 test)**
- ✅ **Test:** `test_same_chunks_produce_identical_output`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-1 - Deterministic output

### Integration Tests (5 tests)

**File:** `tests/integration/test_output/test_txt_pipeline.py` (180 lines)

**Test Class: TestEndToEndPipeline (4 tests)**
- ✅ **Test:** `test_complete_pipeline_processing_result_to_txt`
  - **Status:** RED - Full pipeline not integrated
  - **Verifies:** AC-3.5-1, AC-3.5-2 - End-to-end TXT generation

- ✅ **Test:** `test_pipeline_produces_clean_text`
  - **Status:** RED - Full pipeline not integrated
  - **Verifies:** AC-3.5-1 - Clean text in pipeline

- ✅ **Test:** `test_pipeline_delimiter_between_chunks`
  - **Status:** RED - Full pipeline not integrated
  - **Verifies:** AC-3.5-2 - Delimiters in output

- ✅ **Test:** `test_pipeline_metadata_headers_when_enabled`
  - **Status:** RED - Full pipeline not integrated
  - **Verifies:** AC-3.5-3 - Metadata headers

**Test Class: TestLLMUploadReadiness (2 tests)**
- ✅ **Test:** `test_output_ready_for_direct_copy_paste`
  - **Status:** RED - Full pipeline not integrated
  - **Verifies:** AC-3.5-7 - LLM upload readiness (automated)

- ✅ **Test:** `test_output_metadata_provides_context`
  - **Status:** RED - Full pipeline not integrated
  - **Verifies:** AC-3.5-3, AC-3.5-7 - Metadata context

**Test Class: TestOutputOrganization (2 tests)**
- ✅ **Test:** `test_concatenated_single_file_mode`
  - **Status:** RED - Full pipeline not integrated
  - **Verifies:** AC-3.5-4 - Concatenated output

- ✅ **Test:** `test_utf8_sig_encoding_preserved`
  - **Status:** RED - Full pipeline not integrated
  - **Verifies:** AC-3.5-5 - Encoding in pipeline

### Compatibility Tests (3 tests)

**File:** `tests/integration/test_output/test_txt_compatibility.py` (155 lines)

**Test Class: TestPathCompatibility (2 tests)**
- ✅ **Test:** `test_windows_path_handling`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-4 - Windows path support

- ✅ **Test:** `test_unicode_filename_support`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-5 - Unicode in filenames

**Test Class: TestUnicodeCompatibility (2 tests)**
- ✅ **Test:** `test_multilingual_text_preservation`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-5 - Multilingual Unicode

- ✅ **Test:** `test_emoji_preservation`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-5 - Emoji preservation

**Test Class: TestArtifactValidation (1 test)**
- ✅ **Test:** `test_no_formatting_artifacts_comprehensive`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** AC-3.5-6 - Comprehensive artifact check

### Performance Tests (2 tests)

**File:** `tests/performance/test_txt_performance.py` (120 lines)

**Test Class: TestFormattingLatency (2 tests)**
- ✅ **Test:** `test_small_document_formatting_under_1_second`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** Performance baseline (10 chunks < 1s)

- ✅ **Test:** `test_large_document_formatting_under_3_seconds`
  - **Status:** RED - TxtFormatter not implemented
  - **Verifies:** Performance baseline (100 chunks < 3s)

---

## Test Fixtures and Data Factories

### Reusable Fixtures from tests/conftest.py

**From Story 3.4 (available):**
- `sample_processing_result` - ProcessingResult with content blocks
- `sample_content_blocks` - Mixed content blocks (heading, paragraph, table, image)
- `tmp_path` - pytest built-in temporary directory

**New Fixtures in test_txt_formatter.py:**
- `sample_clean_chunk` - Basic chunk with clean text
- `sample_chunk_with_artifacts` - Chunk with markdown/HTML to clean
- `sample_chunk_with_entities` - Chunk with entity tags for metadata headers
- `sample_chunks` - List of multiple chunks for multi-chunk testing
- `txt_formatter` - TxtFormatter with default configuration
- `txt_formatter_with_metadata` - TxtFormatter with metadata enabled
- `txt_formatter_custom_delimiter` - TxtFormatter with custom delimiter

**New Fixtures in test_txt_pipeline.py:**
- `chunking_engine` - ChunkingEngine with default config
- `txt_formatter` - TxtFormatter instance
- `txt_formatter_with_metadata` - TxtFormatter with metadata

**New Fixtures in test_txt_compatibility.py:**
- `chunk_with_unicode` - Chunk with multilingual Unicode text

**New Fixtures in test_txt_performance.py:**
- `small_document_chunks` - 10 chunks for latency testing
- `large_document_chunks` - 100 chunks for stress testing

### Data Patterns

**Chunk Factory Pattern (inline in fixtures):**
```python
def create_chunk(text: str, **overrides) -> Chunk:
    """Create chunk with defaults, allow overrides."""
    chunk_metadata = ChunkMetadata(
        entity_tags=overrides.get('entity_tags', []),
        quality=overrides.get('quality', None),
        # ... defaults
    )
    return Chunk(
        id=overrides.get('id', 'chunk_001'),
        text=text,
        # ... defaults
    )
```

**No external data factories required** - All test data generated inline via fixtures.

---

## Mock Requirements

**No external service mocks required for Story 3.5.**

TxtFormatter is a pure formatter with no external dependencies:
- No API calls
- No database access
- No network operations
- No third-party service integrations

All functionality testable with in-memory data structures.

---

## Required data-testid Attributes

**Not applicable for Story 3.5** - TxtFormatter is backend-only component with no UI elements.

---

## Implementation Checklist

### Task 1: Create TxtFormatter Core Module

**File:** `src/data_extract/output/formatters/txt_formatter.py`

**Tasks to implement:**

- [ ] Create `TxtFormatter` class implementing `BaseFormatter` protocol
- [ ] Add `__init__(self, include_metadata: bool = False, delimiter: str = "━━━ CHUNK {{n}} ━━━")`
- [ ] Implement `format_chunks(self, chunks: Iterator[Chunk], output_path: Path) -> FormatResult`
- [ ] Add `_clean_text(self, text: str) -> str` method for artifact removal
- [ ] Add `_generate_delimiter(self, chunk_number: int) -> str` method
- [ ] Add `_generate_metadata_header(self, chunk: Chunk) -> str` method (optional)
- [ ] Add `_remove_markdown_artifacts(self, text: str) -> str` helper
- [ ] Add `_remove_html_tags(self, text: str) -> str` helper
- [ ] Add `_normalize_whitespace(self, text: str) -> str` helper
- [ ] Use `utf-8-sig` encoding for all file writes
- [ ] Return `FormatResult` with statistics (chunk_count, duration, errors)
- [ ] Run tests: `pytest tests/unit/test_output/test_txt_formatter.py -v`
- [ ] ✅ All unit tests pass (green phase)

**Estimated Effort:** 4-6 hours

---

### Task 2: Wire TxtFormatter into Output Pipeline

**Files to modify:**
- `src/data_extract/output/writer.py` (or equivalent orchestrator)
- `src/data_extract/cli.py` (add `--format txt` flag)

**Tasks to implement:**

- [ ] Register `TxtFormatter` in output writer registry
- [ ] Add CLI flag: `--format txt` (alongside json, csv)
- [ ] Add CLI flag: `--include-metadata` for TXT metadata headers
- [ ] Add CLI flag: `--delimiter` for custom delimiter pattern
- [ ] Wire formatter selection logic: `if format == "txt": use TxtFormatter`
- [ ] Ensure organization strategies work with TXT output (by_document, flat, etc.)
- [ ] Run tests: `pytest tests/integration/test_output/test_txt_pipeline.py -v`
- [ ] ✅ All integration tests pass (green phase)

**Estimated Effort:** 2-3 hours

---

### Task 3: Cross-Platform Compatibility & Encoding

**Files to validate:**
- `src/data_extract/output/formatters/txt_formatter.py`
- Test path handling on Windows (if available)

**Tasks to implement:**

- [ ] Verify UTF-8-sig encoding on Windows systems
- [ ] Test Unicode filename support
- [ ] Verify Path handling (Windows `C:\...`, Unix `/...`)
- [ ] Document newline behavior (LF default, CRLF configurable)
- [ ] Run tests: `pytest tests/integration/test_output/test_txt_compatibility.py -v`
- [ ] ✅ All compatibility tests pass (green phase)

**Estimated Effort:** 1-2 hours

---

### Task 4: Performance Optimization & Validation

**File:** `src/data_extract/output/formatters/txt_formatter.py`

**Tasks to implement:**

- [ ] Profile formatting latency with 10-chunk document
- [ ] Profile formatting latency with 100-chunk document
- [ ] Optimize text cleaning regex patterns (compile once, reuse)
- [ ] Ensure streaming chunk iteration (don't materialize full list unless required)
- [ ] Run tests: `pytest tests/performance/test_txt_performance.py -v`
- [ ] ✅ Performance tests pass (< 1s for 10 chunks, < 3s for 100 chunks)

**Estimated Effort:** 1-2 hours (non-blocking if fails)

---

### Task 5: Documentation & Sample Outputs

**Files to create/update:**
- `docs/json-schema-reference.md` → Add TXT format section
- `docs/examples/sample_output.txt` → Sample TXT output
- `docs/examples/sample_output_with_metadata.txt` → Sample with metadata headers
- `CLAUDE.md` → Update with TXT formatter usage

**Tasks to implement:**

- [ ] Create sample TXT output without metadata
- [ ] Create sample TXT output with metadata headers
- [ ] Document delimiter patterns and customization
- [ ] Document metadata header format
- [ ] Document encoding and newline behavior
- [ ] Update CLAUDE.md with TXT formatter section
- [ ] Add usage examples to documentation

**Estimated Effort:** 2-3 hours

---

### Task 6: Manual UAT for LLM Upload Readiness (AC-3.5-7)

**Critical Manual Validation Required**

**UAT Script:**

```bash
# Generate sample TXT output from real document
pytest tests/integration/test_output/test_txt_pipeline.py::TestEndToEndPipeline::test_complete_pipeline_processing_result_to_txt -v

# Locate generated output file in tmp_path (captured in test output)
# Example: /tmp/pytest-of-user/pytest-123/test_complete_pipeline0/output.txt

# Manual UAT Steps:
# 1. Open generated TXT file
# 2. Copy entire contents (Ctrl+A, Ctrl+C)
# 3. Open ChatGPT (chat.openai.com)
# 4. Paste into prompt field
# 5. Add query: "Summarize the key points from this document"
# 6. Verify: No cleanup required, ChatGPT processes successfully
# 7. Open Claude (claude.ai)
# 8. Paste same content into prompt field
# 9. Add query: "What are the main topics covered?"
# 10. Verify: No cleanup required, Claude processes successfully
```

**Acceptance Criteria:**
- [ ] Content pastes cleanly into ChatGPT (no formatting errors)
- [ ] ChatGPT processes content without errors
- [ ] Content pastes cleanly into Claude (no formatting errors)
- [ ] Claude processes content without errors
- [ ] No manual cleanup required (no JSON braces, HTML tags, ANSI codes visible)
- [ ] Delimiters clearly separate chunks for LLM understanding
- [ ] Document UAT results in `docs/uat/3.5-llm-upload-validation.md`

**Estimated Effort:** 30 minutes

---

## Running Tests

```bash
# Run all Story 3.5 tests
pytest tests/unit/test_output/test_txt_formatter.py tests/integration/test_output/test_txt_pipeline.py tests/integration/test_output/test_txt_compatibility.py -v

# Run specific test file
pytest tests/unit/test_output/test_txt_formatter.py -v

# Run specific test class
pytest tests/unit/test_output/test_txt_formatter.py::TestTextCleaning -v

# Run specific test
pytest tests/unit/test_output/test_txt_formatter.py::TestTextCleaning::test_clean_text_preserves_paragraph_spacing -v

# Run with coverage
pytest tests/unit/test_output/test_txt_formatter.py --cov=src/data_extract/output/formatters/txt_formatter --cov-report=html

# Run performance tests (non-blocking)
pytest tests/performance/test_txt_performance.py -v

# Run integration tests only
pytest tests/integration/test_output/test_txt_pipeline.py tests/integration/test_output/test_txt_compatibility.py -v

# Run all output tests (including JSON from 3.4)
pytest tests/unit/test_output/ tests/integration/test_output/ -v

# Debug mode (drop to pdb on failure)
pytest tests/unit/test_output/test_txt_formatter.py --pdb
```

---

## Red-Green-Refactor Workflow

### RED Phase (Complete) ✅

**TEA Agent Responsibilities:**

- ✅ All 24 tests written and failing (14 unit, 5 integration, 3 compatibility, 2 performance)
- ✅ Fixtures created with reusable chunk patterns
- ✅ No mock requirements (pure formatter, no external deps)
- ✅ Implementation checklist created with 6 tasks
- ✅ Manual UAT script for LLM upload validation

**Verification:**

- All tests run and fail as expected (TxtFormatter not implemented)
- Failure messages are clear: `ImportError: cannot import name 'TxtFormatter'`
- Tests fail due to missing implementation, not test bugs

---

### GREEN Phase (DEV Team - Next Steps)

**DEV Agent Responsibilities:**

1. **Start with Task 1** - Create TxtFormatter core module
2. **Run unit tests frequently** - Immediate feedback on implementation
3. **Implement one feature at a time** - Text cleaning → Delimiters → Metadata → Encoding
4. **Check off tasks** in implementation checklist as you complete them
5. **Move to Task 2** - Wire into pipeline when unit tests pass
6. **Run integration tests** - Verify end-to-end behavior
7. **Complete Tasks 3-4** - Compatibility and performance
8. **Document in Task 5** - Create samples and update docs
9. **Execute Task 6 UAT** - Manual LLM upload validation

**Key Principles:**

- One test at a time (don't try to fix all at once)
- Minimal implementation (don't over-engineer)
- Run tests frequently (immediate feedback loop)
- Follow BaseFormatter protocol exactly (match JsonFormatter patterns)

**Progress Tracking:**

- Check off tasks as you complete them
- Share progress in daily standup
- Mark story as IN PROGRESS in `docs/sprint-status.yaml`

---

### REFACTOR Phase (DEV Team - After All Tests Pass)

**DEV Agent Responsibilities:**

1. **Verify all tests pass** (24/24 automated tests green)
2. **Review code for quality** - Readability, maintainability, DRY principles
3. **Extract duplications** - Text cleaning helpers could be shared utilities
4. **Optimize performance** - Regex compilation, string operations
5. **Ensure tests still pass** after each refactor
6. **Run pre-commit hooks** - `pre-commit run --all-files`
7. **Update documentation** if API contracts change

**Key Principles:**

- Tests provide safety net (refactor with confidence)
- Make small refactors (easier to debug if tests fail)
- Run tests after each change
- Don't change test behavior (only implementation)

**Completion:**

- All 24 automated tests pass
- Manual UAT for AC-3.5-7 completed and documented
- Code quality meets team standards (black, ruff, mypy pass)
- No duplications or code smells
- Performance baselines met (<1s small docs, <3s large docs)
- Ready for code review and story approval

---

## Next Steps

1. **Review this checklist** with team in standup or planning
2. **Run failing tests** to confirm RED phase: `pytest tests/unit/test_output/test_txt_formatter.py -v`
3. **Begin implementation** using implementation checklist (Task 1: Create TxtFormatter)
4. **Work one test class at a time** - Start with `TestTxtFormatterCreation`
5. **Share progress** in daily standup
6. **When all automated tests pass**, execute manual UAT (Task 6)
7. **When UAT complete**, run `/bmad:bmm:workflows:story-done 3.5` to mark story DONE

---

## Test Coverage Mapping

| Acceptance Criterion | Unit Tests | Integration Tests | Manual UAT |
|---------------------|------------|-------------------|------------|
| AC-3.5-1: Clean text | 6 tests | 1 test | Yes (visual check) |
| AC-3.5-2: Delimiters | 4 tests | 1 test | No |
| AC-3.5-3: Metadata | 7 tests | 2 tests | Yes (format check) |
| AC-3.5-4: Organization | 0 tests | 2 tests | Yes (file structure) |
| AC-3.5-5: Encoding | 2 tests | 4 tests | No |
| AC-3.5-6: Artifacts | 3 tests | 2 tests | Yes (visual check) |
| AC-3.5-7: LLM Ready | 0 tests | 2 tests | Yes (critical) |

**Total Coverage:**
- **Automated Tests:** 22 tests (14 unit + 5 integration + 3 compatibility)
- **Performance Tests:** 2 tests (non-blocking)
- **Manual UAT:** 1 critical validation (LLM upload)
- **Total Test Scenarios:** 25

**Coverage Assessment:**
- All 7 ACs have automated test coverage
- 4 ACs require manual UAT validation (AC-3.5-1, 3, 4, 6, 7)
- AC-3.5-7 (LLM Upload) is **critical** and requires hands-on validation
- Performance tests are **non-blocking** (won't block story if they fail, but should pass)

---

## Knowledge Base References Applied

This ATDD workflow consulted the following BMad TEA knowledge fragments:

- **fixture-architecture.md** - Fixture patterns with setup/teardown (pytest fixture composition)
- **test-quality.md** - Given-When-Then structure, one assertion per test, determinism
- **test-levels-framework.md** - Unit vs Integration test level selection
- **component-tdd.md** - Red-green-refactor workflow principles

**Story 3.4 patterns reused:**
- JsonFormatter test structure (unit + integration + compatibility + performance)
- Chunk fixture patterns (sample_enriched_chunk, sample_chunks)
- BaseFormatter protocol compliance testing
- FormatResult validation patterns

---

## Notes

### Reuse from Story 3.4

- **Fixture Patterns**: Story 3.4 established chunk fixture patterns - reused for TXT tests
- **Test Structure**: Mirror JsonFormatter test organization (4 test files: unit, integration, compatibility, performance)
- **Encoding Patterns**: UTF-8-sig encoding approach matches JsonFormatter (Windows BOM compatibility)
- **BaseFormatter Protocol**: TxtFormatter must follow same contract as JsonFormatter

### Outstanding Action Items from Story 3.4

Story 3.4 has an outstanding action item for integration test encoding fixes. Story 3.5 tests use `encoding="utf-8-sig"` correctly to prevent recurrence.

### Test Execution Order Recommendation

1. **Start with unit tests** - Fast feedback, isolated failures
2. **Move to integration tests** - Validate pipeline integration
3. **Run compatibility tests** - Platform-specific validation
4. **Run performance tests last** - Non-blocking, optimization phase

### Windows-Specific Testing

If developing on Windows:
- UTF-8-sig encoding automatically adds BOM
- Test `test_utf8_sig_encoding_with_bom` will pass automatically
- Verify path handling with `C:\` style paths

If developing on Linux/Mac:
- UTF-8-sig encoding must be explicitly set in file writes
- Test with Windows path mocking or skip platform-specific tests
- Document behavior for Windows users

---

## Contact

**Questions or Issues?**

- Ask in team standup
- Refer to `docs/tech-spec-epic-3.md` for Story 3.5 specification
- Refer to `tests/unit/test_output/test_json_formatter.py` for reference patterns
- Consult `src/data_extract/output/formatters/json_formatter.py` for BaseFormatter implementation example

---

**Generated by BMad TEA Agent (Murat)** - 2025-11-15

**Total Test Scenarios:** 25 (22 automated + 2 performance + 1 manual UAT)
**Estimated Implementation Effort:** 10-16 hours + 30 min UAT
**Story Status:** Ready for Development (RED phase verified)
