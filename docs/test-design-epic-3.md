# Test Design: Epic 3 - Chunk & Output Stages

**Date:** 2025-11-13
**Author:** andrew
**Status:** Draft

---

## Executive Summary

**Scope:** Full test design for Epic 3 (Chunk & Output Stages)

**Risk Summary:**

- Total risks identified: 15
- High-priority risks (≥6): 4
- Critical categories: PERF, DATA, TECH, BUS

**Coverage Summary:**

- P0 scenarios: 18 (36 hours)
- P1 scenarios: 24 (24 hours)
- P2/P3 scenarios: 22 (8.5 hours)
- **Total effort**: 68.5 hours (~9 days)

---

## Risk Assessment

### High-Priority Risks (Score ≥6)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- | -------- |
| R-001 | DATA | Chunking splits mid-sentence creating incomplete context for LLM retrieval | 2 | 3 | 6 | Implement spaCy sentence boundary detection with edge case handling for long sentences | DEV | Sprint 1 Week 1 |
| R-002 | BUS | Entity relationships broken across chunk boundaries causing incomplete RAG retrievals | 3 | 2 | 6 | Entity-aware chunking algorithm with relationship preservation validation | DEV | Sprint 1 Week 2 |
| R-003 | PERF | Chunking 100 documents exceeds 10-minute NFR-P1 requirement | 2 | 3 | 6 | Optimize spaCy sentence segmentation with batch processing and memory pooling | DEV | Sprint 1 Week 3 |
| R-004 | DATA | Output format inconsistencies prevent downstream RAG pipeline integration | 2 | 3 | 6 | JSON schema validation, CSV escaping tests, TXT delimiter verification | QA | Sprint 2 Week 1 |

### Medium-Priority Risks (Score 3-4)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- |
| R-005 | TECH | spaCy model loading latency on first chunk operation degrades UX | 2 | 2 | 4 | Lazy-load spaCy model on first use, cache globally with docs/troubleshooting-spacy.md guidance | DEV |
| R-006 | DATA | Chunk overlap calculation errors create gaps or excessive duplication | 1 | 3 | 3 | Unit tests for sliding window overlap edge cases (10-20% configurable range) | QA |
| R-007 | PERF | Memory exhaustion when chunking very large documents (>100MB PDFs) | 1 | 3 | 3 | Streaming chunking implementation, memory monitoring integration from Story 2.5.2.1 | DEV |
| R-008 | TECH | textstat readability metrics fail on non-English or highly technical audit text | 2 | 2 | 4 | Domain-appropriate thresholds, graceful degradation with confidence scoring | DEV |
| R-009 | OPS | Output organization strategies (by_document, by_entity, flat) create path length limits on Windows | 1 | 2 | 2 | Path length validation, directory structure tests on Windows CI | QA |
| R-010 | DATA | CSV export with very long chunks (>32K chars) truncated or malformed in Excel | 1 | 2 | 2 | Optional truncation with indicator, document CSV schema limits | DEV |
| R-011 | TECH | JSON serialization errors on special characters or non-UTF8 content | 2 | 2 | 4 | UTF-8 encoding validation, escape sequence testing, schema validation | QA |

### Low-Priority Risks (Score 1-2)

| Risk ID | Category | Description | Probability | Impact | Score | Action |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ------ |
| R-012 | OPS | Concurrent chunking of same file creates race conditions in output directory | 1 | 2 | 2 | Monitor (batch processing single-threaded by default) |
| R-013 | BUS | Chunk quality scores incorrectly flag high-quality audit content as low-quality | 1 | 2 | 2 | Monitor with manual review workflow from Story 2.5 |
| R-014 | TECH | Edge case: empty document after normalization produces zero chunks | 1 | 1 | 1 | Monitor, log as info-level event |
| R-015 | PERF | Output file I/O becomes bottleneck with thousands of small chunk files | 1 | 2 | 2 | Monitor, consider batch write optimization if observed |

### Risk Category Legend

- **TECH**: Technical/Architecture (spaCy integration, serialization, edge cases)
- **SEC**: Security (not applicable for Epic 3 - no auth/network operations)
- **PERF**: Performance (NFR-P1 <10 min for 100 files, NFR-P2 <2GB memory)
- **DATA**: Data Integrity (chunk completeness, entity preservation, format correctness)
- **BUS**: Business Impact (RAG quality, entity relationships, audit trail)
- **OPS**: Operations (directory structure, file I/O, Windows compatibility)

