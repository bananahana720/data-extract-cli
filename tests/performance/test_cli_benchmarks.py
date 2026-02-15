"""
CLI Performance Benchmarks and Stress Tests.

This module provides comprehensive performance testing for the CLI,
including single file extraction, batch processing, thread safety,
and progress display overhead measurements.

Benchmarks Include:
    - Single file extraction (all formats)
    - Batch processing (varying worker counts)
    - Thread safety stress tests
    - Progress display overhead
    - Interrupt response time
    - Encoding performance
"""

import pytest

pytestmark = [
    pytest.mark.P1,
    pytest.mark.performance,
]

import os  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from datetime import datetime  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any, Dict, List  # noqa: E402

import psutil  # noqa: E402
import pytest  # noqa: E402

from tests.performance.conftest import (  # noqa: E402
    BaselineManager,
    BenchmarkResult,
    assert_memory_limit,
    assert_performance_target,
    baseline_regression_enabled,
    baseline_write_enabled,
)

# ============================================================================
# Test Configuration
# ============================================================================

# CLI command
CLI_COMMAND = [sys.executable, "-m", "data_extract.cli"]

# Performance targets
SINGLE_FILE_TARGET_MS = 5000  # 5 seconds for single file
BATCH_FILE_TARGET_MS = 3000  # 3 seconds per file in batch (some overhead)
PROGRESS_OVERHEAD_MAX_PCT = 20  # Progress should add <20% overhead

# Memory limits
SINGLE_FILE_MEMORY_MB = 500
BATCH_MEMORY_MB = 2000
BATCH_WARMUP_RUNS = 1
BATCH_MEASURED_RUNS = 3
REGRESSION_THRESHOLD = 0.30
REGRESSION_DURATION_FLOOR_MS = 50.0
REGRESSION_MEMORY_FLOOR_MB = 5.0
BASELINE_FILE = Path(__file__).parent / "baselines.json"


# ============================================================================
# Helper Functions
# ============================================================================


def _coverage_perf_mode() -> bool:
    """Return True when running under coverage instrumentation."""
    coverage_markers = (
        "COV_CORE_SOURCE",
        "COV_CORE_CONFIG",
        "COVERAGE_RUN",
        "PYTEST_COV",
    )
    if any(str(os.environ.get(name, "")).strip() for name in coverage_markers):
        return True
    return "--cov" in str(os.environ.get("PYTEST_ADDOPTS", ""))


def run_cli_command(
    args: List[str], timeout: int = 300, measure_resources: bool = True
) -> Dict[str, Any]:
    """
    Run CLI command and measure performance.

    Args:
        args: CLI arguments (without module launcher prefix)
        timeout: Command timeout in seconds
        measure_resources: Whether to measure CPU/memory

    Returns:
        Dict with execution metrics:
            - success: bool
            - duration_ms: float
            - memory_peak_mb: float (if measured)
            - cpu_percent: float (if measured)
            - stdout: str
            - stderr: str
            - returncode: int
    """
    full_command = CLI_COMMAND + args

    start_time = time.perf_counter()
    deadline = start_time + float(max(1, timeout))
    timed_out = False

    # Start process
    child_env = dict(os.environ)
    for name in list(child_env.keys()):
        if name.startswith("COV_CORE"):
            child_env.pop(name, None)
    child_env.pop("COVERAGE_PROCESS_START", None)

    process = subprocess.Popen(
        full_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=child_env,
    )

    # Monitor resources if requested
    peak_memory_mb = 0.0
    cpu_samples = []

    if measure_resources:
        try:
            psutil_process = psutil.Process(process.pid)

            # Sample every 0.1 seconds
            while process.poll() is None:
                if time.perf_counter() >= deadline:
                    timed_out = True
                    process.kill()
                    break
                try:
                    mem_info = psutil_process.memory_info()
                    peak_memory_mb = max(peak_memory_mb, mem_info.rss / 1024 / 1024)
                    cpu_samples.append(psutil_process.cpu_percent(interval=0.1))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
        except Exception:
            pass  # Process may have finished

    # Wait for completion
    try:
        remaining = max(0.1, deadline - time.perf_counter())
        stdout, stderr = process.communicate(timeout=remaining)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        stdout, stderr = process.communicate()

    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000

    return {
        "success": process.returncode == 0 and not timed_out,
        "duration_ms": duration_ms,
        "memory_peak_mb": peak_memory_mb,
        "cpu_percent": sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0.0,
        "stdout": stdout,
        "stderr": stderr,
        "returncode": process.returncode,
        "timed_out": timed_out,
    }


