"""
Performance test fixtures and utilities.

This module provides shared fixtures, helpers, and configuration for
performance benchmarking tests. It includes timing utilities, memory
measurement, and baseline comparison tools.
"""

import os

import pytest

# In sandboxed environments joblib semaphore checks can fail with EACCES.
# Explicit serial mode avoids noisy warnings during performance test collection.
os.environ.setdefault("JOBLIB_MULTIPROCESSING", "0")

pytestmark = pytest.mark.P0

import json  # noqa: E402
import shutil  # noqa: E402
import time  # noqa: E402
import tracemalloc  # noqa: E402
from dataclasses import asdict, dataclass  # noqa: E402
from datetime import datetime  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any, Callable  # noqa: E402

# Environment switches for baseline refresh automation.
_BASELINE_WRITE_MODE_ENV = "DATA_EXTRACT_BASELINE_WRITE_MODE"
_BASELINE_TARGET_ENV = "DATA_EXTRACT_BASELINE_TARGET"


def _env_truthy(name: str) -> bool:
    return str(os.environ.get(name, "")).strip().lower() in {"1", "true", "yes", "on"}


def baseline_write_enabled() -> bool:
    """Return True when tests should persist baselines to a real target file."""
    return _env_truthy(_BASELINE_WRITE_MODE_ENV)


def baseline_target_path(default_path: Path) -> Path:
    """Return baseline destination path from environment or default."""
    configured = str(os.environ.get(_BASELINE_TARGET_ENV, "")).strip()
    if configured:
        return Path(configured)
    return default_path


def _baseline_file_is_usable(path: Path) -> bool:
    """Return True when path contains valid baseline JSON payload."""
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return False
    baselines = payload.get("baselines")
    return isinstance(baselines, dict)


