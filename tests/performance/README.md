# Performance Benchmarking Suite

Systematic performance testing infrastructure for the Data Extractor Tool.

## Quick Start

### Establish Baselines

```bash
# Run baseline capture (no strict assertions)
pytest tests/performance/test_baseline_capture.py -v -s

# Creates: tests/performance/baselines.json
```

### Run Performance Tests

```bash
# All performance tests
pytest tests/performance/ -v -m performance

# Specific extractors
pytest tests/performance/test_extractor_benchmarks.py -v -m extraction

# Processors and formatters
pytest tests/performance/test_pipeline_benchmarks.py -v -m processing
pytest tests/performance/test_pipeline_benchmarks.py -v -m formatting

# Exclude performance tests from regular runs
pytest tests/ -v -m "not performance"
```

### Run Scripted Performance Suites

```bash
# Existing suites (extractors + pipeline + cli)
python scripts/run_performance_suite.py

# Include API runtime load suite and write consolidated JSON
python scripts/run_performance_suite.py \
  --suites extractors pipeline cli api_runtime \
  --output-json tests/performance/performance_suite_report.json

# Run API runtime load harness directly
python scripts/run_api_load.py \
  --base-url http://127.0.0.1:8000 \
  --endpoint /api/v1/health \
  --concurrency 8 \
  --duration-seconds 15 \
  --output-json tests/performance/api_runtime_health.json
```

### View Results

```bash
# Check baselines
cat tests/performance/baselines.json

# Read canonical baseline reference
cat docs/architecture/epic-4-performance-baselines.md
```

## Test Files

| File | Purpose | Tests |
|------|---------|-------|
| `conftest.py` | Fixtures, measurement utils, baseline management | - |
| `test_baseline_capture.py` | Establish baselines without strict assertions | 5 |
| `test_extractor_benchmarks.py` | Extractor performance tests (PDF, Excel, TXT) | 8 |
| `test_pipeline_benchmarks.py` | Processor, formatter, batch performance | 7 |
| `test_throughput.py` | NFR validation: 100-file batch throughput & memory (Story 2.5.1) | 4+ |
| `baselines.json` | Performance baseline data | - |
| `batch_100_files/` | 100-file test batch for NFR-P1/P2 validation | - |

**Total**: ~1,976 lines of code, 20+ benchmark tests

## 100-File Test Batch (Story 2.5.1)

Location: `batch_100_files/`

### Batch Composition

The performance test batch contains 100 files distributed as follows:

| File Type | Count | Location | Purpose |
|-----------|-------|----------|---------|
| PDF | 40 | `batch_100_files/pdfs/` | Test PDF extraction performance (native + OCR paths) |
| DOCX | 30 | `batch_100_files/docx/` | Test Office document extraction |
| XLSX | 20 | `batch_100_files/xlsx/` | Test spreadsheet extraction with varying row counts |
| Mixed | 10 | `batch_100_files/mixed/` | PPTX, images, and other formats |
| **Total** | **100** | | |

### File Size Distribution

Files are duplicated from existing fixtures in round-robin fashion to create variety:
- **PDFs**: Synthetic and sanitized fixtures from `tests/fixtures/pdfs/`
- **DOCX**: Mix of 1-20 page documents with tables and images
- **XLSX**: Mix of 10-1000 row spreadsheets with formulas and multiple sheets
- **Mixed**: PowerPoint presentations and images

### Batch Creation

The batch is created by `scripts/create_performance_batch.py`:

```bash
python -m scripts.create_performance_batch
```

### NFR Validation Tests (V1.0 - VALIDATED)

The 100-file batch validates:

1. **NFR-P1: Batch Processing Throughput** ✅ PASSING
   - 100 files process in <10 minutes (requirement met)
   - Sustained throughput ~10 files/minute achieved
   - Test: `test_batch_throughput_100_files()` in `test_throughput.py`
   - Status: Validated in V1.0 release (2025-12-01)

