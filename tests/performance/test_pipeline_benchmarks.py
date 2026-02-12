"""Greenfield pipeline performance benchmarks."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from data_extract.services.pipeline_service import PipelineFileResult, PipelineService
from tests.performance.conftest import PerformanceMeasurement, assert_performance_target

pytestmark = [
    pytest.mark.P1,
    pytest.mark.performance,
]


class TestPipelineBenchmarks:
    """Measure end-to-end service latency across common flows."""

    def test_single_txt_pipeline_latency(self, fixture_dir: Path, tmp_path: Path) -> None:
        service = PipelineService()
        file_path = fixture_dir / "sample.txt"

        with PerformanceMeasurement() as perf:
            result = service.process_file(
                file_path=file_path,
                output_dir=tmp_path,
                output_format="json",
                chunk_size=500000,
                include_semantic=False,
                source_root=file_path.parent,
            )

        assert result.chunk_count >= 1
        assert_performance_target(perf.duration_ms, 1200.0, "Single TXT pipeline", tolerance=1.0)
        assert set(result.stage_timings_ms.keys()) == {
            "extract",
            "normalize",
            "chunk",
            "semantic",
            "output",
        }

    def test_pipeline_json_vs_txt_output_latency(self, fixture_dir: Path, tmp_path: Path) -> None:
        service = PipelineService()
        file_path = fixture_dir / "sample.txt"

        with PerformanceMeasurement() as json_perf:
            service.process_file(
                file_path=file_path,
                output_dir=tmp_path,
                output_format="json",
                chunk_size=500000,
                include_semantic=False,
                source_root=file_path.parent,
            )

        with PerformanceMeasurement() as txt_perf:
            service.process_file(
                file_path=file_path,
                output_dir=tmp_path,
                output_format="txt",
                chunk_size=500000,
                include_semantic=False,
                source_root=file_path.parent,
            )

        # JSON serialization should remain within the same order of magnitude as TXT output.
        assert json_perf.duration_ms <= txt_perf.duration_ms * 3.0

    def test_batch_workers_improve_parallel_processing(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        service = PipelineService()
        fake_files = [tmp_path / f"doc_{idx:03d}.txt" for idx in range(12)]

        def fake_process_file(
            self, file_path: Path, output_dir: Path, output_format: str, chunk_size: int, **kwargs
        ):
            time.sleep(0.05)
            return PipelineFileResult(
                source_path=file_path,
                output_path=output_dir / f"{file_path.stem}.{output_format}",
                chunk_count=1,
                stage_timings_ms={"extract": 50.0},
            )

        monkeypatch.setattr(PipelineService, "process_file", fake_process_file)

        start = time.perf_counter()
        sequential = service.process_files(
            files=fake_files,
            output_dir=tmp_path / "seq",
            output_format="json",
            chunk_size=100,
            workers=1,
        )
        sequential_s = time.perf_counter() - start

        start = time.perf_counter()
        parallel = service.process_files(
            files=fake_files,
            output_dir=tmp_path / "par",
            output_format="json",
            chunk_size=100,
            workers=4,
        )
        parallel_s = time.perf_counter() - start

        assert len(sequential.processed) == len(fake_files)
        assert len(parallel.processed) == len(fake_files)
        assert parallel_s < sequential_s * 0.7

    @pytest.mark.slow
    def test_small_batch_real_files_throughput(self, tmp_path: Path) -> None:
        batch_root = Path(__file__).parent / "batch_100_files"
        files = sorted(
            [f for f in batch_root.rglob("*") if f.is_file() and f.suffix.lower() != ".png"]
        )
        files = files[:20]

        service = PipelineService()
        start = time.perf_counter()
        run = service.process_files(
            files=files,
            output_dir=tmp_path / "batch-out",
            output_format="json",
            chunk_size=500000,
            workers=4,
            include_semantic=False,
            source_root=batch_root,
        )
        elapsed_s = time.perf_counter() - start

        assert len(run.processed) + len(run.failed) == len(files)
        assert len(run.processed) >= int(len(files) * 0.95)
        throughput_per_minute = (len(files) / elapsed_s) * 60 if elapsed_s > 0 else 0
        assert throughput_per_minute >= 10.0
