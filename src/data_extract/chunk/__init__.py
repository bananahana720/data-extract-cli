"""Semantic chunking pipeline stage with lazy imports.

Avoid importing heavy dependencies (spaCy, textstat) when only light-weight data
structures are needed (e.g., during unit tests that reference ChunkMetadata or
EntityReference). Attributes are imported on-demand via module-level __getattr__
to keep optional dependencies truly optional.
"""

from __future__ import annotations

import importlib
from typing import Any, Dict, Tuple

__all__ = [
    "ChunkingEngine",
    "ChunkingConfig",
    "SentenceSegmenter",
    "ChunkMetadata",
    "QualityScore",
    "MetadataEnricher",
]

_LAZY_IMPORTS: Dict[str, Tuple[str, str]] = {
    "ChunkingEngine": ("data_extract.chunk.engine", "ChunkingEngine"),
    "ChunkingConfig": ("data_extract.chunk.engine", "ChunkingConfig"),
    "SentenceSegmenter": ("data_extract.chunk.sentence_segmenter", "SentenceSegmenter"),
    "ChunkMetadata": ("data_extract.chunk.models", "ChunkMetadata"),
    "QualityScore": ("data_extract.chunk.quality", "QualityScore"),
    "MetadataEnricher": ("data_extract.chunk.metadata_enricher", "MetadataEnricher"),
}


def __getattr__(name: str) -> Any:
    """Lazily import attributes to avoid mandatory heavy dependencies."""
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module 'data_extract.chunk' has no attribute '{name}'")

    module_name, attr_name = _LAZY_IMPORTS[name]
    module = importlib.import_module(module_name)
    attr = getattr(module, attr_name)
    globals()[name] = attr
    return attr