def _seed_baseline_file(path: Path) -> None:
    """Initialize an empty but valid baseline payload."""
    data = {
        "baselines": {},
        "updated_at": datetime.now().isoformat(),
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


# ============================================================================
# Performance Measurement Models
# ============================================================================


@dataclass
class BenchmarkResult:
    """
    Performance benchmark result.

    Attributes:
        operation: Name of the operation being benchmarked
        duration_ms: Execution time in milliseconds
        memory_mb: Peak memory usage in megabytes
        file_size_kb: Size of input file in kilobytes (if applicable)
        throughput: Items processed per second
        timestamp: When the benchmark was executed
        metadata: Additional benchmark-specific data
    """

    operation: str
    duration_ms: float
    memory_mb: float
    file_size_kb: float
    throughput: float
    timestamp: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class SystemSpecs:
    """
    System specifications for benchmark context.

    Attributes:
        python_version: Python version string
        platform: OS platform
        machine: Machine architecture
        processor: Processor name
        timestamp: When specs were captured
    """

    python_version: str
    platform: str
    machine: str
    processor: str
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


# ============================================================================
# Performance Measurement Context Manager
# ============================================================================


class PerformanceMeasurement:
    """
    Context manager for measuring execution time and memory usage.

    Usage:
        with PerformanceMeasurement() as perf:
            # Code to benchmark
            result = expensive_operation()

        print(f"Duration: {perf.duration_ms:.2f}ms")
        print(f"Peak Memory: {perf.peak_memory_mb:.2f}MB")
    """

    def __init__(self):
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.peak_memory_bytes: int = 0
        self.current_memory_bytes: int = 0

    def __enter__(self) -> "PerformanceMeasurement":
        """Start timing and memory tracking."""
        tracemalloc.start()
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and capture peak memory."""
        self.end_time = time.perf_counter()
        self.current_memory_bytes, self.peak_memory_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

    @property
    def duration_ms(self) -> float:
        """Get execution duration in milliseconds."""
        return (self.end_time - self.start_time) * 1000

    @property
    def duration_seconds(self) -> float:
        """Get execution duration in seconds."""
        return self.end_time - self.start_time

    @property
    def peak_memory_mb(self) -> float:
        """Get peak memory usage in megabytes."""
        return self.peak_memory_bytes / 1024 / 1024

    @property
    def current_memory_mb(self) -> float:
        """Get current memory usage in megabytes."""
        return self.current_memory_bytes / 1024 / 1024


# ============================================================================
# Baseline Management
# ============================================================================


class BaselineManager:
    """
    Manage performance baselines for regression detection.

    Baselines are stored in JSON format and compared against
    current benchmark results to detect performance regressions.
    """

    def __init__(self, baseline_file: Path):
        """
        Initialize baseline manager.

        Args:
            baseline_file: Path to baseline JSON file
        """
        self.baseline_file = baseline_file
        self._baselines: dict[str, BenchmarkResult] = {}

        # Load existing baselines if file exists
        if baseline_file.exists():
            self.load()

    def load(self) -> None:
        """Load baselines from JSON file."""
        with open(self.baseline_file, "r") as f:
            data = json.load(f)

        # Convert dictionaries back to BenchmarkResult objects
        self._baselines = {
            key: BenchmarkResult(**value) for key, value in data.get("baselines", {}).items()
        }

    def save(self) -> None:
        """Save baselines to JSON file."""
        data = {
            "baselines": {key: result.to_dict() for key, result in self._baselines.items()},
            "updated_at": datetime.now().isoformat(),
        }

        # Create directory if it doesn't exist
        self.baseline_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.baseline_file, "w") as f:
            json.dump(data, f, indent=2)

    def update_baseline(self, operation: str, result: BenchmarkResult) -> None:
        """
        Update or create baseline for an operation.

        Args:
            operation: Operation name (unique key)
            result: Benchmark result to store as baseline
        """
        self._baselines[operation] = result

    def get_baseline(self, operation: str) -> BenchmarkResult | None:
        """
        Get baseline for an operation.

        Args:
            operation: Operation name

        Returns:
            Baseline result or None if not found
        """
        return self._baselines.get(operation)

    def compare(
        self, operation: str, current: BenchmarkResult, threshold: float = 0.20
    ) -> dict[str, Any]:
        """
        Compare current result against baseline.

        Args:
            operation: Operation name
            current: Current benchmark result
            threshold: Regression threshold (default 20% degradation)

        Returns:
            Dictionary with comparison results:
                - has_baseline: Whether baseline exists
                - duration_change_pct: Percentage change in duration
                - memory_change_pct: Percentage change in memory
                - is_regression: Whether performance regressed
                - threshold_pct: Threshold used for comparison
        """
        baseline = self.get_baseline(operation)

        if baseline is None:
            return {
                "has_baseline": False,
                "is_regression": False,
                "message": "No baseline available for comparison",
            }

        # Calculate percentage changes
        if baseline.duration_ms > 0:
            duration_change = (
                (current.duration_ms - baseline.duration_ms) / baseline.duration_ms
            ) * 100
        elif current.duration_ms > 0:
            duration_change = float("inf")
        else:
            duration_change = 0.0

        if baseline.memory_mb > 0:
            memory_change = ((current.memory_mb - baseline.memory_mb) / baseline.memory_mb) * 100
        elif current.memory_mb > 0:
            memory_change = float("inf")
        else:
            memory_change = 0.0

        # Check if regression (>threshold% worse)
        is_duration_regression = duration_change > (threshold * 100)
        is_memory_regression = memory_change > (threshold * 100)
        is_regression = is_duration_regression or is_memory_regression

        return {
            "has_baseline": True,
            "baseline_duration_ms": baseline.duration_ms,
            "baseline_memory_mb": baseline.memory_mb,
            "current_duration_ms": current.duration_ms,
            "current_memory_mb": current.memory_mb,
            "duration_change_pct": duration_change,
            "memory_change_pct": memory_change,
            "is_duration_regression": is_duration_regression,
            "is_memory_regression": is_memory_regression,
            "is_regression": is_regression,
            "threshold_pct": threshold * 100,
        }


# ============================================================================
# Pytest Fixtures
# ============================================================================


@pytest.fixture
def perf_measure() -> Callable[[], PerformanceMeasurement]:
    """
    Provide performance measurement context manager factory.

    Returns:
        Factory function that creates PerformanceMeasurement instances

    Usage:
        def test_performance(perf_measure):
            with perf_measure() as perf:
                # Code to benchmark
                pass
            assert perf.duration_ms < 1000
    """
    return PerformanceMeasurement


@pytest.fixture
def baseline_manager(tmp_path: Path) -> BaselineManager:
    """
    Provide baseline manager for tests.

    Uses temporary directory by default for test isolation.
    To use actual baseline file, override in specific tests.

    Args:
        tmp_path: pytest built-in fixture for temporary directory

    Returns:
        BaselineManager instance
    """
    baseline_file = tmp_path / "test_baselines.json"
    return BaselineManager(baseline_file)


@pytest.fixture
def production_baseline_manager(tmp_path_factory: pytest.TempPathFactory) -> BaselineManager:
    """
    Provide baseline manager with production baseline file.

    This fixture uses the actual baseline file for regression detection.
    Use this when you want to compare against real baselines.

    Returns:
        BaselineManager for production baselines
    """
    source_baseline = Path(__file__).parent / "baselines.json"

    if baseline_write_enabled():
        baseline_file = baseline_target_path(source_baseline)
        baseline_file.parent.mkdir(parents=True, exist_ok=True)
        if not _baseline_file_is_usable(baseline_file):
            if (
                source_baseline.exists()
                and _baseline_file_is_usable(source_baseline)
                and baseline_file != source_baseline
            ):
                shutil.copy2(source_baseline, baseline_file)
            else:
                _seed_baseline_file(baseline_file)
        return BaselineManager(baseline_file)

    baseline_dir = tmp_path_factory.mktemp("perf_baselines")
    baseline_file = baseline_dir / "baselines.json"
    if source_baseline.exists():
        shutil.copy2(source_baseline, baseline_file)
    return BaselineManager(baseline_file)


@pytest.fixture
def system_specs() -> SystemSpecs:
    """
    Capture current system specifications.

    Returns:
        SystemSpecs with current system information
    """
    import platform  # noqa: E402
    import sys  # noqa: E402

    return SystemSpecs(
        python_version=sys.version,
        platform=f"{platform.system()} {platform.release()}",
        machine=platform.machine(),
        processor=platform.processor(),
        timestamp=datetime.now().isoformat(),
    )


@pytest.fixture
def benchmark_result_factory() -> Callable[..., BenchmarkResult]:
    """
    Provide factory for creating BenchmarkResult instances.

    Returns:
        Factory function for creating benchmark results

    Usage:
        def test_benchmark(benchmark_result_factory):
            result = benchmark_result_factory(
                operation="test_op",
                duration_ms=100.0,
                memory_mb=50.0
            )
    """

    def _create(
        operation: str,
        duration_ms: float,
        memory_mb: float,
        file_size_kb: float = 0.0,
        throughput: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> BenchmarkResult:
        return BenchmarkResult(
            operation=operation,
            duration_ms=duration_ms,
            memory_mb=memory_mb,
            file_size_kb=file_size_kb,
            throughput=throughput,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {},
        )

    return _create


# ============================================================================
# Test File Size Categories
# ============================================================================


@pytest.fixture
def small_file_threshold() -> int:
    """Small file threshold in KB (< 100KB)."""
    return 100


@pytest.fixture
def medium_file_threshold() -> int:
    """Medium file threshold in KB (100KB - 1MB)."""
    return 1024


@pytest.fixture
def large_file_threshold() -> int:
    """Large file threshold in KB (> 1MB)."""
    return 1024


def categorize_file_size(size_kb: float) -> str:
    """
    Categorize file size into small/medium/large.

    Args:
        size_kb: File size in kilobytes

    Returns:
        Category string: "small", "medium", or "large"
    """
    if size_kb < 100:
        return "small"
    elif size_kb < 1024:
        return "medium"
    else:
        return "large"


# ============================================================================
# Performance Assertion Helpers
# ============================================================================


def assert_performance_target(
    duration_ms: float, target_ms: float, operation: str, tolerance: float = 0.20
) -> None:
    """
    Assert that performance meets target with tolerance.

    Args:
        duration_ms: Actual duration in milliseconds
        target_ms: Target duration in milliseconds
        operation: Operation name for error message
        tolerance: Allowed tolerance as fraction (default 20%)

    Raises:
        AssertionError: If performance exceeds target + tolerance
    """
    max_allowed = target_ms * (1 + tolerance)
    assert duration_ms <= max_allowed, (
        f"{operation} took {duration_ms:.2f}ms, "
        f"exceeding target of {target_ms:.2f}ms "
        f"(+{tolerance*100:.0f}% tolerance = {max_allowed:.2f}ms)"
    )


def assert_memory_limit(
    memory_mb: float, limit_mb: float, operation: str, tolerance: float = 0.10
) -> None:
    """
    Assert that memory usage stays within limit.

    Args:
        memory_mb: Actual memory usage in megabytes
        limit_mb: Memory limit in megabytes
        operation: Operation name for error message
        tolerance: Allowed tolerance as fraction (default 10%)

    Raises:
        AssertionError: If memory exceeds limit + tolerance
    """
    max_allowed = limit_mb * (1 + tolerance)
    assert memory_mb <= max_allowed, (
        f"{operation} used {memory_mb:.2f}MB, "
        f"exceeding limit of {limit_mb:.2f}MB "
        f"(+{tolerance*100:.0f}% tolerance = {max_allowed:.2f}MB)"
    )
