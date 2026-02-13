"""Unit tests for measure_progress_overhead.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

import measure_progress_overhead  # noqa: E402


@pytest.mark.unit
def test_measure_single_file_builds_extract_commands(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("hello")

    calls: list[list[str]] = []

    def fake_run_cli(args: list[str], timeout_s: int = 300):  # noqa: ARG001
        calls.append(args)
        if "--quiet" in args:
            duration = 100.0
        else:
            duration = 102.0
        return {
            "success": True,
            "duration_ms": duration,
            "stdout": "",
            "stderr": "",
            "returncode": 0,
        }

    monkeypatch.setattr(measure_progress_overhead, "run_cli", fake_run_cli)
    result = measure_progress_overhead.measure_single_file(sample, iterations=2)

    assert len(calls) == 4
    assert all(args[0] == "extract" for args in calls)
    assert result["mode"] == "single"
    assert result["overhead_pct"] > 0


@pytest.mark.unit
def test_measure_batch_files_builds_batch_commands(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    files = []
    for idx in range(3):
        path = tmp_path / f"file-{idx}.txt"
        path.write_text(f"sample {idx}")
        files.append(path)

    calls: list[list[str]] = []

    def fake_run_cli(args: list[str], timeout_s: int = 300):  # noqa: ARG001
        calls.append(args)
        duration = 400.0 if "--quiet" in args else 420.0
        return {
            "success": True,
            "duration_ms": duration,
            "stdout": "",
            "stderr": "",
            "returncode": 0,
        }

    monkeypatch.setattr(measure_progress_overhead, "run_cli", fake_run_cli)
    result = measure_progress_overhead.measure_batch_files(files, workers=4, iterations=2)

    assert len(calls) == 4
    assert all(args[0] == "batch" for args in calls)
    assert result["file_count"] == 3
    assert result["workers"] == 4
    assert result["overhead_pct"] > 0


@pytest.mark.unit
def test_main_returns_error_without_inputs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["measure_progress_overhead.py"])
    assert measure_progress_overhead.main() == 1


@pytest.mark.unit
def test_main_single_mode_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_text("hello")

    monkeypatch.setattr(
        measure_progress_overhead,
        "measure_single_file",
        lambda file_path, iterations: {  # noqa: ARG005
            "mode": "single",
            "file": "sample.txt",
            "iterations": 1,
            "baseline_mean_ms": 10.0,
            "baseline_std_ms": 0.0,
            "progress_mean_ms": 10.1,
            "progress_std_ms": 0.0,
            "overhead_ms": 0.1,
            "overhead_pct": 1.0,
        },
    )
    monkeypatch.setattr(measure_progress_overhead, "print_report", lambda **kwargs: None)
    monkeypatch.setattr(sys, "argv", ["measure_progress_overhead.py", "--file", str(file_path)])
    assert measure_progress_overhead.main() == 0
