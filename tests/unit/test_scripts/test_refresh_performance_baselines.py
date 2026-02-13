"""Unit tests for refresh_performance_baselines.py."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

import refresh_performance_baselines  # noqa: E402
from performance_catalog import ACTIVE_BASELINE_KEYS, BASELINE_REFRESH_NODEIDS  # noqa: E402


@pytest.mark.unit
def test_prune_baselines_raises_for_missing_required_key() -> None:
    with pytest.raises(RuntimeError, match="Missing refreshed baseline keys"):
        refresh_performance_baselines._prune_baselines({"cli_extract_txt": {}})


@pytest.mark.unit
def test_run_refresh_tests_sets_expected_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, object] = {}

    def fake_run(command, cwd, env, capture_output, text):  # noqa: ANN001
        captured["command"] = command
        captured["cwd"] = cwd
        captured["env"] = env
        return MagicMock(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(refresh_performance_baselines.subprocess, "run", fake_run)
    monkeypatch.setenv("PYTHONPATH", "existing-path")

    target = tmp_path / "baselines-refresh.json"
    refresh_performance_baselines._run_refresh_tests(target)

    assert captured["command"][:3] == [sys.executable, "-m", "pytest"]
    assert captured["command"][3 : 3 + len(BASELINE_REFRESH_NODEIDS)] == list(
        BASELINE_REFRESH_NODEIDS
    )
    env = captured["env"]
    assert env["DATA_EXTRACT_BASELINE_WRITE_MODE"] == "1"
    assert env["DATA_EXTRACT_BASELINE_TARGET"] == str(target)
    expected_src = str(refresh_performance_baselines.PROJECT_ROOT / "src")
    assert env["PYTHONPATH"] == f"{expected_src}{os.pathsep}existing-path"


@pytest.mark.unit
def test_main_writes_pruned_baselines(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    output_file = tmp_path / "baselines.json"

    def fake_run_refresh_tests(target_file: Path) -> None:
        payload = {"baselines": {}, "updated_at": "2026-01-01T00:00:00"}
        for key in ACTIVE_BASELINE_KEYS:
            payload["baselines"][key] = {
                "operation": key,
                "duration_ms": 1.0,
                "memory_mb": 1.0,
                "file_size_kb": 1.0,
                "throughput": 1.0,
                "timestamp": "2026-01-01T00:00:00",
                "metadata": {},
            }
        payload["baselines"]["legacy_key"] = {
            "operation": "legacy_key",
            "duration_ms": 2.0,
            "memory_mb": 2.0,
            "file_size_kb": 2.0,
            "throughput": 2.0,
            "timestamp": "2026-01-01T00:00:00",
            "metadata": {},
        }
        target_file.write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setattr(refresh_performance_baselines, "_run_refresh_tests", fake_run_refresh_tests)
    monkeypatch.setattr(refresh_performance_baselines, "BASELINE_FILE", output_file)

    exit_code = refresh_performance_baselines.main()
    assert exit_code == 0

    written = json.loads(output_file.read_text(encoding="utf-8"))
    keys = set(written["baselines"].keys())
    assert keys == set(ACTIVE_BASELINE_KEYS)
    assert "legacy_key" not in keys
