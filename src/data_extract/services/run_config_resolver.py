"""Resolve effective process run configuration from request + config cascade."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict

from data_extract.cli.config import load_merged_config
from data_extract.contracts import ProcessJobRequest

DEFAULT_CHUNK_SIZE = int(ProcessJobRequest.model_fields["chunk_size"].default)
DEFAULT_OUTPUT_FORMAT = str(ProcessJobRequest.model_fields["output_format"].default)
DEFAULT_PIPELINE_PROFILE = "auto"
VALID_PIPELINE_PROFILES = {"auto", "legacy", "advanced"}


def _to_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _to_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
        return parsed if parsed > 0 else default
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _nested_get(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return default
        current = current.get(part)
        if current is None:
            return default
    return current


@dataclass(frozen=True)
class ResolvedSemanticConfig:
    """Semantic runtime settings used by process orchestration."""

    enabled: bool
    report: bool
    report_format: str
    export_graph: bool
    graph_format: str
    max_features: int
    duplicate_threshold: float
    related_threshold: float
    n_components: int
    min_quality: float


@dataclass(frozen=True)
class ResolvedRunConfig:
    """Fully resolved execution settings for a processing job."""

    output_format: str
    chunk_size: int
    continue_on_error: bool
    include_semantic: bool
    pipeline_profile: str
    allow_advanced_fallback: bool
    semantic: ResolvedSemanticConfig


class RunConfigResolver:
    """Resolve process runtime options from defaults + preset + env + request."""

    def resolve(self, request: ProcessJobRequest) -> ResolvedRunConfig:
        if load_merged_config is None:
            raise RuntimeError("Configuration loader is unavailable")
        cli_overrides = self._build_cli_overrides(request)
        merged = load_merged_config(
            cli_overrides=cli_overrides,
            preset_name=request.preset,
        ).to_dict()

        format_from_config = str(merged.get("format") or DEFAULT_OUTPUT_FORMAT).lower()
        chunk_from_config = _to_int(
            _nested_get(merged, "chunk.size", _nested_get(merged, "chunk.max_tokens")),
            DEFAULT_CHUNK_SIZE,
        )

        # Preserve existing request defaults unless preset is explicitly selected.
        output_format = (
            format_from_config
            if request.preset and request.output_format == DEFAULT_OUTPUT_FORMAT
            else str(request.output_format).lower()
        )
        chunk_size = (
            chunk_from_config
            if request.preset and request.chunk_size == DEFAULT_CHUNK_SIZE
            else int(request.chunk_size)
        )

        semantic_cfg = merged.get("semantic", {}) if isinstance(merged, dict) else {}
        include_semantic = bool(request.include_semantic)
        report = (
            request.semantic_report
            if request.semantic_report is not None
            else include_semantic
        )
        export_graph = (
            request.semantic_export_graph
            if request.semantic_export_graph is not None
            else include_semantic
        )
        report_format = str(request.semantic_report_format or "json").lower()
        graph_format = str(request.semantic_graph_format or "json").lower()

        resolved_semantic = ResolvedSemanticConfig(
            enabled=include_semantic,
            report=bool(report),
            report_format=report_format,
            export_graph=bool(export_graph),
            graph_format=graph_format,
            max_features=_to_int(
                request.semantic_max_features,
                _to_int(_nested_get(semantic_cfg, "tfidf.max_features", 5000), 5000),
            ),
            duplicate_threshold=_to_float(
                request.semantic_duplicate_threshold,
                _to_float(_nested_get(semantic_cfg, "similarity.duplicate_threshold", 0.95), 0.95),
            ),
            related_threshold=_to_float(
                request.semantic_related_threshold,
                _to_float(_nested_get(semantic_cfg, "similarity.related_threshold", 0.7), 0.7),
            ),
            n_components=_to_int(
                request.semantic_n_components,
                _to_int(_nested_get(semantic_cfg, "lsa.n_components", 100), 100),
            ),
            min_quality=_to_float(
                request.semantic_min_quality,
                _to_float(_nested_get(semantic_cfg, "quality.min_score", 0.3), 0.3),
            ),
        )

        requested_profile = str(
            request.pipeline_profile
            or os.environ.get("DATA_EXTRACT_PIPELINE_PROFILE", DEFAULT_PIPELINE_PROFILE)
        ).lower()
        pipeline_profile = (
            requested_profile if requested_profile in VALID_PIPELINE_PROFILES else DEFAULT_PIPELINE_PROFILE
        )
        allow_advanced_fallback = _to_bool(
            os.environ.get("DATA_EXTRACT_ADVANCED_FALLBACK"),
            True,
        )

        return ResolvedRunConfig(
            output_format=output_format,
            chunk_size=chunk_size,
            continue_on_error=bool(request.continue_on_error),
            include_semantic=include_semantic,
            pipeline_profile=pipeline_profile,
            allow_advanced_fallback=allow_advanced_fallback,
            semantic=resolved_semantic,
        )

    @staticmethod
    def _build_cli_overrides(request: ProcessJobRequest) -> Dict[str, Any]:
        overrides: Dict[str, Any] = {}
        if request.output_format != DEFAULT_OUTPUT_FORMAT or not request.preset:
            overrides["format"] = request.output_format
        if request.chunk_size != DEFAULT_CHUNK_SIZE or not request.preset:
            overrides["chunk_size"] = request.chunk_size
        return overrides
