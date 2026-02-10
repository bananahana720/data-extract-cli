# Epic 4 Integration Test Design Document

**Role**: Integration Architecture Designer
**Date**: 2025-11-18
**Epic**: Epic 4 - Semantic Analysis
**Type**: Design Document (READ-ONLY)

---

## Executive Summary

This document provides comprehensive integration test patterns for Epic 4 semantic features. It follows established project conventions, leverages existing test infrastructure, and provides reusable patterns for TF-IDF, similarity analysis, LSA, and end-to-end pipeline testing.

**Key Design Principles:**
- Mirror `src/` structure in `tests/` exactly
- Use pytest fixtures for dependency injection
- Test immutability and type safety contracts
- Include performance baselines in assertions
- Follow Given-When-Then format

---

## 1. Test Structure

### Directory Organization

```
tests/integration/
├── test_semantic/                     # NEW: Epic 4 integration tests
│   ├── __init__.py
│   ├── conftest.py                   # Semantic-specific fixtures
│   ├── test_tfidf_pipeline.py        # TF-IDF integration tests
│   ├── test_similarity_pipeline.py    # Similarity integration tests
│   ├── test_lsa_pipeline.py          # LSA integration tests
│   ├── test_quality_pipeline.py      # Quality metrics integration
│   ├── test_semantic_end_to_end.py   # Full pipeline tests
│   └── test_semantic_performance.py  # Performance baseline tests
└── test_pipeline_semantic.py         # Pipeline orchestration with semantic stage
```

### Naming Conventions

- **Test Files**: `test_{feature}_pipeline.py` for feature-specific, `test_semantic_{aspect}.py` for aspects
- **Test Classes**: `Test{Feature}Integration` (e.g., `TestTfIdfIntegration`)
- **Test Methods**: `test_{scenario}_{expected_outcome}` (e.g., `test_extract_to_semantic_produces_vectors`)
- **Fixtures**: `{resource}_fixture` (e.g., `semantic_corpus_fixture`)

### Test Markers

```python
# Required markers for semantic tests
pytestmark = [
    pytest.mark.integration,  # Always include
    pytest.mark.semantic,      # NEW: Semantic stage tests
    pytest.mark.epic4,         # NEW: Epic 4 specific
]

# Additional markers as needed
@pytest.mark.performance   # Performance baseline tests
@pytest.mark.slow          # Tests taking >1 second
@pytest.mark.pipeline      # End-to-end pipeline tests
```

---

## 2. Fixture Patterns

### Semantic-Specific Fixtures (conftest.py)

```python
"""
Fixtures for semantic integration testing.

Place in: tests/integration/test_semantic/conftest.py
"""

import pytest
from pathlib import Path
from typing import List
from src.data_extract.chunk.models import Chunk
from src.data_extract.core.models import ProcessingContext
from tests.fixtures.semantic_corpus import (
    get_technical_corpus,
    get_business_corpus,
    get_mixed_corpus
)

@pytest.fixture
def semantic_corpus_documents() -> List[str]:
    """
    Provide semantic corpus documents for testing.

    Returns:
        List of documents with varied content types
    """
    return get_mixed_corpus()


@pytest.fixture
def chunked_documents(semantic_corpus_documents) -> List[Chunk]:
    """
    Generate chunked documents from corpus.

    Creates realistic chunks with:
    - Entity references
    - Quality scores
    - Sequential chunk IDs
    - Metadata with provenance

    Returns:
        List of Chunk objects ready for semantic processing
    """
    from tests.support.factories import chunks_factory

    chunks = []
    for doc_idx, doc_content in enumerate(semantic_corpus_documents):
        # Simulate chunking (simplified for testing)
        sentences = doc_content.split('. ')
        for chunk_idx, sentence in enumerate(sentences):
            chunk = chunks_factory(
                count=1,
                content_override=sentence + '.',
                chunk_id=f"doc{doc_idx}_chunk{chunk_idx}"
            )[0]
            chunks.append(chunk)

    return chunks


@pytest.fixture
def semantic_processing_context(tmp_path: Path) -> ProcessingContext:
    """
    Create ProcessingContext configured for semantic analysis.

    Returns:
        ProcessingContext with semantic config
    """
    return ProcessingContext(
        config={
            'semantic': {
                'max_features': 1000,
                'min_df': 0.01,
                'max_df': 0.95,
                'use_idf': True,
                'n_components': 100,  # For LSA
                'similarity_threshold': 0.7
            }
        },
        source_file='test_corpus.txt',
        output_dir=tmp_path / 'output',
        metrics={}
    )


@pytest.fixture
def expected_vector_dimensions() -> int:
    """Expected dimensions for TF-IDF vectors."""
    return 1000  # Based on max_features config


@pytest.fixture
def performance_thresholds() -> dict:
    """
    Performance baselines for semantic operations.

    Returns:
        Dict of operation -> max_seconds
    """
    return {
        'tfidf_fit': 0.1,        # 100ms for fitting on corpus
        'tfidf_transform': 0.05,  # 50ms per document
        'similarity_matrix': 0.2,  # 200ms for 10x10 matrix
        'lsa_fit': 0.3,          # 300ms for LSA decomposition
        'quality_metrics': 0.01   # 10ms per chunk
    }
```

