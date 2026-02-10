"""Shared path normalization helpers for deterministic processing."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path


def normalize_path(path: Path | str) -> Path:
    """Return normalized absolute path without requiring file existence."""
    return Path(path).expanduser().resolve(strict=False)


def normalized_path_text(path: Path | str) -> str:
    """Return normalized string representation stable across platforms."""
    normalized = normalize_path(path)
    text = normalized.as_posix()
    return text.lower() if os.name == "nt" else text


def source_key_for_path(path: Path | str) -> str:
    """Stable file identity key based on normalized source path."""
    payload = normalized_path_text(path).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]
