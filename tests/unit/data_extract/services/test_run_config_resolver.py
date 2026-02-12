from __future__ import annotations

from typing import Any

import pytest

from data_extract.contracts import ProcessJobRequest
from data_extract.services import run_config_resolver as resolver_module
from data_extract.services.run_config_resolver import RunConfigResolver


class _MergedConfigStub:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def to_dict(self) -> dict[str, Any]:
        return dict(self._payload)


def test_resolve_rejects_unknown_preset(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_load_preset(name: str) -> dict[str, Any]:
        raise ValueError(f"Unknown preset: {name}")

    def fake_load_merged_config(**_: Any) -> _MergedConfigStub:
        return _MergedConfigStub({"format": "json", "chunk": {"size": 512}, "semantic": {}})

    monkeypatch.setattr(resolver_module, "load_preset", fake_load_preset)
    monkeypatch.setattr(resolver_module, "load_merged_config", fake_load_merged_config)

    request = ProcessJobRequest(
        input_path="/tmp/source",
        output_format="json",
        chunk_size=512,
        preset="does-not-exist",
    )

    with pytest.raises(ValueError, match="Preset not found: does-not-exist"):
        RunConfigResolver().resolve(request)


def test_resolve_includes_evaluation_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_load_merged_config(**_: Any) -> _MergedConfigStub:
        return _MergedConfigStub({"format": "json", "chunk": {"size": 512}, "semantic": {}})

    monkeypatch.setattr(resolver_module, "load_merged_config", fake_load_merged_config)

    request = ProcessJobRequest(input_path="/tmp/source")
    resolved = RunConfigResolver().resolve(request)

    assert resolved.evaluation.enabled is True
    assert resolved.evaluation.policy == "baseline_v1"
    assert resolved.evaluation.fail_on_bad is False
