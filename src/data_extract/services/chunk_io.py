"""Shared chunk serialization/deserialization helpers.

This module provides a compatibility layer between process output and semantic
analysis input. It intentionally accepts both legacy-minimal and enriched chunk
payloads and always reads JSON with UTF-8 BOM compatibility.
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List

from data_extract.core.models import Chunk


def _to_json_safe(value: Any) -> Any:
    """Recursively convert values into JSON-safe primitives."""
    if isinstance(value, dict):
        return {str(k): _to_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_to_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "model_dump"):
        return _to_json_safe(value.model_dump(mode="python"))
    if hasattr(value, "to_dict"):
        return _to_json_safe(value.to_dict())
    return value


def _coerce_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
        return parsed if parsed >= 0 else default
    except (TypeError, ValueError):
        return default


def _coerce_float(value: Any, default: float) -> float:
    try:
        parsed = float(value)
        return parsed
    except (TypeError, ValueError):
        return default


def chunk_to_dict(chunk: Any) -> Dict[str, Any]:
    """Serialize a chunk-like object using the canonical enriched schema."""
    text = str(getattr(chunk, "text", ""))
    metadata_obj = getattr(chunk, "metadata", {})
    metadata = _to_json_safe(metadata_obj) if metadata_obj is not None else {}
    if not isinstance(metadata, dict):
        metadata = {"value": metadata}

    word_count_default = len(text.split())
    word_count = _coerce_int(getattr(chunk, "word_count", word_count_default), word_count_default)
    token_count = _coerce_int(getattr(chunk, "token_count", word_count), word_count)

    readability = getattr(chunk, "readability_scores", {}) or {}
    if not isinstance(readability, dict):
        readability = {}

    return {
        "id": getattr(chunk, "id", None),
        "text": text,
        "document_id": str(getattr(chunk, "document_id", "") or ""),
        "position_index": _coerce_int(getattr(chunk, "position_index", 0), 0),
        "token_count": token_count,
        "word_count": word_count,
        "entities": getattr(chunk, "entities", []) if isinstance(getattr(chunk, "entities", []), list) else [],
        "section_context": str(getattr(chunk, "section_context", "") or ""),
        "quality_score": _coerce_float(getattr(chunk, "quality_score", 0.0), 0.0),
        "readability_scores": _to_json_safe(readability),
        "metadata": metadata,
    }


def _iter_chunk_payloads(data: Any) -> Iterable[Dict[str, Any]]:
    """Yield chunk dictionaries from accepted JSON payload shapes."""
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield item
        return

    if isinstance(data, dict):
        chunks = data.get("chunks")
        if isinstance(chunks, list):
            for item in chunks:
                if isinstance(item, dict):
                    yield item
            return
        yield data


def chunk_from_dict(payload: Dict[str, Any]) -> Chunk | None:
    """Best-effort conversion from dictionary to Chunk model."""
    try:
        text = str(payload.get("text", "") or "")
        metadata = payload.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}

        word_count_default = len(text.split())
        word_count = _coerce_int(payload.get("word_count"), word_count_default)
        token_count = _coerce_int(payload.get("token_count"), word_count)

        readability_scores = payload.get("readability_scores")
        if not isinstance(readability_scores, dict):
            readability_scores = {}

        entities = payload.get("entities")
        if not isinstance(entities, list):
            entities = []

        return Chunk(
            id=str(payload.get("id", "") or ""),
            text=text,
            document_id=str(payload.get("document_id", "") or ""),
            position_index=_coerce_int(payload.get("position_index"), 0),
            token_count=token_count,
            word_count=word_count,
            entities=entities,
            section_context=str(payload.get("section_context", "") or ""),
            quality_score=_coerce_float(payload.get("quality_score"), 0.0),
            readability_scores=readability_scores,
            metadata=metadata,
        )
    except Exception:
        return None


def load_chunks(input_path: Path) -> List[Chunk]:
    """Load chunks from a file or directory of JSON files.

    Files are decoded as ``utf-8-sig`` to accept BOM-prefixed process output.
    """
    files = [input_path] if input_path.is_file() else sorted(input_path.glob("**/*.json"))
    chunks: List[Chunk] = []

    for file_path in files:
        try:
            with open(file_path, encoding="utf-8-sig") as handle:
                data = json.load(handle)
        except Exception:
            continue

        for payload in _iter_chunk_payloads(data):
            chunk = chunk_from_dict(payload)
            if chunk is not None:
                chunks.append(chunk)

    return chunks
