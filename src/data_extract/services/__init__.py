"""Shared service layer used by CLI and API.

Exports are resolved lazily to avoid circular imports between CLI and services
modules during package initialization.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORTS: dict[str, tuple[str, str]] = {
    "FileDiscoveryService": (
        "data_extract.services.file_discovery_service",
        "FileDiscoveryService",
    ),
    "PipelineService": ("data_extract.services.pipeline_service", "PipelineService"),
    "JobService": ("data_extract.services.job_service", "JobService"),
    "RetryService": ("data_extract.services.retry_service", "RetryService"),
    "RunConfigResolver": ("data_extract.services.run_config_resolver", "RunConfigResolver"),
    "SemanticOrchestrationService": (
        "data_extract.services.semantic_orchestration_service",
        "SemanticOrchestrationService",
    ),
    "PersistenceRepository": (
        "data_extract.services.persistence_repository",
        "PersistenceRepository",
    ),
    "normalize_path": ("data_extract.services.pathing", "normalize_path"),
    "source_key_for_path": ("data_extract.services.pathing", "source_key_for_path"),
    "list_session_summaries": ("data_extract.services.session_service", "list_session_summaries"),
    "load_session_details": ("data_extract.services.session_service", "load_session_details"),
    "StatusService": ("data_extract.services.status_service", "StatusService"),
}

__all__ = sorted(_EXPORTS.keys())


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _EXPORTS[name]
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + __all__)
