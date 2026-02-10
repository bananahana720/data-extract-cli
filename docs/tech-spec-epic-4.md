# Epic 4 Technical Specification - Knowledge Curation via Classical NLP

**Epic ID**: Epic 4
**Epic Type**: Feature Epic (Semantic Analysis Foundation)
**Dependencies**: Epic 3 (complete), Epic 3.5 (semantic dependencies installed), Story 4-0 (behavioral tests DONE)
**Owner**: PM (John) + Dev (Charlie, Elena, Winston)
**Status**: Specification Complete - Ready for Implementation
**Created**: 2025-11-20
**Last Updated**: 2025-11-20 (enhanced with architecture cross-references and status updates)

---

## 1. Overview & Purpose

### 1.1 Epic Goal

Epic 4 establishes **knowledge curation capabilities** using classical NLP techniques (TF-IDF, LSA, similarity analysis) to prepare documents for economical LLM processing. This epic delivers a 100x cost reduction for enterprise-scale document analysis by pre-filtering with classical NLP ($0.001/document) before expensive LLM operations ($0.10+/document).

### 1.2 Value Proposition

**Economic Optimization**:
- Direct LLM processing: 10,000 docs × $0.10 = $1,000
- Classical NLP curation first: 10,000 docs × $0.001 + 50 clusters × $0.10 = $15
- **Savings: 98.5% cost reduction**

**Key Capabilities**:
1. **Deduplication**: 30-40% corpus reduction via TF-IDF similarity
2. **Clustering**: 10x reduction through LSA topic modeling
3. **Quality Filtering**: 20% noise reduction via readability metrics
4. **Similarity Pre-computation**: 60% faster RAG retrieval

### 1.3 Technical Approach

Classical NLP pipeline using proven algorithms:
- **TF-IDF**: Sparse vector representation for documents
- **LSA**: Dimensionality reduction for topic extraction
- **Cosine Similarity**: Document relationship mapping
- **Textstat**: Readability and quality scoring

---

## 2. Scope & Deliverables

### 2.1 In Scope

**Core Semantic Capabilities**:
1. **TF-IDF Vectorization Engine** (Story 4.1)
   - Sparse matrix representation of document chunks
   - Vocabulary management (max 10,000 features)
   - N-gram support (unigrams and bigrams)
   - Cache-first architecture with joblib

2. **Similarity Analysis** (Story 4.2)
   - Pairwise cosine similarity computation
   - Duplicate detection (threshold: 0.95)
   - Related document graph construction
   - Memory-efficient block-wise processing

3. **LSA Topic Extraction** (Story 4.3)
   - TruncatedSVD dimensionality reduction
   - Topic modeling (100-300 components)
   - Document clustering with K-means
   - Explained variance tracking

4. **Quality Metrics** (Story 4.4)
   - Readability scores (Flesch-Kincaid, Gunning Fog)
   - Lexical diversity measurement
   - Content quality flags for filtering
   - Integration with chunk quality scores

5. **CLI Integration** (Story 4.5)
   - `semantic analyze` command
   - `semantic deduplicate` command
   - `semantic cluster` command
   - Report generation and export

### 2.2 Out of Scope

- ❌ Transformer models or embeddings (classical NLP only)
- ❌ Cloud-based APIs (local processing only)
- ❌ Real-time processing (batch mode only)
- ❌ UI/visualization (CLI and reports only)
- ❌ Multi-language support (English only for Epic 4)

### 2.3 Success Criteria

Epic 4 is complete when:
1. ✅ All 5 stories delivered and passing quality gates
2. ✅ 5 behavioral tests passing (deduplication, clustering, RAG improvement, scale, determinism)
3. ✅ Performance within NFR limits (<100ms TF-IDF, <200ms LSA, <500MB for 10k docs)
4. ✅ Cache strategy implemented and validated
5. ✅ CLI commands integrated and documented
6. ✅ 80%+ test coverage on semantic modules

---

## 3. Architecture & Design

### 3.1 Semantic Pipeline Architecture

