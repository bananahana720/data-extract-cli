# Architecture Decision Records (ADRs)

## ADR-001: Choose Typer Over Click for CLI Framework
**Status**: Accepted
**Context**: Need modern CLI framework with type safety and minimal boilerplate
**Decision**: Use Typer (built on Click) for CLI instead of raw Click or argparse
**Consequences**:
- ✅ Auto-generated help text from type hints
- ✅ Less boilerplate than Click
- ✅ Compatible with Click (can mix if needed)
- ❌ Slightly less mature than Click (but well-maintained)

## ADR-002: Use Pydantic Over Dataclasses
**Status**: Accepted
**Context**: Need type-safe data models with validation
**Decision**: Use Pydantic v2 for all data models (Document, Chunk, Config)
**Consequences**:
- ✅ Runtime validation prevents bugs
- ✅ JSON schema generation (for documentation)
- ✅ Better error messages than dataclasses
- ❌ Slight performance overhead vs dataclasses (acceptable tradeoff)

## ADR-003: File-Based Storage (No Database)
**Status**: Accepted
**Context**: CLI tool needs persistence for caching and configuration
**Decision**: Use file-based storage (JSON manifest, YAML config) instead of database
**Consequences**:
- ✅ Simple, no database dependency
- ✅ Human-readable (can edit YAML config)
- ✅ Git-friendly (config is version-controllable)
- ❌ Not suitable for very large scale (>10k documents) - acceptable for audit use case

## ADR-004: Classical NLP Only (No Transformers)
**Status**: Accepted (Enterprise Constraint)
**Context**: Enterprise IT policy prohibits transformer-based models
**Decision**: Use classical NLP (TF-IDF, LSA, Word2Vec) via scikit-learn and gensim
**Consequences**:
- ✅ Complies with enterprise restrictions
- ✅ Faster inference, lower memory
- ✅ Interpretable results
- ❌ Less semantic understanding than transformers (acceptable for audit domain)

## ADR-005: Streaming Pipeline (Not Batch-Load)
**Status**: Accepted
**Context**: Need to process batches efficiently without exhausting memory
**Decision**: Process files one at a time through pipeline, release memory after each
**Consequences**:
- ✅ Constant memory usage (2GB max)
- ✅ Can process arbitrarily large batches
- ✅ Graceful error handling (one file failure doesn't corrupt batch state)
- ❌ Slightly slower than full batch processing (acceptable tradeoff)

## ADR-006: Continue-On-Error Batch Processing
**Status**: Accepted
**Context**: One corrupted file shouldn't block entire audit engagement processing
**Decision**: Catch per-file errors, log, quarantine, continue with remaining files
**Consequences**:
- ✅ Resilient batch processing
- ✅ Detailed error reporting at end
- ✅ User can fix issues and re-run only failed files
- ❌ Requires careful exception design (ProcessingError vs CriticalError)

## ADR-011: Semantic Boundary-Aware Chunking
**Status**: Accepted (Epic 3, Story 3.1) - **Amended 2025-11-13**
**Context**: RAG systems require text chunks that preserve semantic meaning and context. Chunks split mid-sentence or mid-thought reduce LLM comprehension and retrieval accuracy.
**Decision**: Chunking respects sentence boundaries detected by spaCy's sentence segmentation. Chunks never split in the middle of a sentence.
**Implementation**:
- ChunkingEngine uses SentenceSegmenter (Story 2.5.2) for accurate boundary detection
- spaCy `en_core_web_md` model provides production-ready sentence boundary detection
- Chunks respect target size (default 512 tokens) but extend to complete sentences
- Very long sentences (>chunk_size) become single chunks to preserve context
- **Section boundary detection deferred to Story 3.2** (see Amendment below)
**Rationale**:
- Preserves complete thoughts and context within each chunk
- Improves LLM understanding during RAG retrieval
- Maintains grammatical coherence for better embedding quality
- Aligns with document structure (sentences are natural semantic units)
**Trade-offs**:
- ✅ Better semantic coherence and LLM comprehension
- ✅ Deterministic chunking (same input → same chunks)
- ✅ Respects document structure (sentences, paragraphs)
- ❌ Chunks may exceed target size for very long sentences (acceptable - preserves meaning)
- ❌ spaCy adds ~1.8s latency per 10k words (acceptable for batch processing)
**Alternatives Considered**:
- **Character-based splitting** (rejected): Breaks mid-sentence, destroys context
- **Fixed token windows** (rejected): Splits thoughts arbitrarily
- **Paragraph-based chunking** (rejected): Too coarse, paragraphs often exceed limits
**Performance Impact**:
- **Latency:** ~3s for 10k-word document (60% is spaCy segmentation)
- **Memory:** 255 MB peak (51% of 500 MB limit per document)
- **Scaling:** Linear (0.19s per 1,000 words)
- **Acceptable:** Batch processing use case tolerates 3s latency

**Amendment 2025-11-13 (Story 3.1 Code Review):**
- **AC-3.1-2 (Section Boundary Detection) Deferred to Story 3.2**
- **Rationale**: Current document.structure lacks section/heading markers (only contains page_count, word_count, image_count, etc.). Proper implementation requires Epic 2 enhancements to preserve ContentBlock structure (headings, sections) through extraction and normalization stages.
- **Story 3.1 Scope**: Sentence-boundary chunking (AC-3.1-1) is fully implemented and production-ready.
- **Future Work (Story 3.2)**: Section-aware chunking will be addressed alongside entity boundary detection, once Epic 2 provides the necessary structural metadata.

## ADR-013: Runtime Scaling Thresholds for Local API/Queue/SQLite
**Status**: Accepted
**Context**: The local runtime now exposes queue-overload, DB lock-retry, and startup reconciliation signals, but migration timing to external queue/DB required explicit criteria.
**Decision**: Adopt threshold-based migration triggers tied to runtime telemetry (queue saturation, lock contention, and reconciliation failures), and escalate to external components when multiple thresholds remain breached after one remediation iteration.
**Consequences**:
- ✅ Scaling decisions become measurable and repeatable.
- ✅ Operations can tune local runtime first before architectural migration.
- ✅ Migration planning is triggered by objective reliability signals.
- ❌ Requires ongoing telemetry review discipline.
- 📄 Full details: [`adr-013-runtime-scaling-thresholds.md`](./adr-013-runtime-scaling-thresholds.md)

---

_Generated by BMAD Decision Architecture Workflow v1.3.2_
_Date: 2025-11-09_
_For: andrew (Intermediate Skill Level)_
_Project: data-extraction-tool (Knowledge Quality Gateway for Enterprise Gen AI)_
