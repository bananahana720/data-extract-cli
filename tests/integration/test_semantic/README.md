# Semantic Test Infrastructure

## Overview

This directory contains integration tests for Epic 4 - Semantic Analysis features of the data extraction pipeline. The tests follow the integration pattern design from Wave 1 architecture and are structured to validate TF-IDF vectorization, document similarity, LSA dimensionality reduction, and text quality metrics.

## Test Structure

```
tests/integration/test_semantic/
├── conftest.py                    # Semantic-specific fixtures
├── test_tfidf_pipeline.py         # TF-IDF vectorization tests (TF-001 to TF-012)
├── test_similarity_pipeline.py    # Document similarity tests (SIM-001 to SIM-012)
├── test_lsa_pipeline.py          # LSA reduction tests (LSA-001 to LSA-012)
├── test_quality_pipeline.py      # Quality metrics tests (QUAL-001 to QUAL-012)
├── test_semantic_e2e.py          # End-to-end pipeline tests (E2E-001 to E2E-010)
└── README.md                      # This file
```

## Test Categories

### 1. TF-IDF Tests (`test_tfidf_pipeline.py`)
- **Purpose**: Validate TF-IDF vectorization functionality
- **Test IDs**: TF-001 through TF-012
- **Coverage**:
  - Vector generation from chunks
  - Vocabulary consistency
  - Performance baselines
  - Special character handling
  - Document frequency filtering
  - Edge cases (empty chunks, duplicates)

### 2. Similarity Tests (`test_similarity_pipeline.py`)
- **Purpose**: Validate document and chunk similarity computation
- **Test IDs**: SIM-001 through SIM-012
- **Coverage**:
  - Similarity matrix generation
  - Chunk-to-chunk similarity
  - Top-k similar document retrieval
  - Cross-document similarity
  - Entity-aware similarity
  - Performance and memory efficiency

### 3. LSA Tests (`test_lsa_pipeline.py`)
- **Purpose**: Validate Latent Semantic Analysis functionality
- **Test IDs**: LSA-001 through LSA-012
- **Coverage**:
  - Dimensionality reduction
  - Semantic clustering
  - Noise reduction
  - Component selection
  - Variance preservation
  - Algorithm comparisons

### 4. Quality Metrics Tests (`test_quality_pipeline.py`)
- **Purpose**: Validate text quality assessment
- **Test IDs**: QUAL-001 through QUAL-012
- **Coverage**:
  - Readability scores (Flesch, SMOG, ARI)
  - Complexity metrics
  - Quality threshold filtering
  - Entity density impact
  - Language detection
  - Performance baselines

### 5. End-to-End Tests (`test_semantic_e2e.py`)
- **Purpose**: Validate complete pipeline with semantic stage
- **Test IDs**: E2E-001 through E2E-010
- **Coverage**:
  - Full pipeline integration
  - Batch processing
  - Entity preservation
  - Configuration handling
  - Error recovery
  - Output formats

## Fixtures

### Core Fixtures (`conftest.py`)

#### Corpus Fixtures
- `semantic_corpus_documents`: Mixed content documents for testing
- `technical_corpus`: Technical documentation samples
- `business_corpus`: Business documentation samples

#### Chunk Fixtures
- `chunked_documents`: Pre-chunked documents with metadata
- `entity_rich_chunks`: Chunks with RISK/CONTROL entities

#### Configuration Fixtures
- `semantic_processing_context`: ProcessingContext with semantic config
- `performance_thresholds`: Performance baseline thresholds
- `expected_vector_dimensions`: Expected TF-IDF dimensions
- `expected_lsa_dimensions`: Expected LSA dimensions

#### Mock Fixtures
- `mock_tfidf_stage`: Mock TF-IDF processor for isolation
- `mock_similarity_stage`: Mock similarity analyzer
- `mock_lsa_stage`: Mock LSA processor
- `mock_quality_stage`: Mock quality analyzer

## Test Execution

### Run All Semantic Tests
```bash
pytest tests/integration/test_semantic -m semantic
```

### Run Specific Test Categories
```bash
# TF-IDF tests only
pytest tests/integration/test_semantic -m tfidf

# Similarity tests only
pytest tests/integration/test_semantic -m similarity

# LSA tests only
pytest tests/integration/test_semantic -m lsa

# Quality metrics tests only
pytest tests/integration/test_semantic -m quality_metrics

# End-to-end tests only
pytest tests/integration/test_semantic -m "semantic and pipeline"
```

