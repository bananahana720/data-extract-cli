# Testing Strategy

## Test Organization

Tests mirror source structure exactly:

```
tests/
├── unit/                 # Fast, isolated tests
│   ├── test_extract/
│   ├── test_normalize/
│   ├── test_chunk/
│   ├── test_semantic/
│   └── test_output/
├── integration/          # Multi-component tests
│   ├── test_pipeline_orchestration.py
│   └── test_end_to_end.py
├── performance/          # Benchmarks and stress tests
└── fixtures/             # Shared test data
```

## Test Markers

Available markers (defined in `pytest.ini`):

- `unit` - Fast unit tests (< 1s each)
- `integration` - Integration tests (< 10s each)
- `slow` - Slow running tests (> 5s)
- `performance` - Performance benchmarks (skip in CI)
- `extraction` - Extraction stage tests
- `processing` - Processing stage tests
- `formatting` - Formatting stage tests
- `pipeline` - Pipeline orchestration tests
- `cli` - Command-line interface tests
- `edge_case` - Edge cases and boundary conditions
- `stress` - Resource-intensive tests
- `infrastructure` - Infrastructure component tests
- `cross_format` - Cross-format validation

## Test Execution Strategy

**Recommended approach:**
1. Run unit tests first (fail-fast, instant feedback)
2. Run integration tests
3. Run specific test category if debugging

```bash
# Fail-fast approach (stop on first failure)
pytest -x -m "not performance" --timeout=30

# Run slow tests with longer timeout
pytest -m slow --timeout=120

# Run tests in parallel (faster)
pytest -n auto -m "not performance" --timeout=30
```

## Coverage Requirements

**Current Status (Epic 1):**
- Overall: 88% (923/1047 tests)
- Unit tests: 100% passing
- Integration tests: 71% passing
- CLI tests: 82% passing
- Extractor tests: 98% passing
- Performance tests: Disabled (PDF processing issue)

**Targets by Epic:**
- Epic 1: >60% (achieved: 88%)
- Epic 2: >80%
- Epic 3: >85%
- Epic 4: >85%
- Epic 5: >90% critical paths

## Known Test Issues

See `docs/TESTING-README.md` for complete test status and known issues.

**Quick Wins (2 hours for +2% coverage):**
- PDF path handling (15 tests)
- Tuple vs. object returns (9 tests)
- Import path correction (3 tests)

---