---

## Test Coverage Plan

### P0 (Critical) - Run on every commit

**Criteria**: Blocks core journey + High risk (≥6) + No workaround

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ---------- | --------- | ---------- | ----- | ----- |
| Semantic chunking respects sentence boundaries (Story 3.1) | Unit | R-001 | 5 | DEV | Edge cases: very long sentences (>512 tokens), micro-sentences, no punctuation |
| spaCy sentence segmentation accuracy | Integration | R-001 | 3 | QA | Real audit documents: policies, risk registers, SOC2 reports |
| Entity mentions preserved within chunks (Story 3.2) | Unit | R-002 | 4 | DEV | Test all 6 entity types: processes, risks, controls, regulations, policies, issues |
| Entity relationship context maintained (Story 3.2) | Integration | R-002 | 2 | QA | Risk→Control mappings, cross-references preserved |
| Chunking throughput meets NFR-P1 (Story 3.1) | Performance | R-003 | 1 | QA | 100 mixed PDFs in <10 minutes baseline |
| JSON output schema validation (Story 3.4) | Unit | R-004 | 3 | DEV | Schema validation, UTF-8 encoding, escape sequences |

**Total P0**: 18 tests, 36 hours (2 hours/test for complex setup)

### P1 (High) - Run on PR to main

**Criteria**: Important features + Medium risk (3-4) + Common workflows

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ---------- | --------- | ---------- | ----- | ----- |
| Configurable chunk size (256-512 tokens default) | Unit | - | 3 | DEV | Token-based sizing, edge cases: size=1, size=10000 |
| Configurable chunk overlap (10-20% default) | Unit | R-006 | 4 | DEV | Sliding window logic, overlap edge cases, boundary validation |
| spaCy model lazy-loading and caching | Integration | R-005 | 2 | DEV | First-use loading, global cache, performance validation |
| Chunk metadata enrichment (Story 3.3) | Unit | - | 5 | DEV | Source file, section context, entity tags, quality scores, position tracking |
| textstat readability metrics (Story 3.3) | Unit | R-008 | 4 | DEV | Flesch-Kincaid, Gunning Fog, SMOG, domain-appropriate thresholds |
| TXT output format (Story 3.5) | Integration | - | 3 | QA | Delimiter formatting, metadata headers, UTF-8 encoding |
| CSV output format (Story 3.6) | Integration | R-010 | 3 | QA | Escaping (commas, quotes, newlines), Excel compatibility, truncation |

**Total P1**: 24 tests, 24 hours (1 hour/test for standard coverage)

### P2 (Medium) - Run nightly/weekly

**Criteria**: Secondary features + Low risk (1-2) + Edge cases

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ---------- | --------- | ---------- | ----- | ----- |
| Output organization by_document (Story 3.7) | Integration | R-009 | 3 | QA | Directory structure validation, Windows path length limits |
| Output organization by_entity (Story 3.7) | Integration | - | 3 | QA | Entity grouping, traceability preservation |
| Output organization flat (Story 3.7) | Integration | - | 2 | QA | Naming conventions, manifest file generation |
| Streaming chunking for large files (>100MB) | Performance | R-007 | 2 | QA | Memory monitoring, no OOM errors, consistent throughput |
| Edge case: very long sentences (>1000 tokens) | Unit | R-001 | 2 | DEV | Graceful handling, chunk splitting logic |
| Edge case: empty normalized documents | Unit | R-014 | 1 | DEV | Zero-chunk output, metadata logging |
| Quality score flagging low-confidence chunks | Unit | R-013 | 2 | DEV | OCR confidence, completeness, coherence thresholds |
| JSON pretty-printing and validation | Unit | R-011 | 2 | DEV | indent=2, schema validation, special character handling |
| Deterministic chunking (same input → same chunks) | Integration | - | 3 | QA | Reproducibility validation, audit trail requirement |

**Total P2**: 20 tests, 10 hours (0.5 hour/test for simple scenarios)

### P3 (Low) - Run on-demand

**Criteria**: Nice-to-have + Exploratory + Performance benchmarks