2. **NFR-P2: Memory Efficiency** ✅ PASSING
   - Peak memory <2GB (2048MB) during batch processing (requirement met)
   - No memory leaks detected (memory returns to baseline)
   - Tests: `test_memory_usage_within_limits()`, `test_no_memory_leaks()` in `test_throughput.py`
   - Status: Validated in V1.0 release (2025-12-01)

3. **ADR-005 Validation**: ✅ Streaming pipeline architecture maintains constant memory
4. **ADR-006 Validation**: ✅ Continue-on-error pattern enables graceful degradation

## Performance Metrics

Each benchmark captures:
- **Duration**: Milliseconds to complete operation
- **Peak Memory**: Maximum memory usage in megabytes
- **Throughput**: KB/s or blocks/s
- **File Size**: Input file size for context
- **Timestamp**: When measurement was taken
- **Metadata**: Operation-specific details

## Baseline Management

### BaselineManager API

```python
from tests.performance.conftest import BaselineManager

# Initialize
manager = BaselineManager(Path("tests/performance/baselines.json"))

# Update baseline
manager.update_baseline("operation_name", benchmark_result)
manager.save()

# Compare against baseline
comparison = manager.compare("operation_name", current_result, threshold=0.20)
if comparison['is_regression']:
    print(f"Performance regression detected: {comparison}")
```

### Regression Detection

Default threshold: **20% degradation** triggers regression alert

```python
comparison = {
    'has_baseline': True,
    'baseline_duration_ms': 1000.0,
    'current_duration_ms': 1300.0,
    'duration_change_pct': 30.0,  # 30% slower
    'is_duration_regression': True,  # Exceeds 20% threshold
    'is_regression': True
}
```

## Current Baselines

### Extractors

| Operation | Duration | Memory | Throughput |
|-----------|----------|--------|------------|
| **PDF Small** (807KB) | 70.3s | 304 MB | 11.48 KB/s |
| **PDF Medium** (2.2MB) | 154.0s | 1,234 MB | 14.39 KB/s |
| **PDF Large** (11.6MB) | 353.4s | 1,212 MB | 32.92 KB/s |
| **Excel Small** (5KB) | 17.2ms | 0.24 MB | 276.93 KB/s |
| **Excel Medium** (113KB) | 7.2s | 115.68 MB | 15.83 KB/s |
| **Excel Large** (458KB) | 4.1s | 38.96 MB | 111.62 KB/s |
| **TXT Small** (1KB) | 0.80ms | 0.01 MB | 1,104 KB/s |
| **TXT Medium** (14KB) | 2.05ms | 0.07 MB | 6,991 KB/s |

### Processors (100 blocks)

| Processor | Duration | Memory | Throughput |
|-----------|----------|--------|------------|
| **Context Linking** | 0.98ms | 0.04 MB | 101,750 blocks/s |
| **Metadata Aggregation** | 1.13ms | 0.04 MB | 88,277 blocks/s |
| **Quality Validation** | 1.24ms | 0.03 MB | 80,959 blocks/s |
| **Full Chain** | ~3.35ms | ~0.11 MB | ~29,850 blocks/s |

## Performance Targets

### Updated Targets (based on baselines)

| Component | Target | Notes |
|-----------|--------|-------|
| **PDF Extraction** | 60-90s per MB | Complex layouts, tables, images |
| **Excel Extraction** | 5-10s for complex | Simple files <100ms |
| **TXT Extraction** | <10ms | Already excellent |
| **Processor Chain** | <5ms per 100 blocks | Already excellent |
| **Memory (PDF)** | <1.5GB per file | Increased from 500MB |
| **Memory (Other)** | <200MB per file | Already meeting |

## Continuous Integration

### CI Configuration

```yaml
# .github/workflows/performance.yml (example)
performance-tests:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Run performance tests
      run: pytest tests/performance/ -v -m performance
    - name: Check for regressions
      run: python scripts/check_performance_regressions.py
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
# Quick performance smoke test
pytest tests/performance/test_baseline_capture.py::TestBaselineCapture::test_capture_txt_baselines -q
```

