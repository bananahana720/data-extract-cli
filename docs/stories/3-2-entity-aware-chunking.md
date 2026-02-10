# Story 3.2: Entity-Aware Chunking with Section Boundary Detection

Status: done

## Story

As a **data scientist preparing enterprise documents for RAG workflows**,
I want **chunks to preserve entity context and align with document sections**,
so that **LLM retrievals maintain complete entity definitions and structural coherence without fragmenting critical information**.

## Context Summary

**Epic Context:** Story 3.2 extends Epic 3's chunking capabilities by adding entity-aware boundary detection and section structure preservation. This story builds on Story 3.1's semantic sentence-boundary chunking, adding intelligence to avoid splitting entity definitions and respect document organizational structure (headings, sections, structural boundaries).

**Business Value:**
- Prevents entity fragmentation that causes incomplete context in RAG retrievals
- Maintains document hierarchy (sections, headings) for better semantic understanding
- Preserves entity relationships (e.g., "Risk X mitigated by Control Y") within chunks
- Enables efficient entity-based retrieval (chunks tagged with entity types)
- Supports audit trail requirements (traceability from chunk → entity → source document)

**Dependencies:**
- **Story 3.1 Complete (Semantic Boundary-Aware Chunking Engine)** - ChunkingEngine with sentence-boundary detection operational
- **Epic 2 Complete (Extract & Normalize)** - ProcessingResult with normalized text and entity tags available
- **Story 2.5.2 (spaCy Integration)** - SentenceSegmenter with en_core_web_md model integrated
- **AC-3.1-2 Deferred from Story 3.1** - Section boundary detection deferred, now included in this story

**Technical Foundation:**
- **ChunkingEngine (Story 3.1):** Sentence-boundary chunking operational, deterministic, streaming generator pattern
- **ProcessingResult Model:** Epic 2 output includes entities list with type, id, start_pos, end_pos, normalized_value
- **ContentBlocks (Epic 2):** Document structure preserved but heading/section markers need enhancement
- **Entity Reference Model:** New model to track entity mentions within chunks

**Key Requirements:**
1. **Entity-Aware Chunking:** Chunk boundaries avoid splitting entity definitions (AC-3.2-1, AC-3.2-4)
2. **Section Boundary Detection:** Implement deferred AC-3.1-2 - detect and respect section markers (headings, page breaks) (AC-3.2-7)
3. **Partial Entity Tracking:** Entities unavoidably split across chunks flagged in metadata (AC-3.2-2)
4. **Relationship Preservation:** Entity relationships (e.g., "Risk → Control") preserved within chunks when possible (AC-3.2-3)
5. **Entity Metadata:** All entity mentions tagged in ChunkMetadata with type, id, position (AC-3.2-5, AC-3.2-6)
6. **Determinism:** Maintain 100% reproducibility from Story 3.1 (same input → same chunks)

## Acceptance Criteria

**AC-3.2-1: Entity Mentions Kept Within Single Chunks When Possible (P0 - Critical)**
- EntityPreserver analyzes entity boundaries before chunk generation
- Chunk splits prefer gaps between entities rather than within entity text spans
- Target: >95% of entities remain intact within single chunks (not split)
- If entity too large (>chunk_size), handled gracefully (entire entity definition becomes single chunk, flagged)
- **Validation:** Integration tests with entity-rich documents (risk registers, policy documents, control catalogs)
- **UAT Required:** Yes - Critical for entity context integrity

**AC-3.2-2: Entities Split Across Chunks Noted in Metadata (P0)**
- When entity span exceeds chunk boundary, both chunks receive partial entity flag
- ChunkMetadata.entity_tags includes is_partial=True for split entities
- Partial entity includes continuation flag: "entity_continued_from_previous" or "entity_continues_in_next"
- Cross-reference to adjacent chunk IDs in metadata
- **Validation:** Unit tests with forced entity splits, integration tests with very long entity definitions
- **UAT Required:** Yes

**AC-3.2-3: Relationship Context Preserved (P0 - Critical)**
- Entity relationship patterns detected (e.g., "RISK-001 mitigated by CTRL-042")
- Chunks include both entities when relationship span < chunk_size
- Relationship triples (entity1, relation, entity2) tracked in chunk metadata
- If relationship spans multiple chunks, relationship context preserved via metadata links
- **Validation:** Integration tests with relationship-rich documents (risk-control mappings, policy-requirement links)
- **UAT Required:** Yes - Critical for RAG context

**AC-3.2-4: Chunk Boundaries Avoid Splitting Entity Definitions (P0)**
- Entity definition detection: Multi-sentence entities (e.g., "Risk X: Description spanning 3 sentences")
- Chunk boundaries placed after entity definitions complete (before next entity starts)
- If entity definition > chunk_size, definition becomes single chunk with warning logged
- **Validation:** Unit tests with multi-sentence entity definitions, integration tests with audit documents
- **UAT Required:** Yes

