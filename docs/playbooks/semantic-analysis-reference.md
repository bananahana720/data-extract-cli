# Semantic Analysis Quick Reference Guide

**Epic 3.5, Story 3.5-7**
**Purpose**: Quick API reference and troubleshooting guide for TF-IDF/LSA implementation
**Companion to**: `semantic-analysis-intro.ipynb`

---

## Table of Contents

1. [Quick API Reference](#quick-api-reference)
2. [Common Pitfalls](#common-pitfalls)
3. [Troubleshooting Guide](#troubleshooting-guide)
4. [Performance Optimization](#performance-optimization)
5. [Code Snippets](#code-snippets)
6. [Links to Documentation](#links-to-documentation)

---

## Quick API Reference

### TfidfVectorizer (scikit-learn)

```python
from sklearn.feature_extraction.text import TfidfVectorizer

# Initialize vectorizer
vectorizer = TfidfVectorizer(
    max_features=1000,        # Max vocabulary size
    min_df=2,                 # Min document frequency
    max_df=0.95,              # Max document frequency (0-1)
    ngram_range=(1, 2),       # Unigrams and bigrams
    stop_words='english',     # Remove stopwords
    use_idf=True,            # Use IDF weighting
    smooth_idf=True,         # Add 1 to doc frequencies
    sublinear_tf=True,       # Log normalization
    norm='l2'                # L2 normalize vectors
)

# Fit and transform
tfidf_matrix = vectorizer.fit_transform(corpus)  # Returns sparse CSR matrix
# Or separately:
vectorizer.fit(corpus)                           # Learn vocabulary
tfidf_matrix = vectorizer.transform(new_docs)    # Apply to new documents

# Access components
vocabulary = vectorizer.vocabulary_               # Dict: term -> index
feature_names = vectorizer.get_feature_names_out() # Array of terms
idf_scores = vectorizer.idf_                     # IDF weights array
```

### TruncatedSVD (LSA)

```python
from sklearn.decomposition import TruncatedSVD

# Initialize LSA model
lsa = TruncatedSVD(
    n_components=10,          # Number of topics
    algorithm='randomized',   # 'randomized' or 'arpack'
    n_iter=10,               # Iterations for randomized
    random_state=42          # Reproducibility
)

# Fit and transform
doc_topics = lsa.fit_transform(tfidf_matrix)  # Returns dense array
# Or separately:
lsa.fit(tfidf_matrix)                        # Learn topics
doc_topics = lsa.transform(tfidf_matrix)      # Project documents

# Access components
components = lsa.components_                  # Topic-term matrix
explained_var = lsa.explained_variance_ratio_ # Variance per topic
singular_values = lsa.singular_values_        # Singular values
```

### Cosine Similarity

```python
from sklearn.metrics.pairwise import cosine_similarity

# Compute pairwise similarity
similarity_matrix = cosine_similarity(X, Y=None)  # If Y=None, computes X vs X

# Find similar documents to query
query_vector = vectorizer.transform([query_text])
similarities = cosine_similarity(query_vector, tfidf_matrix)[0]
top_k = similarities.argsort()[-k:][::-1]  # Indices of top k similar
```

### Joblib Persistence

```python
import joblib

# Save model
joblib.dump(model, 'model.joblib', compress=3)  # compress: 0-9

# Load model
model_loaded = joblib.load('model.joblib')

# With caching pattern
import hashlib

def get_or_create_model(corpus, cache_dir):
    # Generate cache key
    corpus_hash = hashlib.sha256(''.join(corpus).encode()).hexdigest()[:8]
    cache_path = f"{cache_dir}/tfidf_{corpus_hash}.joblib"

    if os.path.exists(cache_path):
        return joblib.load(cache_path)
    else:
        model = TfidfVectorizer().fit(corpus)
        joblib.dump(model, cache_path)
        return model
```

### Textstat Metrics

```python
import textstat

# Readability scores
flesch_score = textstat.flesch_reading_ease(text)      # 0-100 (higher=easier)
grade_level = textstat.flesch_kincaid_grade(text)      # US grade level
fog_index = textstat.gunning_fog(text)                 # Years of education
reading_time = textstat.reading_time(text, ms_per_char=14.69)  # Seconds

# Text statistics
lexicon_count = textstat.lexicon_count(text)           # Word count
syllable_count = textstat.syllable_count(text)         # Total syllables
sentence_count = textstat.sentence_count(text)         # Number of sentences
```

---

## Common Pitfalls

### 1. Vocabulary Drift

**Problem**: New documents contain words not in training vocabulary
**Symptoms**: Zero vectors for new documents, poor similarity scores
**Solution**:
```python
# Option 1: Retrain periodically
if new_doc_has_many_oov_words:
    vectorizer = vectorizer.fit(corpus + new_docs)

# Option 2: Use larger initial vocabulary
vectorizer = TfidfVectorizer(max_features=5000)  # Increase limit

# Option 3: Monitor OOV rate
def get_oov_rate(doc, vectorizer):
    words = doc.split()
    oov = [w for w in words if w.lower() not in vectorizer.vocabulary_]
    return len(oov) / len(words)
```

### 2. Cache Invalidation

**Problem**: Model cache becomes stale when corpus changes
**Symptoms**: Inconsistent results, outdated topics
**Solution**:
```python
# Include corpus hash in cache key
def generate_cache_key(corpus, model_params):
    corpus_hash = hashlib.sha256(''.join(corpus).encode()).hexdigest()[:8]
    params_hash = hashlib.md5(str(model_params).encode()).hexdigest()[:8]
    return f"model_{corpus_hash}_{params_hash}.joblib"

# Implement TTL (time-to-live)
import time
cache_ttl_hours = 24
if time.time() - os.path.getmtime(cache_file) > cache_ttl_hours * 3600:
    os.remove(cache_file)  # Force regeneration
```

### 3. Memory Issues with Dense Matrices

**Problem**: Converting sparse to dense causes memory errors
**Symptoms**: MemoryError, system freeze
**Solution**:
```python
# DON'T DO THIS:
dense_matrix = sparse_matrix.todense()  # Can explode memory!

# DO THIS INSTEAD:
# Work with sparse matrices directly
similarities = cosine_similarity(sparse_matrix)  # Works with sparse

# If you need specific rows/cols:
row_dense = sparse_matrix[0].toarray()  # Convert single row only

# For visualization, sample:
sample_indices = np.random.choice(n_docs, size=100, replace=False)
sample_matrix = sparse_matrix[sample_indices]
```

### 4. Poor Topic Quality

**Problem**: LSA topics are not interpretable
**Symptoms**: Topics mix unrelated concepts
**Solution**:
```python
# Tune n_components using explained variance
def find_optimal_components(tfidf_matrix, min_variance=0.8):
    for n in range(2, min(50, tfidf_matrix.shape[0])):
        lsa = TruncatedSVD(n_components=n, random_state=42)
        lsa.fit(tfidf_matrix)
        if sum(lsa.explained_variance_ratio_) >= min_variance:
            return n
    return n

# Better preprocessing
vectorizer = TfidfVectorizer(
    min_df=3,         # Remove very rare terms
    max_df=0.8,       # Remove very common terms
    max_features=2000 # Adequate vocabulary
)
```

### 5. Slow Performance

**Problem**: Processing takes too long
**Symptoms**: Timeouts, long waits
**Solution**:
```python
# Batch processing
def process_in_batches(corpus, vectorizer, batch_size=1000):
    for i in range(0, len(corpus), batch_size):
        batch = corpus[i:i+batch_size]
        yield vectorizer.transform(batch)

# Use sparse operations
# Slower:
for i in range(matrix.shape[0]):
    row = matrix[i].toarray()  # Converts each row

# Faster:
for i in range(matrix.shape[0]):
    row = matrix.getrow(i)  # Keeps sparse

# Enable parallel processing (when available)
lsa = TruncatedSVD(n_components=10, algorithm='randomized', n_jobs=-1)
```

---

## Troubleshooting Guide

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'sklearn'`
```bash
# Solution: Install scikit-learn
pip install scikit-learn>=1.3.0

# If using conda:
conda install scikit-learn
```

**Error**: `ImportError: cannot import name 'TruncatedSVD'`
```python
# Check scikit-learn version
import sklearn
print(sklearn.__version__)  # Should be >= 0.14

# Correct import path
from sklearn.decomposition import TruncatedSVD  # Not sklearn.lsa
```

### Dimension Mismatches

**Error**: `ValueError: Incompatible dimension for X and Y matrices`
```python
# Check shapes
print(f"X shape: {X.shape}, Y shape: {Y.shape}")

# Common fixes:
# 1. Ensure same number of features
X_transformed = vectorizer.transform(X_docs)  # Use same vectorizer!
Y_transformed = vectorizer.transform(Y_docs)

# 2. For LSA, ensure same number of components
X_topics = lsa.transform(X_tfidf)  # Use same LSA model
Y_topics = lsa.transform(Y_tfidf)
```

**Error**: `ValueError: Found input variables with inconsistent numbers of samples`
```python
# Check document count
print(f"Corpus size: {len(corpus)}")
print(f"Matrix shape: {tfidf_matrix.shape}")

# Fix: Ensure corpus is list of strings
corpus = [str(doc) for doc in corpus]  # Convert all to strings
corpus = [doc for doc in corpus if doc]  # Remove empty strings
```

### Performance Issues

**Slow TF-IDF Fitting**:
```python
# Profile the bottleneck
import time

start = time.time()
vectorizer.fit(corpus)
print(f"Fit time: {time.time() - start:.2f}s")

# Solutions:
# 1. Reduce vocabulary size
vectorizer = TfidfVectorizer(max_features=500)  # Smaller vocab

# 2. Increase min_df
vectorizer = TfidfVectorizer(min_df=5)  # Skip rare terms

# 3. Use binary term presence instead of frequency
vectorizer = TfidfVectorizer(binary=True)
```

**High Memory Usage**:
```python
# Monitor memory usage
import psutil
process = psutil.Process()
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")

# Solutions:
# 1. Use dtype=np.float32 instead of float64
vectorizer = TfidfVectorizer(dtype=np.float32)

# 2. Clear intermediate variables
del temp_matrix
import gc
gc.collect()
```

---

## Performance Optimization

### Baseline Performance Targets

From Epic 3.5 requirements:
- TF-IDF fit/transform: < 100ms for 1k words
- LSA fit/transform: < 200ms for 1k words
- Textstat scoring: < 10ms per document
- Model save/load: < 50ms for 10MB model

### Optimization Techniques

```python
# 1. Pre-compile regex patterns
import re
token_pattern = re.compile(r'\b[a-z]{2,}\b')
vectorizer = TfidfVectorizer(token_pattern=token_pattern)

# 2. Use generators for large corpora
def doc_generator(file_paths):
    for path in file_paths:
        with open(path, 'r') as f:
            yield f.read()

# 3. Optimize LSA parameters
lsa = TruncatedSVD(
    n_components=10,        # Fewer components = faster
    algorithm='randomized', # Faster than 'arpack'
    n_iter=5               # Fewer iterations (trade accuracy for speed)
)

# 4. Cache preprocessing
from functools import lru_cache

@lru_cache(maxsize=1000)
def preprocess(text):
    return text.lower().strip()

# 5. Use sparse matrix slicing
# Instead of converting to dense:
subset = sparse_matrix[indices]  # Still sparse
# Not:
subset = sparse_matrix.toarray()[indices]  # Dense!
```

---

## Code Snippets

### Complete Pipeline Example

```python
def semantic_analysis_pipeline(corpus, n_topics=5):
    """Complete semantic analysis pipeline."""

    # Step 1: TF-IDF Vectorization
    vectorizer = TfidfVectorizer(
        max_features=1000,
        min_df=2,
        max_df=0.95,
        ngram_range=(1, 2),
        stop_words='english'
    )
    tfidf_matrix = vectorizer.fit_transform(corpus)

    # Step 2: LSA Topic Modeling
    lsa = TruncatedSVD(n_components=n_topics, random_state=42)
    doc_topics = lsa.fit_transform(tfidf_matrix)

    # Step 3: Document Similarity
    similarities = cosine_similarity(doc_topics)

    # Step 4: Cache Models
    joblib.dump(vectorizer, 'tfidf_model.joblib')
    joblib.dump(lsa, 'lsa_model.joblib')

    return {
        'tfidf_matrix': tfidf_matrix,
        'topics': doc_topics,
        'similarities': similarities,
        'vocabulary_size': len(vectorizer.vocabulary_),
        'explained_variance': sum(lsa.explained_variance_ratio_)
    }
```

### Query Document Similarity

```python
def find_similar_documents(query, vectorizer, lsa, doc_topics, corpus, k=5):
    """Find k most similar documents to query."""

    # Transform query
    query_tfidf = vectorizer.transform([query])
    query_topics = lsa.transform(query_tfidf)

    # Calculate similarities
    similarities = cosine_similarity(query_topics, doc_topics)[0]

    # Get top k
    top_indices = similarities.argsort()[-k:][::-1]

    results = []
    for idx in top_indices:
        results.append({
            'document': corpus[idx][:100] + '...',
            'similarity': similarities[idx],
            'index': idx
        })

    return results
```

### Topic Interpretation

```python
def interpret_topics(lsa, vectorizer, n_terms=10):
    """Extract top terms for each topic."""

    feature_names = vectorizer.get_feature_names_out()
    topics = {}

    for topic_idx, topic in enumerate(lsa.components_):
        top_indices = topic.argsort()[-n_terms:][::-1]
        top_terms = [feature_names[i] for i in top_indices]
        top_weights = [topic[i] for i in top_indices]

        topics[f'Topic_{topic_idx}'] = {
            'terms': top_terms,
            'weights': top_weights,
            'top_5': ', '.join(top_terms[:5])
        }

    return topics
```

---

## Links to Documentation

### Official Documentation

- **Scikit-learn TF-IDF**: https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html
- **Scikit-learn TruncatedSVD**: https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.TruncatedSVD.html
- **Cosine Similarity**: https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.cosine_similarity.html
- **Joblib Persistence**: https://joblib.readthedocs.io/en/latest/persistence.html
- **Textstat Documentation**: https://pypi.org/project/textstat/

### Scikit-learn Guides

- **Text Feature Extraction Guide**: https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction
- **Decomposition Guide (LSA)**: https://scikit-learn.org/stable/modules/decomposition.html#truncated-singular-value-decomposition-and-latent-semantic-analysis
- **Working with Text Data Tutorial**: https://scikit-learn.org/stable/tutorial/text_analytics/working_with_text_data.html

### Project Resources

- **Semantic Test Corpus**: `/tests/fixtures/semantic_corpus.py`
- **Smoke Test Script**: `/scripts/smoke_test_semantic.py`
- **Model Cache ADR**: `/docs/architecture/adr-012-semantic-model-cache.md`
- **Epic 3.5 Tech Spec**: `/docs/tech-spec-epic-3.5.md`
- **Jupyter Notebook**: `/docs/playbooks/semantic-analysis-intro.ipynb`

### Additional Learning Resources

- **TF-IDF Explained**: https://en.wikipedia.org/wiki/Tf%E2%80%93idf
- **LSA Tutorial**: https://technowiki.wordpress.com/2011/08/27/latent-semantic-analysis-lsa-tutorial/
- **Sparse Matrices in SciPy**: https://docs.scipy.org/doc/scipy/reference/sparse.html
- **Python Memory Profiling**: https://pypi.org/project/memory-profiler/

---

## Quick Checklist for Epic 4 Implementation

- [ ] Dependencies installed (scikit-learn ≥1.3.0, joblib ≥1.3.0, textstat ≥0.7.3)
- [ ] Smoke test passes with performance targets met
- [ ] Semantic corpus loaded from fixtures
- [ ] TF-IDF vectorizer configured with appropriate parameters
- [ ] LSA model tuned for optimal n_components
- [ ] Cosine similarity computation working
- [ ] Joblib caching implemented with hash-based keys
- [ ] Memory usage monitored (sparse matrices maintained)
- [ ] Error handling for edge cases (empty docs, OOV words)
- [ ] Performance baselines documented

---

**Last Updated**: 2025-11-18
**Story**: 3.5-7-tfidf-lsa-playbook
**Status**: Implementation Guide Ready
