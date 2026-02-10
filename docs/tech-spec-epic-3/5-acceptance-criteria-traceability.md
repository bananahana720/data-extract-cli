# 5. Acceptance Criteria & Traceability

## 5.1 Story-Level Acceptance Criteria

Epic 3 comprises 7 stories with comprehensive acceptance criteria mapped to the 10-step UAT workflow approved in party-mode discussion.

**UAT Workflow Integration:**
- **Stories 3-1, 3-2, 3-3:** Core chunking logic - Dev executes tests, SM reviews UAT results
- **Stories 3-4, 3-5, 3-6:** Output formats - Dev executes tests, SM reviews UAT results
- **Story 3-7:** Organization strategies - Dev executes tests, SM reviews UAT results
- **Quality Gates:** Pre-commit (0 violations) → CI (60% coverage) → UAT (90% pass rate)

### Story 3.1: Semantic Boundary-Aware Chunking Engine

**Acceptance Criteria:**

| AC ID | Acceptance Criterion | Component | Test Type | UAT Required |
|-------|---------------------|-----------|-----------|--------------|
| AC-3.1-1 | Chunks never split mid-sentence | ChunkingEngine | Unit, Integration | Yes - Critical |
| AC-3.1-2 | Section boundaries respected when possible | ChunkingEngine | Integration | Yes |
| AC-3.1-3 | Chunk size configurable (default: 256-512 tokens) | ChunkingEngine | Unit | No - Unit test sufficient |
| AC-3.1-4 | Chunk overlap configurable (default: 10-20%) | ChunkingEngine | Unit | No - Unit test sufficient |
| AC-3.1-5 | Sentence tokenization uses spaCy | ChunkingEngine | Unit | No - Integration tested |
| AC-3.1-6 | Edge cases handled (long sentences, short sections) | ChunkingEngine | Unit, Integration | Yes |
| AC-3.1-7 | Chunking is deterministic (same input → same chunks) | ChunkingEngine | Unit, Performance | Yes - Critical |

**UAT Focus:** Determinism validation, sentence boundary preservation, edge case handling

### Story 3.2: Entity-Aware Chunking

**Acceptance Criteria:**

| AC ID | Acceptance Criterion | Component | Test Type | UAT Required |
|-------|---------------------|-----------|-----------|--------------|
| AC-3.2-1 | Entity mentions kept within single chunks when possible | EntityPreserver | Integration | Yes |
| AC-3.2-2 | Entities split across chunks noted in metadata | EntityPreserver, ChunkMetadata | Integration | Yes |
| AC-3.2-3 | Relationship context preserved | EntityPreserver | Integration | Yes - Critical |
| AC-3.2-4 | Chunk boundaries avoid splitting entity definitions | EntityPreserver | Integration | Yes |
| AC-3.2-5 | Cross-references maintained with entity IDs | EntityPreserver | Integration | No - Metadata validation |
| AC-3.2-6 | Entity tags in chunk metadata | ChunkMetadata | Unit | No - Unit test sufficient |

**UAT Focus:** Entity preservation rate, relationship context validation, partial entity flagging

### Story 3.3: Chunk Metadata and Quality Scoring

**Acceptance Criteria:**

| AC ID | Acceptance Criterion | Component | Test Type | UAT Required |
|-------|---------------------|-----------|-----------|--------------|
| AC-3.3-1 | Chunk includes source document and file path | ChunkMetadata | Unit | No - Unit test sufficient |
| AC-3.3-2 | Section/heading context included | ChunkMetadata | Integration | No - Metadata validation |
| AC-3.3-3 | Entity tags list all entities in chunk | ChunkMetadata | Integration | No - Covered by AC-3.2-6 |
| AC-3.3-4 | Readability score calculated (FK, Gunning Fog) | MetadataEnricher | Unit | Yes - Sample validation |
| AC-3.3-5 | Quality score combines OCR, completeness, coherence | MetadataEnricher | Unit, Integration | Yes |
| AC-3.3-6 | Chunk position tracked (sequential index) | ChunkMetadata | Unit | No - Unit test sufficient |
| AC-3.3-7 | Word count and token count included | ChunkMetadata | Unit | No - Unit test sufficient |
| AC-3.3-8 | Low-quality chunks flagged with issues | MetadataEnricher | Integration | Yes |