```
┌─────────────────────────────────────────────────────┐
│                  INPUT: List[Chunk]                  │
│              (from Epic 3 ChunkStage)                │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│           STAGE 1: QUALITY ENRICHMENT                │
│  - Textstat readability metrics                      │
│  - Quality score computation (0.0-1.0)               │
│  - Filter low-quality chunks                         │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│           STAGE 2: TF-IDF VECTORIZATION             │
│  - Sparse matrix generation (CSR format)             │
│  - Vocabulary: 10k features, bigrams                 │
│  - Cache key: tfidf_v1_[hash].joblib                │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│         STAGE 3: SIMILARITY ANALYSIS                 │
│  - Cosine similarity matrix                          │
│  - Duplicate pairs (>0.95 similarity)                │
│  - Related document graph                            │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│      STAGE 4: LSA DIMENSIONALITY REDUCTION          │
│  - TruncatedSVD (100 components)                     │
│  - Topic extraction and labeling                     │
│  - K-means clustering on reduced space               │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│              OUTPUT: ProcessingResult                │
│  - Deduplicated corpus                               │
│  - Document clusters                                 │
│  - Similarity matrix                                 │
│  - Quality metrics                                   │
└─────────────────────────────────────────────────────┘
```

### 3.2 Integration with Existing Pipeline

```python
# Type signature for Epic 4
SemanticStage: PipelineStage[List[Chunk], ProcessingResult]

# Integration pattern
full_pipeline = Pipeline([
    ExtractStage(),      # Epic 1
    NormalizeStage(),    # Epic 1
    ChunkStage(),        # Epic 3
    SemanticStage(),     # Epic 4 (NEW)
    OutputStage()        # Epic 5
])
```

### 3.3 Cache Architecture (ADR-012)

**Reference**: See [ADR-012: Semantic Model Cache & Persistence Strategy](./architecture/adr-012-semantic-model-cache.md) for complete cache design decisions.

```yaml
Cache Strategy:
  Storage:
    - Development: .data-extract-cache/models/
    - CI: ~/.cache/data-extract/models/
    - Production: $DATA_EXTRACT_CACHE_DIR

  Keys:
    - TF-IDF: tfidf_v1_{corpus_hash}.joblib
    - LSA: lsa_v1_{corpus_hash}_t{n_components}.joblib
    - Similarity: similarity_v1_{corpus_hash}.joblib

  Limits:
    - Max size: 500MB
    - Eviction: LRU when >80% full
    - Validation: SHA-256 checksums
```

**Performance Impact**: Cache provides 10-100x speedup on repeated analysis (0.1s vs 10s for TF-IDF fit), enabling team collaboration and iterative workflows.

---

## 4. Functional Requirements

### 4.1 TF-IDF Vectorization (Story 4.1)

- **FR-4.1-1**: System shall convert text chunks into TF-IDF sparse vectors
- **FR-4.1-2**: System shall support configurable vocabulary size (default 10,000)
- **FR-4.1-3**: System shall filter by document frequency (min_df=0.01, max_df=0.95)
- **FR-4.1-4**: System shall cache vectorizers for reuse
- **FR-4.1-5**: System shall support unigram and bigram features

### 4.2 Similarity Analysis (Story 4.2)

- **FR-4.2-1**: System shall compute pairwise cosine similarity between documents
- **FR-4.2-2**: System shall identify duplicates using configurable threshold (default 0.95)
- **FR-4.2-3**: System shall build similarity graph for navigation
- **FR-4.2-4**: System shall handle large matrices via block-wise computation
- **FR-4.2-5**: System shall report similarity statistics (mean, std, max)

### 4.3 LSA Topic Extraction (Story 4.3)

- **FR-4.3-1**: System shall reduce dimensionality using TruncatedSVD
- **FR-4.3-2**: System shall extract configurable number of topics (default 100)
- **FR-4.3-3**: System shall cluster documents using K-means on reduced space
- **FR-4.3-4**: System shall report explained variance ratio
- **FR-4.3-5**: System shall cache LSA models for reuse

### 4.4 Quality Metrics (Story 4.4)

- **FR-4.4-1**: System shall compute readability scores for each chunk
- **FR-4.4-2**: System shall calculate lexical diversity metrics
- **FR-4.4-3**: System shall flag low-quality content (score < 0.5)
- **FR-4.4-4**: System shall integrate with existing chunk quality scores
- **FR-4.4-5**: System shall provide composite quality score (0.0-1.0)

### 4.5 CLI Integration (Story 4.5)

- **FR-4.5-1**: System shall provide `semantic analyze` command
- **FR-4.5-2**: System shall support batch processing of document directories
- **FR-4.5-3**: System shall generate analysis reports in JSON/CSV format
- **FR-4.5-4**: System shall provide cache management commands
- **FR-4.5-5**: System shall support configuration via YAML files

---

## 5. Non-Functional Requirements

### 5.1 Performance

