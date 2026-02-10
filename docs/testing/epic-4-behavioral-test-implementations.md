# Epic 4: Behavioral Test Implementation Specifications

Date: 2025-11-20
Author: Murat (Master Test Architect)
Epic ID: 4
Status: Implementation Ready

---

## Executive Summary

This document provides concrete implementation specifications for the 5 critical behavioral tests identified in the Epic 4 Behavioral Test Strategy. Each test includes complete code templates, expected inputs/outputs, and validation criteria.

## Test 1: Duplicate Detection Accuracy

### Purpose
Validate that the semantic analysis correctly identifies near-duplicate audit documents with high precision and recall.

### Implementation

```python
# tests/behavioral/test_semantic/test_duplicate_detection.py

import pytest
import numpy as np
from typing import List, Tuple
from src.data_extract.semantic.similarity import SimilarityAnalyzer
from src.data_extract.chunk.models import Chunk
from tests.fixtures.golden_dataset import load_duplicate_pairs

pytestmark = [pytest.mark.behavioral, pytest.mark.semantic, pytest.mark.epic4]

class TestDuplicateDetection:
    """Behavioral test for duplicate detection accuracy."""

    def test_bt001_duplicate_detection_accuracy(
        self,
        golden_duplicate_pairs: List[Tuple[str, str, float]],
        semantic_processor
    ):
        """
        Test BT-001: Duplicate detection achieves target precision/recall.

        Given: 45 verified duplicate document pairs
        When: Processing through similarity analysis
        Then: Precision ≥ 0.85 AND Recall ≥ 0.80

        Behavioral Outcome: System correctly identifies actual duplicates
        without excessive false positives.
        """
        # Arrange
        documents, duplicate_truth = self._prepare_test_data(golden_duplicate_pairs)
        analyzer = SimilarityAnalyzer(threshold=0.7)

        # Act
        detected_duplicates = analyzer.find_duplicates(documents)

        # Assert behavioral outcomes
        precision = self._calculate_precision(detected_duplicates, duplicate_truth)
        recall = self._calculate_recall(detected_duplicates, duplicate_truth)

        assert precision >= 0.85, f"Precision {precision:.2f} below threshold 0.85"
        assert recall >= 0.80, f"Recall {recall:.2f} below threshold 0.80"

        # Log behavioral metrics for diagnostics
        self._log_behavioral_metrics({
            'precision': precision,
            'recall': recall,
            'true_positives': len(detected_duplicates & duplicate_truth),
            'false_positives': len(detected_duplicates - duplicate_truth),
            'false_negatives': len(duplicate_truth - detected_duplicates)
        })
```

### Expected Inputs
- **Golden Dataset**: 45 verified duplicate pairs from audit documents
- **Similarity Threshold**: 0.7 (cosine similarity)
- **Document Types**: Risk assessments, control descriptions, policy documents

### Success Criteria
- Precision ≥ 85% (few false positives)
- Recall ≥ 80% (finds most true duplicates)
- F1-Score ≥ 0.825

---

## Test 2: Cluster Coherence Validation

### Purpose
Validate that LSA-based clustering produces coherent topic groups where related audit documents cluster together.

### Implementation

```python
# tests/behavioral/test_semantic/test_cluster_coherence.py

import pytest
from sklearn.metrics import silhouette_score
from src.data_extract.semantic.lsa import LSAProcessor
from src.data_extract.semantic.clustering import DocumentClusterer

pytestmark = [pytest.mark.behavioral, pytest.mark.semantic, pytest.mark.epic4]

class TestClusterCoherence:
    """Behavioral test for document cluster quality."""

    def test_bt002_cluster_coherence_validation(
        self,
        labeled_document_clusters,
        semantic_corpus_documents
    ):
        """
        Test BT-002: Document clustering achieves coherent topic groups.

        Given: Documents with known topic labels
        When: Clustering via LSA + K-means
        Then: Silhouette score ≥ 0.65

        Behavioral Outcome: Related audit documents (same risk domain,
        control family) cluster together naturally.
        """
        # Arrange
        documents = semantic_corpus_documents
        expected_clusters = labeled_document_clusters

        lsa_processor = LSAProcessor(n_components=100)
        clusterer = DocumentClusterer(n_clusters=len(expected_clusters))

        # Act
        lsa_vectors = lsa_processor.fit_transform(documents)
        predicted_clusters = clusterer.fit_predict(lsa_vectors)

        # Assert behavioral outcome
        coherence_score = silhouette_score(lsa_vectors, predicted_clusters)
        assert coherence_score >= 0.65, \
            f"Cluster coherence {coherence_score:.2f} below threshold 0.65"

        # Validate specific domain clustering
        self._validate_domain_clustering(predicted_clusters, expected_clusters)

        # Log cluster statistics
        self._log_cluster_metrics({
            'silhouette_score': coherence_score,
            'n_clusters': len(set(predicted_clusters)),
            'cluster_sizes': np.bincount(predicted_clusters),
            'inter_cluster_distance': self._calculate_inter_cluster_distance(lsa_vectors, predicted_clusters)
        })
```

