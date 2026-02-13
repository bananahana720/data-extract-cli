"""Unit tests for CLI benchmark corpus sampling."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.performance.test_cli_benchmarks import _representative_batch_files


@pytest.mark.unit
def test_representative_batch_files_preserves_format_mix() -> None:
    project_root = Path(__file__).resolve().parents[3]
    fixture_dir = project_root / "tests" / "fixtures"

    files = _representative_batch_files(fixture_dir, max_files=24)
    suffixes = {file_path.suffix.lower() for file_path in files}

    assert len(files) == 24
    assert ".txt" in suffixes
    assert ".pdf" in suffixes
    assert ".docx" in suffixes
    assert ".xlsx" in suffixes
    assert ".pptx" in suffixes
