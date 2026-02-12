"""CLI command modules.

Exports:
    cache_app: Cache management command group
    semantic_app: Semantic analysis command group
"""

from __future__ import annotations

from typing import Any


def __getattr__(name: str) -> Any:
    """Lazily import command apps to avoid heavy startup imports."""
    if name == "cache_app":
        from data_extract.cli.commands.cache import cache_app

        return cache_app
    if name == "semantic_app":
        from data_extract.cli.commands.semantic import semantic_app

        return semantic_app
    raise AttributeError(name)


__all__ = ["cache_app", "semantic_app"]