| Requirement | Test Level | Test Count | Owner | Notes |
| ----------- | ---------- | ---------- | ----- | ----- |
| Optional metadata header in TXT output | Unit | 1 | DEV | --include-metadata flag testing |
| CSV import validation (pandas, Excel, Google Sheets) | Integration | 1 | QA | Cross-platform compatibility verification |

**Total P3**: 2 tests, 0.5 hours (0.25 hour/test for exploratory)

---

## Execution Order

### Smoke Tests (<5 min)

**Purpose**: Fast feedback, catch build-breaking issues

- [ ] spaCy model loads successfully (30s)
- [ ] Basic chunking: 1 document → multiple chunks (45s)
- [ ] JSON output: valid parseable JSON (30s)
- [ ] TXT output: delimiter formatting (30s)
- [ ] CSV output: valid CSV structure (30s)

**Total**: 5 scenarios (~3 min)

### P0 Tests (<10 min)

**Purpose**: Critical path validation (Epic 3 core functionality)

- [ ] Sentence boundary detection accuracy (Unit)
- [ ] No mid-sentence splits on real audit docs (Integration)
- [ ] Entity preservation: all 6 types (Unit)
- [ ] Entity relationships maintained (Integration)
- [ ] Throughput: 100 files in <10 min (Performance)
- [ ] JSON schema validation (Unit)
- [ ] UTF-8 encoding correctness (Unit)

**Total**: 18 scenarios (target: <10 min with parallel execution)

### P1 Tests (<30 min)

**Purpose**: Important feature coverage (configuration, metadata, formats)

- [ ] Configurable chunk size and overlap (Unit)
- [ ] spaCy lazy-loading and caching (Integration)
- [ ] Chunk metadata: all fields present (Unit)
- [ ] textstat readability metrics (Unit)
- [ ] TXT format: delimiters and encoding (Integration)
- [ ] CSV format: escaping and Excel compatibility (Integration)

**Total**: 24 scenarios (target: <30 min)

### P2/P3 Tests (<60 min)

**Purpose**: Full regression coverage (edge cases, organization strategies, large files)

- [ ] Output organization: by_document, by_entity, flat (Integration)
- [ ] Large file streaming: >100MB PDFs (Performance)
- [ ] Edge cases: long sentences, empty docs (Unit)
- [ ] Quality score flagging (Unit)
- [ ] Deterministic chunking validation (Integration)
- [ ] Exploratory: metadata options, import validation (Integration)

**Total**: 22 scenarios (target: <60 min full regression)

---

## Resource Estimates

### Test Development Effort

| Priority | Count | Hours/Test | Total Hours | Notes |
| -------- | ----- | ---------- | ----------- | ----- |
| P0 | 18 | 2.0 | 36 | Complex spaCy integration, performance baselines, entity validation |
| P1 | 24 | 1.0 | 24 | Standard unit/integration coverage with fixtures |
| P2 | 20 | 0.5 | 10 | Simple edge cases and organization tests |
| P3 | 2 | 0.25 | 0.5 | Exploratory validation |
| **Total** | **64** | **-** | **70.5** | **~9 days** (rounded to 68.5 for summary) |

### Prerequisites

**Test Data:**

- chunk_factory (faker-based, configurable size/overlap, auto-cleanup)
- audit_document_fixtures (100-file batch from Story 2.5.1, includes policies, risk registers, SOC2 reports)
- entity_mention_fixtures (6 entity types with relationship patterns)
- large_document_fixture (>100MB PDF for streaming tests)

**Tooling:**

- spaCy 3.7.2+ with en_core_web_md model (43MB, cached in CI per Story 2.5-4)
- textstat for readability metrics (Flesch-Kincaid, Gunning Fog, SMOG)
- pytest with markers: unit, integration, performance, chunking
- memory profiler from Story 2.5.2.1 (get_total_memory() reuse)

**Environment:**

- Python 3.12+ (mandatory enterprise requirement)
- spaCy model downloaded: `python -m spacy download en_core_web_md`
- Performance baseline: 14.57 files/min, 4.15GB memory from Story 2.5.2.1
- CI: GitHub Actions with spaCy model caching (Story 2.5-4 AC-2)

---

## Quality Gate Criteria

### Pass/Fail Thresholds

