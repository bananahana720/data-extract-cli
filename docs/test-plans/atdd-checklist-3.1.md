# ATDD Checklist - Story 3.1: Semantic Boundary-Aware Chunking Engine

**Status:** RED Phase Complete ✅
**Generated:** 2025-11-13
**Story:** 3.1 - Semantic Boundary-Aware Chunking Engine
**Epic:** 3 - Chunk & Output Stages

---

## Story Summary

**As a** data scientist preparing enterprise documents for RAG workflows
**I want** text chunked at semantic boundaries (sentences, paragraphs, sections)
**So that** LLM retrievals maintain complete context without mid-sentence splits

**Business Value:**
- Prevents incomplete context causing LLM hallucinations
- Enables deterministic, reproducible chunking for audit trails
- Configurable chunk sizing for different RAG systems
- Preserves document structure for semantic organization

---

## Acceptance Criteria Breakdown

### AC-3.1-1: Chunks Never Split Mid-Sentence (P0 - Critical) 🔴

**Tests Created:**
- `tests/unit/test_chunk/test_engine.py::test_chunk_preserves_sentence_boundaries`
- `tests/unit/test_chunk/test_sentence_boundaries.py::TestVeryLongSentences`

**Coverage:** Unit (mocked SentenceSegmenter) + Integration (real spaCy)

**Status:** Tests written, currently FAILING (missing implementation)

---

### AC-3.1-2: Section Boundaries Respected (P0) 🔴

**Tests Created:**
- `tests/integration/test_chunk/test_chunking_pipeline.py::test_multi_section_document`

**Coverage:** Integration tests with multi-section documents

**Status:** Tests written, currently FAILING (missing implementation)

---

### AC-3.1-3: Chunk Size Configurable (P1) 🔴

**Tests Created:**
- `tests/unit/test_chunk/test_engine.py::TestChunkingEngineInitialization`
- `tests/unit/test_chunk/test_configuration.py::TestChunkSizeValidation`

**Coverage:** Unit tests (128-2048 range, edge cases)

**Status:** Tests written, currently FAILING (missing implementation)

---

### AC-3.1-4: Chunk Overlap Configurable (P1) 🔴

**Tests Created:**
- `tests/unit/test_chunk/test_engine.py::test_sliding_window_with_overlap`
- `tests/unit/test_chunk/test_configuration.py::TestOverlapValidation`

**Coverage:** Unit tests (0.0-0.5 range, sliding window logic)

**Status:** Tests written, currently FAILING (missing implementation)

---

### AC-3.1-5: Sentence Tokenization Uses spaCy (P0) 🔴

**Tests Created:**
- `tests/integration/test_chunk/test_chunking_pipeline.py::test_real_spacy_integration`

**Coverage:** Integration tests with real SentenceSegmenter

**Status:** Tests written, currently FAILING (missing implementation)

---

### AC-3.1-6: Edge Cases Handled (P0) 🔴

**Tests Created:**
- `tests/unit/test_chunk/test_sentence_boundaries.py::TestVeryLongSentences`
- `tests/unit/test_chunk/test_sentence_boundaries.py::TestMicroSentences`
- `tests/unit/test_chunk/test_sentence_boundaries.py::TestNoPunctuation`
- `tests/unit/test_chunk/test_sentence_boundaries.py::TestEmptyDocuments`
- `tests/unit/test_chunk/test_sentence_boundaries.py::TestShortSections`

**Coverage:** Unit tests for all edge cases

**Status:** Tests written, currently FAILING (missing implementation)

---

### AC-3.1-7: Chunking is Deterministic (P0 - Critical) 🔴

**Tests Created:**
- `tests/unit/test_chunk/test_determinism.py::test_same_input_produces_identical_chunks_10_runs`
- `tests/unit/test_chunk/test_determinism.py::test_chunk_id_no_timestamps`

**Coverage:** Unit tests (10-run comparison, ID reproducibility)

**Status:** Tests written, currently FAILING (missing implementation)

---

## Test Files Created

### Unit Tests (Primary - 70% coverage target)

```
tests/unit/test_chunk/
├── __init__.py
├── test_engine.py                   # 10 tests - Core ChunkingEngine logic
├── test_sentence_boundaries.py      # 8 tests - Edge case handling
├── test_configuration.py            # 3 tests - Config validation
└── test_determinism.py              # 3 tests - Reproducibility
```

**Total Unit Tests:** 24 tests

### Integration Tests (25% coverage target)

```
tests/integration/test_chunk/
├── __init__.py
└── test_chunking_pipeline.py        # 2 tests - Epic 2 → Epic 3 pipeline
```

**Total Integration Tests:** 2 tests

### Performance Tests (5% coverage target)

