# Semantic Validation Framework Usage Guide

## Overview

The Semantic Validation Framework provides robust validation for semantic analysis outputs, including TF-IDF vectors, LSA topics, similarity rankings, and quality metrics. This framework is essential for ensuring correctness of Epic 4 semantic features.

**Created**: 2025-11-18
**Epic**: 4 (Semantic Analysis) - Wave 2.3 Preparation Sprint
**Author**: Elena (Dev Agent - Semantic Analysis Specialist)

## Quick Start

### Basic Usage

```python
from tests.validation.semantic_validator import SemanticValidator
import numpy as np

# Create validator
validator = SemanticValidator()

# Validate TF-IDF vectors
actual_tfidf = np.array([[0.5, 0.3, 0.2]])
expected_tfidf = np.array([[0.49, 0.31, 0.20]])

result = validator.validate_tfidf_vectors(
    actual_tfidf,
    expected_tfidf,
    tolerance=0.02  # 2% tolerance
)

if result.passed:
    print(f"Validation passed! Similarity: {result.similarity_score:.2%}")
else:
    print(f"Validation failed. Issues:")
    for issue in result.mismatches:
        print(f"  - {issue}")
```

### Using Convenience Functions

```python
from tests.validation.semantic_validator import (
    validate_tfidf,
    validate_lsa,
    validate_rankings,
    check_regression
)

# Quick TF-IDF validation
result = validate_tfidf(actual, expected, tolerance=0.01)

# Quick LSA validation (handles sign-flipping)
result = validate_lsa(actual_topics, expected_topics, threshold=0.9)

# Quick ranking validation
result = validate_rankings(actual_ranks, expected_ranks, top_k=10)

# Quick regression check
report = check_regression(current_metrics, baseline_metrics)
if report.has_regression:
    print(f"Performance regression detected: {report.degraded_metrics}")
```

## Validation Methods

### 1. TF-IDF Vector Validation

Validates TF-IDF vectors using various comparison methods:

```python
# Cosine similarity (default, most robust)
result = validator.validate_tfidf_vectors(
    actual, expected,
    tolerance=0.01,  # 1% tolerance
    method="cosine"
)

# Euclidean distance
result = validator.validate_tfidf_vectors(
    actual, expected,
    tolerance=0.1,   # 0.1 distance units
    method="euclidean"
)

# Element-wise comparison (strictest)
result = validator.validate_tfidf_vectors(
    actual, expected,
    tolerance=0.001,  # 0.1% per element
    method="elementwise"
)
```

**Tolerance Guidelines:**
- **Cosine**: 0.01 (1%) for strict, 0.05 (5%) for loose
- **Euclidean**: Depends on vector magnitude, typically 0.05-0.2
- **Elementwise**: 0.001-0.01 per element

### 2. LSA Topic Validation

Handles the sign-flipping ambiguity inherent in LSA/SVD:

```python
# LSA topics can have sign ambiguity
actual_topics = np.array([[0.5, -0.3, 0.2]])    # Topic weights
expected_topics = np.array([[0.5, 0.3, 0.2]])   # Sign flipped on topic 2

result = validator.validate_lsa_topics(
    actual_topics,
    expected_topics,
    cosine_threshold=0.9  # 90% similarity required
)

# Result will pass despite sign flip
# Warnings will indicate which topics were sign-flipped
print(f"Sign flips detected: {result.details['sign_flips']}")
```

**Key Points:**
- Uses absolute cosine similarity to handle sign ambiguity
- Topics [0.5, 0.3] and [-0.5, -0.3] are considered equivalent
- Warnings indicate sign flips for debugging

### 3. Similarity Ranking Validation

Validates document similarity rankings with focus on order preservation:

```python
actual_rankings = [
    ("doc1", 0.95),
    ("doc2", 0.85),
    ("doc3", 0.75),
]

expected_rankings = [
    ("doc1", 0.93),  # Slightly different score
    ("doc3", 0.84),  # doc2 and doc3 swapped
    ("doc2", 0.74),
]

result = validator.validate_similarity_rankings(
    actual_rankings,
    expected_rankings,
    top_k=3,         # Only validate top 3
    tolerance=0.05   # 5% score difference allowed
)

print(f"Precision@{result.details['top_k']}: {result.details['precision']:.2%}")
print(f"Avg rank difference: {result.details['avg_rank_diff']:.1f}")
```

**Validation Focus:**
- **Top-K precision**: Are the same documents in the top K?
- **Ranking order**: How much did positions change?
- **Score differences**: Are scores within tolerance?

