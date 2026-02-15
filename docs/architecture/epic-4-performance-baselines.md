# Epic 4 Performance Baseline Recommendations

**Date**: 2025-11-20
**Architect**: Winston (System Architect)
**Context**: Pre-Epic 4 Baseline Establishment

---

## Executive Summary

Epic 4 must establish performance baselines **before implementation** to prevent regression and validate the economic value proposition. Current profiling shows we're operating at **7.6% of capacity**, providing massive headroom. These baselines will become quality gates for semantic operations.

---

## Current Performance Reality

### Existing Measurements (Epic 3.5)

```python
Current Performance (from Epic 3.5 profiling):
├── TF-IDF Operations: 7.6ms / 100ms limit = 7.6% utilization
├── Pipeline Throughput: 2.8% of limit (35x headroom!)
├── Memory Usage: 255MB / 500MB = 51% utilization
├── spaCy Processing: 1.8s per 10k words (within 2.0s limit)
└── Cache Operations: Not yet measured
```

**Key Insight**: We have **92.4% unused performance capacity**. Optimization is unnecessary; correctness is everything.

---

## Required Baseline Metrics

### 1. TF-IDF Vectorization Baselines

```yaml
tfidf_baselines:
  fit_operation:
    small_corpus:
      size: 100 documents
      max_time: 50ms
      memory_limit: 10MB

    medium_corpus:
      size: 1,000 documents
      max_time: 100ms  # Current: 7.6ms
      memory_limit: 50MB

    large_corpus:
      size: 10,000 documents
      max_time: 1000ms
      memory_limit: 200MB

  transform_operation:
    per_document: 0.1ms
    batch_1000: 50ms
    memory_overhead: 5MB per 1000 docs

  vocabulary_size:
    small: 1000 features
    standard: 10000 features  # Recommended
    large: 50000 features
```

### 2. Similarity Computation Baselines

```yaml
similarity_baselines:
  pairwise_computation:
    100x100_matrix:
      max_time: 20ms
      memory: 1MB

    1000x1000_matrix:
      max_time: 200ms
      memory: 40MB

    10000x10000_matrix:
      max_time: 5000ms
      memory: 4GB  # Warning: Approaches limit

  duplicate_detection:
    threshold: 0.95
    100_docs: 10ms
    1000_docs: 100ms
    10000_docs: 2000ms

  similarity_graph_building:
    edges_threshold: 0.7
    max_edges_per_node: 20
    build_time: 2x similarity_computation
```

### 3. LSA/Dimensionality Reduction Baselines

```yaml
lsa_baselines:
  truncated_svd:
    components_50:
      1000_docs: 150ms
      memory: 20MB

    components_100:  # Recommended
      1000_docs: 300ms
      memory: 40MB

    components_300:
      1000_docs: 900ms
      memory: 120MB

  explained_variance:
    min_threshold: 0.8  # 80% variance explained
    typical_components: 100-150

  clustering_kmeans:
    k_10:
      1000_docs: 200ms
    k_50:
      1000_docs: 1000ms
    k_100:
      1000_docs: 2000ms
```

### 4. Cache Performance Baselines

```yaml
cache_baselines:
  cold_start:
    tfidf_fit: 100ms
    lsa_fit: 300ms
    similarity_compute: 200ms
    total_pipeline: 600ms

  warm_cache:
    tfidf_load: 5ms  # 20x speedup
    lsa_load: 10ms   # 30x speedup
    similarity_load: 8ms  # 25x speedup
    total_pipeline: 25ms  # 24x speedup

  cache_operations:
    key_generation: <1ms
    file_write: <50ms
    file_read: <20ms
    compression_ratio: 0.3  # 30% of original size

  storage_requirements:
    per_1k_corpus:
      tfidf_model: 10-20MB
      lsa_model: 5-10MB
      similarity_matrix: 4MB
      total: 20-35MB
```

### 5. Quality Scoring Baselines

```yaml
quality_baselines:
  textstat_metrics:
    per_chunk:
      flesch_kincaid: 2ms
      gunning_fog: 2ms
      smog_index: 2ms
      total: 10ms  # All metrics

    batch_processing:
      100_chunks: 1000ms
      1000_chunks: 10000ms

  quality_thresholds:
    good_content:
      flesch_kincaid: 8-14
      gunning_fog: 10-16
      lexical_diversity: >0.4

    flagged_content:
      flesch_kincaid: >20 or <4
      gunning_fog: >20
      lexical_diversity: <0.2
```

---

## Measurement Script

### Create Performance Baseline Script