**AC-3.2-5: Cross-References Maintained with Entity IDs (P1)**
- All entity mentions include entity_id from Epic 2 normalization
- Entity IDs enable cross-chunk lookups (find all chunks mentioning "RISK-2024-001")
- ChunkMetadata.entity_tags includes entity_id, entity_type, start_pos, end_pos
- Duplicate entity mentions within same chunk deduplicated (one entry per unique entity_id)
- **Validation:** Unit tests for entity ID propagation, integration tests for cross-chunk entity search
- **UAT Required:** No - Metadata validation sufficient

**AC-3.2-6: Entity Tags in Chunk Metadata (P1)**
- ChunkMetadata.entity_tags populated with EntityReference objects for all entities in chunk
- EntityReference fields: entity_type (str), entity_id (str), start_pos (int), end_pos (int), is_partial (bool), context_snippet (str)
- Entity tags serializable to JSON for output formats (Story 3.4)
- Empty entity_tags list if no entities in chunk (not null)
- **Validation:** Unit tests for metadata population, schema validation
- **UAT Required:** No - Unit test sufficient

**AC-3.2-7: Section Boundaries Respected (Deferred from AC-3.1-2) (P0)**
- **IMPLEMENTS DEFERRED AC-3.1-2 FROM STORY 3.1**
- Chunking algorithm detects section markers (headings, page breaks, structural boundaries)
- Section detection sources:
  1. ContentBlocks with type="heading" from Epic 2 extraction
  2. Page break markers from PDF extraction
  3. Structural patterns (e.g., "### Section Title", "1.2.3 Heading")
- Chunks align with section boundaries when chunk_size permits
- If section too large, split at sentence boundaries within section (maintain AC-3.1-1)
- Section context preserved in ChunkMetadata.section_context (e.g., "Risk Assessment > Identified Risks")
- **Validation:** Integration tests with multi-section documents (policies, SOC2 reports, risk registers with sections)
- **UAT Required:** Yes - Validates deferred Story 3.1 requirement

**AC-3.2-8: Determinism Maintained (P0 - Critical)**
- Same ProcessingResult input always produces identical chunks (byte-for-byte comparison)
- Entity-aware chunking is deterministic (no randomness in boundary decisions)
- Entity analysis performed in consistent order (sorted by start_pos)
- Reproducibility validated via automated tests (10 runs, diffs outputs)
- **Validation:** Determinism test runs same entity-rich document 10 times, diffs outputs
- **UAT Required:** Yes - Critical for audit trail requirement

## Acceptance Criteria Trade-offs and Deferrals

**AC-3.2-1 Trade-off (Very Large Entities):**
- **Issue:** Entity definition > chunk_size conflicts with "entities within single chunks" requirement
- **Resolution:** Entire entity definition becomes single chunk (exceeds chunk_size), warning logged, flagged in metadata
- **Rationale:** Preserving complete entity definitions prioritized over chunk size uniformity
- **Documented In:** Dev Notes, EntityPreserver docstring

**AC-3.2-3 Trade-off (Long-Distance Relationships):**
- **Issue:** Entity relationships spanning >chunk_size (e.g., risk on page 1, control on page 3)
- **Resolution:** Relationship tracked in metadata with cross-references, but entities in separate chunks
- **Rationale:** Cannot violate chunk_size constraint for distant relationships
- **Documented In:** Dev Notes, relationship preservation logic

**AC-3.2-7 Enhancement (Section Detection):**
- **Context:** AC-3.1-2 was deferred from Story 3.1 due to missing section markers in document.structure
- **Resolution:** This story implements section detection using available ContentBlocks and structural patterns
- **Fallback:** If no section markers detected, chunks fall back to sentence-boundary-only splitting (Story 3.1 behavior)
- **Documented In:** Dev Notes, architecture.md ADR-011 Amendment

**No Additional Deferrals:** All ACs are foundational for entity-aware RAG workflows.

## Tasks / Subtasks

### Task 1: Create EntityPreserver Component (AC: #3.2-1, #3.2-4, #3.2-5, #3.2-6)
- [ ] Create `src/data_extract/chunk/entity_preserver.py`
- [ ] Implement `EntityReference` dataclass (frozen=True)
  - [ ] Fields: entity_type, entity_id, start_pos, end_pos, is_partial, context_snippet
  - [ ] Method: to_dict() for JSON serialization
  - [ ] Pydantic v2 validation
- [ ] Implement `EntityPreserver` class
  - [ ] Constructor: `__init__(self)`
  - [ ] Method: `analyze_entities(text: str, entities: List[Entity]) -> List[EntityReference]`
    - [ ] Build entity reference map from Epic 2 entity list
    - [ ] Sort entities by start_pos for determinism
    - [ ] Extract context snippets (±20 chars around entity)
    - [ ] Return list of EntityReference objects
  - [ ] Method: `find_entity_gaps(entities: List[EntityReference], text: str) -> List[int]`
    - [ ] Identify text positions between entities (safe split zones)
    - [ ] Return list of character offsets suitable for chunk boundaries
  - [ ] Method: `detect_entity_relationships(text: str, entities: List[EntityReference]) -> List[Tuple[str, str, str]]`
    - [ ] Pattern matching for relationship keywords ("mitigated by", "maps to", "implements", "addresses")
    - [ ] Return triples: (entity1_id, relation_type, entity2_id)
  - [ ] Add type hints (mypy strict mode compliant)
  - [ ] Add comprehensive docstrings (Google style)