**UAT Focus:** Quality score accuracy, readability metrics validation, quality flag correctness

### Story 3.4: JSON Output Format with Full Metadata

**Acceptance Criteria:**

| AC ID | Acceptance Criterion | Component | Test Type | UAT Required |
|-------|---------------------|-----------|-----------|--------------|
| AC-3.4-1 | JSON structure includes chunk text and metadata | JsonFormatter | Unit, Integration | Yes - Schema validation |
| AC-3.4-2 | Output is valid, parsable JSON (not JSON Lines) | JsonFormatter | Unit | Yes - Format validation |
| AC-3.4-3 | Metadata includes all fields | JsonFormatter | Unit | No - Schema test |
| AC-3.4-4 | JSON is pretty-printed (human readable) | JsonFormatter | Unit | No - Visual inspection in dev |
| AC-3.4-5 | Array of chunks filterable/queryable | JsonFormatter | Integration | Yes - jq query tests |
| AC-3.4-6 | Configuration and version in JSON header | JsonFormatter | Unit | No - Unit test sufficient |
| AC-3.4-7 | JSON validates against schema | JsonFormatter | Unit | Yes - Critical |

**UAT Focus:** JSON schema validation, parsability, metadata completeness

### Story 3.5: Plain Text Output Format for LLM Upload

**Acceptance Criteria:**

| AC ID | Acceptance Criterion | Component | Test Type | UAT Required |
|-------|---------------------|-----------|-----------|--------------|
| AC-3.5-1 | Each chunk is clean plain text | TxtFormatter | Unit | Yes - Manual review sample |
| AC-3.5-2 | Chunks separated by configurable delimiter | TxtFormatter | Unit | No - Unit test sufficient |
| AC-3.5-3 | Optional metadata header per chunk | TxtFormatter | Unit | Yes - Format validation |
| AC-3.5-4 | Output organization: concat OR separate files | TxtFormatter | Integration | Yes |
| AC-3.5-5 | Character encoding is UTF-8 | TxtFormatter | Unit | No - Encoding test |
| AC-3.5-6 | No formatting artifacts | TxtFormatter | Integration | Yes - Manual review |
| AC-3.5-7 | TXT files ready for copy-paste/upload | TxtFormatter | UAT Manual | Yes - Critical |

**UAT Focus:** LLM upload readiness (manual test with ChatGPT/Claude), formatting cleanliness

### Story 3.6: CSV Output Format for Analysis and Tracking

**Acceptance Criteria:**

| AC ID | Acceptance Criterion | Component | Test Type | UAT Required |
|-------|---------------------|-----------|-----------|--------------|
| AC-3.6-1 | CSV has required columns | CsvFormatter | Unit | No - Schema test |
| AC-3.6-2 | CSV properly escaped (commas, quotes, newlines) | CsvFormatter | Unit | Yes - Excel import test |
| AC-3.6-3 | Header row labels columns clearly | CsvFormatter | Unit | No - Visual inspection |
| AC-3.6-4 | CSV importable to Excel, Sheets, pandas | CsvFormatter | Integration | Yes - Critical |
| AC-3.6-5 | Long text optionally truncated with indicator | CsvFormatter | Unit | No - Unit test sufficient |
| AC-3.6-6 | Entity lists formatted as semicolon-separated | CsvFormatter | Unit | No - Format test |
| AC-3.6-7 | CSV validates with standard parsers | CsvFormatter | Unit | Yes - Parser validation |

**UAT Focus:** Excel/Sheets import success, CSV parser validation, escaping correctness

