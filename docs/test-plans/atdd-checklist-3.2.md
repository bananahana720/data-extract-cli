# ATDD Checklist - Epic 3, Story 3.2: Entity-Aware Chunking with Section Boundary Detection

**Date:** 2025-11-14
**Author:** Andrew
**Primary Test Level:** Integration
**Story Status:** ready-for-dev

---

## Story Summary

Extends Epic 3's chunking capabilities with entity-aware boundary detection and section structure preservation. Builds on Story 3.1's semantic sentence-boundary chunking by adding intelligence to avoid splitting entity definitions and respect document organizational structure.

**As a** data scientist preparing enterprise documents for RAG workflows
**I want** chunks to preserve entity context and align with document sections
**So that** LLM retrievals maintain complete entity definitions and structural coherence without fragmenting critical information

---

## Acceptance Criteria

This story has **8 testable acceptance criteria** requiring comprehensive test coverage:

### P0 (Critical) - UAT Required

1. **AC-3.2-1:** Entity Mentions Kept Within Single Chunks When Possible
   - Target: >95% of entities remain intact (not split)
   - EntityPreserver analyzes boundaries before chunking
   - Chunk splits prefer gaps between entities

2. **AC-3.2-2:** Entities Split Across Chunks Noted in Metadata
   - Partial entity flag: `is_partial=True` in ChunkMetadata
   - Continuation flags: "entity_continued_from_previous" or "entity_continues_in_next"
   - Cross-references to adjacent chunk IDs

3. **AC-3.2-3:** Relationship Context Preserved
   - Detect patterns: "RISK-001 mitigated by CTRL-042"
   - Relationship triples: (entity1, relation, entity2)
   - Both entities in same chunk when span < chunk_size

4. **AC-3.2-4:** Chunk Boundaries Avoid Splitting Entity Definitions
   - Multi-sentence entity definitions kept together
   - If definition > chunk_size, becomes single chunk with warning

5. **AC-3.2-7:** Section Boundaries Respected (Deferred from AC-3.1-2)
   - Detects section markers (headings, page breaks, structural patterns)
   - Section context preserved in ChunkMetadata.section_context
   - Graceful degradation if no sections detected

6. **AC-3.2-8:** Determinism Maintained
   - Same input → identical chunks (byte-for-byte)
   - 100% reproducibility (10 runs, diff comparison)

### P1 (Important) - Unit Tests Sufficient

7. **AC-3.2-5:** Cross-References Maintained with Entity IDs
   - Entity IDs enable cross-chunk lookups
   - Duplicate mentions deduplicated per chunk

8. **AC-3.2-6:** Entity Tags in Chunk Metadata
   - ChunkMetadata.entity_tags populated with EntityReference objects
   - JSON serializable for output formats

---

## Failing Tests Created (RED Phase)

### Unit Tests (14 tests)

#### File: `tests/unit/test_chunk/test_entity_preserver.py` (NEW - ~350 lines)

**Purpose:** Test EntityPreserver component in isolation

**Tests:**

- ✅ **test_entity_reference_creation**
  - **Status:** RED - EntityReference class not yet implemented
  - **Verifies:** AC-3.2-6 - EntityReference dataclass with required fields
  - **Given:** Entity data with type, id, positions, partial flag
  - **When:** EntityReference instantiated
  - **Then:** All fields populated correctly, frozen=True enforced

- ✅ **test_entity_reference_to_dict**
  - **Status:** RED - to_dict() method not yet implemented
  - **Verifies:** AC-3.2-6 - JSON serialization
  - **Given:** EntityReference with all fields
  - **When:** to_dict() called
  - **Then:** Returns dict with all fields, JSON serializable

- ✅ **test_analyze_entities_sorting**
  - **Status:** RED - EntityPreserver.analyze_entities() not yet implemented
  - **Verifies:** AC-3.2-8 - Determinism (entities sorted by start_pos)
  - **Given:** Entities in random order
  - **When:** analyze_entities() called
  - **Then:** Returns EntityReferences sorted by start_pos

- ✅ **test_analyze_entities_context_snippets**
  - **Status:** RED - Context snippet extraction not implemented
  - **Verifies:** AC-3.2-6 - context_snippet field populated
  - **Given:** Entity at various positions in text
  - **When:** analyze_entities() called
  - **Then:** context_snippet contains ±20 chars around entity

- ✅ **test_find_entity_gaps**
  - **Status:** RED - EntityPreserver.find_entity_gaps() not yet implemented
  - **Verifies:** AC-3.2-1 - Safe split zones identification
  - **Given:** Text with multiple entities
  - **When:** find_entity_gaps() called
  - **Then:** Returns character offsets between entities (not within)