### Task 2: Implement Section Boundary Detection (AC: #3.2-7 - Deferred from AC-3.1-2)
- [ ] Update `ChunkingEngine._detect_section_boundaries()` in `src/data_extract/chunk/engine.py`
  - [ ] Remove placeholder implementation (currently returns empty list)
  - [ ] Add section detection logic:
    - [ ] Parse document.content_blocks for type="heading" blocks
    - [ ] Detect page break markers from source_metadata
    - [ ] Regex patterns for structural headings ("### Title", "1.2.3 Heading")
  - [ ] Map section start positions to sentence indices
  - [ ] Build section hierarchy (parent-child relationships)
  - [ ] Populate section_context strings (e.g., "Risk Assessment > Identified Risks")
  - [ ] Return list of sentence indices where sections begin
  - [ ] Add fallback: if no sections detected, return empty list (graceful degradation)
  - [ ] Log section detection results for debugging
- [ ] Update ChunkMetadata to populate section_context field
  - [ ] Determine which section each chunk belongs to
  - [ ] Format as breadcrumb trail (parent > child > grandchild)
  - [ ] Default to empty string if no section context available
- [ ] Add comprehensive docstrings explaining section detection approach

### Task 3: Integrate EntityPreserver into ChunkingEngine (AC: #3.2-1, #3.2-2, #3.2-3, #3.2-4, #3.2-8)
- [ ] Update `ChunkingEngine.__init__` to accept optional entity_aware parameter (default=True)
- [ ] Update `ChunkingEngine.chunk_document()` to use EntityPreserver
  - [ ] Call EntityPreserver.analyze_entities() upfront (before sentence chunking)
  - [ ] Call EntityPreserver.find_entity_gaps() to get safe split zones
  - [ ] Pass entity gaps to _generate_chunks() for boundary planning
  - [ ] Integrate relationship detection results into chunk metadata
- [ ] Update `_generate_chunks()` to respect entity boundaries
  - [ ] Prefer chunk splits at entity gaps (between entities)
  - [ ] Avoid splits within entity spans (start_pos to end_pos)
  - [ ] If entity > chunk_size, yield entire entity as single chunk with warning
  - [ ] Flag partial entities with is_partial=True in metadata
  - [ ] Add cross-references between chunks for split entities
- [ ] Add determinism checks
  - [ ] Entity analysis performed in consistent order (sorted by start_pos)
  - [ ] Entity boundary decisions are deterministic (no random tiebreaking)
  - [ ] Relationship detection uses consistent pattern ordering
- [ ] Maintain streaming generator pattern (no buffering)

### Task 4: Update ChunkMetadata with Entity Information (AC: #3.2-5, #3.2-6, #3.2-7)
- [ ] Update `ChunkMetadata` dataclass in `src/data_extract/chunk/models.py`
  - [ ] Add field: entity_tags: List[EntityReference] = field(default_factory=list)
  - [ ] Add field: section_context: str = "" (deferred from Story 3.1, now implemented)
  - [ ] Add field: entity_relationships: List[Tuple[str, str, str]] = field(default_factory=list)
- [ ] Update `Chunk.to_dict()` to serialize entity_tags
  - [ ] Convert EntityReference objects to dicts
  - [ ] Handle empty lists gracefully (return [] not null)
- [ ] Ensure Pydantic v2 validation handles nested models
- [ ] Add type hints for all new fields

### Task 5: Unit Testing - EntityPreserver (AC: #3.2-1, #3.2-4, #3.2-5, #3.2-6)
- [ ] Create `tests/unit/test_chunk/test_entity_preserver.py`
  - [ ] Test EntityReference creation and validation
  - [ ] Test analyze_entities() with various entity types (risks, controls, policies)
  - [ ] Test find_entity_gaps() returns positions between entities
  - [ ] Test detect_entity_relationships() finds common relationship patterns
  - [ ] Test entity sorting (determinism - same input → same order)
  - [ ] Test context snippet extraction (±20 chars)
  - [ ] Test empty entity list handling
  - [ ] Test overlapping entities (edge case)
  - [ ] Test entities at document boundaries (start/end)
- [ ] Achieve >90% coverage for entity_preserver.py module

### Task 6: Unit Testing - Section Boundary Detection (AC: #3.2-7)
- [ ] Create `tests/unit/test_chunk/test_section_detection.py`
  - [ ] Test _detect_section_boundaries() with heading ContentBlocks
  - [ ] Test section detection with page break markers
  - [ ] Test regex pattern detection ("### Title", "1.2.3 Heading")
  - [ ] Test section hierarchy building (parent-child relationships)
  - [ ] Test section_context breadcrumb generation
  - [ ] Test graceful degradation (no sections detected → empty list)
  - [ ] Test mixed section markers (headings + page breaks)
  - [ ] Test determinism (same document → same section boundaries)