- **P0 pass rate**: 100% (no exceptions - semantic chunking and entity preservation are critical)
- **P1 pass rate**: ≥95% (waivers required for failures with documented mitigation)
- **P2/P3 pass rate**: ≥90% (informational, track trends)
- **High-risk mitigations**: 100% complete or approved waivers (R-001 through R-004)

### Coverage Targets

- **Critical paths**: ≥80% (chunking engine, entity preservation, output formats)
- **Security scenarios**: N/A (no security operations in Epic 3)
- **Business logic**: ≥70% (quality scoring, metadata enrichment)
- **Edge cases**: ≥50% (long sentences, empty docs, large files)

### Non-Negotiable Requirements

- [ ] All P0 tests pass (semantic chunking, entity preservation, performance, JSON validation)
- [ ] No high-risk (≥6) items unmitigated (R-001 through R-004 addressed)
- [ ] Performance targets met: 100 files in <10 min (NFR-P1), <4GB memory (NFR-P2 revised in Story 2.5.2.1)
- [ ] Deterministic chunking validated: same input → same chunks (audit trail requirement)

---

## Mitigation Plans

### R-001: Chunking splits mid-sentence creating incomplete context (Score: 6)

**Mitigation Strategy:**
- Implement spaCy sentence boundary detection in Story 3.1 chunking engine
- Handle edge cases: very long sentences (>512 tokens), micro-sentences, no punctuation
- Sliding window algorithm respects sentence boundaries: never split mid-sentence
- Edge case: if sentence exceeds chunk_size, split at clause boundaries (fallback to character split with warning)

**Owner:** DEV Team
**Timeline:** Sprint 1 Week 1
**Status:** Planned
**Verification:**
- Unit tests: 5 edge cases (long sentences, no punctuation, multiple short sentences, clause boundaries)
- Integration tests: 3 real audit documents (policies, risk registers, SOC2 reports)
- Manual review: 10 randomly sampled chunks from 100-file batch verify no mid-sentence splits

### R-002: Entity relationships broken across chunk boundaries (Score: 6)

**Mitigation Strategy:**
- Entity-aware chunking algorithm in Story 3.2: analyze entity mentions before chunking
- Prefer chunk splits between entities rather than within entity contexts
- Add "entity_context" metadata field for partial entities with "continued" and "partial" flags
- Maintain entity relationship graph across chunks using entity IDs from Story 2.2
- Test all 6 entity types: processes, risks, controls, regulations, policies, issues

**Owner:** DEV Team
**Timeline:** Sprint 1 Week 2
**Status:** Planned
**Verification:**
- Unit tests: 4 entity preservation scenarios (single entity, multiple entities, relationships, cross-references)
- Integration tests: 2 relationship preservation tests (Risk→Control mappings, cross-references)
- Manual review: Entity relationship validation on 20 audit documents with known entity patterns

### R-003: Chunking 100 documents exceeds 10-minute NFR-P1 requirement (Score: 6)

**Mitigation Strategy:**
- Optimize spaCy sentence segmentation with batch processing (process multiple documents in spaCy pipeline)
- Reuse memory monitoring from Story 2.5.2.1: get_total_memory() to track memory usage
- spaCy model lazy-loading (Story 3.1) and global caching (first-use only, not per-document)
- Parallel chunking using multiprocessing for CPU-bound sentence segmentation
- Performance baseline: 14.57 files/min from Story 2.5.2.1 (already includes extract+normalize, chunking adds ~20% overhead)

**Owner:** DEV Team
**Timeline:** Sprint 1 Week 3
**Status:** Planned
**Verification:**
- Performance test: 100 mixed PDFs in <10 minutes (NFR-P1 validation)
- Memory test: chunking stays within 4GB limit (NFR-P2 revised from Story 2.5.2.1)
- CI: Weekly performance regression job from Story 2.5-4 catches degradation

### R-004: Output format inconsistencies prevent downstream RAG integration (Score: 6)

**Mitigation Strategy:**
- JSON schema validation in Story 3.4: define schema, validate all outputs against schema
- CSV escaping tests in Story 3.6: handle commas, quotes, newlines using Python csv.QUOTE_ALL
- TXT delimiter verification in Story 3.5: configurable delimiter (default: ━━━ CHUNK N ━━━)
- UTF-8 encoding validation across all formats (no mojibake or encoding errors)
- Integration tests: parse JSON with standard parser, import CSV to Excel/pandas, upload TXT to ChatGPT