def get_test_files(fixture_dir: Path, pattern: str, limit: int = None) -> List[Path]:
    """Get test files matching pattern."""
    files = sorted(fixture_dir.rglob(pattern))
    if limit:
        files = files[:limit]
    return files


def _assert_cli_no_regression(
    operation: str,
    benchmark: BenchmarkResult,
    manager: BaselineManager,
) -> None:
    # Default local mode favors deterministic command success/targets.
    # Enable strict baseline regression enforcement explicitly when desired.
    if os.environ.get("DATA_EXTRACT_ENFORCE_PERF_BASELINE", "").strip().lower() not in {
        "1",
        "true",
        "yes",
    }:
        return

    if baseline_write_enabled() or not baseline_regression_enabled():
        return

    comparison = manager.compare(operation, benchmark, threshold=REGRESSION_THRESHOLD)
    if not comparison["has_baseline"]:
        return

    baseline_duration = float(comparison["baseline_duration_ms"])
    if (
        baseline_duration >= REGRESSION_DURATION_FLOOR_MS
        and float(comparison["duration_change_pct"]) > REGRESSION_THRESHOLD * 100
    ):
        raise AssertionError(
            f"{operation} duration regression: +{comparison['duration_change_pct']:.2f}% "
            f"(baseline={baseline_duration:.2f}ms, current={benchmark.duration_ms:.2f}ms)"
        )

    baseline_memory = float(comparison["baseline_memory_mb"])
    if (
        baseline_memory >= REGRESSION_MEMORY_FLOOR_MB
        and float(comparison["memory_change_pct"]) > REGRESSION_THRESHOLD * 100
    ):
        raise AssertionError(
            f"{operation} memory regression: +{comparison['memory_change_pct']:.2f}% "
            f"(baseline={baseline_memory:.2f}MB, current={benchmark.memory_mb:.2f}MB)"
        )


def _persist_baseline_if_requested(
    operation: str,
    benchmark: BenchmarkResult,
    manager: BaselineManager,
) -> None:
    if not baseline_write_enabled():
        return
    manager.update_baseline(operation, benchmark)
    manager.save()


def _representative_batch_files(
    fixture_dir: Path, max_files: int = 24, *, coverage_lite: bool = False
) -> List[Path]:
    """Build a deterministic, mixed-format corpus for CLI batch benchmarks."""
    coverage_mode = coverage_lite and _coverage_perf_mode()
    if coverage_mode:
        max_files = min(max_files, 12)

    # Keep canonical tiny fixtures for compatibility with prior runs.
    canonical = [
        fixture_dir / "sample.txt",
        fixture_dir / "quality_test_documents" / "complex_text.txt",
        fixture_dir / "quality_test_documents" / "simple_text.txt",
    ]

    # Pull in a broader corpus to make startup overhead less dominant.
    perf_batch_root = Path(__file__).parent / "batch_100_files"
    batch_candidates = sorted(
        [
            path
            for path in perf_batch_root.rglob("*")
            if path.is_file() and path.suffix.lower() != ".png"
        ]
    )

    files_by_suffix: dict[str, list[Path]] = {}
    for candidate in batch_candidates:
        suffix = candidate.suffix.lower()
        files_by_suffix.setdefault(suffix, []).append(candidate)

    ordered_suffixes = [".txt", ".pdf", ".docx", ".xlsx", ".pptx"]
    if coverage_mode:
        ordered_suffixes = [".txt", ".docx"]
    ordered_suffixes.extend(
        suffix for suffix in sorted(files_by_suffix.keys()) if suffix not in ordered_suffixes
    )

    deduped: list[Path] = []
    seen: set[Path] = set()

    def _append_unique(file_path: Path) -> None:
        resolved = file_path.resolve()
        if resolved in seen:
            return
        seen.add(resolved)
        deduped.append(file_path)

    for file_path in canonical:
        if file_path.exists():
            _append_unique(file_path)
        if len(deduped) >= max_files:
            return deduped

    while len(deduped) < max_files:
        appended_this_round = False
        for suffix in ordered_suffixes:
            bucket = files_by_suffix.get(suffix)
            if not bucket:
                continue
            candidate = bucket.pop(0)
            _append_unique(candidate)
            if len(deduped) >= max_files:
                return deduped
            appended_this_round = True
        if not appended_this_round:
            break

    return deduped


