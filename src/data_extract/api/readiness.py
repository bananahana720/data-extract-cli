"""Runtime dependency/readiness checks for local UI/API server."""

from __future__ import annotations

import importlib.util
import os
from datetime import datetime, timezone
from typing import Any

REQUIRED_RUNTIME_MODULES: dict[str, str] = {
    "fastapi": "API runtime",
    "uvicorn": "ASGI server",
    "sqlalchemy": "job persistence",
    "multipart": "multipart upload support",
}

REQUIRED_EXTRACTOR_MODULES: dict[str, str] = {
    "pypdf": "PDF extraction",
    "docx": "DOCX extraction",
    "openpyxl": "Excel extraction",
    "pptx": "PPTX extraction",
}
OCR_READINESS_STRICT_ENV = "DATA_EXTRACT_API_OCR_READINESS_STRICT"


def _env_flag_enabled(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _check_spacy_model_ready() -> tuple[bool, str | None]:
    try:
        import spacy

        return bool(spacy.util.is_package("en_core_web_md")), None
    except Exception as exc:
        return False, f"spaCy availability check failed: {exc}"


def _check_ocr_available() -> tuple[bool, str]:
    try:
        from data_extract.cli.ocr_status import check_ocr_available

        available, message = check_ocr_available()
        normalized_message = str(message).strip() if message is not None else ""
        return bool(available), normalized_message or "OCR availability check returned no details."
    except Exception as exc:
        return False, f"OCR availability check failed: {exc}"


def evaluate_runtime_readiness() -> dict[str, Any]:
    """Return readiness report used by startup checks and health endpoint."""
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, bool] = {}

    for module_name, capability in REQUIRED_RUNTIME_MODULES.items():
        is_available = importlib.util.find_spec(module_name) is not None
        checks[f"runtime:{module_name}"] = is_available
        if not is_available:
            errors.append(f"Missing dependency ({capability}): {module_name}")

    for module_name, capability in REQUIRED_EXTRACTOR_MODULES.items():
        is_available = importlib.util.find_spec(module_name) is not None
        checks[f"extractor:{module_name}"] = is_available
        if not is_available:
            errors.append(f"Missing dependency ({capability}): {module_name}")

    spacy_model_ready, spacy_warning = _check_spacy_model_ready()
    if spacy_warning:
        warnings.append(spacy_warning)

    checks["spacy_model:en_core_web_md"] = spacy_model_ready
    if not spacy_model_ready:
        warnings.append(
            "spaCy model 'en_core_web_md' is not installed; sentence segmentation falls back to heuristics."
        )

    ocr_available, ocr_message = _check_ocr_available()
    ocr_strict = _env_flag_enabled(OCR_READINESS_STRICT_ENV, default=False)
    checks["ocr:available"] = ocr_available
    ocr_status = "ok" if ocr_available else ("error" if ocr_strict else "warning")
    if not ocr_available:
        ocr_issue = f"OCR dependencies unavailable: {ocr_message}"
        if ocr_strict:
            errors.append(ocr_issue)
        else:
            warnings.append(ocr_issue)

    if errors:
        status = "error"
    elif warnings:
        status = "degraded"
    else:
        status = "ok"

    return {
        "status": status,
        "ready": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
        "ocr_readiness": {
            "status": ocr_status,
            "available": ocr_available,
            "strict": ocr_strict,
            "message": ocr_message,
        },
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
