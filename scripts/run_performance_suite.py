"""
Comprehensive Performance Benchmark Suite.

Runs all performance tests and generates a detailed report.
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from performance_catalog import RUN_PERFORMANCE_SUITE_NODEIDS

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_command(cmd: List[str], timeout: int = 600) -> Dict[str, Any]:
    """Run command and capture result."""
    print(f"\n{'='*70}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*70}\n")

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=PROJECT_ROOT,
        )

        duration = time.time() - start_time

        return {
            "success": result.returncode == 0,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "duration": timeout,
            "stdout": "",
            "stderr": "TIMEOUT",
            "returncode": -1,
        }


def parse_baseline_file(baseline_path: Path) -> Dict[str, Any]:
    """Parse baselines.json file."""
    if not baseline_path.exists():
        return {}

    try:
        with open(baseline_path, "r") as f:
            data = json.load(f)
            return data.get("baselines", {})
    except Exception as e:
        print(f"Error reading baselines: {e}")
        return {}


def main():
    """Run comprehensive performance benchmarks."""

    print(
        """
======================================================================

          CLI Performance Benchmark Suite - v1.0

  Tests: Single File, Batch Processing, Thread Safety, Overhead

======================================================================
    """
    )

    baseline_path = Path("tests/performance/baselines.json")
    results = []

    # ========================================================================
    # Test Suite 1: Extractor Benchmarks (Lightweight)
    # ========================================================================

    print("\n" + "=" * 70)
    print("TEST SUITE 1: EXTRACTOR PERFORMANCE BENCHMARKS")
    print("=" * 70)

    extractor_tests = list(RUN_PERFORMANCE_SUITE_NODEIDS["extractors"])

    for test in extractor_tests:
        result = run_command(
            [sys.executable, "-m", "pytest", test, "-v", "-s", "--tb=short"], timeout=120
        )

        results.append({"test": test.split("::")[-1], "suite": "extractors", "result": result})

        if not result["success"]:
            print("\n[!] WARNING: Test failed or had issues\n")

    # ========================================================================
    # Test Suite 2: Pipeline Benchmarks
    # ========================================================================

    print("\n" + "=" * 70)
    print("TEST SUITE 2: PIPELINE PERFORMANCE BENCHMARKS")
    print("=" * 70)

    pipeline_tests = list(RUN_PERFORMANCE_SUITE_NODEIDS["pipeline"])

    for test in pipeline_tests:
        result = run_command(
            [sys.executable, "-m", "pytest", test, "-v", "-s", "--tb=short"], timeout=120
        )

        results.append({"test": test.split("::")[-1], "suite": "pipeline", "result": result})

        if not result["success"]:
            print("\n[!] WARNING: Test failed or had issues\n")

    # ========================================================================
    # Test Suite 3: CLI Benchmarks (NEW)
    # ========================================================================

    print("\n" + "=" * 70)
    print("TEST SUITE 3: CLI PERFORMANCE BENCHMARKS")
    print("=" * 70)

    cli_tests = list(RUN_PERFORMANCE_SUITE_NODEIDS["cli"])

    for test in cli_tests:
        result = run_command(
            [sys.executable, "-m", "pytest", test, "-v", "-s", "--tb=short"], timeout=120
        )

        results.append({"test": test.split("::")[-1], "suite": "cli", "result": result})

        if not result["success"]:
            print("\n[!] WARNING: Test failed or had issues\n")

    # ========================================================================
    # Load and Display Baselines
    # ========================================================================

    print("\n" + "=" * 70)
    print("PERFORMANCE BASELINES SUMMARY")
    print("=" * 70)

    baselines = parse_baseline_file(baseline_path)

    if baselines:
        print(f"\nFound {len(baselines)} baseline measurements:\n")

        for operation, data in sorted(baselines.items()):
            duration_ms = data.get("duration_ms", 0)
            memory_mb = data.get("memory_mb", 0)
            throughput = data.get("throughput", 0)

            print(
                f"  {operation:40s}  {duration_ms:8.2f} ms  {memory_mb:7.2f} MB  {throughput:10.2f} /s"
            )
    else:
        print("\n⚠️  No baselines found. Run benchmarks to establish baselines.\n")

    # ========================================================================
    # Summary Report
    # ========================================================================

    print("\n" + "=" * 70)
    print("BENCHMARK EXECUTION SUMMARY")
    print("=" * 70)

    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["result"]["success"])
    failed_tests = total_tests - passed_tests

    print(f"\nTotal Tests Run: {total_tests}")
    print(f"  [OK] Passed: {passed_tests}")
    print(f"  [X] Failed: {failed_tests}")

    print("\n" + "-" * 70)
    print("Test Results by Suite:")
    print("-" * 70 + "\n")

    for suite in ["extractors", "pipeline", "cli"]:
        suite_results = [r for r in results if r["suite"] == suite]
        suite_passed = sum(1 for r in suite_results if r["result"]["success"])

        status = "[OK] PASS" if suite_passed == len(suite_results) else "[!] SOME FAILURES"
        print(f"  {suite.upper():15s}  {suite_passed}/{len(suite_results)} passed  {status}")

    # ========================================================================
    # Failed Tests Details
    # ========================================================================

    if failed_tests > 0:
        print("\n" + "=" * 70)
        print("FAILED TESTS DETAILS")
        print("=" * 70 + "\n")

        for r in results:
            if not r["result"]["success"]:
                print(f"\n[X] {r['test']}")
                print(f"   Suite: {r['suite']}")
                print(f"   Return Code: {r['result']['returncode']}")

                if r["result"]["stderr"]:
                    print("\n   Error Output:")
                    error_lines = r["result"]["stderr"].split("\n")[:10]
                    for line in error_lines:
                        print(f"     {line}")

    # ========================================================================
    # Performance Metrics
    # ========================================================================

    print("\n" + "=" * 70)
    print("PERFORMANCE TARGETS COMPLIANCE")
    print("=" * 70 + "\n")

    print("Performance Targets (from requirements):")
    print("  - Text extraction: <2s per MB")
    print("  - OCR extraction: <15s per page")
    print("  - Memory: <500MB per file, <2GB batch")
    print("  - Quality: 98% native text, 85% OCR")
    print()

    if baselines:
        print("Compliance Status:")

        # Check text extraction speed
        txt_benchmarks = {k: v for k, v in baselines.items() if "txt" in k.lower()}
        if txt_benchmarks:
            for name, data in txt_benchmarks.items():
                duration_s = data.get("duration_ms", 0) / 1000
                file_size_mb = data.get("file_size_kb", 0) / 1024

                if file_size_mb > 0:
                    s_per_mb = duration_s / file_size_mb
                    status = "[OK] PASS" if s_per_mb < 2.0 else "[X] FAIL"
                    print(f"  {name:40s}  {s_per_mb:6.2f} s/MB  {status}")

        # Check memory usage
        print("\nMemory Usage:")
        for name, data in baselines.items():
            memory_mb = data.get("memory_mb", 0)

            # Determine limit based on operation type
            if "batch" in name.lower():
                limit_mb = 2000
            else:
                limit_mb = 500

            status = "[OK] PASS" if memory_mb < limit_mb else "[X] FAIL"
            print(f"  {name:40s}  {memory_mb:7.2f} MB  (limit: {limit_mb}MB)  {status}")

    # ========================================================================
    # Final Status
    # ========================================================================

    print("\n" + "=" * 70)

    if failed_tests == 0:
        print("[OK] ALL BENCHMARKS PASSED")
        exit_code = 0
    else:
        print(f"[!] {failed_tests} BENCHMARKS FAILED OR HAD ISSUES")
        exit_code = 1

    print("=" * 70 + "\n")

    print(f"Baseline file: {baseline_path}")
    print(f"Report generated: {datetime.now().isoformat()}")
    print()

    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