# ============================================================================
# Single File Performance Tests
# ============================================================================


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.cli
class TestSingleFilePerformance:
    """Performance benchmarks for single file extraction via CLI."""

    def test_cli_txt_extraction_performance(
        self, fixture_dir: Path, production_baseline_manager, tmp_path: Path
    ):
        """Benchmark CLI TXT file extraction."""
        txt_file = fixture_dir / "sample.txt"

        if not txt_file.exists():
            pytest.skip(f"Test file not found: {txt_file}")

        # Run CLI command
        result = run_cli_command(
            ["extract", str(txt_file), "--output", str(tmp_path / "output.txt"), "--quiet"]
        )

        # Verify success
        assert result["success"], f"CLI failed: {result['stderr']}"

        # Create benchmark
        file_size_kb = txt_file.stat().st_size / 1024
        benchmark = BenchmarkResult(
            operation="cli_extract_txt",
            duration_ms=result["duration_ms"],
            memory_mb=result["memory_peak_mb"],
            file_size_kb=file_size_kb,
            throughput=(
                file_size_kb / (result["duration_ms"] / 1000) if result["duration_ms"] > 0 else 0
            ),
            timestamp=datetime.now().isoformat(),
            metadata={"file_name": txt_file.name, "cpu_percent": result["cpu_percent"]},
        )

        # Assert performance
        assert_performance_target(
            result["duration_ms"], SINGLE_FILE_TARGET_MS, "CLI TXT extraction"
        )
        assert_memory_limit(result["memory_peak_mb"], SINGLE_FILE_MEMORY_MB, "CLI TXT extraction")

        # Log results
        print(f"\n{'='*60}")
        print("CLI TXT Extraction Benchmark:")
        print(f"  File: {txt_file.name} ({file_size_kb:.2f} KB)")
        print(f"  Duration: {result['duration_ms']:.2f} ms ({result['duration_ms']/1000:.2f}s)")
        print(f"  Memory: {result['memory_peak_mb']:.2f} MB")
        print(f"  CPU: {result['cpu_percent']:.1f}%")
        print(f"  Throughput: {benchmark.throughput:.2f} KB/s")
        print(f"{'='*60}")

        _assert_cli_no_regression("cli_extract_txt", benchmark, production_baseline_manager)
        _persist_baseline_if_requested("cli_extract_txt", benchmark, production_baseline_manager)

    def test_cli_pdf_extraction_performance(
        self, fixture_dir: Path, production_baseline_manager, tmp_path: Path
    ):
        """Benchmark CLI PDF file extraction."""
        pdf_file = fixture_dir / "pdfs" / "large" / "audit-report-large.pdf"

        if not pdf_file.exists():
            pytest.skip(f"Test file not found: {pdf_file}")

        # Run CLI command
        result = run_cli_command(
            ["extract", str(pdf_file), "--output", str(tmp_path / "output.md"), "--quiet"],
            timeout=60,
        )

        # Verify success
        assert result["success"], f"CLI failed: {result['stderr']}"

        # Create benchmark
        file_size_kb = pdf_file.stat().st_size / 1024
        benchmark = BenchmarkResult(
            operation="cli_extract_pdf",
            duration_ms=result["duration_ms"],
            memory_mb=result["memory_peak_mb"],
            file_size_kb=file_size_kb,
            throughput=(
                file_size_kb / (result["duration_ms"] / 1000) if result["duration_ms"] > 0 else 0
            ),
            timestamp=datetime.now().isoformat(),
            metadata={"file_name": pdf_file.name, "cpu_percent": result["cpu_percent"]},
        )

        # Assert performance (more lenient for PDF)
        assert_performance_target(
            result["duration_ms"], SINGLE_FILE_TARGET_MS * 3, "CLI PDF extraction", tolerance=0.5
        )
        assert_memory_limit(
            result["memory_peak_mb"],
            SINGLE_FILE_MEMORY_MB,
            "CLI PDF extraction",
            tolerance=0.30,
        )

        # Log results
        print(f"\n{'='*60}")
        print("CLI PDF Extraction Benchmark:")
        print(f"  File: {pdf_file.name} ({file_size_kb:.2f} KB)")
        print(f"  Duration: {result['duration_ms']:.2f} ms ({result['duration_ms']/1000:.2f}s)")
        print(f"  Memory: {result['memory_peak_mb']:.2f} MB")
        print(f"  CPU: {result['cpu_percent']:.1f}%")
        print(f"  Throughput: {benchmark.throughput:.2f} KB/s")
        print(f"{'='*60}")

        _assert_cli_no_regression("cli_extract_pdf", benchmark, production_baseline_manager)
        _persist_baseline_if_requested("cli_extract_pdf", benchmark, production_baseline_manager)


