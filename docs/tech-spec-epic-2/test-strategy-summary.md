# Test Strategy Summary

## Testing Philosophy

Epic 2 follows the testing framework established in Epic 1 (Story 1.3), with >80% coverage target and comprehensive test organization mirroring the src/ structure.

## Test Organization

```
tests/
├── unit/
│   └── test_normalize/
│       ├── test_cleaning.py           # Story 2.1: 20+ tests
│       ├── test_entities.py           # Story 2.2: 25+ tests
│       ├── test_schema.py             # Story 2.3: 30+ tests
│       ├── test_validation.py         # Story 2.4, 2.5: 25+ tests
│       ├── test_metadata.py           # Story 2.6: 15+ tests
│       └── test_config.py             # Configuration: 10+ tests
├── integration/
│   ├── test_normalization_pipeline.py # End-to-end: Extract → Normalize
│   ├── test_determinism.py           # NFR-R1: Run same doc 10 times
│   ├── test_brownfield_integration.py # Brownfield extractors → normalizers
│   └── test_batch_processing.py      # Batch of 10 mixed documents
├── performance/
│   ├── test_normalization_throughput.py # 100 docs in <10 minutes
│   └── test_entity_recognition_accuracy.py # >90% accuracy validation
└── fixtures/
    └── normalization/
        ├── dirty_text_samples/        # OCR artifacts, formatting issues
        ├── entity_test_docs/          # 6 entity types with known entities
        ├── schema_test_docs/          # Report, matrix, export, image samples
        └── ocr_test_images/           # Scanned PDFs, low/high quality
```

## Coverage Targets by Story

| Story | Module | Target Coverage | Critical Paths |
|-------|--------|----------------|----------------|
| 2.1 | normalize/cleaning.py | >90% | Text cleaning, header/footer detection, audit logging |
| 2.2 | normalize/entities.py | >85% | Entity recognition, normalization, cross-reference resolution |
| 2.3 | normalize/schema.py | >80% | Document type detection, schema transformations, Archer parsing |
| 2.4 | normalize/validation.py (OCR) | >85% | Confidence scoring, preprocessing, quarantine |
| 2.5 | normalize/validation.py (Completeness) | >85% | Gap detection, completeness ratio, validation report |
| 2.6 | normalize/metadata.py | >85% | Metadata enrichment, file hashing, JSON serialization |
| Epic | Overall normalize/ module | >80% | All modules combined |

## Test Types and Strategy

**Unit Tests (125+ tests estimated)**:
- **Story 2.1** (20 tests): Regex patterns, whitespace normalization, header detection, determinism
- **Story 2.2** (25 tests): 6 entity types, abbreviation expansion, cross-refs, config loading
- **Story 2.3** (30 tests): 4 doc types, schema transformations, Archer parsing, Excel tables
- **Story 2.4** (15 tests): OCR confidence, preprocessing, threshold flagging, quarantine
- **Story 2.5** (10 tests): Missing images, complex objects, completeness ratio, gap locations
- **Story 2.6** (15 tests): File hash, entity tags, quality scores, config snapshot, JSON serialization
- **Config** (10 tests): YAML loading, Pydantic validation, cascade precedence

**Integration Tests (10+ tests estimated)**:
- End-to-end pipeline: Extract (brownfield) → Normalize → verify output structure
- Determinism validation: Same document 10 runs, assert byte-identical output
- Brownfield integration: Existing extractors → new normalizers, verify compatibility
- Batch processing: 10 mixed documents (PDF, Word, Excel, Archer), verify all normalized
- Configuration cascade: CLI flags > env vars > YAML, verify precedence
- Quarantine workflow: Low OCR confidence → quarantine directory with log
- Multi-story integration: Text cleaning → entity normalization → schema → metadata
- Epic 1 regression: Run all Epic 1 tests, assert still passing (zero brownfield regressions)

**Performance Tests (2+ benchmarks)**:
- **Throughput**: 100 mixed documents in <10 minutes (NFR-P1), measure per-story overhead
- **Entity accuracy**: 100 documents with known entities, calculate precision/recall (>90% target)

**Test Fixtures Required**:
- **Dirty text samples** (Story 2.1): OCR artifacts (^^^^^, ■■■■), repeated headers, excessive whitespace
- **Entity test docs** (Story 2.2): Documents with known entities (annotated ground truth)
- **Schema test docs** (Story 2.3): Word report, Excel matrix, Archer HTML/XML export, scanned image
- **OCR test images** (Story 2.4): High-quality scan (>95%), low-quality scan (<90%), native PDF
- **Completeness test docs** (Story 2.5): Documents with images, charts, OLE objects (known gaps)

## Test Execution Strategy

**Per Story (Development)**:
1. Write unit tests first (TDD approach)
2. Implement functionality to pass tests
3. Run tests frequently during development (`pytest -v tests/unit/test_normalize/test_<story>.py`)
4. Achieve >85% coverage before marking story complete

**Per Epic (Integration)**:
1. Run all unit tests (`pytest tests/unit/test_normalize/`)
2. Run integration tests (`pytest tests/integration/`)
3. Run performance benchmarks (`pytest tests/performance/`)
4. Generate coverage report (`pytest --cov=src/data_extract/normalize --cov-report=html`)
5. Validate >80% overall coverage
6. Run Epic 1 regression suite (ensure zero brownfield breaks)

**CI/CD Pipeline**:
```yaml
# .github/workflows/test.yml (add Epic 2 jobs)
jobs:
  test-epic2-unit:
    runs-on: ubuntu-latest
    steps:
      - Install dependencies (including spaCy model, Tesseract)
      - Run: pytest tests/unit/test_normalize/ --cov --cov-report=xml
      - Upload coverage to codecov

  test-epic2-integration:
    runs-on: ubuntu-latest
    steps:
      - Install dependencies
      - Run: pytest tests/integration/ -v

  test-epic2-determinism:
    runs-on: ubuntu-latest
    steps:
      - Run: pytest tests/integration/test_determinism.py --runs=10

  test-brownfield-regression:
    runs-on: ubuntu-latest
    steps:
      - Run: pytest tests/ -k "not epic2" --cov
      - Assert: Epic 1 tests still pass
```

## Definition of Done (Testing Perspective)

**Story-Level**:
- [ ] All unit tests written and passing (>85% coverage)
- [ ] Story-specific integration tests passing
- [ ] Pre-commit hooks passing (black, ruff, mypy)
- [ ] No brownfield test regressions

**Epic-Level**:
- [ ] Overall coverage >80% for normalize/ module
- [ ] All integration tests passing
- [ ] Performance benchmarks meet targets (throughput, entity accuracy)
- [ ] Determinism validation passing (10 runs, identical output)
- [ ] All Epic 1 tests still passing (zero regressions)
- [ ] CI/CD pipeline green for all Epic 2 jobs

## Test Automation

**Automated in CI**:
- All unit tests (fast, <1 minute)
- Integration tests (moderate, <5 minutes)
- Coverage reporting (automatic upload)
- Brownfield regression suite (Epic 1 tests)

**Manual/On-Demand**:
- Performance benchmarks (slow, ~10 minutes for 100 docs)
- Entity accuracy validation (requires manual ground truth annotation)
- UX testing (quarantine reports, validation summaries)

**Test Data Management**:
- Fixtures committed to git (sanitized audit documents)
- Large fixtures (<10MB) stored in git LFS
- Synthetic test data generated where real docs unavailable
- Ground truth annotations stored alongside test fixtures (JSON format)