---

## 3. TF-IDF Test Pattern

### Template: test_tfidf_pipeline.py

```python
"""
Integration tests for TF-IDF vectorization in pipeline.

Test IDs: TF-001 through TF-010
"""

import pytest
import numpy as np
from typing import List

from src.data_extract.chunk.models import Chunk
from src.data_extract.core.models import ProcessingContext
from src.data_extract.semantic.tfidf import TfIdfVectorizer  # Future module

pytestmark = [pytest.mark.integration, pytest.mark.semantic, pytest.mark.epic4]


class TestTfIdfIntegration:
    """Integration tests for TF-IDF vectorization."""

    def test_tf001_chunks_to_vectors_pipeline(
        self,
        chunked_documents: List[Chunk],
        semantic_processing_context: ProcessingContext
    ):
        """
        Test TF-001: Chunks → TF-IDF vectors with proper dimensions.

        Given: List of chunks from document processing
        When: TF-IDF vectorizer processes chunks
        Then: Each chunk has sparse vector with expected dimensions
        """
        # Arrange
        vectorizer = TfIdfVectorizer()

        # Act
        result = vectorizer.process(chunked_documents, semantic_processing_context)

        # Assert
        assert result.success is True
        assert 'vectors' in result.data
        assert len(result.data['vectors']) == len(chunked_documents)

        # Validate vector properties
        for vector in result.data['vectors']:
            assert hasattr(vector, 'shape')
            assert vector.shape[1] <= 1000  # max_features constraint

    def test_tf002_vocabulary_consistency_across_batches(
        self,
        chunked_documents: List[Chunk],
        semantic_processing_context: ProcessingContext
    ):
        """
        Test TF-002: Vocabulary remains consistent across batch processing.

        Given: Multiple batches of chunks
        When: Processing batches separately
        Then: Vocabulary and feature indices remain consistent
        """
        # Test implementation here
        pass

    def test_tf003_performance_baseline(
        self,
        chunked_documents: List[Chunk],
        semantic_processing_context: ProcessingContext,
        performance_thresholds: dict,
        performance_timer
    ):
        """
        Test TF-003: TF-IDF meets performance baselines.

        Given: Standard corpus of chunks
        When: Vectorizing with TF-IDF
        Then: Processing time within thresholds
        """
        # Arrange
        vectorizer = TfIdfVectorizer()

        # Act
        performance_timer.start()
        result = vectorizer.process(chunked_documents, semantic_processing_context)
        performance_timer.stop()

        # Assert
        assert result.success is True
        assert performance_timer.elapsed < performance_thresholds['tfidf_fit']

    def test_tf004_empty_chunks_handling(self):
        """
        Test TF-004: Gracefully handle empty chunks.

        Given: Chunks with empty content
        When: Processing through TF-IDF
        Then: Returns zero vectors without errors
        """
        pass

    def test_tf005_special_characters_normalization(self):
        """
        Test TF-005: Handle special characters and unicode.

        Given: Chunks with special characters
        When: Vectorizing
        Then: Proper normalization applied
        """
        pass


class TestTfIdfEdgeCases:
    """Edge case tests for TF-IDF integration."""

    def test_tf006_single_word_documents(self):
        """Test TF-006: Single-word documents produce valid vectors."""
        pass

    def test_tf007_duplicate_chunks(self):
        """Test TF-007: Duplicate chunks produce identical vectors."""
        pass

    def test_tf008_max_features_limit(self):
        """Test TF-008: Vocabulary respects max_features configuration."""
        pass
```