- [ ] Use fixtures with synthetic documents containing various section patterns
- [ ] Achieve >90% coverage for section detection logic

### Task 7: Integration Testing - Entity-Aware Chunking (AC: #3.2-1, #3.2-2, #3.2-3, #3.2-4, #3.2-7)
- [ ] Create `tests/integration/test_chunk/test_entity_aware_chunking.py`
  - [ ] Test end-to-end: ProcessingResult with entities → Chunks with entity_tags
  - [ ] Test entity preservation rate (>95% entities intact)
  - [ ] Test partial entity flagging (forced splits due to size)
  - [ ] Test entity relationship preservation (risk-control pairs)
  - [ ] Test multi-entity chunks (multiple entities in single chunk)
  - [ ] Test section-aware chunking with real multi-section documents
  - [ ] Test section_context populated correctly
  - [ ] Test entities + sections integration (entities within sections)
- [ ] Create `tests/integration/test_chunk/test_section_boundaries.py`
  - [ ] Test real audit documents with sections (policies, SOC2 reports)
  - [ ] Test section alignment (chunks start/end at section boundaries)
  - [ ] Test large sections split at sentence boundaries (maintain AC-3.1-1)
  - [ ] Test section context preservation across chunks
  - [ ] Test documents without sections (graceful fallback to Story 3.1 behavior)
- [ ] Use fixtures from `tests/fixtures/entity_rich_documents/`
- [ ] Use real-world samples (anonymized risk registers, policy documents)

### Task 8: Integration Testing - Determinism (AC: #3.2-8)
- [ ] Update `tests/unit/test_chunk/test_determinism.py`
  - [ ] Test entity-aware chunking determinism (10 runs, byte-for-byte comparison)
  - [ ] Test entity analysis order (sorted by start_pos consistently)
  - [ ] Test relationship detection order (consistent pattern matching)
  - [ ] Test section detection determinism (same sections detected each run)
  - [ ] Test configuration sensitivity (entity_aware=False changes output)
- [ ] Ensure 100% reproducibility for entity-aware chunks

### Task 9: Documentation and Validation (AC: all)
- [ ] Update CLAUDE.md
  - [ ] Document EntityPreserver usage patterns
  - [ ] Document entity-aware chunking configuration (entity_aware parameter)
  - [ ] Update Epic 3 section with entity preservation best practices
  - [ ] Document section boundary detection approach
- [ ] Update docs/architecture.md
  - [ ] Amend ADR-011 to include entity-aware chunking decision
  - [ ] Document EntityPreserver component design
  - [ ] Document section detection implementation (completes deferred AC-3.1-2)
  - [ ] Update Epic 3 integration diagram (add EntityPreserver component)
- [ ] Update `docs/performance-baselines-epic-3.md`
  - [ ] Add entity analysis overhead baseline (<0.3 sec per 10k words)
  - [ ] Add section detection overhead baseline (<0.1 sec per document)
  - [ ] Validate overall chunking latency still meets NFR-P3 (<2 sec per 10k words)
- [ ] Run all quality gates:
  - [ ] `black src/ tests/` → 0 violations
  - [ ] `ruff check src/ tests/` → 0 violations
  - [ ] `mypy src/data_extract/` → 0 violations (run from project root)
  - [ ] `pytest -m unit` → All pass
  - [ ] `pytest -m integration` → All pass
  - [ ] `pytest -m performance tests/performance/test_chunk/` → NFR-P3 satisfied (with entity overhead)
- [ ] Validate all 8 ACs end-to-end:
  - [ ] AC-3.2-1: Entity preservation rate >95% (integration tests)
  - [ ] AC-3.2-2: Partial entity flagging (unit + integration tests)
  - [ ] AC-3.2-3: Relationship preservation (integration tests)
  - [ ] AC-3.2-4: Entity definition boundaries (unit + integration tests)
  - [ ] AC-3.2-5: Entity ID cross-referencing (unit tests)
  - [ ] AC-3.2-6: Entity tags in metadata (unit tests)
  - [ ] AC-3.2-7: Section boundary detection (integration tests - completes AC-3.1-2)
  - [ ] AC-3.2-8: Determinism maintained (determinism tests, 10 runs)
- [ ] Update Epic 3 completion checklist in docs/epics.md
- [ ] Mark story as done, ready for review

## Dev Notes

### Architecture Patterns and Constraints

