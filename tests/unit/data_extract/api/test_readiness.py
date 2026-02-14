from __future__ import annotations

import importlib.util
import os
from pathlib import Path

os.environ.setdefault("DATA_EXTRACT_UI_HOME", "/tmp/data-extract-ui-tests")


def _load_readiness_module():
    module_path = (
        Path(__file__).resolve().parents[4] / "src" / "data_extract" / "api" / "readiness.py"
    )
    spec = importlib.util.spec_from_file_location("data_extract_api_readiness_test", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


readiness_module = _load_readiness_module()


def _stub_non_ocr_checks(monkeypatch) -> None:
    monkeypatch.setattr(readiness_module, "REQUIRED_RUNTIME_MODULES", {})
    monkeypatch.setattr(readiness_module, "REQUIRED_EXTRACTOR_MODULES", {})
    monkeypatch.setattr(readiness_module, "_check_spacy_model_ready", lambda: (True, None))


def test_readiness_marks_missing_ocr_as_warning_by_default(monkeypatch) -> None:
    _stub_non_ocr_checks(monkeypatch)
    monkeypatch.delenv("DATA_EXTRACT_API_OCR_READINESS_STRICT", raising=False)
    monkeypatch.setattr(readiness_module, "_check_ocr_available", lambda: (False, "not installed"))

    report = readiness_module.evaluate_runtime_readiness()

    assert report["ready"] is True
    assert report["status"] == "degraded"
    assert report["ocr_readiness"]["status"] == "warning"
    assert report["ocr_readiness"]["available"] is False
    assert any("OCR dependencies unavailable: not installed" in item for item in report["warnings"])
    assert report["errors"] == []


def test_readiness_promotes_missing_ocr_to_error_in_strict_mode(monkeypatch) -> None:
    _stub_non_ocr_checks(monkeypatch)
    monkeypatch.setenv("DATA_EXTRACT_API_OCR_READINESS_STRICT", "1")
    monkeypatch.setattr(
        readiness_module, "_check_ocr_available", lambda: (False, "missing tesseract")
    )

    report = readiness_module.evaluate_runtime_readiness()

    assert report["ready"] is False
    assert report["status"] == "error"
    assert report["ocr_readiness"]["status"] == "error"
    assert report["ocr_readiness"]["strict"] is True
    assert any(
        "OCR dependencies unavailable: missing tesseract" in item for item in report["errors"]
    )


def test_readiness_reports_ocr_ok_when_available(monkeypatch) -> None:
    _stub_non_ocr_checks(monkeypatch)
    monkeypatch.delenv("DATA_EXTRACT_API_OCR_READINESS_STRICT", raising=False)
    monkeypatch.setattr(readiness_module, "_check_ocr_available", lambda: (True, "OCR available"))

    report = readiness_module.evaluate_runtime_readiness()

    assert report["ready"] is True
    assert report["status"] == "ok"
    assert report["ocr_readiness"] == {
        "status": "ok",
        "available": True,
        "strict": False,
        "message": "OCR available",
    }