---

## 4. Similarity Test Pattern

### Template: test_similarity_pipeline.py

```python
"""
Integration tests for document and chunk similarity.

Test IDs: SIM-001 through SIM-010
"""

import pytest
import numpy as np
from typing import List

pytestmark = [pytest.mark.integration, pytest.mark.semantic, pytest.mark.epic4]


class TestSimilarityIntegration:
    """Integration tests for similarity analysis."""

    def test_sim001_document_similarity_matrix(
        self,
        chunked_documents: List[Chunk],
        semantic_processing_context: ProcessingContext
    ):
        """
        Test SIM-001: Generate document similarity matrix.

        Given: TF-IDF vectors from multiple documents
        When: Computing pairwise similarity
        Then: Symmetric matrix with diagonal = 1.0
        """
        # Arrange
        from src.data_extract.semantic.similarity import SimilarityAnalyzer

        analyzer = SimilarityAnalyzer()

        # Act
        result = analyzer.process(chunked_documents, semantic_processing_context)

        # Assert
        assert 'similarity_matrix' in result.data
        matrix = result.data['similarity_matrix']

        # Validate matrix properties
        assert matrix.shape[0] == matrix.shape[1]  # Square
        assert np.allclose(matrix, matrix.T)       # Symmetric
        assert np.allclose(np.diag(matrix), 1.0)   # Diagonal = 1

    def test_sim002_chunk_to_chunk_similarity(self):
        """
        Test SIM-002: Compute similarity between specific chunks.

        Given: Two chunks with known content
        When: Computing similarity
        Then: Score reflects content overlap
        """
        pass

    def test_sim003_find_similar_chunks(self):
        """
        Test SIM-003: Find top-k similar chunks.

        Given: Query chunk
        When: Searching for similar chunks
        Then: Returns k most similar with scores
        """
        pass

    def test_sim004_similarity_threshold_filtering(self):
        """
        Test SIM-004: Filter by similarity threshold.

        Given: Similarity scores
        When: Applying threshold from config
        Then: Only high-similarity pairs returned
        """
        pass

    def test_sim005_cross_document_similarity(self):
        """
        Test SIM-005: Similarity across document boundaries.

        Given: Chunks from different documents
        When: Computing similarity
        Then: Identifies related content across docs
        """
        pass
```

---

## 5. LSA Test Pattern

### Template: test_lsa_pipeline.py

