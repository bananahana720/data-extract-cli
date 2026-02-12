"""Validate that semantic fixture corpus is free of obvious PII patterns."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def _scan_for_pii(root: Path) -> list[str]:
    """Return a list of file paths that match basic PII regex patterns."""
    patterns = [
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN-like
        re.compile(r"\b\d{16}\b"),  # Card-like 16 contiguous digits
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),  # Email
    ]

    flagged: list[str] = []
    for path in root.rglob("*.txt"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(pattern.search(text) for pattern in patterns):
            flagged.append(str(path))
    return flagged


def main() -> int:
    fixtures_dir = Path(__file__).resolve().parent
    corpus_dir = fixtures_dir / "corpus"
    if not corpus_dir.exists():
        print(f"ERROR: Corpus directory not found: {corpus_dir}")
        return 1

    flagged_files = _scan_for_pii(corpus_dir)
    if flagged_files:
        print("FAILURE: Potential PII detected in fixture corpus.")
        for flagged in flagged_files:
            print(f" - {flagged}")
        return 1

    print("SUCCESS: Corpus is completely PII-free")
    return 0


if __name__ == "__main__":
    sys.exit(main())
