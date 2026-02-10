# Epic 4 Architectural Decision Records

**Date**: 2025-11-20
**Architect**: Winston (System Architect)
**Context**: Wave 1 Test Reality Sprint

---

## ADR-013: Semantic Pipeline Architecture

**Status**: Accepted
**Date**: 2025-11-20
**Decision Makers**: Winston, Andrew

### Context

Epic 4 introduces semantic analysis capabilities to the data extraction pipeline. We need a clean, modular architecture that integrates with the existing streaming pipeline while maintaining separation of concerns.

### Decision

Implement a **three-layer semantic pipeline** with cache-first design:

1. **Vectorization Layer** (TF-IDF)
   - Converts text to sparse vectors
   - Manages vocabulary (10k features)
   - Caches models with joblib

2. **Similarity Layer** (Cosine Similarity)
   - Computes pairwise document similarities
   - Identifies duplicates (>0.95 similarity)
   - Builds similarity graphs

3. **Reduction Layer** (LSA/SVD)
   - Reduces dimensionality to topic space
   - Enables semantic clustering
   - Extracts latent topics

### Consequences

**Positive**:
- Clean separation of concerns
- Each layer independently testable
- Cache reuse across layers
- Streaming-compatible design

**Negative**:
- Three separate cache files per corpus
- Potential memory pressure with large matrices
- Cache invalidation complexity

---

## ADR-014: Classical NLP Over Transformers

**Status**: Accepted
**Date**: 2025-11-20
**Decision Makers**: Winston, Andrew

### Context

Enterprise constraints prohibit transformer models. We need semantic analysis using only classical NLP methods that can run on-premise without GPUs.

### Decision

Use **classical NLP exclusively**:
- TF-IDF for vectorization (not embeddings)
- LSA/TruncatedSVD for dimensionality reduction (not BERT)
- Cosine similarity for comparison (not neural similarity)
- K-means for clustering (not deep clustering)

### Rationale

1. **Economic**: $0.001/doc vs $0.10/doc for LLM-based analysis
2. **Performance**: 7.6ms TF-IDF vs 500ms+ for transformers
3. **Interpretability**: TF-IDF weights are explainable
4. **Determinism**: Same input always produces same output
5. **Simplicity**: No GPU requirements, simple deployment

### Consequences

**Positive**:
- 100x cost reduction
- Deterministic results
- No GPU dependencies
- Fast processing (sub-10ms)
- Interpretable features

**Negative**:
- Less semantic understanding than transformers
- No contextual embeddings
- Requires more feature engineering
- Less transfer learning capability

---

## ADR-015: Knowledge Curation as Pre-Filter

**Status**: Accepted
**Date**: 2025-11-20
**Decision Makers**: Winston, Andrew

### Context

LLM token costs make processing large document corpora prohibitively expensive. We need a strategy to reduce token consumption while maintaining analysis quality.

### Decision

Position classical NLP as a **pre-filter for expensive LLM operations**:

```python
Pipeline Strategy:
1. Classical NLP First ($0.001/doc)
   - Deduplicate corpus (30-40% reduction)
   - Cluster similar documents (10x reduction)
   - Filter low-quality content (20% reduction)
   - Pre-compute similarities

2. LLM Processing Second ($0.10/doc)
   - Process only unique documents
   - Analyze cluster representatives
   - Focus on high-quality content
   - Use similarity for context

Result: 60-80% token reduction
```

### Consequences

**Positive**:
- Massive cost savings (98.5% reduction)
- Faster end-to-end processing
- Reduced hallucination risk
- Better use of LLM capabilities

**Negative**:
- Two-stage complexity
- Potential information loss in clustering
- Requires tuning thresholds
- Cache management overhead

---

## ADR-016: Behavioral Testing Over Coverage

**Status**: Accepted
**Date**: 2025-11-20
**Decision Makers**: Winston, Murat

### Context

Epic 3.5 produced 908 lines of integration test design with zero implementation. We have extensive structural tests but no behavioral validation.