### Expected Inputs
- **Labeled Clusters**: 10 topic groups (IT Security, Financial Controls, Compliance, etc.)
- **Corpus Size**: 200+ documents
- **LSA Components**: 100 dimensions

### Success Criteria
- Silhouette Score ≥ 0.65
- Each cluster contains >80% documents from same domain
- No singleton clusters

---

## Test 3: RAG Retrieval Improvement

### Purpose
Validate that TF-IDF preprocessing improves RAG retrieval precision compared to baseline keyword matching.

### Implementation

```python
# tests/behavioral/test_semantic/test_rag_improvement.py

import pytest
from typing import List, Tuple
from src.data_extract.semantic.tfidf import TfIdfVectorizer
from src.data_extract.semantic.retrieval import SemanticRetriever

pytestmark = [pytest.mark.behavioral, pytest.mark.semantic, pytest.mark.epic4]

class TestRAGImprovement:
    """Behavioral test for RAG retrieval precision improvement."""

    def test_bt003_rag_retrieval_improvement(
        self,
        rag_test_queries: List[str],
        document_corpus: List[str],
        relevance_judgments: List[Tuple[str, str, float]]
    ):
        """
        Test BT-003: TF-IDF improves RAG retrieval precision.

        Given: Query-document relevance judgments
        When: Comparing baseline vs TF-IDF retrieval
        Then: Precision improvement ≥ 25%

        Behavioral Outcome: Semantic preprocessing returns more
        relevant chunks for audit queries.
        """
        # Arrange
        baseline_retriever = self._create_baseline_retriever(document_corpus)
        tfidf_retriever = SemanticRetriever(TfIdfVectorizer())
        tfidf_retriever.index(document_corpus)

        # Act
        baseline_precision = self._evaluate_retrieval(
            baseline_retriever,
            rag_test_queries,
            relevance_judgments
        )

        tfidf_precision = self._evaluate_retrieval(
            tfidf_retriever,
            rag_test_queries,
            relevance_judgments
        )

        # Assert behavioral improvement
        improvement = (tfidf_precision - baseline_precision) / baseline_precision
        assert improvement >= 0.25, \
            f"Precision improvement {improvement:.1%} below threshold 25%"

        # Log retrieval metrics
        self._log_retrieval_metrics({
            'baseline_precision': baseline_precision,
            'tfidf_precision': tfidf_precision,
            'improvement_percentage': improvement * 100,
            'queries_tested': len(rag_test_queries)
        })

    def _evaluate_retrieval(self, retriever, queries, judgments, k=5):
        """Calculate precision@k for retrieval results."""
        precisions = []
        for query in queries:
            results = retriever.retrieve(query, k=k)
            relevant = self._get_relevant_docs(query, judgments)
            precision = len(set(results) & set(relevant)) / k
            precisions.append(precision)
        return np.mean(precisions)
```

### Expected Inputs
- **Test Queries**: 50 audit-specific queries ("SOX compliance controls", "data breach risks")
- **Document Corpus**: 1000+ audit documents
- **Relevance Judgments**: Human-verified query-document pairs

### Success Criteria
- Precision@5 improvement ≥ 25%
- Recall@10 improvement ≥ 20%
- Mean Reciprocal Rank (MRR) improvement ≥ 15%

---

## Test 4: Performance at Scale

### Purpose
Validate that the semantic pipeline can process enterprise-scale document volumes within acceptable resource constraints.

### Implementation

