# Epic Technical Specification: Behavioral Test Strategy for Knowledge Curation

Date: 2025-11-20
Author: andrew
Epic ID: 4
Status: Draft

---

## Overview

This technical specification defines a comprehensive behavioral test strategy for Epic 4's knowledge curation capabilities using classical NLP techniques (TF-IDF, LSA). The strategy focuses on validating semantic correctness through measurable outcomes rather than implementation details. This document addresses the critical gap identified in the deployment readiness assessment: zero behavioral tests for semantic features.

The strategy prioritizes real-world validation of duplicate detection accuracy, cluster coherence, and RAG retrieval precision improvements - the core value propositions of the knowledge curation system.

## Objectives and Scope

### In-Scope:
- **5 critical behavioral tests** validating semantic correctness
- **Golden dataset requirements** with verified duplicates and labeled clusters
- **Assertion patterns** for behavioral outcomes (not structure)
- **Integration with existing test infrastructure** (pytest, fixtures)
- **CI validation approach** for semantic quality metrics
- **Performance baselines** as secondary validation (not primary focus)

### Out-of-Scope:
- Unit tests for individual TF-IDF/LSA functions (covered elsewhere)
- Performance optimization tests (system at 7.6% capacity)
- Real-time monitoring (deferred to production)
- Complex configuration testing (using existing YAML)
- UI/visualization testing (CLI-only focus)

## System Architecture Alignment

The behavioral test strategy aligns with the existing architecture documented in `docs/architecture/data-architecture.md`:

- **Pipeline Integration**: Tests validate the complete Extract → Normalize → Chunk → Semantic → Output pipeline
- **Immutable Data Models**: Leverages frozen dataclasses and Pydantic models for deterministic testing
- **File-Based Storage**: Uses joblib cache and file-based manifests as per ADR-012
- **Classical NLP Stack**: Tests TF-IDF vectorization and LSA dimensionality reduction without transformer dependencies
- **Entity Preservation**: Validates that semantic analysis maintains entity relationships (RISK→CONTROL)

## Detailed Design

### Services and Modules

| Module | Responsibility | Test Coverage | Owner |
|--------|---------------|---------------|-------|
| `semantic.tfidf` | TF-IDF vectorization engine | Behavioral: duplicate detection accuracy | Test Team |
| `semantic.similarity` | Document/chunk similarity analysis | Behavioral: cluster coherence validation | Test Team |
| `semantic.lsa` | Latent Semantic Analysis | Behavioral: dimensionality reduction quality | Test Team |
| `semantic.quality` | Quality metrics integration | Behavioral: readability improvement | Test Team |
| `semantic.pipeline` | End-to-end orchestration | Integration: full pipeline validation | Test Team |

### Data Models and Contracts

```python
# Behavioral Test Data Models
@dataclass(frozen=True)
class BehavioralTestCase:
    """Immutable test case for behavioral validation"""
    test_id: str
    input_documents: List[Document]
    expected_behavior: Dict[str, Any]
    success_criteria: Dict[str, float]

@dataclass(frozen=True)
class SemanticGoldenDataset:
    """Golden dataset for semantic validation"""
    verified_duplicates: List[Tuple[str, str, float]]  # (doc1, doc2, similarity_score)
    labeled_clusters: Dict[str, List[str]]  # cluster_id -> [doc_ids]
    rag_relevance_pairs: List[Tuple[str, str, float]]  # (query, doc, relevance_score)

@dataclass(frozen=True)
class BehavioralTestResult:
    """Result of behavioral test execution"""
    test_id: str
    passed: bool
    actual_metrics: Dict[str, float]
    expected_metrics: Dict[str, float]
    failure_reasons: List[str]
```

### APIs and Interfaces

```python
# Behavioral Test Interface
class BehavioralTestRunner:
    def run_test(self, test_case: BehavioralTestCase) -> BehavioralTestResult:
        """Execute a single behavioral test"""

    def validate_duplicate_detection(self,
                                    documents: List[Document],
                                    expected_duplicates: List[Tuple[str, str]]) -> float:
        """Returns precision/recall for duplicate detection"""

    def validate_cluster_coherence(self,
                                  documents: List[Document],
                                  expected_clusters: Dict[str, List[str]]) -> float:
        """Returns silhouette score for cluster quality"""

    def validate_rag_improvement(self,
                                queries: List[str],
                                documents: List[Document],
                                baseline_results: List[str],
                                tfidf_results: List[str]) -> float:
        """Returns precision improvement percentage"""
```