# ============================================================================
# Batch Processing Performance Tests
# ============================================================================


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.cli
class TestBatchProcessingPerformance:
    """Performance benchmarks for batch processing with different worker counts."""

    @pytest.mark.parametrize("workers", [1, 4, 8, 16])
    def test_cli_batch_processing_workers(
        self,
        fixture_dir: Path,
        workers: int,
        production_baseline_manager,
        tmp_path: Path,
    ):
        """Benchmark batch processing with different worker counts."""
        # Use a broader deterministic corpus to reduce startup-noise dominance.
        test_files = _representative_batch_files(fixture_dir, max_files=24, coverage_lite=True)
        coverage_mode = _coverage_perf_mode()
        warmup_runs = 0 if coverage_mode else BATCH_WARMUP_RUNS
        measured_runs = 1 if coverage_mode else BATCH_MEASURED_RUNS

        if len(test_files) < 10:
            pytest.skip("Not enough test files for batch test")

        import shutil  # noqa: E402

        # Create temporary output directory
        output_dir = tmp_path / f"batch_output_{workers}workers"
        batch_input_dir = tmp_path / f"batch_input_{workers}workers"
        shutil.rmtree(output_dir, ignore_errors=True)
        shutil.rmtree(batch_input_dir, ignore_errors=True)
        output_dir.mkdir(exist_ok=True)
        batch_input_dir.mkdir(exist_ok=True)

        for test_file in test_files:
            shutil.copy2(test_file, batch_input_dir / test_file.name)

        batch_args = [
            "batch",
            str(batch_input_dir),
            "--output",
            str(output_dir),
            "--workers",
            str(workers),
            "--quiet",
        ]

        # Warmup and median-of-N measurement to reduce run-to-run timing noise.
        for _ in range(warmup_runs):
            shutil.rmtree(output_dir, ignore_errors=True)
            output_dir.mkdir(exist_ok=True)
            warmup = run_cli_command(batch_args, timeout=300)
            assert warmup["success"], f"Batch warmup failed: {warmup['stderr']}"

        samples: list[Dict[str, Any]] = []
        for _ in range(measured_runs):
            shutil.rmtree(output_dir, ignore_errors=True)
            output_dir.mkdir(exist_ok=True)
            sample = run_cli_command(batch_args, timeout=300)
            assert sample["success"], f"Batch failed: {sample['stderr']}"
            samples.append(sample)

        assert samples, "No batch samples collected"
        duration_samples = sorted(float(sample["duration_ms"]) for sample in samples)
        memory_samples = sorted(float(sample["memory_peak_mb"]) for sample in samples)
        cpu_samples = [float(sample["cpu_percent"]) for sample in samples]
        median_index = len(samples) // 2

        result = {
            "success": True,
            "duration_ms": duration_samples[median_index],
            "memory_peak_mb": memory_samples[median_index],
            "cpu_percent": sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0.0,
            "stderr": "",
        }

        # Calculate metrics
        total_size_kb = sum(f.stat().st_size / 1024 for f in test_files)
        files_per_second = (
            len(test_files) / (result["duration_ms"] / 1000) if result["duration_ms"] > 0 else 0
        )

        # Create benchmark
        benchmark = BenchmarkResult(
            operation=f"cli_batch_{workers}workers",
            duration_ms=result["duration_ms"],
            memory_mb=result["memory_peak_mb"],
            file_size_kb=total_size_kb,
            throughput=files_per_second,
            timestamp=datetime.now().isoformat(),
            metadata={
                "num_files": len(test_files),
                "workers": workers,
                "cpu_percent": result["cpu_percent"],
                "ms_per_file": result["duration_ms"] / len(test_files),
            },
        )

        # Assert performance
        expected_time = BATCH_FILE_TARGET_MS * len(test_files)
        assert_performance_target(
            result["duration_ms"], expected_time, f"Batch with {workers} workers", tolerance=1.0
        )
        assert_memory_limit(
            result["memory_peak_mb"], BATCH_MEMORY_MB, f"Batch with {workers} workers"
        )

        # Log results
        print(f"\n{'='*60}")
        print(f"CLI Batch Processing Benchmark ({workers} workers):")
        print(f"  Files: {len(test_files)} ({total_size_kb:.2f} KB total)")
        print(f"  Duration: {result['duration_ms']:.2f} ms ({result['duration_ms']/1000:.2f}s)")
        print(f"  Memory: {result['memory_peak_mb']:.2f} MB")
        print(f"  CPU: {result['cpu_percent']:.1f}%")
        print(f"  Throughput: {files_per_second:.2f} files/s")
        print(f"  Per File: {result['duration_ms'] / len(test_files):.2f} ms/file")
        print(
            "  Sample Durations: "
            + ", ".join(f"{sample['duration_ms']:.2f}ms" for sample in samples)
        )
        print(f"{'='*60}")

        operation = f"cli_batch_{workers}workers"
        _assert_cli_no_regression(operation, benchmark, production_baseline_manager)
        _persist_baseline_if_requested(operation, benchmark, production_baseline_manager)

        # Cleanup
        shutil.rmtree(output_dir, ignore_errors=True)
        shutil.rmtree(batch_input_dir, ignore_errors=True)