| Requirement | Target | Validation | Priority |
|-------------|--------|------------|----------|
| **NFR-P1**: TF-IDF vectorization latency | <100ms per 1k words | Benchmark test | CRITICAL |
| **NFR-P2**: LSA transformation latency | <200ms per 100 docs | Benchmark test | CRITICAL |
| **NFR-P3**: Similarity computation | <5s for 1k×1k matrix | Benchmark test | HIGH |
| **NFR-P4**: Memory usage | <500MB for 10k docs | Memory profiler | CRITICAL |
| **NFR-P5**: Cache hit performance | <10ms retrieval | Benchmark test | MEDIUM |

### 5.2 Quality

| Requirement | Target | Validation | Priority |
|-------------|--------|------------|----------|
| **NFR-Q1**: Duplicate detection accuracy | ≥85% precision, ≥80% recall | Golden dataset | CRITICAL |
| **NFR-Q2**: Cluster coherence | Silhouette score ≥0.65 | Behavioral test | HIGH |
| **NFR-Q3**: Deterministic output | 100% identical across runs | Integration test | CRITICAL |
| **NFR-Q4**: Test coverage | ≥80% for new code | Coverage report | HIGH |

### 5.3 Scalability

| Requirement | Target | Validation | Priority |
|-------------|--------|------------|----------|
| **NFR-S1**: Document corpus size | Handle 100k documents | Stress test | MEDIUM |
| **NFR-S2**: Vocabulary growth | Linear memory with features | Profile | MEDIUM |
| **NFR-S3**: Parallel processing | Utilize available cores | Performance test | LOW |

---

## 6. Story Breakdown

| Story ID | Title | Owner | Status | Dependencies |
|----------|-------|-------|--------|--------------|
| **4.0** | **Behavioral Tests Implementation** | **Amelia** | **✅ DONE (2025-11-20)** | **Epic 3.5 fixtures** |
| 4.1 | TF-IDF Vectorization Engine | Charlie | 📋 Ready for Dev | Story 4.0, Epic 3 complete |
| 4.2 | Document Similarity Analysis | Elena | 📋 Ready for Dev | Story 4.1 |
| 4.3 | LSA Topic Extraction | Winston | 📋 Ready for Dev | Story 4.1 |
| 4.4 | Quality Metrics Integration | Charlie | 📋 Ready for Dev | Story 4.1 |
| 4.5 | CLI Integration & Reporting | Elena | 📋 Ready for Dev | Stories 4.1-4.4 |

**Critical Path**: 4.1 → (4.2 || 4.3 || 4.4) → 4.5

**Sprint Status Notes** (from `sprint-status.yaml`):
- ✅ Story 4-0 (behavioral tests): **DONE** - All 5 behavioral tests implemented and APPROVED (2025-11-20)
  - Tests exist in `tests/behavioral/epic_4/`: duplicate detection, cluster coherence, RAG improvement, performance scale, determinism
- 📋 Stories 4.1-4.5: **ready-for-dev** - Context generated, implementation patterns defined
- ✅ Epic 3.5: **complete** - Semantic dependencies (scikit-learn, joblib, textstat) installed and validated

---

## 7. Acceptance Criteria (Epic-Level)

| AC ID | Description | Validation |
|-------|-------------|------------|
| **AC-4-1** | TF-IDF vectorization processes 1000 chunks in <10 seconds | Performance test |
| **AC-4-2** | Duplicate detection achieves ≥85% precision on test corpus | Behavioral test |
| **AC-4-3** | LSA reduces 10,000 features to 100 components with >70% variance explained | Unit test |
| **AC-4-4** | Quality scores correlate with human readability assessment (r>0.7) | Validation study |
| **AC-4-5** | CLI commands process directory and generate report | Integration test |
| **AC-4-6** | Cache reduces repeated analysis time by >90% | Performance test |
| **AC-4-7** | Memory usage stays under 500MB for 10k document corpus | Memory profiler |
| **AC-4-8** | All 5 behavioral tests passing | Test suite |

---

## 8. Dependencies & Prerequisites

### 8.1 Epic Dependencies

**Depends On:**
- ✅ Epic 3 (Chunk Processing) - Complete
- ✅ Epic 3.5 (Semantic Dependencies) - scikit-learn, joblib, textstat installed
- ✅ Epic 1-2 (Foundation) - Pipeline architecture established

**Blocks:**
- ⚠️ Epic 5 (Output & Integration) - Requires semantic analysis for enhanced output

### 8.2 Library Dependencies

