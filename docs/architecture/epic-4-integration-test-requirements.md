# Epic 4 Integration Test Requirements - Behavioral Focus

**Date**: 2025-11-20
**Architect**: Winston (System Architect)
**Type**: Behavioral Test Specification
**Priority**: CRITICAL - Must implement before Story 4.1

---

## Executive Summary

Replace the 908-line integration test design with **5 core behavioral tests** that validate semantic correctness. These tests focus on **what the system does**, not how it's structured. Each test validates a critical semantic behavior that, if broken, would compromise the entire knowledge curation value proposition.

---

## The 5 Core Behavioral Tests

### Test 1: Deduplication Actually Reduces Corpus

```python
# tests/integration/test_semantic_behavior.py

def test_deduplication_reduces_corpus():
    """
    CRITICAL BEHAVIOR: Duplicate detection must actually remove documents.

    Given: A corpus with known duplicates
    When: Deduplication is applied with threshold 0.95
    Then: The corpus size decreases by the number of duplicates
    And: No unique documents are incorrectly removed
    And: The operation is idempotent
    """
    # Arrange
    corpus = [
        "The quick brown fox jumps over the lazy dog.",
        "The quick brown fox jumps over the lazy dog.",  # Exact duplicate
        "The quick brown fox leaps over the lazy dog.",   # Near duplicate
        "A completely different document about cats.",     # Unique
        "The quick brown fox jumps over the lazy dog!",    # Near duplicate (punctuation)
    ]

    # Act
    vectorizer = TfIdfVectorizer(max_features=100)
    vectors = vectorizer.fit_transform(corpus)
    similarities = compute_cosine_similarity(vectors)
    deduplicated = remove_duplicates(corpus, similarities, threshold=0.95)

    # Assert
    assert len(deduplicated) == 2  # Only unique + one representative
    assert "cats" in " ".join(deduplicated)  # Unique doc preserved
    assert "fox" in " ".join(deduplicated)   # Representative preserved

    # Idempotency check
    vectors2 = vectorizer.fit_transform(deduplicated)
    similarities2 = compute_cosine_similarity(vectors2)
    deduplicated2 = remove_duplicates(deduplicated, similarities2, threshold=0.95)
    assert deduplicated == deduplicated2  # Idempotent operation
```

**Why This Matters**: If deduplication doesn't actually reduce the corpus, the entire economic value proposition fails. We'd be processing duplicates at full LLM cost.

---

### Test 2: Similarity Matrix Is Symmetric and Bounded

```python
def test_similarity_matrix_properties():
    """
    CRITICAL BEHAVIOR: Similarity must be mathematically correct.

    Given: Any set of documents
    When: Cosine similarity is computed
    Then: similarity(A,B) == similarity(B,A) for all pairs
    And: All values are in range [0, 1]
    And: Diagonal elements equal 1.0 (self-similarity)
    """
    # Arrange
    corpus = load_semantic_test_corpus()  # 50+ diverse documents

    # Act
    vectorizer = TfIdfVectorizer(max_features=1000)
    vectors = vectorizer.fit_transform(corpus)
    similarity_matrix = compute_cosine_similarity(vectors)

    # Assert - Symmetry
    n = similarity_matrix.shape[0]
    for i in range(n):
        for j in range(i+1, n):
            assert abs(similarity_matrix[i,j] - similarity_matrix[j,i]) < 1e-6

    # Assert - Bounds
    assert similarity_matrix.min() >= -1e-6  # Allow tiny numerical errors
    assert similarity_matrix.max() <= 1.0 + 1e-6

    # Assert - Diagonal
    for i in range(n):
        assert abs(similarity_matrix[i,i] - 1.0) < 1e-6
```

**Why This Matters**: Asymmetric similarity would break deduplication logic. Out-of-bounds values would cause incorrect clustering.

---

### Test 3: Clustering Preserves All Documents