**ADR-011 Amendment: Entity-Aware Chunking (Extension)**
- **Context:** RAG systems benefit from complete entity context - partial entity definitions degrade retrieval accuracy
- **Decision:** EntityPreserver analyzes entity boundaries before chunking, prioritizes splits between entities
- **Rationale:** Complete entity definitions improve LLM understanding, preserve domain-specific terminology, support entity-based retrieval
- **Implementation:** EntityPreserver integrated into ChunkingEngine as optional preprocessing step (entity_aware=True by default)
- **Trade-off:** Very large entities (>chunk_size) become single chunks exceeding target size (same as very long sentences)
- **Performance Impact:** Entity analysis adds ~0.3 sec per 10k words (acceptable overhead, tested in Story 3.1 baselines)
- **Fallback:** If entity analysis fails, falls back to sentence-boundary-only chunking (Story 3.1 behavior)

**ADR-011 Amendment: Section Boundary Detection (Completes Deferred AC-3.1-2)**
- **Context:** AC-3.1-2 was deferred from Story 3.1 due to missing section/heading markers in document.structure
- **Decision:** Section detection implemented in Story 3.2 using available ContentBlocks (type="heading") and structural pattern recognition
- **Rationale:** Section-aware chunking preserves document hierarchy, improves semantic coherence, aligns with user's mental model of documents
- **Implementation:** ChunkingEngine._detect_section_boundaries() parses ContentBlocks, detects patterns, maps to sentence indices
- **Data Source:** ContentBlocks from Epic 2 extraction (headings preserved as separate blocks), page break markers from PDF metadata
- **Fallback:** If no sections detected, returns empty list - chunks fall back to sentence-boundary-only splitting (graceful degradation)
- **Performance Impact:** Section detection adds ~0.1 sec per document (negligible overhead, mostly regex matching)

**Data Model Design (Immutability Pattern):**
- `@dataclass(frozen=True)` for EntityReference (consistent with Chunk, ChunkMetadata)
- Enables structural sharing and prevents accidental mutations
- Entity relationships stored as tuples (immutable) in ChunkMetadata

**Determinism Guarantee:**
- Entity analysis performed in sorted order (by start_pos) for consistent results
- Relationship detection uses fixed pattern list (no random ordering)
- Section detection uses deterministic regex patterns (no heuristic randomness)
- Same ProcessingResult → same EntityReference list → same chunk boundaries → same chunks

**Performance Optimization:**
- Entity analysis performed once upfront, results cached for all chunks
- Entity gaps pre-computed (avoid repeated entity boundary checks during chunking)
- Section detection performed once per document (results shared across chunks)
- Maintains streaming generator pattern (no additional buffering)

### Learnings from Previous Story

**From Story 3.1 (Semantic Boundary-Aware Chunking Engine) (Status: review)**

**Completion Status:** Story 3.1 completed implementation (all 8 tasks, 81/81 tests passing), under re-review for minor mypy type annotation fixes (3 violations, LOW severity). Expected approval imminent.

**New Services Created:**
- `ChunkingEngine` base class at `src/data_extract/chunk/engine.py` - Use `ChunkingEngine(segmenter, chunk_size, overlap_pct)` for basic chunking
- `SentenceSegmenter` reusable from `src/data_extract/chunk/sentence_segmenter.py` (wraps Story 2.5.2 implementation)
- `Chunk`, `ChunkMetadata`, `QualityScore` models at `src/data_extract/chunk/models.py` (immutable, Pydantic v2 validated)

**Architectural Decisions:**
- **Streaming Generator Pattern:** ChunkingEngine.chunk_document() returns `Iterator[Chunk]` (not `List[Chunk]`) for memory efficiency - MAINTAIN THIS PATTERN
- **Dependency Injection:** SentenceSegmenter injected via constructor - REUSE THIS PATTERN for EntityPreserver
- **Deterministic Chunk IDs:** Format `{source_file_stem}_chunk_{position:03d}` (no timestamps) - MAINTAIN THIS FORMAT
- **spaCy Lazy Loading:** Model loaded once, cached globally (saves ~1.2s per doc) - EntityPreserver should follow same pattern if using spaCy

**Technical Debt:**
- **AC-3.1-2 Section Detection:** Deferred to this story (3.2) - MUST IMPLEMENT in Task 2
  - Placeholder at `engine.py:252-281` returns empty list
  - Comprehensive deferral rationale documented in docstring
  - Integration test `test_multi_section_document` only checks `len(chunks) >= 1` (not section context) - NEEDS STRENGTHENING in this story

**Files to MODIFY (not recreate):**
- `src/data_extract/chunk/engine.py` - Update _detect_section_boundaries() (Task 2), integrate EntityPreserver (Task 3)
- `src/data_extract/chunk/models.py` - Add entity_tags, section_context, entity_relationships fields to ChunkMetadata (Task 4)
- `tests/unit/test_chunk/test_determinism.py` - Add entity-aware determinism tests (Task 8)

**Files to CREATE:**
- `src/data_extract/chunk/entity_preserver.py` - NEW component (Task 1)
- `tests/unit/test_chunk/test_entity_preserver.py` - NEW test file (Task 5)
- `tests/unit/test_chunk/test_section_detection.py` - NEW test file (Task 6)
- `tests/integration/test_chunk/test_entity_aware_chunking.py` - NEW test file (Task 7)
- `tests/integration/test_chunk/test_section_boundaries.py` - NEW test file (Task 7)
- `tests/fixtures/entity_rich_documents/` - NEW fixture directory

