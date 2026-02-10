"""CLI command modules for data-extract.

This package intentionally avoids eager imports of the Typer app so runtime
services can import ``data_extract.cli.batch`` and ``data_extract.cli.session``
without requiring full CLI dependencies.
"""

from __future__ import annotations

from typing import Any

__all__ = ["app", "create_app", "get_app"]


def __getattr__(name: str) -> Any:
    if name in {"app", "create_app", "get_app"}:
        from data_extract.cli.base import app, create_app, get_app

        mapping = {
            "app": app,
            "create_app": create_app,
            "get_app": get_app,
        }
        return mapping[name]
    raise AttributeError(f"module 'data_extract.cli' has no attribute '{name}'")