- ✅ **test_find_entity_gaps_no_entities**
  - **Status:** RED - Edge case handling not implemented
  - **Verifies:** AC-3.2-1 - Graceful degradation
  - **Given:** Text with no entities
  - **When:** find_entity_gaps() called
  - **Then:** Returns empty list (no gaps to find)

- ✅ **test_detect_entity_relationships_mitigated_by**
  - **Status:** RED - EntityPreserver.detect_entity_relationships() not yet implemented
  - **Verifies:** AC-3.2-3 - Relationship pattern detection
  - **Given:** Text with "RISK-001 mitigated by CTRL-042" pattern
  - **When:** detect_entity_relationships() called
  - **Then:** Returns triple ("RISK-001", "mitigated_by", "CTRL-042")

- ✅ **test_detect_entity_relationships_multiple_patterns**
  - **Status:** RED - Multiple relationship types not implemented
  - **Verifies:** AC-3.2-3 - Various relationship keywords
  - **Given:** Text with "maps to", "implements", "addresses" patterns
  - **When:** detect_entity_relationships() called
  - **Then:** Returns triples for all detected relationships

- ✅ **test_overlapping_entities_handling**
  - **Status:** RED - Edge case not handled
  - **Verifies:** AC-3.2-1 - Overlapping entity spans
  - **Given:** Entities with overlapping start/end positions
  - **When:** find_entity_gaps() called
  - **Then:** Handles gracefully (prefer earlier entity or flag both)

- ✅ **test_entities_at_document_boundaries**
  - **Status:** RED - Edge case not handled
  - **Verifies:** AC-3.2-1 - Entities at start/end of document
  - **Given:** Entity at position 0 or end of text
  - **When:** analyze_entities() called
  - **Then:** Context snippets truncated appropriately (no negative indices)

**Coverage Target:** >90% for entity_preserver.py module

---

#### File: `tests/unit/test_chunk/test_section_detection.py` (NEW - ~300 lines)

**Purpose:** Test section boundary detection logic (implements deferred AC-3.1-2)

**Tests:**

- ✅ **test_detect_section_boundaries_with_heading_blocks**
  - **Status:** RED - ChunkingEngine._detect_section_boundaries() returns empty list (placeholder)
  - **Verifies:** AC-3.2-7 - ContentBlock type="heading" detection
  - **Given:** ProcessingResult with ContentBlocks including heading blocks
  - **When:** _detect_section_boundaries() called
  - **Then:** Returns sentence indices where sections begin

- ✅ **test_detect_section_boundaries_with_page_breaks**
  - **Status:** RED - Page break marker detection not implemented
  - **Verifies:** AC-3.2-7 - Page break markers from PDF extraction
  - **Given:** ProcessingResult with page_break markers in metadata
  - **When:** _detect_section_boundaries() called
  - **Then:** Returns indices at page break positions

- ✅ **test_detect_section_boundaries_with_regex_patterns**
  - **Status:** RED - Regex pattern detection not implemented
  - **Verifies:** AC-3.2-7 - Structural heading patterns
  - **Given:** Text with "### Title" and "1.2.3 Heading" patterns
  - **When:** _detect_section_boundaries() called
  - **Then:** Detects patterns and returns section start indices

- ✅ **test_section_hierarchy_building**
  - **Status:** RED - Section hierarchy logic not implemented
  - **Verifies:** AC-3.2-7 - Parent-child section relationships
  - **Given:** Nested sections (level 1, 2, 3 headings)
  - **When:** Section hierarchy built
  - **Then:** Breadcrumb format: "Parent > Child > Grandchild"

**Coverage Target:** >90% for section detection logic

---

### Integration Tests (8 tests)

#### File: `tests/integration/test_chunk/test_entity_aware_chunking.py` (NEW - ~450 lines)

**Purpose:** End-to-end entity-aware chunking with real documents

**Tests:**

- ✅ **test_entity_preservation_rate_exceeds_95_percent**
  - **Status:** RED - EntityPreserver not integrated into ChunkingEngine
  - **Verifies:** AC-3.2-1 (CRITICAL) - >95% entities intact
  - **Given:** Real risk register document with 100+ entities
  - **When:** ChunkingEngine.chunk_document() called
  - **Then:** Measure entities intact vs. split, assert >95% intact

- ✅ **test_partial_entity_metadata_flagging**
  - **Status:** RED - Partial entity handling not implemented
  - **Verifies:** AC-3.2-2 - is_partial=True for split entities
  - **Given:** Document with very large entity (>chunk_size)
  - **When:** Entity unavoidably split across chunks
  - **Then:** Both chunks have is_partial=True, continuation flags set

