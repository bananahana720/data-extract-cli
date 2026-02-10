#!/usr/bin/env python3
"""
Profile pipeline performance on 100-file batch using GREENFIELD architecture.

This script runs the Extract stage from src/data_extract/ on the 100-file test batch,
measuring time, memory usage, and identifying bottlenecks.

ARCHITECTURE: Uses greenfield extractors (src/data_extract/extract/) NOT brownfield (src/pipeline/)

Usage:
    # Run with timing and memory monitoring (parallelized)
    python scripts/profile_pipeline.py

    # Run with cProfile for bottleneck analysis
    python -m cProfile -o profile.stats scripts/profile_pipeline.py

    # Analyze profile results
    python -m pstats profile.stats
    >>> sort cumtime
    >>> stats 10

    # Control worker count
    python scripts/profile_pipeline.py --workers 4

Story: 2.5.2.1 Performance Optimization (parallelization)
NFRs: NFR-P1 (<10 min for 100 files), NFR-P2 (<2GB memory)
"""

import multiprocessing
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

# Add project root to path (greenfield uses absolute imports with src. prefix)
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import psutil
except ImportError:
    print("ERROR: psutil not installed. Run: pip install psutil")
    sys.exit(1)

# Import greenfield extractors (at module level for worker processes)
from src.data_extract.core.models import Document  # noqa: E402
from src.data_extract.extract import get_extractor, is_supported  # noqa: E402


class BatchResult:
    """Container for batch processing results."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.success = False
        self.error_message = ""
        self.processing_time_ms = 0.0
        self.document_id = ""
        self.text_length = 0
        self.page_count = 0
        self.word_count = 0
        self.ocr_confidence = None
        self.quality_flags = []


def extract_single_file(file_path: Path) -> "BatchResult":
    """
    Worker function for parallel extraction. Must be top-level for pickling.

    Args:
        file_path: Path to file to extract

    Returns:
        BatchResult with extraction results
    """
    result = BatchResult(file_path)

    # Check if format is supported
    if not is_supported(file_path):
        result.success = False
        result.error_message = f"Unsupported format: {file_path.suffix}"
        return result

    # Extract document
    try:
        start_time = time.time()
        adapter = get_extractor(file_path)
        document: Document = adapter.process(file_path)
        elapsed = time.time() - start_time

        # Populate result
        result.success = True
        result.processing_time_ms = elapsed * 1000
        result.document_id = document.id
        result.text_length = len(document.text)
        result.page_count = document.structure.get("page_count", 0)
        result.word_count = document.structure.get("word_count", 0)
        result.ocr_confidence = document.metadata.quality_scores.get("ocr_confidence")
        result.quality_flags = document.metadata.quality_flags

    except Exception as e:
        result.success = False
        result.error_message = str(e)

    return result


def collect_batch_files() -> List[Path]:
    """Collect all files from the 100-file test batch."""
    batch_dir = PROJECT_ROOT / "tests" / "performance" / "batch_100_files"

    if not batch_dir.exists():
        print(f"ERROR: Batch directory not found: {batch_dir}")
        print("Run: python scripts/create_performance_batch.py")
        sys.exit(1)

    # Collect all files from subdirectories
    files = []
    for subdir in ["pdfs", "docx", "xlsx", "mixed"]:
        subdir_path = batch_dir / subdir
        if subdir_path.exists():
            files.extend(list(subdir_path.glob("*")))

    files = [f for f in files if f.is_file()]

    print(f"Collected {len(files)} files from batch")
    return files


def format_bytes(bytes_val: float) -> str:
    """Format bytes as human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(bytes_val) < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"


def format_duration(seconds: float) -> str:
    """Format duration as human-readable string."""
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.2f}min"
    hours = minutes / 60
    return f"{hours:.2f}hr"


def get_total_memory() -> int:
    """Get total memory usage across main process and all workers."""
    main_process = psutil.Process()
    total_memory = main_process.memory_info().rss

    # Add memory from all child processes (worker pool)
    try:
        children = main_process.children(recursive=True)
        for child in children:
            try:
                total_memory += child.memory_info().rss
            except psutil.NoSuchProcess:
                pass  # Worker exited
    except Exception:
        pass  # Fallback to main process memory only

    return total_memory