**Not yet created** - Will be needed for:
- `tests/performance/test_chunk/test_chunking_latency.py` (NFR-P3: <2 sec per 10k words)
- `tests/performance/test_chunk/test_memory_efficiency.py` (NFR-P2-E3: ≤500MB)

---

## Data Infrastructure

### Fixtures Needed

**Location:** `tests/fixtures/normalized_results/`

**Required Fixtures:**
- `single_sentence.json` - Minimal document (1 sentence)
- `multi_sentence.json` - Standard document (10-20 sentences)
- `multi_section.json` - Document with section structure
- `very_long_sentence.json` - Edge case (>512 token sentence)
- `micro_sentences.json` - Edge case (<10 char sentences)
- `no_punctuation.json` - Edge case (text without punctuation)
- `empty_document.json` - Edge case (empty normalized text)

**Format Example:**
```json
{
  "id": "fixture_001",
  "text": "Sentence 1. Sentence 2. Sentence 3.",
  "entities": [],
  "metadata": {
    "source_file": "test.pdf",
    "source_hash": "abc123"
  },
  "structure": {}
}
```

### Mock Requirements

**SentenceSegmenter Mock** (for unit tests):
```python
from unittest.mock import Mock

mock_segmenter = Mock()
mock_segmenter.segment.return_value = ["Sentence 1.", "Sentence 2."]
```

**Real SentenceSegmenter** (for integration tests):
```python
from data_extract.normalize.sentence_segmenter import SentenceSegmenter

segmenter = SentenceSegmenter()  # Lazy-loads en_core_web_md
```

### No External Service Mocks Needed

Story 3.1 is purely internal pipeline logic - no external API calls or services to mock.

---

## Required data-testid Attributes

**N/A** - Story 3.1 has no UI components. Epic 5 (CLI) will add data-testid for CLI testing.

---

## Implementation Checklist

### Phase 1: Core Models (Task 2)

- [ ] Create `src/data_extract/chunk/__init__.py`
- [ ] Create `src/data_extract/chunk/models.py`
  - [ ] Implement `Chunk` dataclass (frozen=True)
    - Fields: `id`, `text`, `document_id`, `position_index`, `token_count`, `word_count`, `entities`, `section_context`, `quality_score`, `readability_scores`, `metadata`
    - Methods: `to_dict()`, `to_csv_row()`, `to_txt()`
  - [ ] Implement `ChunkMetadata` dataclass (frozen=True)
    - Fields: `chunk_id`, `source_file`, `source_hash`, `document_type`, `section_context`, `position_index`, `entity_tags`, `quality`, `word_count`, `token_count`, `created_at`, `processing_version`
  - [ ] Implement `QualityScore` dataclass (frozen=True)
    - Fields: `readability_score`, `coherence_score`, `completeness_score` (defaults: 0.0)
  - [ ] Add Pydantic v2 validation
  - [ ] Add type hints and docstrings
- [ ] Run: `pytest tests/unit/test_chunk/test_engine.py::test_metadata_population`
- [ ] ✅ Tests pass (models complete)

### Phase 2: ChunkingEngine Configuration (Task 3)

- [ ] Create `src/data_extract/chunk/engine.py`
- [ ] Implement `ChunkingEngine.__init__(segmenter, chunk_size=512, overlap_pct=0.15)`
  - [ ] Store segmenter reference
  - [ ] Validate chunk_size (range: 128-2048, warn on extremes)
  - [ ] Validate overlap_pct (range: 0.0-0.5, warn if > 0.5)
  - [ ] Calculate `overlap_tokens = int(chunk_size * overlap_pct)`
  - [ ] Add configuration logging
- [ ] Run: `pytest tests/unit/test_chunk/test_engine.py::TestChunkingEngineInitialization`
- [ ] Run: `pytest tests/unit/test_chunk/test_configuration.py`
- [ ] ✅ Configuration tests pass

### Phase 3: Basic Chunking Algorithm (Task 1)