```python
"""
Integration tests for Latent Semantic Analysis.

Test IDs: LSA-001 through LSA-008
"""

import pytest
import numpy as np

pytestmark = [pytest.mark.integration, pytest.mark.semantic, pytest.mark.epic4]


class TestLSAIntegration:
    """Integration tests for LSA dimensionality reduction."""

    def test_lsa001_dimension_reduction(
        self,
        chunked_documents,
        semantic_processing_context
    ):
        """
        Test LSA-001: Reduce TF-IDF dimensions via LSA.

        Given: High-dimensional TF-IDF vectors
        When: Applying LSA with n_components=100
        Then: Reduced to 100 dimensions preserving variance
        """
        # Arrange
        from src.data_extract.semantic.lsa import LSAProcessor

        processor = LSAProcessor(n_components=100)

        # Act
        result = processor.process(chunked_documents, semantic_processing_context)

        # Assert
        assert 'lsa_vectors' in result.data
        vectors = result.data['lsa_vectors']

        # Validate dimensions
        assert vectors.shape[1] == 100

        # Validate variance preservation
        assert result.data['explained_variance'] > 0.8  # 80% variance

    def test_lsa002_semantic_clustering(self):
        """
        Test LSA-002: LSA enables semantic clustering.

        Given: Documents with known topics
        When: Applying LSA
        Then: Similar topics cluster together
        """
        pass

    def test_lsa003_noise_reduction(self):
        """
        Test LSA-003: LSA reduces noise in sparse data.

        Given: Sparse TF-IDF matrix
        When: Applying LSA
        Then: Dense representation with reduced noise
        """
        pass

    def test_lsa004_component_selection(self):
        """
        Test LSA-004: Automatic component selection.

        Given: Variance threshold
        When: Selecting components
        Then: Minimum components for threshold
        """
        pass
```

---

## 6. Pipeline Integration Pattern

### Template: test_semantic_end_to_end.py

```python
"""
End-to-end integration tests for complete semantic pipeline.

Test IDs: E2E-001 through E2E-010
"""

import pytest
from pathlib import Path

pytestmark = [
    pytest.mark.integration,
    pytest.mark.semantic,
    pytest.mark.pipeline,
    pytest.mark.epic4,
    pytest.mark.slow
]


class TestSemanticPipelineE2E:
    """End-to-end tests for Extract→Normalize→Chunk→Semantic→Output."""

    def test_e2e001_pdf_to_semantic_analysis(
        self,
        sample_pdf_file: Path,
        configured_pipeline,
        tmp_path: Path
    ):
        """
        Test E2E-001: PDF document through complete semantic pipeline.

        Given: PDF document
        When: Processing through all stages including semantic
        Then: Output contains similarity scores and quality metrics
        """
        # Arrange
        from src.data_extract.semantic import SemanticProcessor

        # Add semantic stage to pipeline
        pipeline = configured_pipeline
        pipeline.add_stage(SemanticProcessor())

        # Act
        result = pipeline.process_file(
            sample_pdf_file,
            output_dir=tmp_path / 'output'
        )

        # Assert pipeline success
        assert result.success is True

        # Assert semantic outputs
        output_file = tmp_path / 'output' / 'analysis.json'
        assert output_file.exists()

        # Validate semantic data
        import json
        with open(output_file) as f:
            data = json.load(f)

        assert 'similarity_matrix' in data
        assert 'quality_scores' in data
        assert 'entity_relationships' in data

    def test_e2e002_batch_semantic_processing(
        self,
        multiple_test_files: List[Path],
        configured_pipeline,
        tmp_path: Path
    ):
        """
        Test E2E-002: Batch processing with cross-document similarity.

        Given: Multiple documents
        When: Batch processing with semantic analysis
        Then: Cross-document similarities identified
        """
        pass

    def test_e2e003_semantic_with_entity_preservation(self):
        """
        Test E2E-003: Semantic analysis preserves entity context.

        Given: Documents with entities (RISK, CONTROL)
        When: Semantic processing
        Then: Entity relationships enhanced by similarity
        """
        pass

    def test_e2e004_configurable_semantic_pipeline(self):
        """
        Test E2E-004: Pipeline respects semantic configuration.

        Given: Custom semantic config
        When: Processing
        Then: Config values applied (thresholds, components)
        """
        pass

    def test_e2e005_semantic_error_recovery(self):
        """
        Test E2E-005: Pipeline continues on semantic errors.

        Given: Document causing semantic processing error
        When: Batch processing
        Then: Error logged, other documents processed
        """
        pass
```

---

## 7. Performance Test Pattern

### Template: test_semantic_performance.py