# ============================================================================
# Thread Safety Stress Tests
# ============================================================================


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.cli
class TestThreadSafetyStress:
    """Stress tests for thread safety and concurrency."""

    def test_cli_high_concurrency_stress(
        self, fixture_dir: Path, production_baseline_manager, tmp_path: Path
    ):
        """Stress test with maximum workers and many files."""
        # Reuse broad corpus for more representative concurrency stress.
        test_files = _representative_batch_files(fixture_dir, max_files=30, coverage_lite=True)

        if len(test_files) < 10:
            pytest.skip("Not enough test files for stress test")

        import shutil  # noqa: E402

        # Create output directory
        output_dir = tmp_path / "stress_output"
        stress_input_dir = tmp_path / "stress_input"
        shutil.rmtree(output_dir, ignore_errors=True)
        shutil.rmtree(stress_input_dir, ignore_errors=True)
        output_dir.mkdir(exist_ok=True)
        stress_input_dir.mkdir(exist_ok=True)

        for test_file in test_files:
            shutil.copy2(test_file, stress_input_dir / test_file.name)

        # Run with maximum workers
        result = run_cli_command(
            [
                "batch",
                str(stress_input_dir),
                "--output",
                str(output_dir),
                "--workers",
                "16",
                "--quiet",
            ],
            timeout=600,
        )

        # Verify success (no deadlocks or hangs)
        assert result["success"], f"Stress test failed: {result['stderr']}"

        # Verify all files processed
        output_files = list(output_dir.glob("*.json"))
        assert len(output_files) >= len(test_files), "Not all files processed"

        # Create benchmark
        total_size_kb = sum(f.stat().st_size / 1024 for f in test_files)
        benchmark = BenchmarkResult(
            operation="cli_stress_high_concurrency",
            duration_ms=result["duration_ms"],
            memory_mb=result["memory_peak_mb"],
            file_size_kb=total_size_kb,
            throughput=(
                len(test_files) / (result["duration_ms"] / 1000) if result["duration_ms"] > 0 else 0
            ),
            timestamp=datetime.now().isoformat(),
            metadata={
                "num_files": len(test_files),
                "workers": 16,
                "cpu_percent": result["cpu_percent"],
                "output_files": len(output_files),
            },
        )

        # Log results
        print(f"\n{'='*60}")
        print("CLI High Concurrency Stress Test:")
        print(f"  Files: {len(test_files)}")
        print("  Workers: 16 (maximum)")
        print(f"  Duration: {result['duration_ms']:.2f} ms ({result['duration_ms']/1000:.2f}s)")
        print(f"  Memory: {result['memory_peak_mb']:.2f} MB")
        print(f"  CPU: {result['cpu_percent']:.1f}%")
        print(f"  Throughput: {benchmark.throughput:.2f} files/s")
        print(f"  Output Files: {len(output_files)}/{len(test_files)}")
        print(f"  Status: {'PASS - No deadlocks' if result['success'] else 'FAIL'}")
        print(f"{'='*60}")

        _assert_cli_no_regression(
            "cli_stress_high_concurrency", benchmark, production_baseline_manager
        )
        _persist_baseline_if_requested(
            "cli_stress_high_concurrency", benchmark, production_baseline_manager
        )

        # Cleanup
        shutil.rmtree(output_dir, ignore_errors=True)
        shutil.rmtree(stress_input_dir, ignore_errors=True)


