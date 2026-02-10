# ADR-012: Semantic Model Cache & Persistence Strategy

**Status**: Accepted
**Date**: 2025-11-18
**Decision Maker(s)**: Winston, Andrew
**Epic**: 3.5 (Tooling & Semantic Preparation) / Epic 4 (Semantic Analysis)

## Context

Epic 4 semantic analysis introduces compute-intensive operations that create significant performance bottlenecks when processing audit documents at scale:

- **TF-IDF Vectorization**: Fitting a TF-IDF model on a 10k-document corpus takes ~10 seconds, with transformation adding ~2 seconds per batch
- **LSA Model Training**: Latent Semantic Analysis via TruncatedSVD requires ~15 seconds for a 10k-document corpus with 100 topics
- **Similarity Matrix Computation**: Calculating pairwise cosine similarities for 1k documents generates a 1M-element matrix, taking ~5 seconds

For typical audit engagements processing the same corpus repeatedly (iterative analysis, multiple reports, team collaboration), this recomputation overhead is unacceptable. Users expect sub-second response times after initial processing.

**Performance Goals:**
- 10-100x speedup on repeated analysis (0.1s vs. 10s for TF-IDF fit)
- Support collaborative workflows where multiple analysts share models
- Enable incremental corpus updates without full recomputation
- Maintain deterministic results across sessions

## Decision

Implement a hash-based caching system using **joblib** for model persistence, with environment-aware storage paths and automatic invalidation.

### Storage Locations

Cache paths follow a three-tier strategy based on execution environment:

1. **Development** (default):
   - Path: `.data-extract-cache/models/`
   - Gitignored to prevent accidental commits
   - Per-project isolation
   - Automatic directory creation

2. **CI/CD** (GitHub Actions):
   - Path: `~/.cache/data-extract/models/`
   - Integrates with `actions/cache@v4` for persistence across runs
   - Speeds up test suite execution
   - Reduces API calls to download test corpora

3. **Production** (enterprise deployment):
   - Path: Configurable via `DATA_EXTRACT_CACHE_DIR` environment variable
   - Default: `${XDG_CACHE_HOME}/data-extract/models/` or `~/.cache/data-extract/models/`
   - Supports shared network drives for team collaboration
   - Respects enterprise storage policies

### Cache Key Pattern

Deterministic, content-based keys prevent cache corruption and ensure reproducibility:

```python
def generate_cache_key(
    model_type: str,
    version: str,
    corpus_hash: str,
    **kwargs
) -> str:
    """Generate deterministic cache key for model persistence.

    Args:
        model_type: Type of model ('tfidf', 'lsa', 'similarity')
        version: Model version string (e.g., 'v1', 'v2')
        corpus_hash: SHA-256 hash of corpus content
        **kwargs: Model-specific parameters (e.g., num_topics for LSA)

    Returns:
        Cache key like 'tfidf_v1_a3f5d2b1.joblib'
    """
    # Base key components
    key_parts = [model_type, version, corpus_hash[:8]]

    # Add model-specific parameters
    if model_type == 'lsa' and 'num_topics' in kwargs:
        key_parts.append(f"t{kwargs['num_topics']}")
    elif model_type == 'similarity' and 'metric' in kwargs:
        key_parts.append(kwargs['metric'])

    return f"{'_'.join(key_parts)}.joblib"
```

**Key Examples:**
- TF-IDF: `tfidf_v1_a3f5d2b1.joblib`
- LSA: `lsa_v1_a3f5d2b1_t100.joblib` (100 topics)
- Similarity: `similarity_v1_q7c2a_a3f5d2b1_cosine.joblib`

### Corpus Hash Generation

```python
def compute_corpus_hash(documents: List[str]) -> str:
    """Compute SHA-256 hash of corpus for cache invalidation.

    Ensures deterministic hashing by:
    1. Sorting documents by content (order-independent)
    2. Normalizing line endings (platform-independent)
    3. Using UTF-8 encoding (encoding-independent)
    """
    import hashlib

    # Sort for determinism
    sorted_docs = sorted(documents)

    # Normalize and concatenate
    normalized = '\n'.join(doc.replace('\r\n', '\n') for doc in sorted_docs)

    # Compute hash
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
```