### Workflows and Sequencing

```
Behavioral Test Execution Flow:

1. Load Golden Dataset
   ├─→ Verified duplicates (45 document pairs)
   ├─→ Labeled clusters (10 topic groups)
   └─→ RAG relevance judgments (100 query-doc pairs)

2. Execute Test Case
   ├─→ Process documents through semantic pipeline
   ├─→ Collect actual behavioral metrics
   └─→ Compare against success criteria

3. Validate Behaviors
   ├─→ Test 1: Duplicate Detection
   │    ├─→ Identify near-duplicates using cosine similarity
   │    ├─→ Compare with golden duplicate pairs
   │    └─→ Assert: Precision ≥ 0.85, Recall ≥ 0.80
   │
   ├─→ Test 2: Cluster Coherence
   │    ├─→ Cluster documents using LSA + K-means
   │    ├─→ Calculate silhouette score
   │    └─→ Assert: Score ≥ 0.65 (good separation)
   │
   ├─→ Test 3: RAG Improvement
   │    ├─→ Compare baseline vs TF-IDF retrieval
   │    ├─→ Measure precision@k improvement
   │    └─→ Assert: Improvement ≥ 25%
   │
   ├─→ Test 4: Scale Performance
   │    ├─→ Process 10K document corpus
   │    ├─→ Measure memory and latency
   │    └─→ Assert: <500MB memory, <60s processing
   │
   └─→ Test 5: Determinism
        ├─→ Process same input 3 times
        ├─→ Compare outputs byte-for-byte
        └─→ Assert: 100% identical outputs

4. Report Results
   └─→ Generate behavioral test report with metrics
```

## Non-Functional Requirements

### Performance

- **Latency**: TF-IDF vectorization <100ms for 1000 documents
- **Memory**: <500MB for 10K document corpus
- **Throughput**: Process 100 documents/second
- **Note**: Performance is secondary to correctness (system at 7.6% capacity)

### Security

- **PII Protection**: All test fixtures confirmed PII-free
- **Input Validation**: Sanitize all text inputs before processing
- **Cache Security**: Secure joblib cache with file permissions

### Reliability/Availability

- **Determinism**: Same input MUST produce identical outputs
- **Error Recovery**: Graceful handling of malformed documents
- **Partial Failure**: Continue processing valid documents when some fail

### Observability

- **Test Metrics**: Log all behavioral metric calculations
- **Failure Diagnostics**: Detailed reasons for test failures
- **Coverage Tracking**: Report behavioral coverage percentage

## Dependencies and Integrations

```yaml
# Test Dependencies
dependencies:
  runtime:
    - scikit-learn==1.3.0  # TF-IDF, LSA, clustering
    - numpy==1.24.3        # Numerical operations
    - scipy==1.11.1        # Similarity calculations
    - spacy==3.6.0         # Tokenization (en_core_web_md)

  testing:
    - pytest==7.4.0        # Test framework
    - pytest-benchmark     # Performance baselines
    - pandas==2.0.3        # Golden dataset management

  fixtures:
    - semantic_corpus      # 264K word corpus from Story 3.5-6
    - gold_annotations     # 45 document annotations
    - entity_fixtures      # RISK/CONTROL test data
```

## Acceptance Criteria (Authoritative)

1. **AC-BT-1**: Duplicate detection achieves ≥85% precision and ≥80% recall on golden dataset
2. **AC-BT-2**: Document clustering achieves silhouette score ≥0.65 for coherent topic groups
3. **AC-BT-3**: TF-IDF improves RAG retrieval precision by ≥25% over baseline
4. **AC-BT-4**: System processes 10K documents in <60 seconds with <500MB memory
5. **AC-BT-5**: Identical inputs produce 100% deterministic outputs across runs
6. **AC-BT-6**: All 5 behavioral tests integrated into CI pipeline
7. **AC-BT-7**: Golden dataset contains minimum 45 verified duplicate pairs
8. **AC-BT-8**: Test framework generates actionable failure diagnostics

