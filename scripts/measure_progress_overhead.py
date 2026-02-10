"""
Measure Performance Overhead of Progress Display.

Compares extraction performance with and without progress tracking
to verify the <3% overhead target specified in requirements.

Usage:
    python scripts/measure_progress_overhead.py --file path/to/test/file.pdf
    python scripts/measure_progress_overhead.py --files path/to/files/*.pdf
"""

import statistics
import sys
import time
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractors import DocxExtractor, PdfExtractor
from src.formatters import JsonFormatter
from src.pipeline import BatchProcessor, ExtractionPipeline
from src.processors import ContextLinker, MetadataAggregator, QualityValidator


def create_test_pipeline() -> ExtractionPipeline:
    """Create pipeline for testing."""
    pipeline = ExtractionPipeline()

    # Register extractors
    pipeline.register_extractor("docx", DocxExtractor())
    pipeline.register_extractor("pdf", PdfExtractor())
    pipeline.register_extractor("txt", DocxExtractor())  # Fallback

    # Add processors
    pipeline.add_processor(ContextLinker())
    pipeline.add_processor(MetadataAggregator())
    pipeline.add_processor(QualityValidator())

    # Add formatter
    pipeline.add_formatter(JsonFormatter())

    return pipeline


def measure_single_file(file_path: Path, iterations: int = 5) -> dict:
    """
    Measure single file extraction performance.

    Args:
        file_path: Path to test file
        iterations: Number of test iterations

    Returns:
        Dict with timing statistics
    """
    print(f"\nMeasuring single file performance: {file_path.name}")
    print(f"Running {iterations} iterations...")

    pipeline = create_test_pipeline()

    # Warm-up run
    print("  Warm-up run...")
    pipeline.process_file(file_path)

    # Baseline: No progress callback
    print("  Baseline (no progress)...")
    baseline_times = []
    for i in range(iterations):
        start = time.perf_counter()
        _result = pipeline.process_file(file_path, progress_callback=None)
        elapsed = time.perf_counter() - start
        baseline_times.append(elapsed)
        print(f"    Run {i+1}: {elapsed:.3f}s")

    # With progress callback
    print("  With progress tracking...")
    progress_times = []
    call_count = [0]  # Use list to capture in nested function

    def progress_callback(status):
        call_count[0] += 1

    for i in range(iterations):
        call_count[0] = 0
        start = time.perf_counter()
        _result = pipeline.process_file(file_path, progress_callback=progress_callback)
        elapsed = time.perf_counter() - start
        progress_times.append(elapsed)
        print(f"    Run {i+1}: {elapsed:.3f}s ({call_count[0]} callbacks)")

    # Calculate statistics
    baseline_mean = statistics.mean(baseline_times)
    baseline_stdev = statistics.stdev(baseline_times) if len(baseline_times) > 1 else 0

    progress_mean = statistics.mean(progress_times)
    progress_stdev = statistics.stdev(progress_times) if len(progress_times) > 1 else 0

    overhead_abs = progress_mean - baseline_mean
    overhead_pct = (overhead_abs / baseline_mean) * 100 if baseline_mean > 0 else 0

    return {
        "file": file_path.name,
        "baseline_mean": baseline_mean,
        "baseline_stdev": baseline_stdev,
        "progress_mean": progress_mean,
        "progress_stdev": progress_stdev,
        "overhead_abs": overhead_abs,
        "overhead_pct": overhead_pct,
        "callback_count": call_count[0],
        "iterations": iterations,
    }


def measure_batch_files(file_paths: List[Path], workers: int = 4) -> dict:
    """
    Measure batch processing performance.

    Args:
        file_paths: List of test files
        workers: Number of parallel workers

    Returns:
        Dict with timing statistics
    """
    print(f"\nMeasuring batch performance: {len(file_paths)} files")
    print(f"Using {workers} workers...")

    pipeline = create_test_pipeline()

    # Baseline: No progress callback
    print("  Baseline (no progress)...")
    batch_processor = BatchProcessor(pipeline=pipeline, max_workers=workers)

    start = time.perf_counter()
    _results_baseline = batch_processor.process_batch(file_paths, progress_callback=None)
    baseline_time = time.perf_counter() - start
    print(f"    Time: {baseline_time:.3f}s")

    # With progress callback
    print("  With progress tracking...")
    call_count = [0]

    def progress_callback(status):
        call_count[0] += 1

    start = time.perf_counter()
    _results_progress = batch_processor.process_batch(
        file_paths, progress_callback=progress_callback
    )
    progress_time = time.perf_counter() - start
    print(f"    Time: {progress_time:.3f}s ({call_count[0]} callbacks)")

    # Calculate overhead
    overhead_abs = progress_time - baseline_time
    overhead_pct = (overhead_abs / baseline_time) * 100 if baseline_time > 0 else 0

    return {
        "file_count": len(file_paths),
        "workers": workers,
        "baseline_time": baseline_time,
        "progress_time": progress_time,
        "overhead_abs": overhead_abs,
        "overhead_pct": overhead_pct,
        "callback_count": call_count[0],
    }