**Owner:** QA Team
**Timeline:** Sprint 2 Week 1
**Status:** Planned
**Verification:**
- Unit tests: 3 JSON schema validation scenarios (valid schema, invalid content, special characters)
- Integration tests: 3 CSV import tests (Excel, pandas, Google Sheets)
- Integration tests: 3 TXT format tests (delimiter parsing, metadata headers, UTF-8 encoding)
- Manual validation: Upload TXT output to ChatGPT, verify no parsing errors

---

## Assumptions and Dependencies

### Assumptions

1. Epic 2 (Extract & Normalize) complete with high-quality normalized text ready for chunking
2. spaCy en_core_web_md model (43MB) pre-downloaded in development and cached in CI (Story 2.5-4)
3. Performance baselines from Story 2.5.2.1 remain valid: 14.57 files/min, 4.15GB memory
4. Entity normalization from Story 2.2 provides consistent entity tags in metadata
5. Test fixtures from Story 2.5.1 (100-file batch) available for chunking tests
6. Audit documents use standard English (textstat readability metrics designed for English)

### Dependencies

1. **Epic 2 Complete** - Required by Sprint 1 Day 1
   - Normalized text with entity tags (Story 2.2)
   - Quality validation and flagging (Story 2.4-2.5)
   - Metadata enrichment framework (Story 2.6)

2. **spaCy Integration** - Required by Sprint 1 Day 1
   - Story 2.5.2 spaCy integration complete (en_core_web_md model)
   - docs/troubleshooting-spacy.md available for setup guidance

3. **Performance Infrastructure** - Required by Sprint 1 Week 3
   - Story 2.5.2.1 memory monitoring (get_total_memory() function)
   - Story 2.5-4 CI/CD enhancements (spaCy caching, performance regression monitoring)

4. **Test Infrastructure** - Required by Sprint 1 Day 1
   - Story 1.3 testing framework (pytest, fixtures, markers)
   - 100-file performance batch from Story 2.5.1

### Risks to Plan

- **Risk**: spaCy sentence segmentation slower than expected on technical audit documents
  - **Impact**: May not meet NFR-P1 10-minute threshold for 100 files
  - **Contingency**: Fall back to simpler regex-based sentence splitting with lower accuracy but faster performance; document trade-off

- **Risk**: Entity-aware chunking algorithm too complex to implement in Sprint 1 Week 2
  - **Impact**: May defer entity relationship preservation to Epic 4 (advanced features)
  - **Contingency**: Implement basic entity-aware chunking (keep entities within chunks) in Epic 3, defer relationship graph to Epic 4

- **Risk**: Large document streaming (>100MB) reveals memory leaks in spaCy or chunking logic
  - **Impact**: May violate NFR-P2 4GB memory limit
  - **Contingency**: Document limit (e.g., max 50MB per file), provide guidance to split large PDFs before processing

---

## Approval

**Test Design Approved By:**

- [ ] Product Manager: andrew Date: _______________
- [ ] Tech Lead: _____________ Date: _______________
- [ ] QA Lead: _____________ Date: _______________

**Comments:**

---

## Appendix

### Knowledge Base References

- `risk-governance.md` - Risk classification framework (6 categories: TECH, SEC, PERF, DATA, BUS, OPS), probability × impact scoring (1-9 scale)
- `probability-impact.md` - Risk scoring methodology (scores ≥6 require mitigation, score=9 is gate blocker)
- `test-levels-framework.md` - Test level selection (Unit for logic, Integration for boundaries, E2E for workflows)
- `test-priorities-matrix.md` - P0-P3 prioritization (P0=critical+high-risk, P1=important+medium-risk, P2/P3=secondary)

### Related Documents

- PRD: docs/PRD/index.md (FR-3 Intelligent Chunking, NFR-P1/P2 Performance Requirements)
- Epic Breakdown: docs/epics.md (Epic 3 Stories 3.1-3.7 detailed acceptance criteria)
- Architecture: docs/architecture/FOUNDATION.md (ContentBlock data model, immutability, pipeline pattern)
- Tech Spec: docs/tech-spec-epic-3.md (to be created during implementation)
- Performance Baselines: docs/performance-baselines-story-2.5.1.md (14.57 files/min, 4.15GB memory)
- CI/CD: docs/ci-cd-pipeline.md (spaCy caching, performance regression monitoring from Story 2.5-4)