## Traceability Mapping

| AC ID | Spec Section | Component/API | Test Implementation |
|-------|-------------|---------------|---------------------|
| AC-BT-1 | Duplicate Detection | `semantic.similarity` | `test_duplicate_detection_accuracy()` |
| AC-BT-2 | Cluster Coherence | `semantic.lsa` | `test_cluster_coherence_validation()` |
| AC-BT-3 | RAG Improvement | `semantic.tfidf` | `test_rag_precision_improvement()` |
| AC-BT-4 | Scale Performance | `semantic.pipeline` | `test_scale_performance_10k_docs()` |
| AC-BT-5 | Determinism | All components | `test_deterministic_output()` |
| AC-BT-6 | CI Integration | Test Runner | `pytest.ini` markers |
| AC-BT-7 | Golden Dataset | Test Fixtures | `fixtures/golden_dataset.json` |
| AC-BT-8 | Diagnostics | Test Reporter | `BehavioralTestResult` model |

## Risks, Assumptions, Open Questions

### Risks:
- **Risk-1**: Golden dataset quality affects all behavioral validations
  - *Mitigation*: Manual review of all annotations by 2 reviewers
- **Risk-2**: Non-deterministic clustering algorithms
  - *Mitigation*: Fix random seeds, use deterministic K-means initialization
- **Risk-3**: Memory constraints on CI servers
  - *Mitigation*: Implement chunked processing for large corpus tests

### Assumptions:
- **Assumption-1**: Semantic corpus (264K words) represents production data distribution
- **Assumption-2**: Cosine similarity threshold of 0.7 identifies true duplicates
- **Assumption-3**: Silhouette score is valid metric for document cluster quality

### Open Questions:
- **Question-1**: Should we test cross-language duplicate detection?
- **Question-2**: What's the minimum cluster size for valid coherence scoring?
- **Question-3**: Should behavioral tests validate entity relationship preservation?

## Test Strategy Summary

### Test Levels:
1. **Behavioral Tests** (Primary): 5 critical tests validating semantic correctness
2. **Integration Tests** (Secondary): Pipeline end-to-end validation
3. **Performance Tests** (Tertiary): Baseline validation only

### Test Framework:
- **Runner**: pytest with custom behavioral test markers
- **Fixtures**: Reusable golden datasets and semantic corpus
- **Assertions**: Outcome-based (precision, recall, coherence scores)
- **Reporting**: Detailed behavioral metrics with failure diagnostics

### Coverage Goals:
- **Behavioral Coverage**: 100% of critical semantic behaviors
- **Integration Coverage**: Key pipeline paths (80%)
- **Code Coverage**: Not a primary metric (focus on behavior)

### CI Integration:
```bash
# Run behavioral tests in CI
pytest tests/behavioral/test_semantic/ -m "behavioral and semantic" --benchmark-only

# Validate golden dataset integrity
pytest tests/fixtures/test_golden_dataset.py -m "golden"

# Generate behavioral coverage report
pytest --behavioral-cov=src/data_extract/semantic --behavioral-cov-report=term
```

### Edge Cases:
- Empty documents
- Single-word documents
- Documents with only special characters
- Identical documents (100% duplicates)
- Completely unrelated documents (0% similarity)
- Very large documents (>10MB)
- Mixed language documents

---

## Implementation Roadmap

### Wave 1: Test Reality Sprint (Current)
1. ✅ Generate behavioral test strategy (this document)
2. Create golden dataset with verified annotations
3. Implement 5 critical behavioral tests
4. Validate tests with existing semantic corpus

### Wave 2: CI Integration
1. Add behavioral test markers to pytest
2. Configure CI pipeline for behavioral validation
3. Create behavioral coverage reporting
4. Document failure diagnosis procedures

### Wave 3: Continuous Improvement
1. Expand golden dataset based on production data
2. Add cross-validation for cluster stability
3. Implement A/B testing framework for algorithm comparison
4. Create behavioral test dashboard

---

**Status**: This behavioral test strategy is ready for implementation. The 5 critical tests defined here will validate Epic 4's semantic correctness before deployment.