### Decision

Replace comprehensive test design with **5 core behavioral tests**:

```python
Core Behavioral Tests:
1. test_deduplication_reduces_corpus()
   - Verify duplicates actually removed

2. test_similarity_is_symmetric()
   - Validate mathematical properties

3. test_clustering_preserves_documents()
   - Ensure no data loss

4. test_cache_is_deterministic()
   - Same input → same output

5. test_quality_flags_bad_content()
   - Verify gibberish detection
```

### Rationale

- 5 good tests > 500 bad tests
- Behavior matters, not structure
- Generated tests provide false confidence
- Focus on semantic correctness

### Consequences

**Positive**:
- Real confidence in correctness
- Faster test execution
- Easier to maintain
- Clear failure diagnosis

**Negative**:
- Lower coverage metrics
- Pushback from coverage tools
- Requires careful test selection

---

## ADR-017: Cache-First Performance Strategy

**Status**: Accepted
**Date**: 2025-11-20
**Decision Makers**: Winston, Andrew

### Context

Semantic operations are computationally expensive: TF-IDF fitting takes ~10s for 10k documents, LSA takes ~15s. Repeated analysis of the same corpus is common in audit workflows.

### Decision

Implement **aggressive caching with joblib**:

```python
Cache Strategy:
- Location: .data-extract-cache/models/
- Key pattern: {model}_{version}_{corpus_hash}.joblib
- Size limit: 500MB with LRU eviction
- Warming: Pre-compute common models
- Invalidation: Automatic on corpus change
```

### Performance Impact

- Cold start: 10-15 seconds
- Warm cache: 0.1 seconds
- Speedup: 100-150x

### Consequences

**Positive**:
- Sub-second repeated analysis
- Team collaboration via shared cache
- CI/CD test acceleration
- Predictable performance

**Negative**:
- 500MB disk usage
- Cache invalidation complexity
- Network latency for shared caches
- Version management overhead

---

## ADR-018: Simplification Over Completeness

**Status**: Accepted
**Date**: 2025-11-20
**Decision Makers**: Winston

### Context

The project shows signs of over-engineering: 33 automation scripts, 1000+ line monoliths, 908-line test designs with zero implementation.

### Decision

**Radically simplify Epic 4**:

```python
Instead of Planned:          Do This:
- 50 integration tests   →   5 behavioral tests
- 10 configuration flags →   3 key parameters
- 5 output formats       →   2 formats (JSON, TXT)
- Real-time progress     →   Batch patience
- Complex clustering     →   Simple K-means
- Multiple algorithms    →   TF-IDF + LSA only
```

### Rationale

- Complexity is technical debt
- Simple systems are maintainable
- We're at 7.6% capacity already
- Perfect is the enemy of good

### Consequences

**Positive**:
- Faster delivery
- Easier maintenance
- Lower cognitive load
- Higher reliability

**Negative**:
- Less flexibility
- Fewer features
- Potential future rework

---

## Summary of Decisions

| ADR | Decision | Impact |
|-----|----------|--------|
| 013 | Three-layer semantic pipeline | Clean architecture |
| 014 | Classical NLP only | 100x cost reduction |
| 015 | Knowledge curation as pre-filter | 60-80% token savings |
| 016 | Behavioral testing focus | Real confidence |
| 017 | Cache-first performance | 100x speedup |
| 018 | Radical simplification | Maintainable system |

---

## Implementation Priority

1. **Immediate** (Before Story 4.1):
   - Implement 5 behavioral tests
   - Create semantic fixtures
   - Establish performance baselines

2. **During Epic 4**:
   - Build three-layer pipeline
   - Implement joblib caching
   - Keep it simple

3. **Post-Epic 4**:
   - Monitor cache performance
   - Tune thresholds based on usage
   - Consider incremental improvements

---

*ADRs Created: 2025-11-20*
*Next Review: After Epic 4 Story 4.3*