### 4. Quality Metrics Validation

Validates readability and quality metrics:

```python
actual_metrics = {
    "flesch_reading_ease": 45.3,
    "flesch_kincaid_grade": 12.5,
    "smog_index": 14.2,
}

expected_metrics = {
    "flesch_reading_ease": 46.0,
    "flesch_kincaid_grade": 12.3,
    "smog_index": 14.0,
}

result = validator.validate_quality_metrics(
    actual_metrics,
    expected_metrics,
    tolerance=0.1  # 10% relative difference
)

# Access detailed comparison
for metric, details in result.details["metric_details"].items():
    print(f"{metric}: actual={details['actual']:.1f}, "
          f"expected={details['expected']:.1f}, "
          f"similarity={details['similarity']:.2%}")
```

### 5. Regression Detection

Detects performance degradation vs baseline:

```python
baseline_results = {
    "accuracy": 0.95,
    "f1_score": 0.92,
    "processing_time_ms": 100,  # Lower is better
    "memory_usage_mb": 50,      # Lower is better
}

current_results = {
    "accuracy": 0.93,           # Degraded
    "f1_score": 0.94,           # Improved
    "processing_time_ms": 120,  # Degraded (worse)
    "memory_usage_mb": 45,      # Improved (better)
}

report = validator.detect_regression(
    current_results,
    baseline_results,
    tolerance=0.05  # 5% degradation threshold
)

if report.has_regression:
    print(f"Regressions: {report.degraded_metrics}")
    print(f"Improvements: {report.improved_metrics}")

    # Get detailed metrics
    for metric, details in report.details.items():
        if isinstance(details, dict) and 'change_pct' in details:
            print(f"{metric}: {details['change_pct']:.1f}% change")
```

**Smart Detection:**
- Recognizes "lower is better" metrics (time, memory, error_rate)
- Handles missing metrics (treated as regression)
- Skips non-numeric metrics

## Using with Gold Standards

### Setting Up Gold Standards

1. Create gold standard JSON files:

```json
// tests/fixtures/semantic/gold-standard/tfidf_expected.json
{
    "vocabulary_size": 1000,
    "num_documents": 50,
    "top_terms": ["risk", "control", "assessment", "audit"],
    "avg_tfidf_score": 0.25,
    "sparsity": 0.95
}

// tests/fixtures/semantic/gold-standard/lsa_expected.json
{
    "num_topics": 10,
    "explained_variance": 0.75,
    "topic_coherence": 0.65,
    "perplexity": 120.5
}
```

2. Initialize validator with gold standards:

```python
from pathlib import Path

validator = SemanticValidator(
    gold_standard_path=Path("tests/fixtures/semantic/gold-standard")
)

# Gold standards are now available
print(f"Loaded standards: {list(validator._gold_standards.keys())}")
```

### Using in Pytest Tests

```python
import pytest
from tests.validation.semantic_validator import SemanticValidator

class TestSemanticAnalysis:

    @pytest.fixture
    def validator(self):
        """Provide semantic validator."""
        return SemanticValidator()

    def test_tfidf_correctness(self, validator):
        """Test TF-IDF implementation correctness."""
        # Your TF-IDF implementation
        from src.data_extract.semantic.tfidf import TfIdfVectorizer

        vectorizer = TfIdfVectorizer()
        actual = vectorizer.fit_transform(corpus)

        # Load expected from gold standard
        expected = load_gold_standard_tfidf()

        # Validate
        result = validator.validate_tfidf_vectors(
            actual, expected, tolerance=0.01
        )

        assert result.passed, f"TF-IDF validation failed: {result.mismatches}"
        assert result.similarity_score > 0.99

    def test_no_regression(self, validator):
        """Test for performance regression."""
        baseline = load_baseline_metrics()
        current = run_semantic_pipeline()

        report = validator.detect_regression(
            current, baseline, tolerance=0.05
        )

        assert not report.has_regression, (
            f"Performance regression detected:\n"
            f"Degraded: {report.degraded_metrics}\n"
            f"Details: {report.details}"
        )
```

## Troubleshooting Validation Failures

### Common Issues and Solutions

#### 1. TF-IDF Validation Failures

**Issue**: "Vocabulary size mismatch"
```python
# This is a WARNING, not an error
# The validator will pad matrices and continue
result.warnings  # Contains vocabulary mismatch info
```

**Issue**: "Document count mismatch"
```python
# This is an ERROR - cannot compare different document sets
# Ensure both matrices have same number of documents (rows)
```