```toml
[project]
dependencies = [
    "scikit-learn>=1.3.0,<2.0.0",  # TF-IDF, LSA, clustering
    "joblib>=1.3.0",                # Model persistence
    "textstat>=0.7.3",              # Readability metrics
    "numpy>=1.24.0",                # Array operations
    "scipy>=1.11.0",                # Sparse matrices
]
```

### 8.3 Data Dependencies

- ✅ Semantic test corpus (50+ documents, 250k+ words) - Created in Epic 3.5
- ✅ Golden dataset with verified duplicates (45 documents, 264k words) - Story 3.5-6
- ✅ Labeled clusters for validation - Available in `tests/fixtures/semantic/`
- ✅ RAG relevance judgments - Available in `tests/fixtures/semantic/gold-standard/`

### 8.4 Architecture Assessment

**Winston's Epic 4 Knowledge Curation Architecture** (2025-11-20):
- Reference: [architecture/epic-4-knowledge-curation-architecture.md](./architecture/epic-4-knowledge-curation-architecture.md)
- Validates 100x cost reduction economic model ($1,000 → $15 per 10k docs)
- Confirms classical NLP approach for LLM pre-filtering
- Verifies performance headroom (7.6% TF-IDF utilization, 35x throughput capacity)
- **Verdict**: APPROVED with conditions (behavioral tests required)
- ✅ **Conditions MET** (2025-11-20): Story 4-0 behavioral tests implemented and approved

---

## 9. Risks & Mitigations

| Risk ID | Description | Probability | Impact | Mitigation |
|---------|-------------|-------------|--------|------------|
| **R-4-1** | Memory overflow with large similarity matrices | Medium | HIGH | Sparse matrices, block-wise computation |
| **R-4-2** | Cache corruption affecting results | Low | HIGH | Checksums, automatic regeneration |
| **R-4-3** | Poor clustering quality | Medium | MEDIUM | Multiple algorithms, parameter tuning |
| **R-4-4** | Performance degradation at scale | Medium | MEDIUM | Profiling, optimization, batching |
| **R-4-5** | Vocabulary explosion | Low | LOW | Max features cap, min/max df |

---

## 10. Test Strategy

### 10.1 Behavioral Tests (Primary) - ✅ IMPLEMENTED

**Status**: All 5 behavioral tests implemented and approved in Story 4-0 (2025-11-20)

**Location**: `tests/behavioral/epic_4/`

```python
# 5 Critical Behavioral Tests - ✅ ALL PASSING
test_duplicate_detection_accuracy()  # BT-001: ≥85% precision - tests/behavioral/epic_4/test_duplicate_detection.py
test_cluster_coherence_validation()  # BT-002: Silhouette ≥0.65 - tests/behavioral/epic_4/test_cluster_coherence.py
test_rag_precision_improvement()     # BT-003: ≥25% improvement - tests/behavioral/epic_4/test_rag_improvement.py
test_scale_performance_10k_docs()    # BT-004: <60s, <500MB - tests/behavioral/epic_4/test_performance_scale.py
test_deterministic_output()          # BT-005: 100% reproducible - tests/behavioral/epic_4/test_determinism.py
```

**Golden Dataset**: 45 verified duplicate pairs created in Story 3.5-6, available in `tests/fixtures/semantic/`

### 10.2 Integration Tests

- End-to-end pipeline: Chunks → TF-IDF → LSA → Similarity → Report
- Cache warming and retrieval validation
- CLI command execution and output verification

### 10.3 Performance Tests

- TF-IDF baseline: <100ms per 1k words
- LSA baseline: <200ms per 100 docs
- Memory profiling: <500MB for 10k docs
- Cache effectiveness: >90% speedup

---

## 11. Implementation Strategy

### 11.1 Development Phases

**Phase 0: Test Infrastructure (COMPLETED ✅)**
- Story 4.0: Behavioral tests implementation (DONE 2025-11-20)
- All 5 behavioral tests created and validated
- Golden dataset with 45 verified duplicate pairs
- Test fixtures in place

**Phase 1: Foundation (Day 1-2)**
- Story 4.1: TF-IDF vectorization with caching
- Validate against BT-001 (duplicate detection)

**Phase 2: Analysis (Day 2-3)**
- Story 4.2: Similarity analysis (parallel with 4.3)
- Story 4.3: LSA topic extraction
- Validate against BT-002, BT-003

**Phase 3: Enhancement (Day 3-4)**
- Story 4.4: Quality metrics
- Validate against BT-004, BT-005

**Phase 4: Integration (Day 4-5)**
- Story 4.5: CLI commands and reporting
- End-to-end integration testing
- Documentation and handoff