### Story 3.7: Configurable Output Organization Strategies

**Acceptance Criteria:**

| AC ID | Acceptance Criterion | Component | Test Type | UAT Required |
|-------|---------------------|-----------|-----------|--------------|
| AC-3.7-1 | Three strategies supported (by_document, by_entity, flat) | Organizer | Unit | Yes - All 3 tested |
| AC-3.7-2 | by_document creates folder per source file | Organizer | Integration | Yes |
| AC-3.7-3 | by_entity groups chunks by entity type | Organizer | Integration | Yes |
| AC-3.7-4 | flat puts chunks in single directory | Organizer | Integration | Yes |
| AC-3.7-5 | Organization configurable via CLI/config | Organizer | CLI Test | Yes - CLI integration |
| AC-3.7-6 | Source file traceability maintained | Organizer | Integration | Yes - Critical |
| AC-3.7-7 | All formats respect organization strategy | Organizer | Integration | Yes |
| AC-3.7-8 | Output directory structure documented | Documentation | Manual | No - Docs review |

**UAT Focus:** Organization strategy correctness, traceability validation, manifest accuracy

## 5.2 Traceability Matrix: Requirements → Components → Tests

| Epic Requirement | Stories | Components | Test Coverage | UAT Validation |
|-----------------|---------|------------|---------------|----------------|
| Semantic chunking respects boundaries | 3.1 | ChunkingEngine, SentenceSegmenter | Unit (15 tests), Integration (8 tests) | Yes - Boundary violation detection |
| Entity-aware chunking preserves context | 3.2 | EntityPreserver, ChunkingEngine | Unit (12 tests), Integration (10 tests) | Yes - Entity preservation rate >95% |
| Chunks enriched with quality metadata | 3.3 | MetadataEnricher, QualityScore | Unit (18 tests), Integration (6 tests) | Yes - Quality score sampling |
| JSON output with full metadata | 3.4 | JsonFormatter, ParallelWriter | Unit (10 tests), Integration (5 tests) | Yes - Schema validation |
| Plain text optimized for LLM upload | 3.5 | TxtFormatter, ParallelWriter | Unit (8 tests), Integration (4 tests), Manual UAT | Yes - Manual LLM upload test |
| CSV output for spreadsheet analysis | 3.6 | CsvFormatter, ParallelWriter | Unit (9 tests), Integration (6 tests) | Yes - Excel/Sheets import |
| Configurable output organization | 3.7 | Organizer, OrganizationStrategy | Unit (7 tests), Integration (9 tests) | Yes - All 3 strategies tested |

**Test Count Summary:**
- **Unit Tests:** ~79 tests across all stories
- **Integration Tests:** ~48 tests across all stories
- **Performance Tests:** 5 tests (chunking latency, output generation, memory profiling)
- **UAT Tests:** ~25 manual/automated UAT validations
- **Total:** ~157 tests for Epic 3

## 5.3 NFR Traceability: NFRs → Components → Validation

| NFR ID | Requirement | Component | Validation Method | Story |
|--------|-------------|-----------|-------------------|-------|
| NFR-P1-E3 | <10 min for 100 PDFs | Full pipeline | Integration performance test | All stories |
| NFR-P2-E3 | <5.5GB memory | ChunkingEngine, OutputFormatter | Memory profiling with `get_total_memory()` | 3-1, 3-4, 3-5, 3-6 |
| NFR-P3 | <2 sec per 10k words | ChunkingEngine | Per-document timing tests | 3-1 |
| NFR-P4 | 100% determinism | ChunkingEngine | Repeated runs diff | 3-1, 3-2, 3-3 |
| NFR-S1 | Data sanitization | All formatters | Output path scanning | 3-4, 3-5, 3-6 |
| NFR-S2 | No PII leakage | ChunkMetadata, All formatters | PII scanner validation | 3-3, 3-4, 3-5, 3-6 |
| NFR-R1 | Continue-on-error | ParallelWriter, Organizer | Error injection tests | 3-4, 3-5, 3-6, 3-7 |
| NFR-R2 | Graceful degradation | All components | Failure simulation | All stories |
| NFR-R3 | 100% traceability | ChunkMetadata, Organizer | Manifest validation, reverse lookup | 3-3, 3-7 |
| NFR-O1 | Chunking metrics | ChunkingEngine | Log inspection, metrics export | 3-1, 3-2 |
| NFR-O2 | Output format metrics | All formatters | Performance logging | 3-4, 3-5, 3-6 |
| NFR-O3 | Quality distributions | MetadataEnricher | Summary report validation | 3-3 |