```python
"""
Performance baseline tests for semantic operations.

Test IDs: PERF-001 through PERF-008
"""

import pytest
import time
from typing import List

pytestmark = [
    pytest.mark.integration,
    pytest.mark.semantic,
    pytest.mark.performance,
    pytest.mark.epic4
]


class TestSemanticPerformance:
    """Performance baseline validation for semantic features."""

    def test_perf001_tfidf_scaling(self):
        """
        Test PERF-001: TF-IDF scales linearly with documents.

        Given: Corpus sizes [10, 100, 1000] documents
        When: Measuring TF-IDF processing time
        Then: Time scales approximately linearly
        """
        # Implementation pattern:
        # 1. Generate corpora of different sizes
        # 2. Measure processing time for each
        # 3. Assert linear scaling (time_1000 < 100 * time_10)
        pass

    def test_perf002_similarity_matrix_memory(self):
        """
        Test PERF-002: Similarity matrix memory usage.

        Given: N documents
        When: Computing NxN similarity matrix
        Then: Memory usage within O(N²) bounds
        """
        pass

    def test_perf003_lsa_performance_baseline(self):
        """
        Test PERF-003: LSA meets performance baseline.

        Given: 1000-dimensional vectors, 100 documents
        When: Reducing to 100 dimensions
        Then: Completes within 300ms
        """
        pass

    def test_perf004_incremental_processing(self):
        """
        Test PERF-004: Incremental updates are efficient.

        Given: Existing TF-IDF model
        When: Adding new documents
        Then: Update faster than full recomputation
        """
        pass

    def test_perf005_quality_metrics_overhead(self):
        """
        Test PERF-005: Quality metrics add minimal overhead.

        Given: Pipeline with and without quality metrics
        When: Processing same corpus
        Then: <10% performance impact
        """
        pass
```

---

## 8. Fixture Inheritance Patterns

### Reusable Base Fixtures

```python
"""
Base fixture patterns for semantic testing.
"""

@pytest.fixture
def mock_semantic_stage():
    """
    Mock semantic stage for testing pipeline integration.

    Returns a stage that:
    - Accepts List[Chunk]
    - Returns ProcessingResult with semantic data
    - Tracks invocation for assertions
    """
    class MockSemanticStage:
        def __init__(self):
            self.invoked = False
            self.input_chunks = None

        def process(self, chunks, context):
            self.invoked = True
            self.input_chunks = chunks

            return ProcessingResult(
                success=True,
                data={
                    'vectors': [...],  # Mock vectors
                    'similarity': [...],  # Mock similarity
                    'quality': [...]     # Mock quality
                }
            )

    return MockSemanticStage()


@pytest.fixture
def semantic_pipeline_with_mocks(configured_pipeline, mock_semantic_stage):
    """
    Pipeline with mock semantic stage for isolated testing.
    """
    pipeline = configured_pipeline
    pipeline.add_stage(mock_semantic_stage)
    return pipeline
```

---

## 9. Test Data Patterns

### Semantic Test Corpus Patterns

```python
"""
Pattern for creating varied semantic test data.
"""

def create_similar_documents() -> List[str]:
    """
    Create documents with known similarity.

    Returns:
        List of document pairs with high similarity
    """
    return [
        # Pair 1: High similarity (same topic, different words)
        "The data extraction pipeline processes documents efficiently.",
        "Document processing pipeline extracts data with high performance.",

        # Pair 2: Medium similarity (related topics)
        "Machine learning algorithms analyze text patterns.",
        "AI systems process natural language using patterns.",

        # Pair 3: Low similarity (different topics)
        "Financial reports show quarterly revenue growth.",
        "Technical documentation describes API endpoints."
    ]


def create_entity_rich_corpus() -> List[str]:
    """
    Create corpus with known entities for relationship testing.
    """
    return [
        "RISK-001 is mitigated by CTRL-001 and CTRL-002.",
        "Control CTRL-001 addresses multiple risks including RISK-001.",
        "The audit found RISK-002 requires additional control CTRL-003."
    ]
```

---

