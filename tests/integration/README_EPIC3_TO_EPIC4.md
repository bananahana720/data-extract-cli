# Epic 3→4 Integration Tests

## Overview

This document describes the critical integration tests for the Epic 3 to Epic 4 handoff (Chunk → Semantic pipeline stage transition). These tests were implemented to address the **ZERO integration test coverage** gap identified during Wave 1 analysis.

## Test File Location

**Primary Test File**: `tests/integration/test_pipeline_epic3_to_epic4.py`

## Purpose

These integration tests validate that the output from Epic 3 (chunking) is fully compatible with the input requirements of Epic 4 (semantic analysis). This is the most critical pipeline boundary as identified in the gap analysis.

## Test Coverage

### Critical Path Tests (P0)

| Test ID | Test Name | Description | Status |
|---------|-----------|-------------|--------|
| E34-001 | `test_chunks_have_text_content` | Validates all chunks have non-empty text (prevents TF-IDF crashes) | ✅ |
| E34-002 | `test_chunk_metadata_serializable` | Ensures chunk metadata is JSON-serializable for caching | ✅ |
| E34-005 | `test_chunk_ids_unique_and_valid` | Validates unique chunk IDs with proper format | ✅ |
| E34-006 | `test_chunks_vectorizable_with_tfidf` | **CORE TEST**: Validates TF-IDF compatibility | ✅ |

### Data Contract Tests

| Test ID | Test Name | Description | Status |
|---------|-----------|-------------|--------|
| E34-007 | `test_chunk_metadata_includes_required_fields` | Validates presence of Epic 4 required metadata | ✅ |
| E34-008 | `test_chunks_preserve_entity_boundaries` | Ensures entities aren't split across chunks | ✅ |

### Performance Tests

| Test ID | Test Name | Description | Status |
|---------|-----------|-------------|--------|
| E34-009 | `test_vectorization_within_nfr_limits` | Validates <100ms per 1k-word NFR | ✅ |
| E34-010 | `test_chunk_serialization_performance` | Validates <50ms serialization target | ✅ |
| E34-003 | `test_memory_stability_batch_processing` | Ensures no memory leaks in batch processing | ✅ |

### Error Recovery Tests

| Test ID | Test Name | Description | Status |
|---------|-----------|-------------|--------|
| E34-004 | `test_empty_chunk_handling` | Graceful handling of empty chunks | ✅ |
| E34-011 | `test_special_character_handling` | Unicode, emoji, control character support | ✅ |
| E34-012 | `test_large_corpus_processing` | Stress test with 1000+ chunks | ✅ |

## Critical Risks Addressed

### 1. Empty Chunk Text
**Risk**: TF-IDF vectorization crashes with `ValueError: empty vocabulary`
**Mitigation**: Test E34-001 ensures all chunks have non-empty text

### 2. Non-Serializable Metadata
**Risk**: `TypeError: Object of type numpy.ndarray is not JSON serializable`
**Mitigation**: Test E34-002 validates full JSON serialization

### 3. Duplicate Chunk IDs
**Risk**: Similarity analysis tracking breaks with duplicate IDs
**Mitigation**: Test E34-005 ensures unique IDs with proper format

### 4. Memory Explosion
**Risk**: Memory grows unbounded with large chunk sets
**Mitigation**: Test E34-003 monitors memory stability across batches

## Running the Tests

### Run All Epic 3→4 Tests
```bash
pytest tests/integration/test_pipeline_epic3_to_epic4.py -v
```

### Run Only Critical Path Tests
```bash
pytest tests/integration/test_pipeline_epic3_to_epic4.py -v -m p0
```

### Run Performance Tests
```bash
pytest tests/integration/test_pipeline_epic3_to_epic4.py -v -m performance
```

### Run with Coverage
```bash
pytest tests/integration/test_pipeline_epic3_to_epic4.py \
    --cov=src/data_extract/chunk \
    --cov=src/data_extract/semantic \
    -v
```

## Expected Results

When Epic 4 is not yet implemented:
- Data format tests should **PASS** (validates Epic 3 output)
- Vectorization tests should **PASS** (using scikit-learn directly)
- Performance tests should **PASS** (within tolerances)
- Some semantic-specific tests may **SKIP** if modules don't exist

## Epic 4 Implementation Contract

Based on these tests, Epic 4 implementation MUST:

1. **Accept Chunk objects** with the following fields:
   - `id`: string, unique identifier
   - `text`: string, non-empty content
   - `document_id`: string, parent document reference
   - `position_index`: int, position in document
   - `word_count`: int, >0
   - `token_count`: int, >0
   - `quality_score`: float, 0.0-1.0

2. **Handle edge cases**:
   - Filter out empty chunks before vectorization
   - Support Unicode and special characters
   - Process batches without memory leaks

3. **Meet performance targets**:
   - TF-IDF vectorization: <100ms per 1k words
   - Chunk serialization: <50ms for 100 chunks
   - Memory usage: <500MB for 1000 chunks

## Adding New Tests

To add new integration tests:

1. Add test to appropriate class in `test_pipeline_epic3_to_epic4.py`
2. Use descriptive test ID (E34-XXX format)
3. Mark with appropriate pytest markers
4. Document failure modes in docstring
5. Update this README with the new test

## Test Fixtures

### Location
`tests/fixtures/semantic/` and `tests/fixtures/entity_rich_documents/`

### Available Fixtures
- Edge case chunks (empty, single word, max size)
- Unicode-heavy content
- Performance test corpus (1000+ chunks)

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all Epic 3 modules are installed
```bash
pip install -e ".[dev]"
```

2. **Missing spaCy Model**: Required for chunking
```bash
python -m spacy download en_core_web_md
```

3. **scikit-learn Not Found**: Required for TF-IDF tests
```bash
pip install scikit-learn>=1.3.0
```

### Debug Mode

Run with verbose output and debugging:
```bash
pytest tests/integration/test_pipeline_epic3_to_epic4.py -vv -s --log-cli-level=DEBUG
```

## Maintenance

These tests should be:
- Run on every PR that touches chunk or semantic modules
- Updated when Epic 4 implementation changes the contract
- Monitored for flakiness (target: 0% flaky rate)
- Used as acceptance criteria for Epic 4 completion

## Contact

**Author**: Wave 2.2 Agent (Winston)
**Date**: 2025-11-18
**Sprint**: Epic 4 Preparation (Wave 2)
**Priority**: P0 - Critical for Epic 4 success