### Size Management

Prevent unbounded cache growth with configurable limits:

- **Maximum cache size**: 500 MB (default, configurable via `DATA_EXTRACT_MAX_CACHE_MB`)
- **LRU eviction**: Remove least recently used models when limit exceeded
- **Warning threshold**: Log warning when cache exceeds 80% of limit (400 MB)
- **Model size estimates**:
  - TF-IDF vectorizer: ~10-50 MB for 10k-document corpus
  - LSA model: ~5-20 MB depending on topics
  - Similarity matrix: ~40 MB for 1k×1k dense matrix

### CLI Integration

```bash
# Clear entire cache
data-extract --clear-cache

# Clear specific model type
data-extract --clear-cache --model-type tfidf

# Show cache status
data-extract cache-status
# Output:
# Cache location: .data-extract-cache/models/
# Total size: 127.3 MB / 500 MB (25.5%)
# Models cached: 8
#   - TF-IDF: 3 models, 67.2 MB
#   - LSA: 2 models, 31.1 MB
#   - Similarity: 3 models, 29.0 MB
# Oldest: 2025-11-01 14:23:17 (tfidf_v1_c9a2f.joblib)
# Newest: 2025-11-18 09:15:43 (lsa_v1_a3f5d_t50.joblib)

# Force cache refresh for specific run
data-extract process --no-cache [...]
```

### Cache Warming Strategy

For common workflows, **cache warming** pre-computes models to eliminate cold-start latency:

#### Automatic Warming (Default Behavior)

Models are automatically cached on first use:

```bash
# First run: Fits models and caches them (~10-15 seconds)
data-extract process audit-docs/ --output analysis.json

# Subsequent runs: Loads from cache (<1 second)
data-extract process audit-docs/ --output analysis2.json
```

#### Manual Warming for Production Deployment

Pre-warm caches during deployment for instant user experience:

```bash
# Warm cache with representative corpus (CI/CD or onboarding script)
data-extract warm-cache --corpus path/to/training-docs/ \
  --models tfidf,lsa \
  --lsa-topics 50,100,200

# Verifies models cached:
# ✓ TF-IDF vectorizer cached (67.2 MB)
# ✓ LSA model (50 topics) cached (15.3 MB)
# ✓ LSA model (100 topics) cached (31.1 MB)
# ✓ LSA model (200 topics) cached (58.7 MB)
# Cache ready for production workloads
```

#### Team Collaboration Warming

Share pre-computed models via network cache:

```bash
# Team lead pre-warms shared cache on network drive
export DATA_EXTRACT_CACHE_DIR="/mnt/shared/audit-cache"
data-extract warm-cache --corpus /mnt/corpora/q4-2025/ \
  --models tfidf,lsa,similarity

# Team members inherit warm cache instantly
export DATA_EXTRACT_CACHE_DIR="/mnt/shared/audit-cache"
data-extract process my-docs/ --output report.json  # Uses pre-warmed models
```

#### Incremental Warming for CI/CD

Speed up test suites by warming test corpus models:

```yaml
# .github/workflows/test.yml
- name: Warm semantic cache
  run: |
    python -c "
    from tests.fixtures.semantic_corpus import load_test_corpus
    from src.data_extract.semantic.cache import warm_cache
    corpus = load_test_corpus()
    warm_cache(corpus, models=['tfidf', 'lsa'])
    "
```

#### Selective Warming by Use Case

Warm only models needed for specific workflows:

```bash
# Audit similarity analysis workflow (TF-IDF + similarity only)
data-extract warm-cache --corpus audit-q4/ --models tfidf,similarity

# Topic modeling workflow (LSA with multiple topic counts)
data-extract warm-cache --corpus compliance-docs/ \
  --models lsa --lsa-topics 25,50,100,150
```