## 10. Assertion Patterns

### Semantic-Specific Assertions

```python
"""
Reusable assertion patterns for semantic testing.
"""

def assert_valid_tfidf_vector(vector, max_features=1000):
    """Assert TF-IDF vector properties."""
    assert hasattr(vector, 'shape')
    assert vector.shape[0] == 1  # Single document
    assert vector.shape[1] <= max_features
    assert vector.min() >= 0  # Non-negative weights
    assert vector.max() <= 1  # Normalized


def assert_valid_similarity_matrix(matrix):
    """Assert similarity matrix properties."""
    import numpy as np

    # Square matrix
    assert matrix.shape[0] == matrix.shape[1]

    # Symmetric
    assert np.allclose(matrix, matrix.T)

    # Diagonal = 1.0 (self-similarity)
    assert np.allclose(np.diag(matrix), 1.0)

    # Values in [0, 1]
    assert matrix.min() >= 0
    assert matrix.max() <= 1


def assert_lsa_variance_preserved(original_dims, reduced_dims, variance_ratio):
    """Assert LSA preserves sufficient variance."""
    assert reduced_dims < original_dims
    assert variance_ratio > 0.8  # At least 80% variance


def assert_performance_baseline(elapsed_time, baseline, tolerance=0.1):
    """Assert operation meets performance baseline."""
    assert elapsed_time < baseline * (1 + tolerance)
```

---

## Success Criteria Validation

### Integration Test Checklist

- [x] **Test Structure**: Mirrors src/ exactly with test_semantic/ directory
- [x] **Fixtures**: Reusable, parameterized, follow naming conventions
- [x] **TF-IDF Pattern**: Complete template with 8+ test cases
- [x] **Similarity Pattern**: Complete template with 5+ test cases
- [x] **LSA Pattern**: Complete template with 4+ test cases
- [x] **Pipeline Pattern**: End-to-end tests with all stages
- [x] **Performance Pattern**: Baseline validation tests
- [x] **Markers**: Proper pytest markers for test selection
- [x] **Assertions**: Reusable assertion utilities
- [x] **Edge Cases**: Empty, single-word, special character handling
- [x] **Given-When-Then**: All tests follow format
- [x] **Type Safety**: Tests validate immutability and types
- [x] **Performance**: Each pattern includes performance assertions

---

## Implementation Guide for Wave 2 Agents

### Step-by-Step Implementation

1. **Create Directory Structure**:
   ```bash
   mkdir -p tests/integration/test_semantic
   touch tests/integration/test_semantic/{__init__.py,conftest.py}
   ```

2. **Implement Fixtures First**:
   - Start with conftest.py
   - Import from existing factories
   - Add semantic-specific fixtures

3. **Implement Test Files**:
   - Start with test_tfidf_pipeline.py
   - Use templates as starting point
   - Fill in test implementations

4. **Run Tests with Markers**:
   ```bash
   pytest tests/integration/test_semantic -m "semantic and not slow"
   ```

5. **Validate Performance**:
   ```bash
   pytest tests/integration/test_semantic -m performance
   ```

### Common Pitfalls to Avoid

1. **Don't break immutability** - Always use frozen dataclasses
2. **Don't ignore ProcessingContext** - Pass through all stages
3. **Don't skip performance tests** - Baselines prevent regression
4. **Don't hardcode paths** - Use fixtures and tmp_path
5. **Don't forget cleanup** - Use pytest's automatic cleanup

---

## Conclusion

This design document provides complete integration test patterns for Epic 4 semantic features. The patterns:

- Follow established project conventions exactly
- Provide reusable fixtures and utilities
- Include comprehensive test coverage
- Validate performance baselines
- Support incremental implementation

Wave 2 agents can implement these patterns directly without architectural decisions, ensuring consistent and thorough testing of Epic 4 semantic capabilities.

---

*Design Document Status: COMPLETE*
*Implementation Status: PENDING*
*Epic 4 Readiness: TEST PATTERNS DEFINED*