# ============================================================================
# Progress Display Overhead Tests
# ============================================================================


@pytest.mark.performance
@pytest.mark.cli
class TestProgressDisplayOverhead:
    """Measure overhead of progress display."""

    def test_progress_vs_quiet_overhead(
        self, fixture_dir: Path, production_baseline_manager, tmp_path: Path
    ):
        """Compare performance with and without progress display."""
        test_file = fixture_dir / "sample.txt"

        if not test_file.exists():
            pytest.skip(f"Test file not found: {test_file}")

        progress_output = tmp_path / "output_progress.json"
        quiet_output = tmp_path / "output_quiet.json"

        # Run with progress (default)
        result_with_progress = run_cli_command(
            ["extract", str(test_file), "--output", str(progress_output)]
        )

        # Run with quiet mode
        result_quiet = run_cli_command(
            ["extract", str(test_file), "--output", str(quiet_output), "--quiet"]
        )

        assert result_with_progress[
            "success"
        ], f"Progress run failed: {result_with_progress['stderr']}"
        assert result_quiet["success"], f"Quiet run failed: {result_quiet['stderr']}"

        # Calculate overhead
        raw_overhead_ms = result_with_progress["duration_ms"] - result_quiet["duration_ms"]
        raw_overhead_pct = (
            (raw_overhead_ms / result_quiet["duration_ms"]) * 100
            if result_quiet["duration_ms"] > 0
            else 0
        )

        # Keep baseline metrics non-negative so baseline comparisons stay valid.
        overhead_ms = max(0.0, raw_overhead_ms)
        overhead_pct = max(0.0, raw_overhead_pct)

        # Create benchmark
        benchmark = BenchmarkResult(
            operation="cli_progress_overhead",
            duration_ms=overhead_ms,
            memory_mb=0.0,
            file_size_kb=test_file.stat().st_size / 1024,
            throughput=0.0,
            timestamp=datetime.now().isoformat(),
            metadata={
                "with_progress_ms": result_with_progress["duration_ms"],
                "quiet_ms": result_quiet["duration_ms"],
                "overhead_pct": overhead_pct,
            },
        )

        # Assert overhead is acceptable
        assert (
            overhead_pct < PROGRESS_OVERHEAD_MAX_PCT
        ), f"Progress overhead {overhead_pct:.1f}% exceeds limit of {PROGRESS_OVERHEAD_MAX_PCT}%"

        # Log results
        print(f"\n{'='*60}")
        print("Progress Display Overhead Test:")
        print(f"  With Progress: {result_with_progress['duration_ms']:.2f} ms")
        print(f"  Quiet Mode: {result_quiet['duration_ms']:.2f} ms")
        print(f"  Raw Delta: {raw_overhead_ms:.2f} ms ({raw_overhead_pct:.1f}%)")
        print(f"  Overhead: {overhead_ms:.2f} ms ({overhead_pct:.1f}%)")
        print(f"  Limit: {PROGRESS_OVERHEAD_MAX_PCT}%")
        print(f"  Status: {'PASS' if overhead_pct < PROGRESS_OVERHEAD_MAX_PCT else 'FAIL'}")
        print(f"{'='*60}")

        _assert_cli_no_regression("cli_progress_overhead", benchmark, production_baseline_manager)
        _persist_baseline_if_requested(
            "cli_progress_overhead", benchmark, production_baseline_manager
        )