- [ ] Implement `ChunkingEngine.process(document: Document, context: ProcessingContext) -> Iterator[Chunk]`
  - [ ] Extract `document.text`
  - [ ] Call `segmenter.segment(text)` to get sentence list
  - [ ] Implement sliding window with overlap
    - Start at sentence 0
    - Accumulate sentences until chunk_size reached
    - Yield chunk
    - Move window by (chunk_size - overlap_tokens)
    - Repeat until end
  - [ ] Generate chunk_id: `{source_file_stem}_chunk_{position:03d}`
  - [ ] Populate ChunkMetadata fields
  - [ ] Calculate word_count and token_count (token_count = len(text) // 4)
  - [ ] Use `yield` for streaming (not list)
- [ ] Run: `pytest tests/unit/test_chunk/test_engine.py::TestChunkingEngineBasicOperation`
- [ ] ✅ Basic chunking tests pass

### Phase 4: Sentence Boundary Preservation (Task 1, AC-3.1-1)

- [ ] Ensure chunking never splits mid-sentence
  - [ ] Always chunk at sentence boundaries
  - [ ] Never truncate sentences
- [ ] Run: `pytest tests/unit/test_chunk/test_engine.py::test_chunk_preserves_sentence_boundaries`
- [ ] ✅ Sentence boundary tests pass

### Phase 5: Edge Case Handling (Task 4, AC-3.1-6)

- [ ] Handle very long sentences (>chunk_size)
  - [ ] If sentence > chunk_size: yield entire sentence as single chunk
  - [ ] Log warning with sentence length
- [ ] Handle micro-sentences (<10 chars)
  - [ ] Combine with adjacent sentences until chunk_size reached
- [ ] Handle short sections (<chunk_size)
  - [ ] Section becomes single chunk, no artificial splitting
- [ ] Handle empty documents
  - [ ] Return empty iterator (no chunks)
  - [ ] Log info message
- [ ] Handle no punctuation
  - [ ] Defer to spaCy statistical model
- [ ] Run: `pytest tests/unit/test_chunk/test_sentence_boundaries.py`
- [ ] ✅ Edge case tests pass

### Phase 6: Section Boundary Detection (AC-3.1-2)

- [ ] Detect section boundaries from `document.structure`
  - [ ] Parse section markers (headings, page breaks)
  - [ ] Prefer chunk splits at section boundaries when possible
  - [ ] Preserve section context in `ChunkMetadata.section_context`
- [ ] Run: `pytest tests/integration/test_chunk/test_chunking_pipeline.py::test_multi_section_document`
- [ ] ✅ Section boundary tests pass

### Phase 7: Determinism Validation (AC-3.1-7)

- [ ] Verify no timestamps in chunk IDs
- [ ] Verify no random number generators
- [ ] Embed configuration in metadata.processing_version
- [ ] Run: `pytest tests/unit/test_chunk/test_determinism.py`
- [ ] ✅ Determinism tests pass (10 runs identical)

### Phase 8: Integration Testing

- [ ] Implement PipelineStage[Document, List[Chunk]] protocol
- [ ] Test with real SentenceSegmenter
- [ ] Test Epic 2 → Epic 3 pipeline
- [ ] Run: `pytest tests/integration/test_chunk/`
- [ ] ✅ Integration tests pass

### Phase 9: Performance Validation

- [ ] Create performance test fixtures
- [ ] Implement NFR-P3 test (<2 sec per 10k words)
- [ ] Implement NFR-P2-E3 test (≤500MB memory)
- [ ] Run: `pytest tests/performance/test_chunk/`
- [ ] ✅ Performance tests pass

### Phase 10: Documentation and Quality Gates

- [ ] Update `CLAUDE.md` (Epic 3 section, chunking marker)
- [ ] Update `docs/architecture.md` (ADR-011)
- [ ] Create `docs/performance-baselines-epic-3.md`
- [ ] Run quality gates:
  - [ ] `black src/ tests/` → 0 violations
  - [ ] `ruff check src/ tests/` → 0 violations
  - [ ] `mypy src/data_extract/` → 0 violations
  - [ ] `pytest -m unit` → All pass
  - [ ] `pytest -m integration` → All pass
- [ ] ✅ All quality gates pass

---

## Red-Green-Refactor Workflow

### ✅ RED Phase (Complete - TEA Responsibility)

- ✅ All tests written and failing
- ✅ Test infrastructure created (fixtures needed, documented)
- ✅ Mock requirements documented
- ✅ 26 total tests in RED phase

### 🔄 GREEN Phase (DEV Team - Next Steps)

**Workflow:**
1. Pick one failing test from implementation checklist
2. Implement minimal code to make it pass
3. Run test: `pytest tests/unit/test_chunk/test_engine.py::test_name -v`
4. Verify test passes (green)
5. Move to next test
6. Repeat until all tests pass

**Recommended Order:**
1. Models (Phase 1) → Foundation
2. Configuration (Phase 2) → Initialization
3. Basic chunking (Phase 3) → Core logic
4. Sentence boundaries (Phase 4) → Critical AC
5. Edge cases (Phase 5) → Robustness
6. Section boundaries (Phase 6) → Advanced feature
7. Determinism (Phase 7) → Critical AC
8. Integration (Phase 8) → Pipeline validation
9. Performance (Phase 9) → NFR validation
10. Documentation (Phase 10) → Quality gates

### ⚪ REFACTOR Phase (DEV Team - After GREEN)

**When:** All tests passing (green)

**Activities:**
1. Improve code quality (extract methods, reduce complexity)
2. Optimize performance (profile first, optimize second)
3. Extract duplications (DRY principle)
4. Add docstrings and comments
5. Ensure tests still pass after each refactor

**Safety Net:** Tests provide confidence for refactoring

---

## Running Tests

### Run All Failing Tests

```bash
# All chunking tests
pytest tests/unit/test_chunk/ tests/integration/test_chunk/ -v

# Expected: All tests FAIL (missing implementation)
```

### Run Specific Test File

```bash
# Unit tests for ChunkingEngine core
pytest tests/unit/test_chunk/test_engine.py -v

# Sentence boundary edge cases
pytest tests/unit/test_chunk/test_sentence_boundaries.py -v

# Configuration validation
pytest tests/unit/test_chunk/test_configuration.py -v

# Determinism tests
pytest tests/unit/test_chunk/test_determinism.py -v

# Integration tests
pytest tests/integration/test_chunk/test_chunking_pipeline.py -v
```

### Run Tests by Marker

```bash
# All unit tests
pytest -m unit -v

# All integration tests
pytest -m integration -v

# All chunking tests
pytest -m chunking -v
```

### Debug Specific Test

```bash
# Run with debugger (drops to pdb on failure)
pytest tests/unit/test_chunk/test_engine.py::test_chunk_preserves_sentence_boundaries --pdb

# Verbose with local variables
pytest tests/unit/test_chunk/test_engine.py -vv --showlocals

# Show print statements
pytest tests/unit/test_chunk/test_engine.py -s
```

---

## Output Summary

### Tests in RED Phase ✅

**Story:** 3.1 - Semantic Boundary-Aware Chunking Engine
**Primary Test Level:** Unit (70% coverage)

### Failing Tests Created

- **Unit tests:** 24 tests in 4 files
  - `test_engine.py` (10 tests)
  - `test_sentence_boundaries.py` (8 tests)
  - `test_configuration.py` (3 tests)
  - `test_determinism.py` (3 tests)

- **Integration tests:** 2 tests in 1 file
  - `test_chunking_pipeline.py` (2 tests)

- **Performance tests:** 0 tests (to be created in Phase 9)

**Total Tests:** 26 tests

### Supporting Infrastructure

- **Fixtures:** 7 fixtures documented (to be created by DEV)
- **Mocks:** SentenceSegmenter mock pattern provided
- **Mock requirements:** None (no external services)

### Implementation Checklist

- **Total tasks:** 10 phases (models → documentation)
- **Estimated effort:** 16-24 hours (2-3 days for experienced dev)

### Required data-testid Attributes

- **None** - Story 3.1 is internal pipeline (no UI)

---

## Next Steps for DEV Team

1. **Run failing tests:** `pytest tests/unit/test_chunk/ tests/integration/test_chunk/ -v`
2. **Verify RED phase:** All 26 tests should FAIL (missing implementation)
3. **Review implementation checklist** (10 phases above)
4. **Start Phase 1:** Create models (`src/data_extract/chunk/models.py`)
5. **Follow TDD cycle:** One test at a time (RED → GREEN)
6. **Run quality gates:** Black, Ruff, Mypy before each commit
7. **Share progress:** Daily standup updates on phase completion

---

## Knowledge Base References Applied

### Core Patterns

- **Test Quality Principles** - Deterministic tests, explicit assertions, atomic tests
- **Data Factory Patterns** - Not needed (internal pipeline, no test data generation)
- **Fixture Architecture** - pytest fixtures for test documents, mock objects
- **Test Healing Patterns** - Edge case handling, graceful degradation

### Testing Best Practices

- **Given-When-Then** structure in all tests
- **One assertion per test** (atomic test design)
- **Mock external dependencies** (SentenceSegmenter mocked in unit tests)
- **Real integration tests** (SentenceSegmenter real in integration tests)

---

## Validation Checklist

After completing implementation, verify:

- [ ] Story acceptance criteria analyzed and mapped to tests ✅
- [ ] Appropriate test levels selected (Unit, Integration, Performance) ✅
- [ ] All tests written in Given-When-Then format ✅
- [ ] All tests fail initially (RED phase verified) ✅
- [ ] Data infrastructure documented (fixtures, mocks) ✅
- [ ] Implementation checklist created with clear tasks ✅
- [ ] Red-green-refactor workflow documented ✅
- [ ] Execution commands provided ✅
- [ ] Output file created and formatted correctly ✅

---

**Output File:** `docs/atdd-checklist-3.1.md`

**Generated by:** Murat (Master Test Architect)
**Workflow:** BMAD ATDD Workflow v4.0
**Date:** 2025-11-13

🧪 **All tests in RED phase. Ready for implementation.** 🔴

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
