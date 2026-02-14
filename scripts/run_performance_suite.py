"""
Comprehensive Performance Benchmark Suite.

Runs all performance tests and generates a detailed report.
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from performance_catalog import (
    RUN_PERFORMANCE_SUITE_ALL_SUITES,
    RUN_PERFORMANCE_SUITE_API_RUNTIME_SELECTORS,
    RUN_PERFORMANCE_SUITE_DEFAULT_SUITES,
    RUN_PERFORMANCE_SUITE_NODEIDS,
)

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


def _parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run performance benchmark suites")
    parser.add_argument(
        "--suites",
        nargs="+",
        choices=list(RUN_PERFORMANCE_SUITE_ALL_SUITES),
        default=list(RUN_PERFORMANCE_SUITE_DEFAULT_SUITES),
        help="Suite selectors to execute",
    )
    parser.add_argument(
        "--test-timeout",
        type=int,
        default=120,
        help="Timeout in seconds for each pytest selector execution",
    )
    parser.add_argument(
        "--api-base-url",
        default="http://127.0.0.1:8000",
        help="API base URL for api_runtime suite",
    )
    parser.add_argument(
        "--api-concurrency",
        type=int,
        default=8,
        help="Concurrency for api_runtime load checks",
    )
    parser.add_argument(
        "--api-duration-seconds",
        type=float,
        default=15.0,
        help="Duration for each api_runtime load check",
    )
    parser.add_argument(
        "--api-timeout-seconds",
        type=float,
        default=5.0,
        help="Per-request timeout for api_runtime checks",
    )
    parser.add_argument(
        "--api-warmup-requests",
        type=int,
        default=3,
        help="Warmup requests before each api_runtime load check",
    )
    parser.add_argument(
        "--api-max-error-rate-pct",
        type=float,
        default=0.0,
        help="Maximum allowed error rate for api_runtime checks",
    )
    parser.add_argument(
        "--api-max-p95-latency-ms",
        type=float,
        default=None,
        help="Optional p95 latency threshold for api_runtime checks",
    )
    parser.add_argument(
        "--api-min-rps",
        type=float,
        default=None,
        help="Optional minimum requests/sec threshold for api_runtime checks",
    )
    parser.add_argument(
        "--api-output-dir",
        type=Path,
        default=None,
        help="Optional directory for per-selector api_runtime JSON reports",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional path for the consolidated suite JSON report",
    )
    return parser.parse_args(argv)


def _run_pytest_suite(
    suite_name: str,
    selector_tests: list[str],
    *,
    timeout_seconds: int,
    results: list[dict[str, Any]],
) -> None:
    print("\n" + "=" * 70)
    print(f"TEST SUITE: {suite_name.upper()} PERFORMANCE BENCHMARKS")
    print("=" * 70)

    for test in selector_tests:
        result = run_command(
            [sys.executable, "-m", "pytest", test, "-v", "-s", "--tb=short"],
            timeout=timeout_seconds,
        )
        results.append({"test": test.split("::")[-1], "suite": suite_name, "result": result})
        if not result["success"]:
            print("\n[!] WARNING: Test failed or had issues\n")


def _api_result_path(output_dir: Path | None, selector_name: str) -> Path | None:
    if output_dir is None:
        return None
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = selector_name.replace("/", "_").replace("?", "_").replace("&", "_")
    return output_dir / f"api_runtime_{safe_name}.json"


def _run_api_runtime_suite(args: argparse.Namespace, results: list[dict[str, Any]]) -> None:
    print("\n" + "=" * 70)
    print("TEST SUITE: API_RUNTIME PERFORMANCE BENCHMARKS")
    print("=" * 70)

    runner = PROJECT_ROOT / "scripts" / "run_api_load.py"
    base_timeout = int(max(30.0, args.api_duration_seconds + 20.0))

    for selector_name, endpoint in RUN_PERFORMANCE_SUITE_API_RUNTIME_SELECTORS:
        cmd = [
            sys.executable,
            str(runner),
            "--name",
            selector_name,
            "--base-url",
            str(args.api_base_url),
            "--endpoint",
            endpoint,
            "--concurrency",
            str(max(1, int(args.api_concurrency))),
            "--duration-seconds",
            str(max(0.1, float(args.api_duration_seconds))),
            "--timeout-seconds",
            str(max(0.1, float(args.api_timeout_seconds))),
            "--warmup-requests",
            str(max(0, int(args.api_warmup_requests))),
            "--max-error-rate-pct",
            str(float(args.api_max_error_rate_pct)),
        ]

        if args.api_max_p95_latency_ms is not None:
            cmd.extend(["--max-p95-latency-ms", str(float(args.api_max_p95_latency_ms))])
        if args.api_min_rps is not None:
            cmd.extend(["--min-rps", str(float(args.api_min_rps))])

        selector_output = _api_result_path(args.api_output_dir, selector_name)
        if selector_output is not None:
            cmd.extend(["--output-json", str(selector_output)])

        result = run_command(cmd, timeout=base_timeout)
        results.append(
            {
                "test": selector_name,
                "suite": "api_runtime",
                "selector": endpoint,
                "result": result,
                "json_output": None if selector_output is None else str(selector_output),
            }
        )
        if not result["success"]:
            print("\n[!] WARNING: API runtime load check failed or had issues\n")


def _write_json_report(
    *,
    output_path: Path,
    selected_suites: list[str],
    results: list[dict[str, Any]],
    baselines: dict[str, Any],
) -> None:
    payload = {
        "generated_at": datetime.now().isoformat(),
        "selected_suites": selected_suites,
        "total_results": len(results),
        "passed_results": sum(1 for item in results if bool(item["result"]["success"])),
        "failed_results": sum(1 for item in results if not bool(item["result"]["success"])),
        "results": results,
        "baseline_summary": baselines,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main(argv: list[str] | None = None):
    """Run comprehensive performance benchmarks."""
    args = _parse_arguments([] if argv is None else argv)
    selected_suites = list(args.suites)

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

    for suite in selected_suites:
        if suite in RUN_PERFORMANCE_SUITE_NODEIDS:
            _run_pytest_suite(
                suite,
                list(RUN_PERFORMANCE_SUITE_NODEIDS[suite]),
                timeout_seconds=max(1, int(args.test_timeout)),
                results=results,
            )
            continue
        if suite == "api_runtime":
            _run_api_runtime_suite(args, results)
            continue

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

    for suite in selected_suites:
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
    if args.output_json is not None:
        _write_json_report(
            output_path=args.output_json,
            selected_suites=selected_suites,
            results=results,
            baselines=baselines,
        )
        print(f"JSON report: {args.output_json}")
    print()

    return exit_code


if __name__ == "__main__":
    exit_code = main(sys.argv[1:])
    sys.exit(exit_code)
