"""NFR throughput and memory checks for greenfield batch processing."""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Callable

import psutil
import pytest

from data_extract.services.file_discovery_service import FileDiscoveryService
from data_extract.services.pipeline_service import PipelineService

pytestmark = [
    pytest.mark.P1,
    pytest.mark.performance,
    pytest.mark.slow,
]


def _measure_peak_rss_mb(
    fn: Callable[[], object], sample_interval_s: float = 0.05
) -> tuple[object, float]:
    process = psutil.Process()
    peak_rss = process.memory_info().rss
    stop = threading.Event()

    def _sampler() -> None:
        nonlocal peak_rss
        while not stop.is_set():
            peak_rss = max(peak_rss, process.memory_info().rss)
            time.sleep(sample_interval_s)

    thread = threading.Thread(target=_sampler, daemon=True)
    thread.start()
    try:
        result = fn()
    finally:
        stop.set()
        thread.join(timeout=1.0)

    return result, peak_rss / 1024 / 1024


def _run_full_batch(output_dir: Path) -> dict[str, object]:
    batch_root = Path(__file__).parent / "batch_100_files"
    discovery = FileDiscoveryService()
    files, source_root = discovery.discover(batch_root, recursive=True)
    service = PipelineService()

    def _run() -> object:
        return service.process_files(
            files=files,
            output_dir=output_dir,
            output_format="json",
            chunk_size=500000,
            workers=4,
            include_semantic=False,
            source_root=source_root,
        )

    start = time.perf_counter()
    run, peak_rss_mb = _measure_peak_rss_mb(_run)
    elapsed_s = time.perf_counter() - start
    throughput_files_per_sec = len(files) / elapsed_s if elapsed_s > 0 else 0.0

    metrics_path = os.getenv("DATA_EXTRACT_PERF_METRICS_FILE")
    if metrics_path:
        Path(metrics_path).write_text(
            json.dumps(
                {
                    "files_total": len(files),
                    "elapsed_s": elapsed_s,
                    "throughput_files_per_sec": throughput_files_per_sec,
                    "throughput_files_per_min": throughput_files_per_sec * 60,
                    "peak_rss_mb": peak_rss_mb,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    return {
        "files": files,
        "run": run,
        "elapsed_s": elapsed_s,
        "peak_rss_mb": peak_rss_mb,
    }


@pytest.fixture(scope="module")
def full_batch_metrics(tmp_path_factory: pytest.TempPathFactory) -> dict[str, object]:
    output_dir = tmp_path_factory.mktemp("throughput_full_batch")
    return _run_full_batch(output_dir)


class TestBatchThroughputNfr:
    """Validate Story 2.5 throughput and memory NFR targets."""

    def test_batch_throughput_100_files_under_10_minutes(
        self, full_batch_metrics: dict[str, object]
    ) -> None:
        files = full_batch_metrics["files"]
        run = full_batch_metrics["run"]
        elapsed_min = float(full_batch_metrics["elapsed_s"]) / 60

        assert elapsed_min < 10.0, f"Batch took {elapsed_min:.2f} minutes"
        assert len(run.processed) + len(run.failed) == len(files)
        assert len(run.processed) >= int(len(files) * 0.99)

    def test_memory_usage_under_2gb_for_100_file_batch(
        self, full_batch_metrics: dict[str, object]
    ) -> None:
        files = full_batch_metrics["files"]
        run = full_batch_metrics["run"]
        peak_rss_mb = float(full_batch_metrics["peak_rss_mb"])

        assert len(run.processed) >= int(len(files) * 0.99)
        assert peak_rss_mb < 2048.0, f"Peak RSS {peak_rss_mb:.2f} MB exceeded 2GB"

    def test_no_memory_leak_across_repeated_batches(self, tmp_path: Path) -> None:
        batch_root = Path(__file__).parent / "batch_100_files"
        discovery = FileDiscoveryService()
        files, source_root = discovery.discover(batch_root, recursive=True)
        files = files[:10]

        process = psutil.Process()
        baseline_mb = process.memory_info().rss / 1024 / 1024

        service = PipelineService()
        for idx in range(2):
            run = service.process_files(
                files=files,
                output_dir=tmp_path / f"nfr-repeat-{idx}",
                output_format="json",
                chunk_size=500000,
                workers=4,
                include_semantic=False,
                source_root=source_root,
            )
            assert len(run.processed) >= int(len(files) * 0.99)

        final_mb = process.memory_info().rss / 1024 / 1024
        leak_mb = final_mb - baseline_mb
        assert leak_mb < 300.0, f"Memory increased by {leak_mb:.2f} MB across repeated runs"