**Warming Benefits:**
- Eliminates 10-15 second cold-start latency
- Enables instant onboarding for new team members
- Reduces CI/CD test suite runtime by 30-40%
- Supports offline/disconnected workflows (pre-warmed cache available)

## Consequences

### Positive Consequences

1. **Performance Improvement**: 10-100x speedup (0.1s vs. 10s) on repeated analysis
2. **Team Collaboration**: Shared cache enables multiple analysts to reuse models
3. **Deterministic Results**: Hash-based keys ensure same input → same model
4. **Storage Efficiency**: LRU eviction prevents unbounded growth
5. **Debugging Support**: Cache status command aids troubleshooting
6. **CI/CD Integration**: Speeds up test suites by caching test models

### Negative Consequences

1. **Disk Usage**: Up to 500 MB additional storage per environment
2. **Cache Invalidation Complexity**: Must carefully manage when corpus changes
3. **Network Latency**: Shared cache on network drives may add 50-100ms overhead
4. **Version Management**: Model version changes require cache key updates

### Risk Mitigation

- **Stale Cache**: Corpus hash ensures automatic invalidation on content change
- **Corruption**: joblib includes checksums, corrupted files are auto-regenerated
- **Concurrency**: File locking prevents simultaneous write conflicts
- **Privacy**: Cache inherits filesystem permissions, no additional exposure

## Alternatives Considered

### SQLite Database Cache
- **Pros**: ACID guarantees, complex queries, metadata storage
- **Cons**: Overkill for simple key-value storage, adds SQL dependency
- **Rejected**: Unnecessary complexity for model blob storage

### No Caching
- **Pros**: Simplest implementation, no disk usage, no invalidation issues
- **Cons**: Unacceptable 10-15 second latency per operation
- **Rejected**: Performance requirements mandate caching

### In-Memory Only Cache
- **Pros**: Fastest access (no disk I/O), no persistence concerns
- **Cons**: Cache lost on process exit, no sharing between sessions
- **Rejected**: Doesn't support collaborative workflows or CLI usage pattern

### Redis/Memcached
- **Pros**: Distributed caching, team sharing, TTL support
- **Cons**: Requires external service, operational complexity
- **Rejected**: Over-engineered for single-machine audit tool

## Implementation Notes

### Integration Points

1. **Epic 4 Semantic Processors**: Primary consumers of cache functionality
2. **Epic 5 Configuration System**: Will provide cascade for cache settings
3. **CLI Commands**: New flags and cache-status command
4. **CI/CD Pipeline**: GitHub Actions cache configuration

### Testing Strategy

```python
# Test cache key determinism
def test_cache_key_deterministic():
    key1 = generate_cache_key('tfidf', 'v1', 'abcd1234')
    key2 = generate_cache_key('tfidf', 'v1', 'abcd1234')
    assert key1 == key2

# Test LRU eviction
def test_lru_eviction(tmp_path, monkeypatch):
    monkeypatch.setenv('DATA_EXTRACT_MAX_CACHE_MB', '1')  # 1 MB limit
    # Add models until eviction triggers
    # Verify oldest model removed

# Test corpus hash stability
def test_corpus_hash_stable():
    docs = ["Document 1", "Document 2"]
    hash1 = compute_corpus_hash(docs)
    hash2 = compute_corpus_hash(docs[::-1])  # Reverse order
    assert hash1 == hash2  # Order-independent
```

### Monitoring & Observability

- Log cache hits/misses with structlog
- Track cache size after each operation
- Alert when approaching size limit
- Include cache metrics in performance reports

## References

- [Epic 3.5 Tech Spec - Cache ADR Requirements](../tech-spec-epic-3.5.md#L186-L222)
- [joblib Documentation - Persistence](https://joblib.readthedocs.io/en/latest/persistence.html)
- [scikit-learn Model Persistence Guide](https://scikit-learn.org/stable/model_persistence.html)
- [Epic 3 Retrospective - Performance Findings](../retrospectives/epic-3-retro-2025-11-16.md#L57)

---

_ADR-012 created for Epic 3.5 preparation sprint_
_Next: Epic 4 implementation will consume this caching infrastructure_