```python
def test_clustering_preserves_all_documents():
    """
    CRITICAL BEHAVIOR: No documents lost during clustering.

    Given: N unique documents
    When: K-means clustering is applied
    Then: Sum of cluster sizes equals N
    And: Each document appears in exactly one cluster
    And: No empty clusters exist (up to K)
    """
    # Arrange
    corpus = generate_diverse_corpus(n_docs=100)

    # Act
    vectorizer = TfIdfVectorizer(max_features=500)
    vectors = vectorizer.fit_transform(corpus)
    lsa = TruncatedSVD(n_components=50)
    lsa_vectors = lsa.fit_transform(vectors)

    k = min(10, len(corpus))  # Number of clusters
    clusters = kmeans_clustering(lsa_vectors, k=k)

    # Assert - All documents preserved
    total_docs_in_clusters = sum(len(cluster) for cluster in clusters)
    assert total_docs_in_clusters == len(corpus)

    # Assert - No duplicates across clusters
    all_indices = []
    for cluster in clusters:
        all_indices.extend(cluster['document_indices'])
    assert len(all_indices) == len(set(all_indices))  # No duplicates

    # Assert - No empty clusters (unless k > n)
    if k <= len(corpus):
        assert all(len(cluster) > 0 for cluster in clusters)
```

**Why This Matters**: Lost documents during clustering would cause incomplete analysis and break audit trail requirements.

---

### Test 4: Cache Returns Identical Results

```python
def test_cache_determinism():
    """
    CRITICAL BEHAVIOR: Cached results must be deterministic.

    Given: The same corpus processed twice
    When: Second processing uses cache
    Then: Results are byte-for-byte identical
    And: Cache hit is logged
    And: Performance improvement > 10x
    """
    # Arrange
    corpus = load_standard_test_corpus()
    cache_dir = Path(".data-extract-cache/models/")
    cache_dir.mkdir(exist_ok=True)

    # Act - First run (cold cache)
    start_cold = time.time()
    result1 = semantic_pipeline(corpus, cache_dir=cache_dir)
    time_cold = time.time() - start_cold

    # Act - Second run (warm cache)
    start_warm = time.time()
    result2 = semantic_pipeline(corpus, cache_dir=cache_dir)
    time_warm = time.time() - start_warm

    # Assert - Identical results
    assert result1.tfidf_vectors.shape == result2.tfidf_vectors.shape
    assert np.allclose(result1.tfidf_vectors.toarray(),
                       result2.tfidf_vectors.toarray())
    assert result1.similarity_matrix.tolist() == result2.similarity_matrix.tolist()
    assert result1.clusters == result2.clusters

    # Assert - Performance improvement
    speedup = time_cold / time_warm
    assert speedup > 10, f"Cache speedup only {speedup:.1f}x, expected >10x"

    # Assert - Cache was used (check logs or cache files)
    cache_files = list(cache_dir.glob("*.joblib"))
    assert len(cache_files) > 0, "No cache files created"
```

**Why This Matters**: Non-deterministic results would break reproducibility requirements for audit compliance.

---

### Test 5: Quality Scoring Identifies Bad Content

```python
def test_quality_scoring_identifies_gibberish():
    """
    CRITICAL BEHAVIOR: Quality metrics must flag problematic content.

    Given: A mix of good content and known bad content
    When: Quality scoring is applied
    Then: Gibberish scores poorly
    And: Good content scores well
    And: OCR artifacts are flagged
    """
    # Arrange
    good_content = [
        "This is a well-written paragraph about risk management.",
        "The internal audit found three control deficiencies.",
    ]

    bad_content = [
        "████ ░░░░ ▓▓▓▓ ####",  # OCR artifacts
        "asfklj askdfj alskdfj alskdfj",  # Keyboard mash
        "The the the the the the the",  # Repetition
    ]

    # Act
    all_content = good_content + bad_content
    quality_scores = compute_quality_scores(all_content)

    # Assert - Good content scores well
    for i, content in enumerate(good_content):
        score = quality_scores[i]
        assert score.flesch_kincaid < 15, f"Good content scored poorly: {score}"
        assert score.quality_flag == "GOOD"

    # Assert - Bad content flagged
    for i, content in enumerate(bad_content):
        score = quality_scores[len(good_content) + i]
        assert score.quality_flag in ["LOW_QUALITY", "GIBBERISH", "OCR_ARTIFACT"]
        assert score.confidence < 0.5, f"Bad content not flagged: {score}"
```

