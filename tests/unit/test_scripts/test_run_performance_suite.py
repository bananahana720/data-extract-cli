"""Unit tests for run_performance_suite.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

import run_performance_suite  # noqa: E402
from performance_catalog import RUN_PERFORMANCE_SUITE_NODEIDS  # noqa: E402


@pytest.mark.unit
def test_catalog_suite_selectors_are_present() -> None:
    assert set(RUN_PERFORMANCE_SUITE_NODEIDS.keys()) == {"extractors", "pipeline", "cli"}
    for selectors in RUN_PERFORMANCE_SUITE_NODEIDS.values():
        assert selectors
        assert all("::" in selector for selector in selectors)


@pytest.mark.unit
def test_main_executes_catalog_selectors(monkeypatch: pytest.MonkeyPatch) -> None:
    executed: list[str] = []

    def fake_run_command(cmd: list[str], timeout: int = 600):  # noqa: ARG001
        selector = cmd[3]
        executed.append(selector)
        return {
            "success": True,
            "duration": 0.01,
            "stdout": "",
            "stderr": "",
            "returncode": 0,
        }

    monkeypatch.setattr(run_performance_suite, "run_command", fake_run_command)
    monkeypatch.setattr(run_performance_suite, "parse_baseline_file", lambda _path: {})

    exit_code = run_performance_suite.main()

    expected = [
        *RUN_PERFORMANCE_SUITE_NODEIDS["extractors"],
        *RUN_PERFORMANCE_SUITE_NODEIDS["pipeline"],
        *RUN_PERFORMANCE_SUITE_NODEIDS["cli"],
    ]
    assert exit_code == 0
    assert executed == expected


@pytest.mark.unit
def test_main_returns_nonzero_when_any_selector_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    with patch.object(run_performance_suite, "parse_baseline_file", return_value={}):
        with patch.object(
            run_performance_suite,
            "run_command",
            return_value={
                "success": False,
                "duration": 0.1,
                "stdout": "",
                "stderr": "boom",
                "returncode": 1,
            },
        ):
            assert run_performance_suite.main() == 1