```python
# tests/behavioral/test_semantic/test_scale_performance.py

import pytest
import time
import psutil
from src.data_extract.semantic.pipeline import SemanticPipeline

pytestmark = [pytest.mark.behavioral, pytest.mark.semantic, pytest.mark.performance]

class TestScalePerformance:
    """Behavioral test for performance at scale."""

    def test_bt004_scale_performance_10k_documents(
        self,
        large_corpus_generator
    ):
        """
        Test BT-004: Process 10K documents within resource constraints.

        Given: 10,000 document corpus
        When: Processing through complete semantic pipeline
        Then: <60 seconds AND <500MB memory

        Behavioral Outcome: System remains responsive and stable
        at enterprise scale.
        """
        # Arrange
        documents = large_corpus_generator(count=10000)
        pipeline = SemanticPipeline()
        process = psutil.Process()

        # Measure baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Act
        start_time = time.time()
        result = pipeline.process_batch(documents)
        elapsed_time = time.time() - start_time

        # Measure peak memory
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = peak_memory - baseline_memory

        # Assert behavioral constraints
        assert elapsed_time < 60, \
            f"Processing time {elapsed_time:.1f}s exceeds 60s limit"
        assert memory_used < 500, \
            f"Memory usage {memory_used:.0f}MB exceeds 500MB limit"
        assert result.success, "Pipeline failed to process documents"

        # Validate output completeness
        assert len(result.vectors) == 10000, "Not all documents processed"
        assert result.similarity_matrix.shape == (10000, 10000), \
            "Incomplete similarity matrix"

        # Log performance metrics
        self._log_performance_metrics({
            'documents_processed': 10000,
            'elapsed_seconds': elapsed_time,
            'memory_mb': memory_used,
            'throughput_docs_per_sec': 10000 / elapsed_time,
            'memory_per_doc_kb': (memory_used * 1024) / 10000
        })
```

### Expected Inputs
- **Corpus Size**: 10,000 documents
- **Document Size**: Average 2KB each
- **Total Data**: ~20MB raw text

### Success Criteria
- Processing time < 60 seconds
- Memory usage < 500MB
- 100% documents processed
- No memory leaks (stable after GC)

---

## Test 5: Determinism Validation

### Purpose
Validate that semantic processing produces identical outputs for identical inputs, ensuring reproducibility.

### Implementation

```python
# tests/behavioral/test_semantic/test_determinism.py

import pytest
import hashlib
import json
from src.data_extract.semantic.pipeline import SemanticPipeline

pytestmark = [pytest.mark.behavioral, pytest.mark.semantic, pytest.mark.determinism]

class TestDeterminism:
    """Behavioral test for output determinism."""

    def test_bt005_deterministic_output_validation(
        self,
        determinism_test_corpus
    ):
        """
        Test BT-005: Identical inputs produce identical outputs.

        Given: Same document corpus
        When: Processing 3 times independently
        Then: All outputs byte-for-byte identical

        Behavioral Outcome: Results are reproducible for audit trails
        and debugging.
        """
        # Arrange
        documents = determinism_test_corpus
        pipeline = SemanticPipeline(seed=42)  # Fixed seed

        # Act - Process same input 3 times
        results = []
        output_hashes = []

        for run in range(3):
            # Reset pipeline state
            pipeline = SemanticPipeline(seed=42)

            # Process documents
            result = pipeline.process_batch(documents)
            results.append(result)

            # Calculate hash of serialized output
            output_json = json.dumps(result.to_dict(), sort_keys=True)
            output_hash = hashlib.sha256(output_json.encode()).hexdigest()
            output_hashes.append(output_hash)

        # Assert complete determinism
        assert len(set(output_hashes)) == 1, \
            f"Non-deterministic output: {len(set(output_hashes))} unique hashes"

        # Validate specific components
        self._validate_vector_determinism(results)
        self._validate_cluster_determinism(results)
        self._validate_similarity_determinism(results)

        # Log determinism verification
        self._log_determinism_metrics({
            'runs': 3,
            'unique_hashes': len(set(output_hashes)),
            'output_hash': output_hashes[0],
            'corpus_size': len(documents)
        })

    def _validate_vector_determinism(self, results):
        """Ensure TF-IDF vectors are identical across runs."""
        for i in range(1, len(results)):
            np.testing.assert_array_equal(
                results[0].vectors.toarray(),
                results[i].vectors.toarray(),
                err_msg=f"Vectors differ between run 0 and run {i}"
            )
```