def process_batch(
    files: List[Path], progress_callback=None, worker_count: Optional[int] = None
) -> List[BatchResult]:
    """
    Process batch of files through greenfield Extract stage with parallelization.

    Args:
        files: List of file paths to process
        progress_callback: Optional callback(result) called after each file
        worker_count: Number of worker processes (default: min(cpu_count, 4))

    Returns:
        List of BatchResult objects (order may differ from input)
    """
    # Determine worker count
    if worker_count is None:
        cpu_count = multiprocessing.cpu_count()
        # Story 2.5.2.1: 4 workers meets NFR-P1 (throughput) but exceeds NFR-P2 (memory: 4.15GB vs 2GB target)
        # Trade-off: Prioritize throughput (primary user need) over memory constraint
        # Future work: Implement streaming optimization (AC-2.5-2.1-3) to enable 4 workers within 2GB
        worker_count = min(cpu_count, 4)

    print(f"  - Worker processes: {worker_count}")

    results = []
    completed_count = 0

    # Use ProcessPoolExecutor for CPU-bound extraction tasks
    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        # Submit all files to work queue
        future_to_file = {
            executor.submit(extract_single_file, file_path): file_path for file_path in files
        }

        # Collect results as they complete (unordered for max throughput)
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]

            try:
                # Get result with timeout (60s per file)
                result = future.result(timeout=60)
                results.append(result)

            except TimeoutError:
                # File took too long - mark as timeout failure
                result = BatchResult(file_path)
                result.success = False
                result.error_message = "Processing timeout (>60s)"
                results.append(result)

            except Exception as e:
                # Worker crashed or other error - continue processing
                result = BatchResult(file_path)
                result.success = False
                result.error_message = f"Worker error: {str(e)}"
                results.append(result)

            completed_count += 1

            # Call progress callback if provided
            if progress_callback:
                progress_callback(result)

    return results