```python
# scripts/measure_semantic_baselines.py

import time
import tracemalloc
import numpy as np
from pathlib import Path
from typing import Dict, List
import json

def measure_tfidf_baseline(corpus: List[str]) -> Dict:
    """Measure TF-IDF performance baselines."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    results = {}

    # Measure fit operation
    vectorizer = TfidfVectorizer(max_features=10000)

    tracemalloc.start()
    start = time.perf_counter()

    vectors = vectorizer.fit_transform(corpus)

    elapsed = time.perf_counter() - start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    results['tfidf'] = {
        'corpus_size': len(corpus),
        'fit_time_ms': elapsed * 1000,
        'memory_mb': peak / 1024 / 1024,
        'vocabulary_size': len(vectorizer.vocabulary_),
        'matrix_shape': vectors.shape,
        'sparsity': 1.0 - (vectors.nnz / (vectors.shape[0] * vectors.shape[1]))
    }

    return results, vectors

def measure_similarity_baseline(vectors) -> Dict:
    """Measure similarity computation baselines."""
    from sklearn.metrics.pairwise import cosine_similarity

    tracemalloc.start()
    start = time.perf_counter()

    similarity_matrix = cosine_similarity(vectors)

    elapsed = time.perf_counter() - start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Find duplicates
    duplicate_threshold = 0.95
    duplicates = np.sum(similarity_matrix > duplicate_threshold) - vectors.shape[0]

    return {
        'similarity': {
            'matrix_size': similarity_matrix.shape,
            'computation_time_ms': elapsed * 1000,
            'memory_mb': peak / 1024 / 1024,
            'duplicates_found': duplicates // 2,  # Symmetric matrix
            'mean_similarity': np.mean(similarity_matrix),
            'std_similarity': np.std(similarity_matrix)
        }
    }

def measure_lsa_baseline(vectors, n_components=100) -> Dict:
    """Measure LSA performance baselines."""
    from sklearn.decomposition import TruncatedSVD

    tracemalloc.start()
    start = time.perf_counter()

    svd = TruncatedSVD(n_components=n_components)
    lsa_vectors = svd.fit_transform(vectors)

    elapsed = time.perf_counter() - start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        'lsa': {
            'n_components': n_components,
            'fit_time_ms': elapsed * 1000,
            'memory_mb': peak / 1024 / 1024,
            'explained_variance': float(np.sum(svd.explained_variance_ratio_)),
            'output_shape': lsa_vectors.shape
        }
    }

def measure_cache_baseline(corpus: List[str]) -> Dict:
    """Measure cache performance baselines."""
    import joblib
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = Path(tmpdir) / "test_model.joblib"

        # Create a model
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer(max_features=10000)
        vectorizer.fit(corpus)

        # Measure save time
        start_save = time.perf_counter()
        joblib.dump(vectorizer, cache_file, compress=3)
        save_time = time.perf_counter() - start_save

        file_size = cache_file.stat().st_size

        # Measure load time
        start_load = time.perf_counter()
        loaded_model = joblib.load(cache_file)
        load_time = time.perf_counter() - start_load

        return {
            'cache': {
                'save_time_ms': save_time * 1000,
                'load_time_ms': load_time * 1000,
                'file_size_mb': file_size / 1024 / 1024,
                'compression_ratio': file_size / (len(corpus) * 100)  # Approximate
            }
        }

def run_baseline_suite(corpus_sizes=[100, 1000, 5000]):
    """Run complete baseline measurements."""
    from tests.fixtures.semantic_corpus import generate_corpus

    all_results = {}

    for size in corpus_sizes:
        print(f"\nMeasuring baselines for {size} documents...")
        corpus = generate_corpus(size)

        # TF-IDF
        tfidf_results, vectors = measure_tfidf_baseline(corpus)
        all_results[f'corpus_{size}'] = tfidf_results

        # Similarity
        sim_results = measure_similarity_baseline(vectors)
        all_results[f'corpus_{size}'].update(sim_results)

        # LSA
        lsa_results = measure_lsa_baseline(vectors)
        all_results[f'corpus_{size}'].update(lsa_results)

        # Cache
        cache_results = measure_cache_baseline(corpus)
        all_results[f'corpus_{size}'].update(cache_results)

    return all_results

if __name__ == "__main__":
    results = run_baseline_suite()

    # Save results
    output_file = Path("tests/baselines/semantic_performance_measured.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nBaselines saved to {output_file}")

    # Print summary
    for corpus_size, metrics in results.items():
        print(f"\n{corpus_size}:")
        print(f"  TF-IDF: {metrics['tfidf']['fit_time_ms']:.1f}ms")
        print(f"  Similarity: {metrics['similarity']['computation_time_ms']:.1f}ms")
        print(f"  LSA: {metrics['lsa']['fit_time_ms']:.1f}ms")
        print(f"  Cache Save: {metrics['cache']['save_time_ms']:.1f}ms")
        print(f"  Cache Load: {metrics['cache']['load_time_ms']:.1f}ms")
```