### Expected Inputs
- **Test Corpus**: 100 documents with varied content
- **Random Seeds**: Fixed at 42
- **Number of Runs**: 3 independent executions

### Success Criteria
- 100% identical outputs (SHA-256 hash match)
- Identical TF-IDF vectors
- Identical cluster assignments
- Identical similarity scores

---

## Test Fixture Requirements

### Golden Dataset Structure

```yaml
# tests/fixtures/golden_dataset.yaml
golden_dataset:
  duplicate_pairs:
    - doc1: "risk_assessment_q1_2024.txt"
      doc2: "risk_assessment_q1_2024_v2.txt"
      similarity: 0.95
      verified_by: ["reviewer1", "reviewer2"]

  labeled_clusters:
    it_security:
      - "access_control_policy.txt"
      - "password_standards.txt"
      - "encryption_guidelines.txt"

    financial_controls:
      - "sox_compliance_checklist.txt"
      - "internal_audit_procedures.txt"
      - "financial_reporting_controls.txt"

  rag_relevance:
    - query: "SOX compliance requirements"
      relevant_docs:
        - doc: "sox_compliance_checklist.txt"
          relevance: 1.0
        - doc: "internal_audit_procedures.txt"
          relevance: 0.8
```

### Semantic Corpus Requirements

```python
# tests/fixtures/semantic_corpus.py

def get_behavioral_test_corpus():
    """
    Returns 264K word corpus optimized for behavioral testing.

    Characteristics:
    - 200+ documents
    - Mix of audit domains (IT, Financial, Compliance)
    - Known duplicate pairs
    - Verified PII-free
    - Consistent formatting
    """
    return load_corpus_from_json("fixtures/semantic_corpus_264k.json")
```

---

## CI Integration Configuration

```yaml
# .github/workflows/behavioral-tests.yml
name: Behavioral Test Suite

on:
  pull_request:
    paths:
      - 'src/data_extract/semantic/**'
      - 'tests/behavioral/**'

jobs:
  behavioral-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          python -m spacy download en_core_web_md

      - name: Run behavioral tests
        run: |
          pytest tests/behavioral/test_semantic/ \
            -m "behavioral and semantic" \
            --behavioral-report=behavioral-results.json \
            -v

      - name: Validate behavioral metrics
        run: |
          python scripts/validate_behavioral_metrics.py \
            --results behavioral-results.json \
            --thresholds tests/behavioral/thresholds.yaml

      - name: Upload behavioral report
        uses: actions/upload-artifact@v3
        with:
          name: behavioral-test-results
          path: behavioral-results.json
```

---

## Diagnostic Output Format

```json
{
  "test_run": {
    "timestamp": "2025-11-20T10:30:00Z",
    "epic": 4,
    "tests_executed": 5,
    "tests_passed": 4,
    "tests_failed": 1
  },
  "behavioral_metrics": {
    "duplicate_detection": {
      "precision": 0.87,
      "recall": 0.82,
      "f1_score": 0.845,
      "status": "PASS"
    },
    "cluster_coherence": {
      "silhouette_score": 0.68,
      "domain_accuracy": 0.85,
      "status": "PASS"
    },
    "rag_improvement": {
      "baseline_precision": 0.45,
      "tfidf_precision": 0.62,
      "improvement_percent": 37.8,
      "status": "PASS"
    },
    "scale_performance": {
      "elapsed_seconds": 72.3,
      "memory_mb": 487,
      "status": "FAIL",
      "failure_reason": "Exceeded 60 second time limit"
    },
    "determinism": {
      "identical_outputs": true,
      "hash": "a3f5c8d2...",
      "status": "PASS"
    }
  }
}
```

---

## Implementation Priority

1. **Week 1 - Test Reality Sprint**:
   - Day 1-2: Implement Test 1 (Duplicate Detection)
   - Day 3-4: Implement Test 2 (Cluster Coherence)
   - Day 5: Implement Test 3 (RAG Improvement)

2. **Week 2 - Scale & Reliability**:
   - Day 1-2: Implement Test 4 (Scale Performance)
   - Day 3: Implement Test 5 (Determinism)
   - Day 4-5: CI integration and validation

---

**Status**: These behavioral test implementations are ready for execution by the Test Reality Sprint team.
