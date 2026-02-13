"""Measure CLI progress-display overhead using current greenfield command paths."""

from __future__ import annotations

import argparse
import glob
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

TARGET_OVERHEAD_PCT = 3.0
CLI_COMMAND = [sys.executable, "-m", "data_extract.cli"]


def run_cli(args: list[str], timeout_s: int = 300) -> dict[str, Any]:
    """Run a CLI command and return timing/result metadata."""
    command = CLI_COMMAND + args
    start = time.perf_counter()
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout_s,
    )
    duration_ms = (time.perf_counter() - start) * 1000
    return {
        "success": result.returncode == 0,
        "duration_ms": duration_ms,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }


def _stats(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return values[0], 0.0
    return statistics.mean(values), statistics.stdev(values)


def measure_single_file(file_path: Path, iterations: int = 5) -> dict[str, Any]:
    """Measure extract overhead for one file."""
    with tempfile.TemporaryDirectory(prefix="progress-overhead-single-") as tmpdir:
        tmp = Path(tmpdir)
        baseline_times: list[float] = []
        progress_times: list[float] = []

        for i in range(iterations):
            quiet_out = tmp / f"quiet-{i}.json"
            progress_out = tmp / f"progress-{i}.json"

            quiet = run_cli(
                [
                    "extract",
                    str(file_path),
                    "--output",
                    str(quiet_out),
                    "--quiet",
                ]
            )
            if not quiet["success"]:
                raise RuntimeError(f"quiet extract failed: {quiet['stderr']}")
            baseline_times.append(float(quiet["duration_ms"]))

            progress = run_cli(
                [
                    "extract",
                    str(file_path),
                    "--output",
                    str(progress_out),
                ]
            )
            if not progress["success"]:
                raise RuntimeError(f"progress extract failed: {progress['stderr']}")
            progress_times.append(float(progress["duration_ms"]))

    baseline_mean, baseline_std = _stats(baseline_times)
    progress_mean, progress_std = _stats(progress_times)
    overhead_ms = progress_mean - baseline_mean
    overhead_pct = (overhead_ms / baseline_mean * 100.0) if baseline_mean > 0 else 0.0

    return {
        "mode": "single",
        "file": file_path.name,
        "iterations": iterations,
        "baseline_mean_ms": baseline_mean,
        "baseline_std_ms": baseline_std,
        "progress_mean_ms": progress_mean,
        "progress_std_ms": progress_std,
        "overhead_ms": overhead_ms,
        "overhead_pct": overhead_pct,
    }


def measure_batch_files(
    file_paths: list[Path], workers: int = 4, iterations: int = 3
) -> dict[str, Any]:
    """Measure batch overhead for a set of files."""
    with tempfile.TemporaryDirectory(prefix="progress-overhead-batch-") as tmpdir:
        tmp = Path(tmpdir)
        source_dir = tmp / "source"
        source_dir.mkdir(parents=True, exist_ok=True)

        for file_path in file_paths:
            shutil.copy2(file_path, source_dir / file_path.name)

        baseline_times: list[float] = []
        progress_times: list[float] = []

        for i in range(iterations):
            quiet_out = tmp / f"quiet-out-{i}"
            progress_out = tmp / f"progress-out-{i}"
            quiet_out.mkdir(parents=True, exist_ok=True)
            progress_out.mkdir(parents=True, exist_ok=True)

            quiet = run_cli(
                [
                    "batch",
                    str(source_dir),
                    "--output",
                    str(quiet_out),
                    "--workers",
                    str(workers),
                    "--quiet",
                ],
                timeout_s=600,
            )
            if not quiet["success"]:
                raise RuntimeError(f"quiet batch failed: {quiet['stderr']}")
            baseline_times.append(float(quiet["duration_ms"]))

            progress = run_cli(
                [
                    "batch",
                    str(source_dir),
                    "--output",
                    str(progress_out),
                    "--workers",
                    str(workers),
                ],
                timeout_s=600,
            )
            if not progress["success"]:
                raise RuntimeError(f"progress batch failed: {progress['stderr']}")
            progress_times.append(float(progress["duration_ms"]))

    baseline_mean, baseline_std = _stats(baseline_times)
    progress_mean, progress_std = _stats(progress_times)
    overhead_ms = progress_mean - baseline_mean
    overhead_pct = (overhead_ms / baseline_mean * 100.0) if baseline_mean > 0 else 0.0

    return {
        "mode": "batch",
        "file_count": len(file_paths),
        "workers": workers,
        "iterations": iterations,
        "baseline_mean_ms": baseline_mean,
        "baseline_std_ms": baseline_std,
        "progress_mean_ms": progress_mean,
        "progress_std_ms": progress_std,
        "overhead_ms": overhead_ms,
        "overhead_pct": overhead_pct,
    }


def print_report(single_result: dict[str, Any] | None, batch_result: dict[str, Any] | None) -> None:
    """Render human-readable measurement report."""
    print("\n" + "=" * 70)
    print("PROGRESS DISPLAY PERFORMANCE REPORT")
    print("=" * 70)

    if single_result:
        print("\nSINGLE FILE RESULTS:")
        print("-" * 70)
        print(f"File: {single_result['file']}")
        print(f"Iterations: {single_result['iterations']}")
        print(
            f"Baseline: {single_result['baseline_mean_ms']:.2f}ms ± "
            f"{single_result['baseline_std_ms']:.2f}ms"
        )
        print(
            f"With Progress: {single_result['progress_mean_ms']:.2f}ms ± "
            f"{single_result['progress_std_ms']:.2f}ms"
        )
        print(
            f"Overhead: {single_result['overhead_ms']:.2f}ms "
            f"({single_result['overhead_pct']:.2f}%)"
        )

    if batch_result:
        print("\nBATCH RESULTS:")
        print("-" * 70)
        print(
            f"Files: {batch_result['file_count']} | Workers: {batch_result['workers']} | "
            f"Iterations: {batch_result['iterations']}"
        )
        print(
            f"Baseline: {batch_result['baseline_mean_ms']:.2f}ms ± "
            f"{batch_result['baseline_std_ms']:.2f}ms"
        )
        print(
            f"With Progress: {batch_result['progress_mean_ms']:.2f}ms ± "
            f"{batch_result['progress_std_ms']:.2f}ms"
        )
        print(
            f"Overhead: {batch_result['overhead_ms']:.2f}ms "
            f"({batch_result['overhead_pct']:.2f}%)"
        )

    print("\n" + "=" * 70)
    print(f"TARGET: <{TARGET_OVERHEAD_PCT:.1f}% overhead")
    print("=" * 70)


def _expand_glob(glob_pattern: str) -> list[Path]:
    return [Path(p) for p in sorted(glob.glob(glob_pattern))]


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure progress display overhead")
    parser.add_argument("--file", type=str, help="Single file to test")
    parser.add_argument(
        "--files",
        type=str,
        help='Glob pattern for batch testing (e.g., "tests/fixtures/*.pdf")',
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of iterations for single-file test (default: 5)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of workers for batch test (default: 4)",
    )

    args = parser.parse_args()

    if not args.file and not args.files:
        print("ERROR: Must specify --file or --files")
        return 1

    single_result: dict[str, Any] | None = None
    batch_result: dict[str, Any] | None = None

    try:
        if args.file:
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"ERROR: File not found: {file_path}")
                return 1
            single_result = measure_single_file(
                file_path=file_path, iterations=max(1, args.iterations)
            )

        if args.files:
            files = _expand_glob(args.files)
            if not files:
                print(f"ERROR: No files found matching: {args.files}")
                return 1
            if len(files) > 20:
                files = files[:20]
            batch_result = measure_batch_files(
                file_paths=files,
                workers=max(1, args.workers),
                iterations=max(1, min(args.iterations, 5)),
            )

        print_report(single_result=single_result, batch_result=batch_result)

        failures = []
        if single_result and single_result["overhead_pct"] >= TARGET_OVERHEAD_PCT:
            failures.append("single-file overhead exceeded target")
        if batch_result and batch_result["overhead_pct"] >= TARGET_OVERHEAD_PCT:
            failures.append("batch overhead exceeded target")

        if failures:
            print("\nWARNING: " + "; ".join(failures))
            return 1

        print("\nSUCCESS: All measurements are below target overhead")
        return 0
    except subprocess.TimeoutExpired:
        print("ERROR: Command timed out while measuring progress overhead")
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