**Performance Baselines (from Story 3.1):**
- Chunking latency: ~0.19s per 1,000 words (linear scaling, 3.0s for 10k words)
- Memory: 255 MB peak for 10k-word document (51% of 500 MB limit)
- spaCy model load: <0.005s cached, <5s cold
- **Targets for Story 3.2:**
  - Entity analysis overhead: <0.3s per 10k words (total latency <3.3s still meets NFR-P3 <4s adjusted threshold)
  - Section detection overhead: <0.1s per document
  - Memory: Maintain <500 MB for individual documents

**Testing Patterns:**
- Use `tests/fixtures/normalized_results/` for ProcessingResult fixtures
- Follow Story 3.1 test organization: unit (90% coverage target), integration (end-to-end), performance (NFR validation)
- Determinism tests: 10 runs, byte-for-byte diff comparison
- Use pytest markers: `-m unit`, `-m integration`, `-m performance`, `-m chunking`

**Quality Gates (0 violations required):**
1. `black src/ tests/` → 0 violations
2. `ruff check src/ tests/` → 0 violations
3. `mypy src/data_extract/` → 0 violations (MUST run from project root, not subdirectory)
4. `pytest -m unit` → All pass (run before commit)
5. Fix violations IMMEDIATELY, do not defer to later stories

**Code Review Findings (to avoid):**
- Story 3.1 received "CHANGES REQUESTED" twice for placeholder implementation marked complete (AC-3.1-2)
- Lesson: Do NOT mark tasks complete if implementation is placeholder/deferred - either implement or explicitly document deferral
- Story 3.1 had 3 mypy type parameter violations missed initially - always run mypy from project root before marking complete

