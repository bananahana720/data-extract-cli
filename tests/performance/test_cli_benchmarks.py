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

import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from datetime import datetime  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any, Dict, List  # noqa: E402

import psutil  # noqa: E402
import pytest  # noqa: E402

from tests.performance.conftest import (  # noqa: E402
    BenchmarkResult,
    assert_memory_limit,
    assert_performance_target,
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


# ============================================================================
# Helper Functions
# ============================================================================


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

    # Start process
    process = subprocess.Popen(
        full_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Monitor resources if requested
    peak_memory_mb = 0.0
    cpu_samples = []

    if measure_resources:
        try:
            psutil_process = psutil.Process(process.pid)

            # Sample every 0.1 seconds
            while process.poll() is None:
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
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()

    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000

    return {
        "success": process.returncode == 0,
        "duration_ms": duration_ms,
        "memory_peak_mb": peak_memory_mb,
        "cpu_percent": sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0.0,
        "stdout": stdout,
        "stderr": stderr,
        "returncode": process.returncode,
    }


def get_test_files(fixture_dir: Path, pattern: str, limit: int = None) -> List[Path]:
    """Get test files matching pattern."""
    files = list(fixture_dir.rglob(pattern))
    if limit:
        files = files[:limit]
    return files


# ============================================================================
# Single File Performance Tests
# ============================================================================


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.cli
class TestSingleFilePerformance:
    """Performance benchmarks for single file extraction via CLI."""

    def test_cli_txt_extraction_performance(self, fixture_dir: Path, production_baseline_manager):
        """Benchmark CLI TXT file extraction."""
        txt_file = fixture_dir / "sample.txt"

        if not txt_file.exists():
            pytest.skip(f"Test file not found: {txt_file}")

        # Run CLI command
        result = run_cli_command(
            ["extract", str(txt_file), "--output", str(fixture_dir / "output.md"), "--quiet"]
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

        # Save baseline
        production_baseline_manager.update_baseline("cli_extract_txt", benchmark)
        production_baseline_manager.save()

    def test_cli_pdf_extraction_performance(self, fixture_dir: Path, production_baseline_manager):
        """Benchmark CLI PDF file extraction."""
        pdf_file = (
            fixture_dir
            / "real_world_files"
            / "COBIT-2019-Framework-Introduction-and-Methodology_res_eng_1118.pdf"
        )

        if not pdf_file.exists():
            pytest.skip(f"Test file not found: {pdf_file}")

        # Run CLI command
        result = run_cli_command(
            ["extract", str(pdf_file), "--output", str(fixture_dir / "output.md"), "--quiet"],
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
        assert_memory_limit(result["memory_peak_mb"], SINGLE_FILE_MEMORY_MB, "CLI PDF extraction")

        # Log results
        print(f"\n{'='*60}")
        print("CLI PDF Extraction Benchmark:")
        print(f"  File: {pdf_file.name} ({file_size_kb:.2f} KB)")
        print(f"  Duration: {result['duration_ms']:.2f} ms ({result['duration_ms']/1000:.2f}s)")
        print(f"  Memory: {result['memory_peak_mb']:.2f} MB")
        print(f"  CPU: {result['cpu_percent']:.1f}%")
        print(f"  Throughput: {benchmark.throughput:.2f} KB/s")
        print(f"{'='*60}")

        # Save baseline
        production_baseline_manager.update_baseline("cli_extract_pdf", benchmark)
        production_baseline_manager.save()


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
        self, fixture_dir: Path, workers: int, production_baseline_manager
    ):
        """Benchmark batch processing with different worker counts."""
        # Get deterministic test files (mix of formats) without recursive drift.
        test_files = [
            file_path
            for file_path in [
                fixture_dir / "sample.txt",
                fixture_dir / "quality_test_documents" / "complex_text.txt",
                fixture_dir / "quality_test_documents" / "simple_text.txt",
            ]
            if file_path.exists()
        ]
        test_files.extend(get_test_files(fixture_dir / "excel", "*.xlsx", limit=2))

        if len(test_files) < 3:
            pytest.skip("Not enough test files for batch test")

        import shutil  # noqa: E402

        # Create temporary output directory
        output_dir = fixture_dir / f"batch_output_{workers}workers"
        batch_input_dir = fixture_dir / f"batch_input_{workers}workers"
        shutil.rmtree(output_dir, ignore_errors=True)
        shutil.rmtree(batch_input_dir, ignore_errors=True)
        output_dir.mkdir(exist_ok=True)
        batch_input_dir.mkdir(exist_ok=True)

        for test_file in test_files:
            shutil.copy2(test_file, batch_input_dir / test_file.name)

        # Run batch command
        result = run_cli_command(
            [
                "batch",
                str(batch_input_dir),
                "--output",
                str(output_dir),
                "--workers",
                str(workers),
                "--quiet",
            ],
            timeout=300,
        )

        # Verify success
        assert result["success"], f"Batch failed: {result['stderr']}"

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
        # `--workers` is currently a compatibility hint in the CLI and may run serially.
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
        print(f"{'='*60}")

        # Save baseline
        production_baseline_manager.update_baseline(f"cli_batch_{workers}workers", benchmark)
        production_baseline_manager.save()

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

    def test_cli_high_concurrency_stress(self, fixture_dir: Path, production_baseline_manager):
        """Stress test with maximum workers and many files."""
        # Get deterministic stress corpus without recursively including generated dirs.
        quality_docs = sorted((fixture_dir / "quality_test_documents").glob("*.txt"))
        test_files = [fixture_dir / "sample.txt", *quality_docs][:10]
        test_files = [file_path for file_path in test_files if file_path.exists()]

        if len(test_files) < 5:
            pytest.skip("Not enough test files for stress test")

        import shutil  # noqa: E402

        # Create output directory
        output_dir = fixture_dir / "stress_output"
        stress_input_dir = fixture_dir / "stress_input"
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

        # Save baseline
        production_baseline_manager.update_baseline("cli_stress_high_concurrency", benchmark)
        production_baseline_manager.save()

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
        overhead_ms = result_with_progress["duration_ms"] - result_quiet["duration_ms"]
        overhead_pct = (
            (overhead_ms / result_quiet["duration_ms"]) * 100
            if result_quiet["duration_ms"] > 0
            else 0
        )

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
        print(f"  Overhead: {overhead_ms:.2f} ms ({overhead_pct:.1f}%)")
        print(f"  Limit: {PROGRESS_OVERHEAD_MAX_PCT}%")
        print(f"  Status: {'PASS' if overhead_pct < PROGRESS_OVERHEAD_MAX_PCT else 'FAIL'}")
        print(f"{'='*60}")

        # Save baseline
        production_baseline_manager.update_baseline("cli_progress_overhead", benchmark)
        production_baseline_manager.save()


# ============================================================================
# Encoding Performance Tests
# ============================================================================


@pytest.mark.performance
@pytest.mark.cli
class TestEncodingPerformance:
    """Test encoding and Unicode performance."""

    def test_unicode_heavy_content(self, fixture_dir: Path, production_baseline_manager):
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
                str(fixture_dir / "unicode_output.md"),
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

        # Save baseline
        production_baseline_manager.update_baseline("cli_unicode_encoding", benchmark)
        production_baseline_manager.save()