---

## Baseline Validation Rules

### Performance Gates

```python
# tests/integration/test_performance_gates.py

def test_tfidf_performance_gate():
    """TF-IDF must stay within baseline limits."""
    corpus = generate_standard_corpus(1000)

    start = time.perf_counter()
    vectorizer = TfidfVectorizer(max_features=10000)
    vectors = vectorizer.fit_transform(corpus)
    elapsed = (time.perf_counter() - start) * 1000

    assert elapsed < 100, f"TF-IDF took {elapsed:.1f}ms, limit is 100ms"

def test_cache_speedup_gate():
    """Cache must provide >10x speedup."""
    corpus = generate_standard_corpus(1000)

    # Cold run
    start_cold = time.perf_counter()
    result1 = semantic_pipeline(corpus, use_cache=False)
    time_cold = time.perf_counter() - start_cold

    # Warm run
    start_warm = time.perf_counter()
    result2 = semantic_pipeline(corpus, use_cache=True)
    time_warm = time.perf_counter() - start_warm

    speedup = time_cold / time_warm
    assert speedup > 10, f"Cache speedup only {speedup:.1f}x, need >10x"
```

### Memory Gates

```python
def test_memory_usage_gate():
    """Memory must stay within limits."""
    import tracemalloc

    corpus = generate_standard_corpus(10000)

    tracemalloc.start()
    initial = tracemalloc.get_traced_memory()[0]

    # Run semantic pipeline
    result = semantic_pipeline(corpus)

    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()

    memory_used_mb = (peak - initial) / 1024 / 1024
    assert memory_used_mb < 500, f"Used {memory_used_mb:.1f}MB, limit is 500MB"
```

---

## Regression Detection

### Continuous Monitoring

```yaml
# .github/workflows/performance.yml

name: Performance Regression Check

on:
  pull_request:
    paths:
      - 'src/data_extract/semantic/**'

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Performance Baselines
        run: |
          python scripts/measure_semantic_baselines.py

      - name: Compare Against Baselines
        run: |
          python scripts/compare_baselines.py \
            --current tests/baselines/semantic_performance_measured.json \
            --reference tests/baselines/semantic_performance_expected.json \
            --tolerance 0.2  # Allow 20% variance

      - name: Upload Results
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: performance-regression
          path: tests/baselines/
```

---

## Recommendations

### Must-Have Baselines (Before Epic 4)

1. **TF-IDF fit time** for 1000 documents
2. **Similarity matrix computation** for 1000x1000
3. **Cache speedup factor** (must be >10x)
4. **Memory usage** for standard corpus
5. **Quality scoring speed** per chunk

### Nice-to-Have Baselines

1. Incremental corpus updates
2. Parallel processing speedup
3. Disk I/O patterns
4. Network cache latency
5. Garbage collection impact

### What NOT to Measure

❌ **Don't measure library internals** (scikit-learn performance)
❌ **Don't micro-optimize** (we're at 7.6% capacity!)
❌ **Don't measure test code** (only production code)
❌ **Don't measure mock performance** (meaningless)

---

## Action Items

### Before Epic 4 Story 4.1

1. **Run baseline script** on standard corpus
   ```bash
   python scripts/measure_semantic_baselines.py
   ```

2. **Commit baseline file** to repository
   ```bash
   git add tests/baselines/semantic_performance_measured.json
   git commit -m "Establish Epic 4 performance baselines"
   ```

3. **Add to CI pipeline**
   - Create performance regression workflow
   - Set 20% tolerance for variance
   - Block PRs that exceed limits

4. **Document in README**
   ```markdown
   ## Performance Baselines
   - TF-IDF: <100ms for 1k documents
   - Cache Speedup: >10x
   - Memory: <500MB for 10k documents
   ```

---

## The Bottom Line

**Winston's Take**: "We're running at 7.6% capacity. These baselines aren't about optimization—they're about not making things worse. Measure once, validate continuously, optimize never."

**Key Insight**: Performance is already 13x better than required. Focus on **correctness and maintainability**, not speed.

---

*Baseline Recommendations Complete: 2025-11-20*
*Must Implement Before: Epic 4 Story 4.1*
*Time Required: 4 hours*

## Updated Baselines (2026-02-15 16:56)

| Metric | Value | Unit | Component |
|--------|-------|------|----------|
| test_metric | 1.500 | seconds | test |