- ✅ **test_relationship_context_preserved**
  - **Status:** RED - Relationship detection not integrated
  - **Verifies:** AC-3.2-3 (CRITICAL) - Risk-control relationships
  - **Given:** Document with "RISK-001 mitigated by CTRL-042" patterns
  - **When:** chunk_document() called
  - **Then:** Relationship triples in ChunkMetadata, both entities in same chunk

- ✅ **test_multi_sentence_entity_definitions_kept_together**
  - **Status:** RED - Entity definition boundary logic not implemented
  - **Verifies:** AC-3.2-4 - Multi-sentence entity definitions
  - **Given:** Document with entity spanning 3 sentences
  - **When:** chunk_document() called
  - **Then:** All 3 sentences in same chunk, boundary after definition complete

- ✅ **test_entity_ids_enable_cross_chunk_search**
  - **Status:** RED - Entity ID propagation not implemented
  - **Verifies:** AC-3.2-5 - Cross-chunk entity lookups
  - **Given:** Entity "RISK-2024-001" mentioned in multiple chunks
  - **When:** Search all chunks for entity_id="RISK-2024-001"
  - **Then:** Returns all chunks containing that entity

- ✅ **test_entity_tags_json_serialization**
  - **Status:** RED - Chunk.to_dict() doesn't serialize entity_tags yet
  - **Verifies:** AC-3.2-6 - JSON serialization for output formats
  - **Given:** Chunk with entity_tags populated
  - **When:** Chunk.to_dict() called
  - **Then:** entity_tags converted to list of dicts, JSON serializable

- ✅ **test_entity_aware_with_multiple_entity_types**
  - **Status:** RED - Mixed entity type handling not tested
  - **Verifies:** AC-3.2-1, AC-3.2-6 - Various entity types
  - **Given:** Document with risks, controls, policies, processes
  - **When:** chunk_document() called
  - **Then:** All entity types preserved, tagged correctly in metadata

- ✅ **test_large_entity_exceeding_chunk_size**
  - **Status:** RED - Oversized entity handling not implemented
  - **Verifies:** AC-3.2-1, AC-3.2-4 - Graceful handling of large entities
  - **Given:** Entity definition > chunk_size (e.g., 1000 tokens)
  - **When:** chunk_document() called
  - **Then:** Entity becomes single chunk exceeding chunk_size, warning logged

**Fixture Requirements:**
- `tests/fixtures/entity_rich_documents/risk_register.md` (100+ entities)
- `tests/fixtures/entity_rich_documents/policy_document.md` (multi-sentence entities)
- `tests/fixtures/entity_rich_documents/audit_mappings.md` (relationship patterns)

---

#### File: `tests/integration/test_chunk/test_section_boundaries.py` (NEW - ~400 lines)

**Purpose:** Section-aware chunking with multi-section documents (completes deferred AC-3.1-2)

**Tests:**

- ✅ **test_section_aware_chunking_with_policy_document**
  - **Status:** RED - Section detection not implemented
  - **Verifies:** AC-3.2-7 (CRITICAL) - Real multi-section document
  - **Given:** Policy document with 5 sections (headings + page breaks)
  - **When:** chunk_document() called
  - **Then:** Chunks align with section boundaries, section_context populated

- ✅ **test_section_context_breadcrumb_format**
  - **Status:** RED - Breadcrumb generation not implemented
  - **Verifies:** AC-3.2-7 - Section hierarchy formatting
  - **Given:** Nested sections (Risk Assessment > Identified Risks > High Severity)
  - **When:** chunk_document() called
  - **Then:** ChunkMetadata.section_context = "Risk Assessment > Identified Risks > High Severity"

- ✅ **test_large_section_split_at_sentence_boundaries**
  - **Status:** RED - Section splitting logic not implemented
  - **Verifies:** AC-3.2-7, AC-3.1-1 - Maintain sentence boundaries
  - **Given:** Section larger than chunk_size
  - **When:** chunk_document() called
  - **Then:** Section split at sentence boundaries (not mid-sentence), section_context preserved

- ✅ **test_document_without_sections_graceful_degradation**
  - **Status:** RED - Fallback behavior not tested
  - **Verifies:** AC-3.2-7 - Graceful degradation
  - **Given:** Document with no section markers
  - **When:** chunk_document() called
  - **Then:** Returns empty section list, falls back to sentence-only chunking

---

#### File: `tests/unit/test_chunk/test_determinism.py` (EXTEND - add 2 tests)

**Purpose:** Extend existing determinism tests with entity-aware chunking

**Tests:**