**Issue**: "Similarity below threshold"
```python
# Try these solutions:
# 1. Increase tolerance
result = validate_tfidf(actual, expected, tolerance=0.05)  # 5% instead of 1%

# 2. Use different comparison method
result = validate_tfidf(actual, expected, method="euclidean")

# 3. Check for normalization differences
actual_normalized = actual / np.linalg.norm(actual, axis=1, keepdims=True)
```

#### 2. LSA Validation Failures

**Issue**: "Sign flipped topics"
```python
# This is EXPECTED and handled automatically
# Check warnings for which topics flipped
for warning in result.warnings:
    if "Sign flipped" in warning:
        print(warning)  # e.g., "Topic 2: Sign flipped (similarity=-0.95)"
```

**Issue**: "Low topic similarity"
```python
# Solutions:
# 1. Lower threshold (LSA is less deterministic than TF-IDF)
result = validate_lsa(actual, expected, threshold=0.8)  # 80% instead of 90%

# 2. Check number of components matches
assert actual.shape[1] == expected.shape[1], "Different number of topics"
```

#### 3. Ranking Validation Failures

**Issue**: "Missing from top-K"
```python
# Document not in expected top results
# Solutions:
# 1. Increase K
result = validate_rankings(actual, expected, top_k=20)  # Top 20 instead of 10

# 2. Focus on precision rather than exact matches
if result.details["precision"] >= 0.8:  # 80% overlap
    # Consider it acceptable
    pass
```

#### 4. Regression Detection False Positives

**Issue**: "Small variations flagged as regression"
```python
# Solution: Increase tolerance for normal variation
report = check_regression(current, baseline, tolerance=0.1)  # 10% instead of 5%
```

**Issue**: "Metrics with different scales"
```python
# Solution: Normalize metrics before comparison
def normalize_metrics(metrics):
    return {k: v / baseline[k] if baseline[k] != 0 else v
            for k, v in metrics.items()}
```

## Best Practices

### 1. Choose Appropriate Tolerances

```python
# Strict validation for critical paths
STRICT_TOLERANCE = 0.01  # 1%

# Looser validation for non-deterministic algorithms
LSA_TOLERANCE = 0.1  # 10%

# Very loose for development/debugging
DEBUG_TOLERANCE = 0.25  # 25%
```

### 2. Handle Warnings vs Errors

```python
result = validator.validate_tfidf_vectors(actual, expected)

# Errors mean validation failed
if not result.passed:
    raise AssertionError(f"Validation failed: {result.mismatches}")

# Warnings are informational
if result.warnings:
    logger.warning(f"Validation warnings: {result.warnings}")
```

### 3. Create Reusable Validation Fixtures

```python
@pytest.fixture
def validation_context():
    """Reusable validation context."""
    return {
        "tfidf_tolerance": 0.02,
        "lsa_threshold": 0.85,
        "ranking_top_k": 10,
        "regression_tolerance": 0.05,
    }

def test_semantic_pipeline(validation_context):
    # Use consistent tolerances across tests
    result = validate_tfidf(
        actual, expected,
        tolerance=validation_context["tfidf_tolerance"]
    )
```

### 4. Document Expected Variations

```python
# Document why certain tolerances are used
result = validator.validate_lsa_topics(
    actual, expected,
    cosine_threshold=0.85  # LSA has 10-15% variation due to randomized SVD
)
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Run Semantic Validation
  run: |
    python -m pytest tests/unit/test_validation/test_semantic_validator.py -v
    python scripts/validate_semantic_baseline.py
```

### Validation Script Example

```python
#!/usr/bin/env python
"""Validate semantic analysis against baseline."""

from tests.validation.semantic_validator import SemanticValidator
import json
import sys

def main():
    validator = SemanticValidator()

    # Load baseline
    with open("baseline_metrics.json") as f:
        baseline = json.load(f)

    # Run current implementation
    current = run_semantic_analysis()

    # Check for regression
    report = validator.detect_regression(
        current, baseline, tolerance=0.05
    )

    if report.has_regression:
        print(f"❌ Regression detected: {report.degraded_metrics}")
        sys.exit(1)
    else:
        print(f"✅ No regression. Improvements: {report.improved_metrics}")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

## Summary

The Semantic Validation Framework provides:

- **Robust validation** for TF-IDF, LSA, rankings, and metrics
- **Smart handling** of LSA sign-flipping ambiguity
- **Flexible tolerances** for different validation scenarios
- **Regression detection** with metric-aware comparisons
- **Integration support** for pytest and CI/CD pipelines

Use this framework to ensure semantic analysis correctness throughout Epic 4 implementation.