## 5.4 UAT Workflow Mapping

**10-Step UAT Workflow (Approved in Party-Mode Discussion):**

1. **Drafted** → SM creates story from epic, saves to `docs/stories/`
2. **Ready for Dev** → SM marks story ready, updates sprint status
3. **Dev Codes** → Dev implements story following tech spec
4. **Pre-commit** → Dev runs pre-commit hooks (0 violations gate)
5. **CI** → GitHub Actions runs tests (60% coverage gate)
6. **Dev Marks Review** → Dev sets story status to "ready-for-review"
7. **SM Creates Test Cases** → SM runs `/bmad:bmm:workflows:create-test-cases`
8. **SM Builds Test Context** → SM runs `/bmad:bmm:workflows:build-test-context`
9. **Dev Executes Tests** → Dev runs `/bmad:bmm:workflows:execute-tests` (automated + CLI via tmux-cli)
10. **SM Reviews UAT Results** → SM runs `/bmad:bmm:workflows:review-uat-results` (90% pass rate gate)
11. **Approved** → Story marked DONE, sprint status updated

**Epic 3 UAT Validation Points:**

| Story | Critical UAT Tests | Dev Execution Method | SM Review Focus |
|-------|-------------------|---------------------|-----------------|
| 3-1 | Sentence boundary preservation, determinism | pytest + manual inspection | Boundary violations = 0 |
| 3-2 | Entity preservation rate >95% | pytest + entity analysis script | Entity completeness validation |
| 3-3 | Quality scores accuracy, readability metrics | pytest + sample manual review | Quality score distributions |
| 3-4 | JSON schema validation, parsability | pytest + jq query tests | Schema compliance |
| 3-5 | LLM upload readiness | Manual upload to ChatGPT/Claude | Format cleanliness, usability |
| 3-6 | Excel/Sheets import success | Manual import to Excel/Sheets | CSV parser validation |
| 3-7 | Organization strategies correctness | pytest + manual directory inspection | Traceability, manifest accuracy |

**Quality Gates Summary:**
- **Pre-commit:** black, ruff, mypy (0 violations)
- **CI:** pytest (60% coverage minimum), performance regression check
- **UAT:** 90% pass rate (critical ACs must be 100%)

## 5.5 Test Type Distribution

```
Epic 3 Test Pyramid:

                    ▲
                   / \
                  /   \
                 / UAT \           ~25 tests (manual + automated)
                /-------\          Focus: End-user workflows, format validation
               /         \
              / Integration\       ~48 tests
             /-------------\       Focus: Multi-component workflows
            /               \
           /   Unit Tests    \     ~79 tests
          /-------------------\    Focus: Component logic, edge cases
         /                     \
        /   Performance Tests   \  ~5 tests
       /-------------------------\ Focus: NFR validation, regression detection
```

**Test Strategy Alignment (Murat's Hybrid Approach):**
- **Story 3-1:** Heavy unit + integration testing, performance baseline establishment
- **Stories 3-2, 3-3:** Unit + integration, skip micro-benchmarks (metadata overhead negligible)
- **Stories 3-4, 3-5, 3-6:** Unit + integration + UAT, measure output format overhead
- **Story 3-7:** Integration + UAT, measure organization overhead
- **Epic-end:** Full pipeline integration test vs <10 min target

---