- ✅ **test_entity_aware_chunking_determinism**
  - **Status:** RED - Entity-aware chunking not implemented yet
  - **Verifies:** AC-3.2-8 (CRITICAL) - 100% reproducibility
  - **Given:** ProcessingResult with entities
  - **When:** chunk_document() called 10 times
  - **Then:** All outputs byte-for-byte identical (sha256 hash comparison)

- ✅ **test_entity_analysis_order_determinism**
  - **Status:** RED - Entity analysis not implemented
  - **Verifies:** AC-3.2-8 - Consistent entity processing order
  - **Given:** Entities in random order in ProcessingResult
  - **When:** EntityPreserver.analyze_entities() called multiple times
  - **Then:** Always returns same sorted order (by start_pos)

---

### Performance Tests (3 tests)

#### File: `tests/performance/test_chunk/test_chunking_latency.py` (EXTEND - add 1 test)

**Purpose:** Validate NFR-P3 with entity overhead

**Tests:**

- ✅ **test_entity_aware_chunking_latency**
  - **Status:** RED - Entity-aware chunking not implemented
  - **Verifies:** NFR-P3 - Total latency <3.3s per 10k words
  - **Given:** 10k-word document with 50 entities
  - **When:** chunk_document() called with entity_aware=True
  - **Then:** Total latency <3.3s (Story 3.1 baseline 3.0s + 0.3s entity overhead)

- ✅ **test_entity_analysis_overhead**
  - **Status:** RED - EntityPreserver not implemented
  - **Verifies:** NFR-P3 - Entity analysis <0.3s per 10k words
  - **Given:** 10k-word document with 50 entities
  - **When:** EntityPreserver.analyze_entities() called
  - **Then:** Execution time <0.3s

- ✅ **test_section_detection_overhead**
  - **Status:** RED - Section detection not implemented
  - **Verifies:** NFR-P3 - Section detection <0.1s per document
  - **Given:** Document with 10 sections
  - **When:** _detect_section_boundaries() called
  - **Then:** Execution time <0.1s

---

## Test Summary Statistics

**Total Tests:** 27 tests (14 unit + 8 integration + 3 performance + 2 determinism)

**Test Distribution:**
- Unit tests: 14 (52%)
- Integration tests: 8 (30%)
- Performance tests: 3 (11%)
- Determinism tests: 2 (7%)

**Acceptance Criteria Coverage:**
- AC-3.2-1: 7 tests (unit + integration)
- AC-3.2-2: 1 test (integration)
- AC-3.2-3: 2 tests (unit + integration)
- AC-3.2-4: 3 tests (unit + integration)
- AC-3.2-5: 1 test (integration)
- AC-3.2-6: 4 tests (unit + integration)
- AC-3.2-7: 8 tests (unit + integration)
- AC-3.2-8: 4 tests (determinism)

---

## Data Fixtures Created

### Entity-Rich Document Fixtures (NEW)

#### tests/fixtures/entity_rich_documents/risk_register.md

**Purpose:** Real-world risk register with 100+ entities for preservation rate testing

**Entities:**
- 50 RISK entities (RISK-2024-001 through RISK-2024-050)
- 30 CONTROL entities (CTRL-001 through CTRL-030)
- 20 POLICY entities (POL-001 through POL-020)

**Relationships:**
- Risk-control mappings (e.g., "RISK-001 mitigated by CTRL-005")
- Policy-risk links (e.g., "POL-003 addresses RISK-015")

**Size:** ~15,000 words, generates ~30 chunks

---

#### tests/fixtures/entity_rich_documents/policy_document.md

**Purpose:** Policy document with multi-sentence entity definitions

