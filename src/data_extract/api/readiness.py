"""Runtime dependency/readiness checks for local UI/API server."""

from __future__ import annotations

import importlib.util
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

    spacy_model_ready = False
    try:
        import spacy

        spacy_model_ready = bool(spacy.util.is_package("en_core_web_md"))
    except Exception as exc:
        warnings.append(f"spaCy availability check failed: {exc}")

    checks["spacy_model:en_core_web_md"] = spacy_model_ready
    if not spacy_model_ready:
        warnings.append(
            "spaCy model 'en_core_web_md' is not installed; sentence segmentation falls back to heuristics."
        )

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
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