## Troubleshooting

### Tests Taking Too Long

Performance tests are marked with `@pytest.mark.slow` - they can take 10+ minutes.
Use `-m "not slow"` to skip them during development.

### Baseline File Not Found

Run `test_baseline_capture.py` to create initial baselines:
```bash
pytest tests/performance/test_baseline_capture.py -v -s
```

### Memory Errors

Large PDF tests may exceed available RAM. Adjust test selection:
```bash
# Skip large file tests
pytest tests/performance/ -v -k "not large"
```

### Inconsistent Results

Performance can vary based on:
- System load
- Background processes
- Disk I/O
- Initial JIT warmup

**Solution**: Run multiple times and average, or increase regression threshold.

## Architecture

### Measurement Infrastructure

```
PerformanceMeasurement (context manager)
    ├── time.perf_counter() - High-resolution timing
    ├── tracemalloc - Memory tracking
    └── Returns: duration_ms, peak_memory_mb

BenchmarkResult (data class)
    ├── operation: str
    ├── duration_ms: float
    ├── memory_mb: float
    ├── file_size_kb: float
    ├── throughput: float
    └── metadata: dict

BaselineManager
    ├── load() - Read baselines from JSON
    ├── save() - Write baselines to JSON
    ├── update_baseline() - Store new baseline
    └── compare() - Detect regressions
```

### Test Structure

```python
@pytest.mark.performance
@pytest.mark.slow
class TestComponentBenchmarks:
    def test_operation_performance(self, perf_measure, production_baseline_manager):
        # Measure
        with perf_measure() as perf:
            result = component.operation(input_data)

        # Create benchmark
        benchmark = BenchmarkResult(
            operation="test_operation",
            duration_ms=perf.duration_ms,
            memory_mb=perf.peak_memory_mb,
            ...
        )

        # Assert (optional for strict tests)
        assert_performance_target(perf.duration_ms, target_ms, "operation")

        # Save baseline
        production_baseline_manager.update_baseline("test_operation", benchmark)
        production_baseline_manager.save()
```

## Epic 4 Performance Achievements (V1.0)

### Completed in V1.0 Release

- ✅ **End-to-end pipeline benchmarks** (Story 4.1-4.5)
- ✅ **Semantic analysis baselines** (TF-IDF: 10ms, Similarity: 4.8ms, Quality: 0.12ms)
- ✅ **Performance profiling integration** (Scripts: validate_performance.py, smoke_test_semantic.py)
- ✅ **NFR-P1/P2 validation** (Throughput and memory requirements met)

### Future Enhancements

#### Planned Improvements

- [ ] Parallel batch processing benchmarks (Epic 5.7 optimization)
- [ ] Formatter performance baselines (currently missing)
- [ ] Load testing with concurrent operations
- [ ] Automated regression alerts in CI
- [ ] Performance dashboard/visualization
- [ ] Comparison across Python versions

#### Optimization Opportunities

Based on V1.0 baseline analysis:

**High Priority**:
1. PDF extraction optimization (largest gap vs targets)
2. Memory usage reduction for large PDFs

**Medium Priority**:
1. Excel complex workbook optimization
2. Parallel batch processing (incremental updates implemented in Story 5.7)

**Low Priority**:
1. TXT extraction (already excellent)
2. Processor chain (already excellent)
3. Semantic analysis (10-80x faster than requirements)

## References

- **Baseline Report**: `docs/architecture/epic-4-performance-baselines.md`
- **Test Infrastructure**: `tests/performance/conftest.py`
- **Baseline Data**: `tests/performance/baselines.json`
- **Project State**: `docs/index.md`

---

**Last Updated**: 2025-12-01 (V1.0 Release)
**Baseline Version**: 1.0
**Python**: 3.11+ (minimum requirement)
**Platform**: Windows 11 / Linux (WSL2)
**Status**: Production - All NFRs validated
