"""Module entry point for ``python -m data_extract``."""

from __future__ import annotations

from typing import cast

from data_extract.app import app


def main() -> int:
    """Execute the Typer CLI app."""
    return cast(int, app())


if __name__ == "__main__":
    raise SystemExit(main())
