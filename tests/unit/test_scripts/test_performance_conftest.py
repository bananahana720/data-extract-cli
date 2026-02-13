"""Unit tests for performance conftest baseline setup helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.performance import conftest as perf_conftest


@pytest.mark.unit
def test_production_baseline_manager_seeds_empty_target_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    target_file = tmp_path / "empty-baseline.json"
    target_file.touch()

    monkeypatch.setenv("DATA_EXTRACT_BASELINE_WRITE_MODE", "1")
    monkeypatch.setenv("DATA_EXTRACT_BASELINE_TARGET", str(target_file))

    manager = perf_conftest.production_baseline_manager.__wrapped__(tmp_path_factory)

    assert manager.baseline_file == target_file
    payload = json.loads(target_file.read_text(encoding="utf-8"))
    assert isinstance(payload.get("baselines"), dict)