### 11.2 Quality Gates

Each story must pass:
1. Unit tests (>80% coverage)
2. Code quality (Black, Ruff, Mypy)
3. Performance benchmarks
4. Behavioral validation
5. Peer review

---

## 12. Definition of Done

Epic 4 is **DONE** when:

### 12.1 Code Complete
- ✅ All 5 stories implemented and merged
- ✅ All quality gates passing (Black/Ruff/Mypy)
- ✅ Test coverage ≥80% for semantic modules

### 12.2 Testing Complete
- ✅ 5 behavioral tests passing
- ✅ Integration tests passing
- ✅ Performance within NFR limits

### 12.3 Documentation Complete
- ✅ API documentation for all public methods
- ✅ CLI command documentation
- ✅ Configuration examples

### 12.4 Validation Complete
- ✅ Golden dataset validation passing
- ✅ Cache strategy working as designed
- ✅ Memory usage under limits

---

## 13. Traceability Matrix

### 13.1 Requirements to Stories

| Requirement | Story | Test | Status |
|-------------|-------|------|--------|
| **Behavioral Tests** | **4.0** | **BT-001 to BT-005** | **✅ DONE (2025-11-20)** |
| Vectorization | 4.1 | BT-001, unit tests | 📋 Ready for Dev |
| Deduplication | 4.2 | BT-001 | 📋 Ready for Dev |
| Clustering | 4.3 | BT-002 | 📋 Ready for Dev |
| Quality | 4.4 | Unit tests | 📋 Ready for Dev |
| CLI | 4.5 | Integration tests | 📋 Ready for Dev |

### 13.2 Architecture Alignment

| Component | Architecture Doc | Implementation | Status |
|-----------|------------------|----------------|--------|
| Behavioral Tests | Winston's assessment (Epic 4) | Story 4.0 | ✅ Complete |
| TF-IDF Engine | Winston's assessment, ADR-012 | Story 4.1 | 📋 Ready |
| Similarity Analysis | Winston's assessment | Story 4.2 | 📋 Ready |
| LSA/Clustering | Winston's assessment | Story 4.3 | 📋 Ready |
| Quality Metrics | PRD FR-5.4 | Story 4.4 | 📋 Ready |
| CLI Integration | PRD FR-7 | Story 4.5 | 📋 Ready |
| Cache Strategy | ADR-012 | All stories | ✅ Designed |

### 13.3 PRD Requirements Coverage

| PRD Requirement | Epic 4 Stories | Status |
|-----------------|----------------|--------|
| FR-5.1: TF-IDF Vectorization | Story 4.1 | 📋 Ready |
| FR-5.2: Document Similarity | Story 4.2 | 📋 Ready |
| FR-5.3: LSA Topic Extraction | Story 4.3 | 📋 Ready |
| FR-5.4: Quality Metrics | Story 4.4 | 📋 Ready |
| FR-7: CLI Integration | Story 4.5 | 📋 Ready |

---

## Appendix A: Technical Details

### A.1 TF-IDF Configuration

```python
TfidfVectorizer(
    max_features=10000,
    min_df=0.01,
    max_df=0.95,
    ngram_range=(1, 2),
    sublinear_tf=True,
    use_idf=True
)
```

### A.2 LSA Configuration

```python
TruncatedSVD(
    n_components=100,
    algorithm='randomized',
    n_iter=5,
    random_state=42
)
```

### A.3 Clustering Configuration

```python
KMeans(
    n_clusters=50,
    init='k-means++',
    n_init=10,
    max_iter=300,
    random_state=42
)
```

---

## Appendix B: CLI Examples

```bash
# Analyze document corpus
data-extract semantic analyze --input docs/ --output analysis.json

# Deduplicate documents
data-extract semantic deduplicate --threshold 0.95 --input docs/ --output unique/

# Cluster documents
data-extract semantic cluster --n-clusters 50 --input docs/ --output clusters/

# Generate quality report
data-extract semantic quality --min-score 0.7 --input docs/ --report quality.csv

# Cache management
data-extract cache status
data-extract cache clear --model tfidf
data-extract cache warm --corpus training/
```

---

**Epic Owner Approval**: John (PM)
**Technical Review**: Winston (Architect) ✅
**Implementation Team**: Charlie, Elena, Winston
**Next Step**: Begin Story 4.1 implementation

---

*This technical specification provides the complete blueprint for Epic 4 implementation, focusing on classical NLP techniques for knowledge curation and economic optimization of LLM processing.*
