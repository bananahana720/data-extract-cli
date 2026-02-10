# 6. Risks, Assumptions, and Open Questions

## 6.1 Technical Risks

### RISK-E3-1: Performance Target Aggressive (10 minutes)
**Severity:** Medium | **Probability:** Medium | **Impact:** Medium

**Description:**
NFR-P1-E3 targets <10 minutes for 100 PDFs (full pipeline). This is ~33% improvement over conservative 15-minute baseline. While Epic 2 achieved 6.86 minutes (148% improvement), Epic 3 adds chunking, metadata enrichment, and output generation overhead.

**Mitigation Strategy:**
1. **Baseline early** (Story 3-1): Measure chunking engine performance to validate feasibility
2. **Hybrid benchmarking** (Murat's approach): Measure critical paths (Stories 3-1, 3-4/5/6, 3-7), skip micro-benchmarks
3. **Winston's optimizations**: Lazy spaCy loading, streaming generators, parallel writes, memory pooling
4. **Fallback position**: Document actual performance, adjust target if necessary (transparency over false goals)

**Indicators:**
- Story 3-1 chunking >2 minutes for 100 PDFs → Risk materializes
- Output format generation >1.5 minutes → Risk materializes

**Contingency:**
- If target missed: Document actual performance in `docs/performance-baselines-epic-3.md`
- Negotiate target adjustment with stakeholders (e.g., <12 minutes acceptable for MVP)
- Identify optimization opportunities for post-MVP (e.g., C extensions, Cython for hotspots)

### RISK-E3-2: Chunk Quality Subjective and Hard to Validate
**Severity:** Medium | **Probability:** Low | **Impact:** High

**Description:**
Chunk quality (semantic coherence, entity preservation) is partially subjective. Automated tests can catch sentence boundary violations, but semantic coherence requires human judgment. Risk: Chunks technically correct but semantically poor for RAG retrieval.

**Mitigation Strategy:**
1. **Manual review sampling**: UAT includes manual review of 20 sample chunks (diverse document types)
2. **Entity preservation metrics**: >95% entity completeness (quantitative gate)
3. **Readability scores**: Use textstat as objective proxy for quality
4. **Dogfooding**: Dev/SM test chunks with actual LLM upload (ChatGPT/Claude) in UAT
5. **Iterative refinement**: Collect user feedback post-MVP, refine chunking heuristics

**Indicators:**
- Manual review flags >10% chunks as incoherent → Risk materializes
- Entity preservation rate <90% → Risk materializes
- LLM upload test: chunks confuse AI or lose context → Risk materializes

**Contingency:**
- Adjust chunk size defaults (e.g., increase to 768 tokens for more context)
- Enhance entity-aware chunking logic (prefer entity-boundary splits)
- Add post-processing step: merge tiny chunks, split mega-chunks

### RISK-E3-3: spaCy Model Accuracy Insufficient for Audit Documents
**Severity:** Low | **Probability:** Low | **Impact:** Medium

**Description:**
en_core_web_md trained on news corpus (97.2% accuracy). Audit documents have different linguistic patterns (technical jargon, regulatory language, complex sentence structures). Risk: Sentence boundary detection fails on audit-specific constructs.

**Mitigation Strategy:**
1. **Early validation** (Story 3-1): Test on diverse audit document samples
2. **Edge case handling**: Detect and handle very long sentences (>100 words), micro-sections
3. **Manual review**: UAT validates sentence boundary correctness on sample corpus
4. **Fallback heuristics**: If spaCy fails, fall back to rule-based segmentation (period + capital letter)
5. **Post-MVP option**: Fine-tune spaCy model on audit corpus (requires labeled data)

**Indicators:**
- Sentence boundary violations detected in >1% of chunks → Risk materializes
- Manual review finds systematic segmentation errors → Risk materializes

**Contingency:**
- Implement hybrid segmentation: spaCy + rule-based fallback
- Add configuration option: disable spaCy, use simple period-based splitting
- Explore alternative models: en_core_web_lg (larger, more accurate)

### RISK-E3-4: Memory Budget Exceeded (>5.5GB)
**Severity:** Low | **Probability:** Low | **Impact:** Medium

**Description:**
Epic 2 batch processing uses 4.15GB. Epic 3 budget allows 1.35GB headroom for chunking + output. Winston's optimizations (streaming, lazy loading, pooling) should prevent overrun, but risk remains if assumptions wrong.

**Mitigation Strategy:**
1. **Early profiling** (Story 3-1): Measure chunking memory overhead on single document and batch
2. **Winston's optimizations**: Streaming generators (no buffering), metadata pooling, lazy spaCy loading
3. **Continuous monitoring**: Track memory usage in performance baselines document
4. **Streaming architecture**: Generator pattern throughout (chunks yielded one at a time)

**Indicators:**
- Single-document chunking >500MB → Risk materializes
- Batch processing >5.5GB peak RSS → Risk materializes

**Contingency:**
- Reduce parallel output workers (3 → 2 or 1) to save memory
- Disable metadata pooling if it causes issues (trade memory for simplicity)
- Process documents in smaller batches (50 PDFs instead of 100)

## 6.2 Business/Operational Risks

### RISK-E3-5: Output Formats Don't Meet User Needs
**Severity:** Medium | **Probability:** Low | **Impact:** High

**Description:**
Epic 3 delivers JSON, TXT, CSV. Risk: Users need additional formats (Parquet, Avro, JSON Lines) or different metadata structure for downstream tools (e.g., vector database expects specific schema).

**Mitigation Strategy:**
1. **UAT validation**: Test outputs with actual downstream tools (LLM upload, Excel import)
2. **Extensibility**: BaseFormatter protocol allows adding new formats post-MVP
3. **Configuration**: Output metadata structure configurable (Epic 5)
4. **User feedback**: Collect feedback post-MVP, prioritize format additions

**Indicators:**
- UAT testers request alternative formats → Risk materializes
- Downstream tools reject output format → Risk materializes

**Contingency:**
- Add requested format in Epic 5 (quick-flow story)
- Provide format conversion scripts (e.g., JSON → JSON Lines, JSON → Parquet)
- Document output schema clearly to enable user-side conversion

### RISK-E3-6: UAT Workflow Overhead Slows Velocity
**Severity:** Low | **Probability:** Medium | **Impact:** Low

**Description:**
10-step UAT workflow (approved in party-mode) adds overhead: SM creates test cases, builds context, reviews results. Risk: Workflow slows down story completion, reduces Epic 3 velocity.

**Mitigation Strategy:**
1. **UAT selective application**: Not all ACs require UAT (see Section 5.1 UAT Required column)
2. **Automation**: Dev executes automated tests (pytest), manual UAT only for critical paths
3. **Parallel work**: SM creates test cases while Dev codes (no blocking dependency)
4. **Learning curve**: Workflow overhead reduces over time as team learns patterns

**Indicators:**
- Story completion time >2x baseline → Risk materializes
- Dev waiting on SM for test case creation → Risk materializes

**Contingency:**
- Simplify UAT for non-critical stories (unit tests sufficient)
- Batch UAT review (SM reviews multiple stories together)
- Dev creates own test cases, SM reviews (shift left)

## 6.3 Assumptions

### ASSUMPTION-E3-1: spaCy Sentence Boundaries Sufficient
**Assumption:** spaCy's sentence segmentation is accurate enough for audit documents without custom training.

**Validation:** Story 3-1 UAT includes manual review of sentence boundaries on sample corpus.

**If False:** Implement hybrid segmentation (spaCy + rule-based fallback) or fine-tune spaCy model on audit corpus.

### ASSUMPTION-E3-2: Three Output Formats Adequate for MVP
**Assumption:** JSON, TXT, CSV cover 90%+ of user workflows (LLM upload, vector database, spreadsheet analysis).

**Validation:** UAT testing with actual downstream tools validates format sufficiency.

**If False:** Add additional formats in Epic 5 or post-MVP (Parquet, Avro, JSON Lines, XML).

### ASSUMPTION-E3-3: Entity-Aware Chunking Improves Quality
**Assumption:** Preserving entity context within chunks improves RAG retrieval quality vs. naive chunking.

**Validation:** UAT includes comparison test (entity-aware vs. semantic-only chunking).

**If False:** Make entity-aware chunking optional (configuration flag), default to semantic-only.

### ASSUMPTION-E3-4: Parallel Output Writes Improve Throughput
**Assumption:** JSON/TXT/CSV generation is I/O-bound, so parallel writes improve performance.

**Validation:** Story 3-4 benchmarks parallel vs. sequential writes.

**If False:** Disable parallel writes (simpler code, easier debugging), accept slower output generation.

### ASSUMPTION-E3-5: textstat Readability Metrics Meaningful for Audit Docs
**Assumption:** Flesch-Kincaid, Gunning Fog, SMOG index are useful quality signals for technical audit documents.

**Validation:** Story 3-3 analyzes readability score distributions on sample corpus.

**If False:** De-emphasize readability scores in quality composite, focus on OCR confidence and completeness.

### ASSUMPTION-E3-6: Chunk Size 256-512 Tokens Optimal
**Assumption:** Default chunk size (256-512 tokens) balances context preservation vs. retrieval precision for RAG.

**Validation:** UAT includes chunk size sensitivity analysis (128, 256, 512, 1024 tokens).

**If False:** Adjust defaults based on UAT findings, make chunk size highly configurable.

## 6.4 Open Questions

### QUESTION-E3-1: Post-MVP Vector Database Integration?
**Question:** Should Epic 3 include direct vector database integration (e.g., Pinecone, Weaviate, Chroma)?

**Context:** Current design outputs JSON files. Users manually upload to vector DBs. Direct integration would streamline workflow.

**Decision Needed By:** Epic 3 planning (before Story 3-4)

**Options:**
1. **Out of scope for MVP**: Document output format requirements for vector DBs, defer integration to post-MVP
2. **Add to Epic 3**: Create Story 3-8 for direct vector DB upload (blocks MVP timeline)
3. **Add to Epic 5**: Include in CLI enhancement epic (batch processing + vector DB integration)

**Recommendation:** Out of scope for MVP. Document JSON schema requirements for popular vector DBs (Pinecone, Weaviate, Chroma). Add integration in post-MVP if user demand high.

### QUESTION-E3-2: JSON Schema Validation Mandatory or Optional?
**Question:** Should JSON output always validate against JSON Schema, or make validation optional?

**Context:** JSON Schema validation adds overhead (parse schema, validate every output). Benefits: guarantees correctness, enables tooling integration.

**Decision Needed By:** Story 3-4 implementation

**Options:**
1. **Always validate**: Every JSON output validated (fail if schema violation)
2. **Optional via flag**: `--validate-schema` flag enables validation (default: off for performance)
3. **Dev-mode only**: Validate in tests, skip in production (trust code correctness)

**Recommendation:** Optional via flag (default: off). Enable in CI tests and with `--strict` mode. Provides safety without performance penalty in production.

### QUESTION-E3-3: Chunk Overlap Strategy: Sentence-Based or Token-Based?
**Question:** Should chunk overlap use sentence boundaries (complete sentences) or token count (may split sentences)?

**Context:** Sentence-based overlap is semantically cleaner but variable size. Token-based overlap is predictable but may split sentences.

**Decision Needed By:** Story 3-1 implementation

**Options:**
1. **Sentence-based**: Overlap includes complete sentences (variable overlap size)
2. **Token-based**: Fixed overlap token count (may split sentences at chunk boundaries)
3. **Hybrid**: Prefer sentence boundaries, fall back to token count if overlap too large

**Recommendation:** Hybrid approach. Prefer complete sentences in overlap region, but enforce maximum overlap token count to prevent huge overlaps.

### QUESTION-E3-4: Organization Strategy Default: by_document or flat?
**Question:** What should be the default organization strategy if user doesn't specify?

**Context:**
- **by_document**: Most intuitive (files grouped by source), but deep directory nesting
- **flat**: Simplest (single directory), but hundreds of files in one folder
- **by_entity**: Most powerful (semantic grouping), but requires entity tagging

**Decision Needed By:** Story 3-7 implementation

**Options:**
1. **Default: by_document** (intuitive, source-centric)
2. **Default: flat** (simplest, no nesting)
3. **Default: by_entity** (most powerful, semantic)
4. **No default** (force user to choose explicitly)

**Recommendation:** Default to **by_document**. Most intuitive for first-time users, preserves source file grouping, easy to understand output structure.

### QUESTION-E3-5: Manifest Format: JSON, YAML, or CSV?
**Question:** What format should the manifest file use (lists all outputs with metadata)?

**Context:** Manifest tracks all generated chunks, source files, organization. Needs to be human-readable and machine-parseable.

**Decision Needed By:** Story 3-7 implementation

**Options:**
1. **JSON**: Structured, parseable, consistent with JSON output format
2. **YAML**: Human-friendly, supports comments, easier to read
3. **CSV**: Tabular, Excel-friendly, but limited structure
4. **Multiple formats**: Generate all three (manifest.json, manifest.yaml, manifest.csv)

**Recommendation:** **JSON** (manifest.json). Consistent with primary output format, widely supported, programmatically queryable. Add YAML/CSV if user demand emerges.

## 6.5 Risk Summary Table

| Risk ID | Category | Severity | Probability | Mitigation Strategy | Owner |
|---------|----------|----------|-------------|---------------------|-------|
| RISK-E3-1 | Performance target aggressive | Medium | Medium | Early baseline, hybrid benchmarking, optimizations | Dev |
| RISK-E3-2 | Chunk quality subjective | Medium | Low | Manual sampling, entity metrics, dogfooding | SM |
| RISK-E3-3 | spaCy accuracy insufficient | Low | Low | Early validation, edge case handling, fallback | Dev |
| RISK-E3-4 | Memory budget exceeded | Low | Low | Early profiling, streaming architecture, monitoring | Dev |
| RISK-E3-5 | Output formats inadequate | Medium | Low | UAT validation, extensibility design | SM |
| RISK-E3-6 | UAT workflow overhead | Low | Medium | Selective UAT, automation, parallel work | SM |

**Risk Mitigation Priority:**
1. **RISK-E3-1** (Performance): Baseline early in Story 3-1, track continuously
2. **RISK-E3-2** (Quality): UAT validation critical, manual review essential
3. **RISK-E3-5** (Formats): Extensible design enables quick post-MVP additions

---