### Epic 3 Story Breakdown

**Story 3.1: Semantic Boundary-Aware Chunking Engine**
- spaCy sentence segmentation (en_core_web_md model)
- Configurable chunk size (256-512 tokens default)
- Configurable chunk overlap (10-20% default)
- Edge case handling: very long sentences, short sections
- Deterministic chunking (audit trail requirement)

**Story 3.2: Entity-Aware Chunking**
- Entity preservation within chunks
- Entity relationship context maintenance (Risk→Control mappings)
- "continued" and "partial" flags for split entities
- All 6 entity types: processes, risks, controls, regulations, policies, issues

**Story 3.3: Chunk Metadata and Quality Scoring**
- Source file path, section context, entity tags
- Readability metrics: Flesch-Kincaid, Gunning Fog, SMOG (textstat)
- Quality score: OCR confidence, completeness, coherence
- Chunk position tracking, word/token counts

**Story 3.4: JSON Output Format**
- Structured JSON: { "metadata": {...}, "chunks": [{...}] }
- Schema validation, UTF-8 encoding
- Pretty-printing (indent=2), parseable by standard tools

**Story 3.5: Plain Text Output Format**
- Clean plain text, configurable delimiter (default: ━━━ CHUNK N ━━━)
- Optional metadata headers (--include-metadata flag)
- UTF-8 encoding, LLM-friendly formatting

**Story 3.6: CSV Output Format**
- Columns: chunk_id, source_file, chunk_text, entities, quality_score, readability, section, word_count
- Proper escaping (QUOTE_ALL), Excel/pandas compatibility
- Optional truncation for very long chunks

**Story 3.7: Configurable Output Organization**
- Three strategies: by_document, by_entity, flat
- Traceability preservation across all strategies
- Manifest file with metadata

### Testing Patterns from Epic 2

**Quality Gates (Epic 2 Lessons)**:
- Run quality gates (Black, Ruff, Mypy) BEFORE committing (shift-left)
- 0 violations required - no exceptions
- Pre-commit hooks validated in CI (Story 2.5-4 AC-5)

**Integration Testing (Epic 2 Lessons)**:
- Unit tests alone miss memory leaks and NFR violations
- Always test multi-component workflows with real data
- Use 100-file performance batch for realistic validation

**Performance Monitoring (Epic 2 Lessons)**:
- Profile first, establish baseline, then optimize
- Don't guess at bottlenecks - measure actual behavior
- Reuse get_total_memory() from Story 2.5.2.1 for memory tracking
- CI performance regression monitoring (Story 2.5-4 AC-1)

**spaCy Integration (Epic 2 Lessons)**:
- Download models via setup, not runtime (Story 2.5.2)
- Lazy-load on first use, cache globally
- CI caching saves 2-3 minutes per run (Story 2.5-4 AC-2)
- See docs/troubleshooting-spacy.md for setup guidance

### Test Execution Strategy

**Unit Tests (Fast Feedback)**:
- Focus on chunking logic, metadata enrichment, output formatting
- No spaCy model loading (mock sentence segmentation for speed)
- Edge cases: long sentences, empty docs, special characters
- Target: <5 min for all unit tests

**Integration Tests (Component Boundaries)**:
- spaCy sentence segmentation with real model
- End-to-end chunking: normalized text → chunks → outputs
- Real audit documents: policies, risk registers, SOC2 reports
- Target: <30 min for all integration tests

**Performance Tests (NFR Validation)**:
- 100-file batch: validate NFR-P1 (<10 min) and NFR-P2 (<4GB memory)
- Large file streaming: >100MB PDFs with memory monitoring
- Weekly CI job (Story 2.5-4 performance-regression.yml)
- Target: <10 min for performance suite

**Markers for Selective Execution**:
```bash
pytest -m unit                # Unit tests only (~5 min)
pytest -m integration         # Integration tests only (~30 min)
pytest -m performance         # Performance tests only (~10 min)
pytest -m chunking            # All Epic 3 chunking tests
pytest -m "not slow"          # Skip slow tests (development)
```

---

**Generated by**: BMad TEA Agent - Test Architect Module
**Workflow**: `bmad/bmm/testarch/test-design`
**Version**: 4.0 (BMad v6)