**Why This Matters**: Undetected gibberish would poison LLM context and cause hallucinations.

---

## Test Implementation Requirements

### Test Fixtures

```python
# tests/fixtures/semantic_golden.py

GOLDEN_CORPUS = {
    "duplicates": [
        # Exact and near-duplicates for Test 1
        ("doc1.txt", "doc1_copy.txt", 1.0),  # Exact
        ("doc2.txt", "doc2_typo.txt", 0.98), # Near
    ],
    "unique": [
        # Diverse documents for Test 3
        "technical_report.txt",
        "financial_audit.txt",
        "security_policy.txt",
    ],
    "gibberish": [
        # Known bad content for Test 5
        "ocr_artifacts.txt",
        "corrupted_extraction.txt",
    ]
}
```

### Performance Baselines

```yaml
# tests/baselines/semantic_performance.yaml

performance_requirements:
  tfidf_fit:
    max_time_ms: 100
    test_corpus_size: 1000

  similarity_matrix:
    max_time_ms: 200
    matrix_size: 1000x1000

  lsa_transform:
    max_time_ms: 300
    n_components: 100

  cache_speedup:
    min_factor: 10

  quality_scoring:
    max_time_per_doc_ms: 10
```

### Test Execution

```bash
# Run only the 5 core behavioral tests
pytest tests/integration/test_semantic_behavior.py -v

# Expected output:
test_deduplication_reduces_corpus PASSED
test_similarity_matrix_properties PASSED
test_clustering_preserves_all_documents PASSED
test_cache_determinism PASSED
test_quality_scoring_identifies_gibberish PASSED

# With performance validation
pytest tests/integration/test_semantic_behavior.py \
  --benchmark-only \
  --benchmark-compare=tests/baselines/semantic_performance.yaml
```

---

## What NOT to Test

### Don't Test Structure

```python
# ❌ BAD: Testing structure
def test_tfidf_returns_sparse_matrix():
    assert isinstance(result, scipy.sparse.csr_matrix)

# ✅ GOOD: Testing behavior
def test_tfidf_identifies_duplicates():
    assert len(find_duplicates(corpus)) == expected_duplicates
```

### Don't Test Implementation Details

```python
# ❌ BAD: Testing internals
def test_cache_uses_joblib():
    assert cache_file.endswith('.joblib')

# ✅ GOOD: Testing behavior
def test_cache_returns_same_results():
    assert first_run_results == cached_run_results
```

### Don't Test Library Functions

```python
# ❌ BAD: Testing scikit-learn
def test_sklearn_cosine_similarity():
    assert cosine_similarity([[1,0]], [[1,0]]) == 1.0

# ✅ GOOD: Testing our usage
def test_our_similarity_handles_empty_documents():
    assert compute_similarity(["", "text"]) == expected
```

---

## Implementation Timeline

### Before Story 4.1 (2 Days)

**Day 1**:
- Morning: Implement test_deduplication_reduces_corpus
- Afternoon: Implement test_similarity_matrix_properties

**Day 2**:
- Morning: Implement test_clustering_preserves_all_documents
- Afternoon: Implement test_cache_determinism
- Evening: Implement test_quality_scoring_identifies_gibberish

### Success Criteria

✅ All 5 tests passing
✅ Performance within baselines
✅ No flaky tests (run 10x successfully)
✅ Clear failure messages when broken
✅ Total test runtime < 30 seconds

---

## Why Only 5 Tests?

**Winston's Wisdom**: "These 5 tests validate the core semantic behaviors that, if broken, would destroy the entire value proposition. Everything else is implementation detail."

**What These Tests Prove**:
1. Deduplication saves money (Test 1)
2. Math is correct (Test 2)
3. No data loss (Test 3)
4. Reproducible results (Test 4)
5. Quality control works (Test 5)

**What We're NOT Testing**:
- Code coverage percentages
- Class structures
- Function signatures
- Mock interactions
- Generated test cases

---

*Test Requirements Complete: 2025-11-20*
*Implementation Required Before: Epic 4 Story 4.1*
*Time Estimate: 2 days*
