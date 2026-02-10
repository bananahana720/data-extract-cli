"""Module entry point for ``python -m data_extract``."""

from __future__ import annotations

from data_extract.app import app


def main() -> int:
    """Execute the Typer CLI app."""
    return app()


if __name__ == "__main__":
    raise SystemExit(main())