[Source: docs/stories/3-1-semantic-boundary-aware-chunking-engine.md#Dev-Agent-Record, #Senior-Developer-Review, #Change-Log]

### Source Tree Components to Touch

**Files to MODIFY (from Story 3.1):**
- `src/data_extract/chunk/engine.py` - Update _detect_section_boundaries() (Task 2), integrate EntityPreserver (Task 3)
- `src/data_extract/chunk/models.py` - Add entity_tags, section_context, entity_relationships to ChunkMetadata (Task 4)
- `tests/unit/test_chunk/test_determinism.py` - Add entity-aware determinism tests (Task 8)

**Files to CREATE (Greenfield - src/data_extract/chunk/):**
- `src/data_extract/chunk/entity_preserver.py` - EntityPreserver, EntityReference models (PRIMARY)

**Files to REFERENCE (Epic 2 Integration):**
- `src/data_extract/core/models.py` - ProcessingResult input model, Entity model (Epic 2 output)
- `src/data_extract/chunk/sentence_segmenter.py` - SentenceSegmenter (Story 2.5.2)

**Files to CREATE (Testing):**
- `tests/unit/test_chunk/test_entity_preserver.py` - EntityPreserver unit tests
- `tests/unit/test_chunk/test_section_detection.py` - Section detection unit tests
- `tests/integration/test_chunk/test_entity_aware_chunking.py` - Entity-aware integration tests
- `tests/integration/test_chunk/test_section_boundaries.py` - Section boundary integration tests
- `tests/fixtures/entity_rich_documents/` - Entity-rich document fixtures (risk registers, policies)

**Files to MODIFY (Documentation):**
- `CLAUDE.md` - Add entity-aware chunking documentation
- `docs/architecture.md` - Amend ADR-011 with entity-aware and section detection decisions
- `docs/performance-baselines-epic-3.md` - Add entity/section overhead baselines

**No Changes to Brownfield Code:**
- Epic 3 remains pure greenfield development
- All new components in `src/data_extract/chunk/`

### Key Patterns and Anti-Patterns

**Pattern: Entity Gap Optimization (ADOPT)**
- Pre-compute safe split zones (gaps between entities) before chunking
- Prioritize chunk boundaries at entity gaps (no entity fragmentation)
- Graceful degradation: If no gaps available, split at sentence boundaries (maintain AC-3.1-1)
- Example: `entity_gaps = EntityPreserver.find_entity_gaps(entities, text)` → pass to chunk generator

**Pattern: Partial Entity Metadata Enrichment (ADOPT)**
- When entity unavoidably split, enrich BOTH chunks with cross-references
- Metadata includes: is_partial=True, continuation_direction ("from_previous" or "to_next"), adjacent_chunk_id
- Enables downstream reconstruction of full entity context
- Example: Chunk N: entity_tag(is_partial=True, continues_in="doc_chunk_005"), Chunk N+1: entity_tag(is_partial=True, continued_from="doc_chunk_004")

**Pattern: Relationship Triple Storage (ADOPT)**
- Relationships stored as tuples: (entity1_id, relation_type, entity2_id)
- Immutable storage (tuples in frozen dataclass)
- Enables downstream relationship queries (find all chunks with "mitigates" relationships)
- Example: `("RISK-001", "mitigated_by", "CTRL-042")`

**Pattern: Section Hierarchy Breadcrumbs (ADOPT)**
- Section context formatted as breadcrumb trail: "Parent > Child > Grandchild"
- Consistent delimiter (` > `) for parsing
- Empty string if no section context (not null, not "unknown")
- Example: `section_context = "Risk Assessment > Identified Risks > High Severity"`

**Anti-Pattern: Buffering Entity Analysis Results (AVOID)**
- **Problem:** Storing full entity analysis in memory accumulates for large documents
- **Solution:** Analyze entities once, extract needed data (gaps, relationships), discard intermediate results
- **Benefit:** Constant memory usage (streaming architecture maintained)

**Anti-Pattern: Random Entity Boundary Tiebreaking (AVOID)**
- **Problem:** Multiple equivalent split points (same entity gap) → random choice breaks determinism
- **Solution:** Deterministic tiebreaking (prefer earlier position, or closer to chunk_size target)
- **Benefit:** 100% reproducibility maintained (AC-3.2-8)

**Anti-Pattern: Ignoring Section Detection Failures (AVOID)**
- **Problem:** Section detection regex fails silently, returns empty list, no visibility
- **Solution:** Log section detection results (found X sections, patterns matched: ...), log warning if no sections detected but expected
- **Benefit:** Debugging visibility, users understand when section-aware chunking is active

### Testing Strategy

**Test Organization (Mirror src/ Structure):**
```text
tests/
├── unit/test_chunk/                # Fast, isolated tests
│   ├── test_entity_preserver.py    # EntityPreserver logic (NEW)
│   ├── test_section_detection.py   # Section boundary detection (NEW)
│   ├── test_determinism.py         # Entity-aware determinism (EXTEND)
│   └── (existing from Story 3.1)
├── integration/test_chunk/         # Multi-component tests
│   ├── test_entity_aware_chunking.py  # End-to-end entity preservation (NEW)
│   ├── test_section_boundaries.py     # Section-aware chunking (NEW)
│   └── (existing from Story 3.1)
└── performance/test_chunk/         # NFR validation
    ├── test_chunking_latency.py    # Validate <3.3s with entity overhead (EXTEND)
    └── (existing from Story 3.1)
```yaml

**Coverage Target:**
- **Story 3.2:** >90% coverage for `entity_preserver.py` module
- **Updated Coverage:** >90% for entire `src/data_extract/chunk/` module (including Story 3.1 + 3.2)
- **Epic 3 Overall:** >80% (by Story 3.7)
- **CI Threshold:** 60% aggregate (greenfield + brownfield)

**Test Markers:**
- `pytest -m unit` - Fast unit tests
- `pytest -m integration` - Integration tests
- `pytest -m performance` - Performance benchmarks
- `pytest -m chunking` - All chunking-related tests (Story 3.1 + 3.2)
- `pytest -m entity_aware` - Entity-specific tests (NEW marker for Story 3.2)

**Fixture Strategy:**
- Reuse Epic 2 ProcessingResult fixtures (normalized text with entities)
- Create NEW fixtures: `tests/fixtures/entity_rich_documents/` (risk registers, policy docs with many entities)
- Keep total fixture size <100MB
- Document in `tests/fixtures/README.md`

**UAT Workflow Integration:**
1. `workflow create-test-cases` → Generate test cases from Story 3.2 ACs
2. `workflow build-test-context` → Assemble test infrastructure context
3. `workflow execute-tests` → Run automated + manual tests
4. `workflow review-uat-results` → QA review and approval

**UAT Focus:**
- AC-3.2-1: Entity preservation rate >95% (critical)
- AC-3.2-3: Relationship context preservation (critical)
- AC-3.2-7: Section boundary detection (validates deferred AC-3.1-2)
- AC-3.2-8: Determinism maintained (audit trail requirement)

### Project Structure Notes

**Alignment with Unified Project Structure:**
- `src/data_extract/chunk/` - Existing greenfield module from Story 3.1, extended in Story 3.2
- NEW component: `entity_preserver.py` (follows Epic pattern: `{stage}/{component}.py`)
- Consistent with existing structure: `extract/`, `normalize/`, `chunk/`

**Module Organization (Updated):**
```text
src/data_extract/chunk/
├── __init__.py               # Package exports (EXISTING)
├── engine.py                 # ChunkingEngine core component (MODIFY - Story 3.1)
├── models.py                 # Chunk, ChunkMetadata, QualityScore (MODIFY - Story 3.1)
├── sentence_segmenter.py     # SentenceSegmenter wrapper (EXISTING - Story 3.1)
└── entity_preserver.py       # EntityPreserver, EntityReference (NEW - Story 3.2)
```yaml

**No Conflicts Detected:**
- Epic 3 remains pure greenfield (no brownfield dependencies)
- No namespace collisions with Epic 1/2 modules
- EntityPreserver integrates cleanly with ChunkingEngine (dependency injection pattern)

### References

**Technical Specifications:**
- [Source: docs/tech-spec-epic-3.md#Section-2.2] - ChunkingEngine Design (Story 3.1 baseline)
- [Source: docs/tech-spec-epic-3.md#Section-2.2] - EntityPreserver Design
- [Source: docs/tech-spec-epic-3.md#Section-2.3] - Data Models (EntityReference, ChunkMetadata extensions)
- [Source: docs/tech-spec-epic-3.md#Section-3.1] - NFR-P3 (Chunking Latency <2 sec, extended to <3.3s with entity overhead)
- [Source: docs/tech-spec-epic-3.md#Section-3.1] - NFR-P4 (Deterministic Chunking)
- [Source: docs/tech-spec-epic-3.md#Section-5.1] - Story 3.2 Acceptance Criteria

**Product Requirements:**
- [Source: docs/PRD/index.md#NFR-P1] - NFR-P1 throughput requirements (<10 min for 100 files)
- [Source: docs/PRD/index.md#NFR-P2] - NFR-P2 memory requirements (<2GB individual, 4.15GB batch from Epic 2)
- [Source: docs/PRD/index.md#NFR-R1] - NFR-R1 continue-on-error pattern (graceful degradation)

**Architecture Decisions:**
- [Source: docs/architecture.md#ADR-001] - Immutable models prevent pipeline state corruption
- [Source: docs/architecture.md#ADR-006] - Streaming pipeline for memory efficiency
- [Source: docs/architecture.md#ADR-011] - Semantic Boundary-Aware Chunking (Story 3.1, to be amended in Story 3.2)

**Dependencies:**
- [Source: src/data_extract/core/models.py] - ProcessingResult, Entity (Epic 2 output models)
- [Source: src/data_extract/chunk/engine.py] - ChunkingEngine (Story 3.1)
- [Source: src/data_extract/chunk/sentence_segmenter.py] - SentenceSegmenter (Story 2.5.2)
- [Source: docs/stories/3-1-semantic-boundary-aware-chunking-engine.md] - Story 3.1 implementation details, deferred AC-3.1-2

**Performance Baselines:**
- [Source: docs/performance-baselines-epic-3.md] - Story 3.1 chunking baselines (0.19s per 1k words, 255 MB memory)
- [Source: docs/performance-baselines-story-2.5.1.md] - Epic 2 performance baselines (14.57 files/min, 4.15GB batch)

**Testing Infrastructure:**
- [Source: docs/test-design-epic-3.md#Section-2] - Risk Assessment (R-001, R-003, R-005, R-006, R-007)
- [Source: docs/test-design-epic-3.md#Section-3] - Test Coverage Plan (P0, P1, P2 tests)
- [Source: CLAUDE.md#Testing-Strategy] - Test organization, markers, coverage requirements

**Related Stories:**
- [Source: docs/stories/3-1-semantic-boundary-aware-chunking-engine.md] - Story 3.1 baseline chunking (AC-3.1-2 deferred)
- [Source: docs/stories/2.5-2-spacy-integration-and-end-to-end-testing.md] - spaCy integration (SentenceSegmenter)
- [Source: docs/stories/2.5-4-ci-cd-enhancement-for-epic-3-readiness.md] - CI/CD maturity, quality gates

## Change Log

- **2025-11-14:** Story 3.2 created - Entity-Aware Chunking with Section Boundary Detection
  - 8 acceptance criteria defined: entity preservation, partial entity tracking, relationship context, entity definition boundaries, entity IDs, entity metadata, section detection (deferred AC-3.1-2), determinism
  - 9 tasks with detailed subtasks covering EntityPreserver implementation, section detection, testing, documentation
  - Incorporates deferred AC-3.1-2 from Story 3.1 (section boundary detection)
  - Targets NFR-P3 (<3.3 sec per 10k words with entity overhead), NFR-P4 (100% determinism), >95% entity preservation rate
  - Builds on Story 3.1 (ChunkingEngine operational, 81/81 tests passing, under final review)
  - All Epic 3 prerequisites satisfied by Story 3.1 and Epic 2.5 completion

## Dev Agent Record

### Context Reference

- `docs/stories/3-2-entity-aware-chunking.context.xml` (Generated: 2025-11-14)

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

### Completion Notes

**Completed:** 2025-11-14
**Definition of Done:** All acceptance criteria met (8/8), 120/120 automated tests passed (100%), quality gates passed (black/ruff/mypy 0 violations), performance requirements exceeded (NFR-P3: 43% margin, NFR-P2: 47% margin), UAT review APPROVED, code reviewed and production-ready.

**UAT Review:** docs/uat/reviews/3.2-uat-review.md (APPROVED)
**Test Results:** docs/uat/test-results/3-2-test-results.md (100% pass rate)
**Entity Preservation Rate:** >95% achieved across all test scenarios
**Section Detection:** Implements deferred AC-3.1-2 from Story 3.1

### Completion Notes List

### File List