def print_report(single_results: List[dict], batch_result: dict = None):
    """Print performance report."""
    print("\n" + "=" * 70)
    print("PROGRESS DISPLAY PERFORMANCE REPORT")
    print("=" * 70)

    if single_results:
        print("\nSINGLE FILE RESULTS:")
        print("-" * 70)

        for result in single_results:
            print(f"\nFile: {result['file']}")
            print(
                f"  Baseline:       {result['baseline_mean']:.3f}s ± {result['baseline_stdev']:.3f}s"
            )
            print(
                f"  With Progress:  {result['progress_mean']:.3f}s ± {result['progress_stdev']:.3f}s"
            )
            print(
                f"  Overhead:       {result['overhead_abs']:.3f}s ({result['overhead_pct']:.2f}%)"
            )
            print(f"  Callbacks:      {result['callback_count']}")

            # Check against target
            if result["overhead_pct"] < 3.0:
                print("  Result:         [OK] Under 3% target")
            else:
                print("  Result:         [WARNING] Exceeds 3% target")

    if batch_result:
        print("\nBATCH PROCESSING RESULTS:")
        print("-" * 70)
        print(f"\nFiles: {batch_result['file_count']} (workers: {batch_result['workers']})")
        print(f"  Baseline:       {batch_result['baseline_time']:.3f}s")
        print(f"  With Progress:  {batch_result['progress_time']:.3f}s")
        print(
            f"  Overhead:       {batch_result['overhead_abs']:.3f}s ({batch_result['overhead_pct']:.2f}%)"
        )
        print(f"  Callbacks:      {batch_result['callback_count']}")

        # Check against target
        if batch_result["overhead_pct"] < 3.0:
            print("  Result:         [OK] Under 3% target")
        else:
            print("  Result:         [WARNING] Exceeds 3% target")

    print("\n" + "=" * 70)
    print("TARGET: <3% overhead (from assessment requirements)")
    print("=" * 70 + "\n")


def main():
    """Main measurement runner."""
    import argparse
    import glob

    parser = argparse.ArgumentParser(description="Measure progress display overhead")
    parser.add_argument("--file", type=str, help="Single file to test")
    parser.add_argument(
        "--files", type=str, help='Glob pattern for batch testing (e.g., "tests/fixtures/*.pdf")'
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of iterations for single file test (default: 5)",
    )
    parser.add_argument(
        "--workers", type=int, default=4, help="Number of workers for batch test (default: 4)"
    )

    args = parser.parse_args()

    if not args.file and not args.files:
        print("ERROR: Must specify --file or --files")
        print("\nExamples:")
        print('  python scripts/measure_progress_overhead.py --file "tests/fixtures/test.pdf"')
        print(
            '  python scripts/measure_progress_overhead.py --files "tests/fixtures/real-world-files/*.pdf"'
        )
        return 1

    single_results = []
    batch_result = None

    try:
        # Single file test
        if args.file:
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"ERROR: File not found: {file_path}")
                return 1

            result = measure_single_file(file_path, iterations=args.iterations)
            single_results.append(result)

        # Batch test
        if args.files:
            file_paths = [Path(f) for f in glob.glob(args.files)]
            if not file_paths:
                print(f"ERROR: No files found matching: {args.files}")
                return 1

            # Limit to reasonable number for testing
            if len(file_paths) > 10:
                print(f"  Note: Limiting to first 10 files (found {len(file_paths)})")
                file_paths = file_paths[:10]

            batch_result = measure_batch_files(file_paths, workers=args.workers)

        # Print report
        print_report(single_results, batch_result)

        # Check if all passed
        all_passed = True
        for result in single_results:
            if result["overhead_pct"] >= 3.0:
                all_passed = False

        if batch_result and batch_result["overhead_pct"] >= 3.0:
            all_passed = False

        if all_passed:
            print("SUCCESS: All tests passed <3% overhead target!")
            return 0
        else:
            print("WARNING: Some tests exceeded 3% overhead target")
            return 1

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