### Run Tests by Priority
```bash
# Fast tests (exclude slow)
pytest tests/integration/test_semantic -m "semantic and not slow"

# Performance tests
pytest tests/integration/test_semantic -m "semantic and performance"
```

### Run with Coverage
```bash
pytest tests/integration/test_semantic --cov=src/data_extract/semantic --cov-report=term-missing
```

## Test Implementation Status

All test files are currently templates with TODO comments. As Epic 4 implementation progresses:

1. **Phase 1**: Implement TF-IDF module → Complete TF-* tests
2. **Phase 2**: Implement Similarity module → Complete SIM-* tests
3. **Phase 3**: Implement LSA module → Complete LSA-* tests
4. **Phase 4**: Implement Quality module → Complete QUAL-* tests
5. **Phase 5**: Integration → Complete E2E-* tests

## Performance Baselines

Expected performance targets (from `performance_thresholds` fixture):

| Operation | Max Time | Notes |
|-----------|----------|-------|
| TF-IDF Fit | 100ms | For standard corpus |
| TF-IDF Transform | 50ms | Per document |
| Similarity Matrix | 200ms | For 10x10 matrix |
| LSA Fit | 300ms | For dimensionality reduction |
| LSA Transform | 50ms | Per document |
| Quality Metrics | 10ms | Per chunk |
| Full Pipeline | 500ms | Complete semantic processing |

## Test Data

### Provided Test Corpora

1. **Semantic Corpus**: Mixed technical and business content
2. **Technical Corpus**: API docs, code samples, technical specs
3. **Business Corpus**: Financial reports, audits, risk assessments
4. **Entity-Rich Corpus**: Documents with RISK-* and CTRL-* entities

### Mock Data Generation

Tests use factory patterns to generate:
- Sparse TF-IDF vectors
- Similarity matrices
- LSA reduced vectors
- Quality scores

## Dependencies

The semantic tests require:
- `numpy`: Vector operations and matrix computations
- `scikit-learn`: TF-IDF, LSA, similarity (when implemented)
- `textstat`: Readability metrics (when implemented)

## Best Practices

1. **Isolation**: Use mock fixtures for unit-style integration tests
2. **Performance**: Always include performance assertions
3. **Immutability**: Verify frozen dataclasses not mutated
4. **Type Safety**: Assert proper types throughout pipeline
5. **Edge Cases**: Test empty, single-item, and extreme inputs
6. **Configuration**: Test all configurable parameters

## Common Patterns

### Given-When-Then Format
All tests follow the Given-When-Then format:
```python
def test_example(self, fixture):
    """Test description."""
    # Given: Setup conditions
    # When: Perform action
    # Then: Assert outcomes
```

### Performance Testing
```python
def test_performance(self, performance_timer, performance_thresholds):
    performance_timer.start()
    # ... operation ...
    performance_timer.stop()
    assert performance_timer.elapsed < performance_thresholds['operation_name']
```

### Matrix Validation
```python
def assert_valid_similarity_matrix(matrix):
    assert matrix.shape[0] == matrix.shape[1]  # Square
    assert np.allclose(matrix, matrix.T)       # Symmetric
    assert np.allclose(np.diag(matrix), 1.0)   # Diagonal = 1
```

## Troubleshooting

### Import Errors
If semantic modules not yet implemented:
- Tests are templates with TODO comments
- Can run with `pytest --co` to collect without execution

### Performance Failures
If performance tests fail:
- Check system load
- Verify test data size matches expectations
- Consider adjusting thresholds in conftest.py

### Memory Issues
For large corpus tests:
- Use sparse representations
- Test with smaller batches
- Monitor with memory profiler

## Contributing

When implementing tests:
1. Remove TODO comment
2. Implement test following template structure
3. Ensure test passes locally
4. Update this README if adding new fixtures/patterns
5. Run full test suite before committing

## References

- [Epic 4 Integration Test Design](../../../docs/architecture/epic-4-integration-test-requirements.md)
- [Semantic Analysis Playbook](../../../docs/playbooks/semantic-analysis-intro.ipynb)
- [Project Testing Strategy](../../../docs/development-operations-guide-2025-11-13/testing-strategy.md)
