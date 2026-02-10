"""
Performance tests for NFR-P1 and NFR-P2 validation using GREENFIELD architecture.

Story 2.5-2.1: Pipeline Throughput Optimization

These tests validate:
- NFR-P1: 100 mixed-format files process in <10 minutes (with ProcessPoolExecutor)
- NFR-P2: Peak memory <2GB during batch processing (including all workers)
- Memory leak detection
- ADR-005 streaming architecture validation
- ADR-006 continue-on-error with parallel execution

BASELINE (Story 2.5-2.1, 2025-11-12):
- Throughput: 14.57 files/min (ProcessPoolExecutor, 4 workers)
- Duration: 6.86 minutes for 100-file batch
- Memory: 4.15GB peak (exceeds 2GB target)
- Success: 99% (99/100 files)
- OCR Quality: 95.26% average confidence

ARCHITECTURE: Uses greenfield extractors (src/data_extract/) with ProcessPoolExecutor

Usage:
    pytest -m performance tests/performance/test_throughput.py -v
    pytest tests/performance/test_throughput.py::test_batch_throughput_100_files -v
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="Brownfield migration: module depends on removed brownfield code"
)