def main():
    """Run performance profiling on 100-file batch."""
    # Parse command-line arguments
    import argparse

    parser = argparse.ArgumentParser(
        description="Profile pipeline performance with parallelization"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of worker processes (default: min(cpu_count, 4))",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("PERFORMANCE PROFILING - 100-File Batch")
    print("Story 2.5.2.1: Pipeline Throughput Optimization")
    print("Architecture: GREENFIELD (src/data_extract/) with ProcessPoolExecutor")
    print("=" * 70)
    print()

    # Get process for memory monitoring
    process = psutil.Process()

    # Record baseline memory
    baseline_memory = process.memory_info().rss
    print(f"Baseline Memory: {format_bytes(baseline_memory)}")
    print()

    # Collect batch files
    print("Step 1: Collecting batch files...")
    files = collect_batch_files()

    if len(files) != 100:
        print(f"WARNING: Expected 100 files, found {len(files)}")
        print("Continuing with available files...")
    print()

    # Initialize progress tracking
    print("Step 2: Initializing greenfield extractors...")
    print("  - Auto-detection enabled (factory pattern)")
    print("  - Supported formats: PDF, DOCX, XLSX, PPTX, TXT, CSV")
    print("  - Continue-on-error enabled")
    print()

    # Run batch processing with timing and memory monitoring
    print("Step 3: Processing batch...")
    print(f"  - Files to process: {len(files)}")
    print(f"  - Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    start_time = time.time()
    start_memory = process.memory_info().rss
    peak_memory = start_memory
    files_processed = 0
    successful_count = 0
    failed_count = 0

    # Progress callback for memory tracking (monitors all workers)
    def progress_callback(result: BatchResult):
        nonlocal peak_memory, files_processed, successful_count, failed_count
        current_memory = get_total_memory()  # Track main + all worker processes
        peak_memory = max(peak_memory, current_memory)
        files_processed += 1

        if result.success:
            successful_count += 1
        else:
            failed_count += 1

        if files_processed % 10 == 0:
            elapsed = time.time() - start_time
            throughput = (files_processed / elapsed * 60) if elapsed > 0 else 0
            print(
                f"  [{files_processed}/{len(files)}] "
                f"Success: {successful_count}/{files_processed} "
                f"Memory: {format_bytes(current_memory)} "
                f"Throughput: {throughput:.2f} files/min"
            )

    # Process batch with parallelization
    try:
        results = process_batch(
            files, progress_callback=progress_callback, worker_count=args.workers
        )
    except Exception as e:
        print(f"\nERROR: Batch processing failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    end_time = time.time()
    end_memory = process.memory_info().rss

    # Calculate metrics
    elapsed_seconds = end_time - start_time
    elapsed_minutes = elapsed_seconds / 60
    throughput_files_per_minute = len(files) / elapsed_minutes if elapsed_minutes > 0 else 0

    memory_delta = end_memory - start_memory
    peak_memory_mb = peak_memory / (1024 * 1024)
    end_memory_mb = end_memory / (1024 * 1024)

    successful_files = sum(1 for r in results if r.success)
    failed_files = len(results) - successful_files

    # Print results
    print()
    print("=" * 70)
    print("PERFORMANCE RESULTS")
    print("=" * 70)
    print()

    print("THROUGHPUT (NFR-P1):")
    print(f"  Total Time:        {format_duration(elapsed_seconds)}")
    print(f"  Files Processed:   {len(files)}")
    print(f"  Throughput:        {throughput_files_per_minute:.2f} files/min")
    print("  NFR-P1 Target:     <10 minutes for 100 files")
    print(f"  NFR-P1 Status:     {'PASS' if elapsed_minutes < 10 else 'FAIL'}")
    print()

    print("MEMORY USAGE (NFR-P2):")
    print(f"  Peak Memory:       {format_bytes(peak_memory)} ({peak_memory_mb:.2f} MB)")
    print(f"  End Memory:        {format_bytes(end_memory)} ({end_memory_mb:.2f} MB)")
    print(f"  Memory Delta:      {format_bytes(memory_delta)}")
    print("  NFR-P2 Target:     <2048 MB (2GB)")
    print(f"  NFR-P2 Status:     {'PASS' if peak_memory_mb < 2048 else 'FAIL'}")
    print()

    print("BATCH RESULTS:")
    print(f"  Successful:        {successful_files}/{len(files)}")
    print(f"  Failed:            {failed_files}/{len(files)}")
    print(f"  Success Rate:      {(successful_files/len(files)*100):.1f}%")
    print()

    # Show sample failures
    if failed_files > 0:
        print("SAMPLE FAILURES (first 5):")
        failure_count = 0
        for result in results:
            if not result.success and failure_count < 5:
                print(f"  - {result.file_path.name}: {result.error_message}")
                failure_count += 1
        print()

    # Show quality metrics
    ocr_documents = [r for r in results if r.success and r.ocr_confidence is not None]
    if ocr_documents:
        avg_ocr_confidence = sum(r.ocr_confidence for r in ocr_documents) / len(ocr_documents)
        print("QUALITY METRICS:")
        print(f"  OCR Documents:     {len(ocr_documents)}/{successful_files}")
        print(f"  Avg OCR Confidence: {avg_ocr_confidence:.2%}")
        print()

    print("NEXT STEPS:")
    print(
        "  1. Run cProfile analysis: python -m cProfile -o profile.stats scripts/profile_pipeline.py"
    )
    print("  2. Analyze bottlenecks: python -m pstats profile.stats")
    print("  3. In pstats: sort cumtime -> stats 10")
    print()

    print("=" * 70)

    # Exit with appropriate code
    if elapsed_minutes >= 10:
        print("FAILED: NFR-P1 throughput target not met")
        sys.exit(1)
    if peak_memory_mb >= 2048:
        print("FAILED: NFR-P2 memory target exceeded")
        sys.exit(1)
    if successful_files == 0:
        print("FAILED: Zero files successfully processed")
        sys.exit(1)

    print("SUCCESS: All NFR targets met")
    return 0


if __name__ == "__main__":
    # CRITICAL: multiprocessing.freeze_support() required for Windows
    # ProcessPoolExecutor on Windows uses spawn, which requires this guard
    multiprocessing.freeze_support()
    sys.exit(main())