**Structure:**
- 5 sections (Introduction, Scope, Requirements, Controls, Appendix)
- 20 policy entities with 2-4 sentence definitions each
- Section headings (### format and numbered format 1.2.3)

**Size:** ~8,000 words, generates ~16 chunks

---

#### tests/fixtures/entity_rich_documents/audit_mappings.md

**Purpose:** Audit document with dense relationship patterns

**Relationships:**
- 30 risk-control mappings
- 20 control-policy mappings
- 15 requirement-control mappings

**Size:** ~10,000 words, generates ~20 chunks

---

### Pytest Fixtures (conftest.py extensions)

#### tests/unit/test_chunk/conftest.py (NEW)

**Fixtures:**

```python
@pytest.fixture
def sample_entities() -> List[Entity]:
    """Create sample Entity objects from Epic 2 for testing."""
    return [
        Entity(
            type=EntityType.RISK,
            id="RISK-2024-001",
            text="Data breach risk",
            confidence=0.95,
            location=EntityLocation(start=100, end=120)
        ),
        Entity(
            type=EntityType.CONTROL,
            id="CTRL-042",
            text="Encryption control",
            confidence=0.92,
            location=EntityLocation(start=250, end=270)
        ),
    ]


@pytest.fixture
def processing_result_with_entities(sample_entities) -> ProcessingResult:
    """Create ProcessingResult with entities for integration tests."""
    # Returns ProcessingResult with normalized text and entity list


@pytest.fixture
def large_entity_document() -> ProcessingResult:
    """Document with entity definition exceeding chunk_size."""
    # Returns ProcessingResult with 1000-token entity definition


@pytest.fixture
def multi_section_document() -> ProcessingResult:
    """Document with 5 sections for section detection tests."""
    # Returns ProcessingResult with heading ContentBlocks
```

**Auto-cleanup:** All fixtures use pytest's automatic teardown (no manual cleanup needed)

---

## Mock Requirements

**No external service mocks required** for this story. All testing is pure library code (no API calls, no UI).

**Logging verification:**
- Warning logged when entity > chunk_size
- Section detection results logged for debugging

---

## Implementation Checklist

### Test Group 1: EntityPreserver Component (AC-3.2-1, 3.2-4, 3.2-5, 3.2-6)

**Test:** `test_entity_reference_creation` (and 9 other EntityPreserver tests)

**Tasks to make these tests pass:**

- [ ] Create `src/data_extract/chunk/entity_preserver.py`
- [ ] Implement `EntityReference` dataclass
  - [ ] Fields: entity_type, entity_id, start_pos, end_pos, is_partial, context_snippet
  - [ ] Decorator: `@dataclass(frozen=True)` for immutability
  - [ ] Method: `to_dict()` for JSON serialization
  - [ ] Add Pydantic v2 validation
- [ ] Implement `EntityPreserver` class
  - [ ] Constructor: `__init__(self)`
  - [ ] Method: `analyze_entities(text: str, entities: List[Entity]) -> List[EntityReference]`
  - [ ] Method: `find_entity_gaps(entities: List[EntityReference], text: str) -> List[int]`
  - [ ] Method: `detect_entity_relationships(text: str, entities: List[EntityReference]) -> List[Tuple[str, str, str]]`
- [ ] Add comprehensive type hints (mypy strict mode compliant)
- [ ] Add Google-style docstrings for all public methods
- [ ] Run tests: `pytest tests/unit/test_chunk/test_entity_preserver.py -v`
- [ ] ✅ All EntityPreserver tests pass (green phase)

**Estimated Effort:** 4-6 hours

---

### Test Group 2: Section Boundary Detection (AC-3.2-7 - Deferred from AC-3.1-2)

**Test:** `test_detect_section_boundaries_with_heading_blocks` (and 3 other section detection tests)

**Tasks to make these tests pass:**

- [ ] Update `src/data_extract/chunk/engine.py`
- [ ] Replace `_detect_section_boundaries()` placeholder (lines 252-281)
  - [ ] Remove "return []" placeholder
  - [ ] Add section detection logic:
    - [ ] Parse document.content_blocks for type="heading" blocks
    - [ ] Detect page break markers from source_metadata
    - [ ] Regex patterns: r'^#{1,6}\s+(.+)$' (Markdown), r'^\d+(\.\d+)*\s+(.+)$' (numbered)
  - [ ] Map section start positions to sentence indices
  - [ ] Build section hierarchy (parent-child relationships)
  - [ ] Generate section_context breadcrumbs (e.g., "Parent > Child")
  - [ ] Return list of sentence indices where sections begin
  - [ ] Add fallback: if no sections detected, return empty list (graceful degradation)
  - [ ] Add logging: log section detection results for debugging
- [ ] Update docstring explaining section detection approach
- [ ] Run tests: `pytest tests/unit/test_chunk/test_section_detection.py -v`
- [ ] ✅ All section detection tests pass (green phase)

**Estimated Effort:** 3-4 hours

---

### Test Group 3: EntityPreserver Integration (AC-3.2-1, 3.2-2, 3.2-3, 3.2-4, 3.2-8)

**Test:** `test_entity_preservation_rate_exceeds_95_percent` (and 7 other integration tests)

**Tasks to make these tests pass:**

- [ ] Update `src/data_extract/chunk/engine.py`
- [ ] Update `ChunkingEngine.__init__` to accept `entity_aware: bool = True` parameter
- [ ] Update `chunk_document()` method
  - [ ] Call `EntityPreserver.analyze_entities()` upfront (before sentence chunking)
  - [ ] Call `EntityPreserver.find_entity_gaps()` to get safe split zones
  - [ ] Call `EntityPreserver.detect_entity_relationships()` for relationship detection
  - [ ] Pass entity gaps to `_generate_chunks()` for boundary planning
  - [ ] Integrate relationship triples into chunk metadata
- [ ] Update `_generate_chunks()` method
  - [ ] Prefer chunk splits at entity gaps (between entities, not within)
  - [ ] Avoid splits within entity spans (start_pos to end_pos)
  - [ ] If entity > chunk_size, yield entire entity as single chunk
  - [ ] Log warning when entity exceeds chunk_size
  - [ ] Flag partial entities with `is_partial=True` in metadata
  - [ ] Add cross-references between chunks for split entities
- [ ] Ensure determinism: entity analysis sorted by start_pos, consistent tiebreaking
- [ ] Maintain streaming generator pattern (no buffering)
- [ ] Run tests: `pytest tests/integration/test_chunk/test_entity_aware_chunking.py -v`
- [ ] ✅ All entity-aware integration tests pass (green phase)

**Estimated Effort:** 6-8 hours

---

### Test Group 4: ChunkMetadata Extensions (AC-3.2-5, 3.2-6, 3.2-7)

**Test:** `test_entity_tags_json_serialization` (metadata validation tests)

**Tasks to make these tests pass:**

- [ ] Update `src/data_extract/chunk/models.py`
- [ ] Add fields to `ChunkMetadata` dataclass:
  - [ ] `entity_tags: List[EntityReference] = field(default_factory=list)`
  - [ ] `section_context: str = ""` (deferred from Story 3.1)
  - [ ] `entity_relationships: List[Tuple[str, str, str]] = field(default_factory=list)`
- [ ] Update `Chunk.to_dict()` method
  - [ ] Convert EntityReference objects to dicts via `to_dict()`
  - [ ] Handle empty lists gracefully (return [] not null)
  - [ ] Ensure JSON serializable (test with `json.dumps()`)
- [ ] Ensure Pydantic v2 validation handles nested models
- [ ] Add type hints for all new fields
- [ ] Run tests: `pytest tests/integration/test_chunk/test_entity_aware_chunking.py::test_entity_tags_json_serialization -v`
- [ ] ✅ Metadata tests pass (green phase)

**Estimated Effort:** 2-3 hours

---

### Test Group 5: Section Integration (AC-3.2-7)

**Test:** `test_section_aware_chunking_with_policy_document` (section integration tests)

**Tasks to make these tests pass:**

- [ ] Update `ChunkingEngine` to populate `section_context` field
  - [ ] Determine which section each chunk belongs to
  - [ ] Format as breadcrumb trail (parent > child > grandchild)
  - [ ] Default to empty string if no section context
- [ ] Integrate section boundaries with chunk generation
  - [ ] Prefer chunk splits at section boundaries when chunk_size permits
  - [ ] If section > chunk_size, split at sentence boundaries within section
  - [ ] Preserve section_context across chunks within same section
- [ ] Run tests: `pytest tests/integration/test_chunk/test_section_boundaries.py -v`
- [ ] ✅ All section integration tests pass (green phase)

**Estimated Effort:** 3-4 hours

---

### Test Group 6: Determinism Validation (AC-3.2-8)

**Test:** `test_entity_aware_chunking_determinism` (determinism tests)

**Tasks to make these tests pass:**

- [ ] Update `tests/unit/test_chunk/test_determinism.py`
- [ ] Verify entity analysis performed in sorted order (by start_pos)
- [ ] Verify relationship detection uses fixed pattern order
- [ ] Verify section detection is deterministic (no random heuristics)
- [ ] Run test 10 times, compute sha256 hash of output
- [ ] Assert all 10 hashes identical
- [ ] Run tests: `pytest tests/unit/test_chunk/test_determinism.py -v`
- [ ] ✅ All determinism tests pass (green phase)

**Estimated Effort:** 2 hours

---

### Test Group 7: Performance Validation (NFR-P3)

**Test:** `test_entity_aware_chunking_latency` (performance tests)

**Tasks to make these tests pass:**

- [ ] Optimize EntityPreserver if needed (profiling)
- [ ] Optimize section detection if needed (cached regex patterns)
- [ ] Run performance tests: `pytest tests/performance/test_chunk/ -v`
- [ ] Verify total latency <3.3s per 10k words
- [ ] Verify entity analysis overhead <0.3s
- [ ] Verify section detection overhead <0.1s
- [ ] Update `docs/performance-baselines-epic-3.md` with measurements
- [ ] ✅ All performance tests pass (green phase)

**Estimated Effort:** 2-3 hours

---

## Running Tests

```bash
# Run all failing tests for Story 3.2
pytest tests/unit/test_chunk/test_entity_preserver.py tests/unit/test_chunk/test_section_detection.py tests/integration/test_chunk/test_entity_aware_chunking.py tests/integration/test_chunk/test_section_boundaries.py -v

# Run specific test file
pytest tests/unit/test_chunk/test_entity_preserver.py -v

# Run tests with coverage
pytest tests/unit/test_chunk/ tests/integration/test_chunk/ --cov=src/data_extract/chunk --cov-report=html

# Run only entity-aware tests (new marker)
pytest -m entity_aware -v

# Run only integration tests
pytest -m integration tests/integration/test_chunk/ -v

# Run determinism tests (10 iterations)
pytest tests/unit/test_chunk/test_determinism.py::test_entity_aware_chunking_determinism -v --count=10

# Run performance tests
pytest tests/performance/test_chunk/ -v -m performance

# Debug specific test with pdb
pytest tests/unit/test_chunk/test_entity_preserver.py::test_analyze_entities_sorting --pdb

# Run tests in parallel (faster)
pytest tests/unit/test_chunk/ -n auto
```

---

## Red-Green-Refactor Workflow

### RED Phase (Complete) ✅

**TEA Agent Responsibilities:**

- ✅ All 27 tests written and failing
- ✅ Fixtures created for entity-rich documents
- ✅ pytest fixtures extended in conftest.py
- ✅ Implementation checklist created with clear tasks
- ✅ Coverage targets defined (>90% entity_preserver.py, >80% Epic 3 overall)

**Verification:**

```bash
# Run all tests to verify RED phase
pytest tests/unit/test_chunk/test_entity_preserver.py tests/unit/test_chunk/test_section_detection.py tests/integration/test_chunk/test_entity_aware_chunking.py tests/integration/test_chunk/test_section_boundaries.py -v

# Expected result: All 27 tests FAIL (RED phase verified)
```

**Expected Failure Messages:**

- `ModuleNotFoundError: No module named 'entity_preserver'` (entity_preserver.py not created)
- `AttributeError: 'ChunkingEngine' object has no attribute 'entity_aware'` (parameter not added)
- `AssertionError: Section boundaries returned empty list` (_detect_section_boundaries placeholder)
- `KeyError: 'entity_tags'` (ChunkMetadata fields not added)

---

### GREEN Phase (DEV Team - Next Steps)

**DEV Agent Responsibilities:**

1. **Pick one test group** from implementation checklist (start with Test Group 1: EntityPreserver)
2. **Read the tests** to understand expected behavior (Given-When-Then structure)
3. **Implement minimal code** to make that specific test group pass
4. **Run the test group** to verify now passes (green)
5. **Check off tasks** in implementation checklist
6. **Move to next test group** and repeat

**Key Principles:**

- One test group at a time (don't try to fix all 27 tests at once)
- Minimal implementation (don't over-engineer)
- Run tests frequently (immediate feedback via `pytest -v`)
- Use implementation checklist as roadmap

**Progress Tracking:**

- Check off tasks in implementation checklist as completed
- Share progress in daily standup
- Update `docs/sprint-status.yaml` with story progress

**Recommended Implementation Order:**

1. Test Group 1: EntityPreserver Component (foundation)
2. Test Group 2: Section Boundary Detection (completes deferred AC-3.1-2)
3. Test Group 4: ChunkMetadata Extensions (data models)
4. Test Group 3: EntityPreserver Integration (brings it all together)
5. Test Group 5: Section Integration (section-aware chunking)
6. Test Group 6: Determinism Validation (reproducibility check)
7. Test Group 7: Performance Validation (NFR compliance)

---

### REFACTOR Phase (DEV Team - After All Tests Pass)

**DEV Agent Responsibilities:**

1. **Verify all 27 tests pass** (green phase complete)
2. **Review code for quality** (readability, maintainability, performance)
3. **Extract duplications** (DRY principle)
   - Entity analysis logic shared across components?
   - Section detection patterns reusable?
4. **Optimize performance** (if needed)
   - Profile entity analysis (target <0.3s per 10k words)
   - Cache section detection results
5. **Ensure tests still pass** after each refactor
6. **Update documentation** (architecture.md, CLAUDE.md)

**Key Principles:**

- Tests provide safety net (refactor with confidence)
- Make small refactors (easier to debug if tests fail)
- Run tests after each change (`pytest -v`)
- Don't change test behavior (only implementation)

**Quality Gates (0 violations required):**

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check (MUST run from project root)
mypy src/data_extract/

# Run all tests
pytest tests/unit/test_chunk/ tests/integration/test_chunk/ -v

# All commands must return 0 violations
```

**Completion Criteria:**

- ✅ All 27 tests pass
- ✅ Code quality meets team standards (black, ruff, mypy 0 violations)
- ✅ Coverage >90% for entity_preserver.py (check with `pytest --cov`)
- ✅ Performance tests validate NFR-P3 (<3.3s per 10k words)
- ✅ No duplications or code smells
- ✅ Documentation updated (architecture.md ADR-011 amendment, CLAUDE.md)
- ✅ Ready for code review and story approval

---

## Next Steps

1. **Review this checklist** with team in standup or planning
2. **Run failing tests** to confirm RED phase:
   ```bash
   pytest tests/unit/test_chunk/test_entity_preserver.py -v
   ```
3. **Begin implementation** using implementation checklist as guide (Test Group 1 → 7)
4. **Work one test group at a time** (red → green for each group)
5. **Share progress** in daily standup and `docs/sprint-status.yaml`
6. **When all tests pass**, refactor code for quality (run quality gates)
7. **When refactoring complete**, mark story as done: `workflow story-done 3.2`

---

## Documentation Updates Required

After all tests pass and refactoring complete:

### CLAUDE.md

- [ ] Document EntityPreserver usage patterns
- [ ] Document entity-aware chunking configuration (`entity_aware` parameter)
- [ ] Update Epic 3 section with entity preservation best practices
- [ ] Document section boundary detection approach

### docs/architecture.md

- [ ] Amend ADR-011 with entity-aware chunking decision
- [ ] Document EntityPreserver component design
- [ ] Document section detection implementation (completes deferred AC-3.1-2)
- [ ] Update Epic 3 integration diagram (add EntityPreserver component)

### docs/performance-baselines-epic-3.md

- [ ] Add entity analysis overhead baseline (<0.3s per 10k words)
- [ ] Add section detection overhead baseline (<0.1s per document)
- [ ] Validate overall chunking latency still meets NFR-P3 (<3.3s per 10k words)

---

## Test Design Patterns Applied

This ATDD workflow follows proven pytest patterns:

**Given-When-Then Structure:**
- Tests organized with clear setup (Given), action (When), assertion (Then)
- Comment blocks in test code document test intent
- Makes tests self-documenting and easy to understand

**Pytest Fixtures with Auto-Cleanup:**
- All fixtures use pytest's automatic teardown
- No manual cleanup in test code
- Fixtures are composable (fixtures can use other fixtures)

**Marker-Based Selective Execution:**
- Tests marked with `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.performance`
- Enables fast feedback loop (`pytest -m unit` runs only fast tests)
- CI can run different test suites at different stages

**Parameterized Tests:**
- Use `@pytest.mark.parametrize` for testing multiple scenarios
- Example: Test all relationship types (mitigated_by, maps_to, implements, addresses)
- Reduces test duplication, improves coverage

**Frozen Dataclasses:**
- EntityReference uses `@dataclass(frozen=True)` for immutability
- Prevents accidental mutations in tests
- Makes tests more predictable and debuggable

**Coverage-Driven Development:**
- Coverage target >90% for entity_preserver.py ensures thoroughness
- Use `pytest --cov --cov-report=html` to identify untested code paths
- Focus on meaningful coverage, not just line count

---

## Testing Philosophy

**Tests First, Implementation Second:**
- Tests define expected behavior (specification by example)
- Implementation guided by failing tests
- Prevents scope creep and over-engineering

**One Assertion Per Test (Atomic Tests):**
- Each test validates one specific behavior
- If test fails, immediately know what broke
- Makes tests easier to debug and maintain

**Fast Feedback Loop:**
- Unit tests run in <1 second (immediate feedback)
- Integration tests run in <10 seconds (quick validation)
- Performance tests run separately (not on every commit)

**Test Independence:**
- Each test can run in isolation (no order dependencies)
- Tests don't share mutable state
- Parallel execution safe (`pytest -n auto`)

**Readable Tests:**
- Test names describe what's being tested (test_entity_preservation_rate_exceeds_95_percent)
- Given-When-Then comments explain test intent
- Self-documenting (tests serve as executable specifications)

---

## Contact

**Questions or Issues?**

- Ask in team standup
- Refer to `CLAUDE.md` for project conventions
- Consult `docs/test-design-epic-3.md` for test strategy
- Review `docs/stories/3-2-entity-aware-chunking.md` for story details

---

**Generated by BMad TEA Agent (Master Test Architect)** - 2025-11-14

**ATDD Workflow Version:** 4.0 (BMad v6)
**Test Coverage:** 27 tests across 8 acceptance criteria
**Primary Test Level:** Integration (with unit and performance support)
**Estimated Implementation Effort:** 22-31 hours (across 7 test groups)