# ============================================================================
# Encoding Performance Tests
# ============================================================================


@pytest.mark.performance
@pytest.mark.cli
class TestEncodingPerformance:
    """Test encoding and Unicode performance."""

    def test_unicode_heavy_content(
        self, fixture_dir: Path, production_baseline_manager, tmp_path: Path
    ):
        """Test performance with Unicode-heavy content."""
        # Use a file with lots of special characters (using complex_text as proxy)
        test_file = fixture_dir / "quality_test_documents" / "complex_text.txt"

        if not test_file.exists():
            pytest.skip(f"Test file not found: {test_file}")

        # Run CLI command
        result = run_cli_command(
            [
                "extract",
                str(test_file),
                "--output",
                str(tmp_path / "unicode_output.md"),
                "--quiet",
            ]
        )

        # Verify success
        assert result["success"], f"Unicode test failed: {result['stderr']}"

        # Create benchmark
        file_size_kb = test_file.stat().st_size / 1024
        benchmark = BenchmarkResult(
            operation="cli_unicode_encoding",
            duration_ms=result["duration_ms"],
            memory_mb=result["memory_peak_mb"],
            file_size_kb=file_size_kb,
            throughput=(
                file_size_kb / (result["duration_ms"] / 1000) if result["duration_ms"] > 0 else 0
            ),
            timestamp=datetime.now().isoformat(),
            metadata={"file_name": test_file.name, "cpu_percent": result["cpu_percent"]},
        )

        # Assert performance
        assert_performance_target(result["duration_ms"], SINGLE_FILE_TARGET_MS, "Unicode encoding")

        # Log results
        print(f"\n{'='*60}")
        print("Unicode Encoding Performance Test:")
        print(f"  File: {test_file.name} ({file_size_kb:.2f} KB)")
        print(f"  Duration: {result['duration_ms']:.2f} ms ({result['duration_ms']/1000:.2f}s)")
        print(f"  Memory: {result['memory_peak_mb']:.2f} MB")
        print(f"  CPU: {result['cpu_percent']:.1f}%")
        print(f"  Throughput: {benchmark.throughput:.2f} KB/s")
        print(f"{'='*60}")

        _assert_cli_no_regression("cli_unicode_encoding", benchmark, production_baseline_manager)
        _persist_baseline_if_requested(
            "cli_unicode_encoding", benchmark, production_baseline_manager
        )
