from __future__ import annotations

from pathlib import Path

import pytest

from data_extract.services.file_discovery_service import FileDiscoveryService

pytestmark = [pytest.mark.unit]


def test_discover_absolute_glob_resolves_without_cwd_anchor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    file_path = source_dir / "match.txt"
    file_path.write_text("match", encoding="utf-8")

    unrelated_cwd = tmp_path / "unrelated"
    unrelated_cwd.mkdir()
    monkeypatch.chdir(unrelated_cwd)

    files, discovered_source = FileDiscoveryService().discover(str(source_dir / "*.txt"))

    assert files == [file_path.resolve()]
    assert discovered_source == source_dir.resolve()


def test_discover_relative_recursive_glob_keeps_pattern_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pattern_root = tmp_path / "input"
    nested = pattern_root / "nested"
    nested.mkdir(parents=True)
    file_a = pattern_root / "a.txt"
    file_b = nested / "b.txt"
    file_a.write_text("a", encoding="utf-8")
    file_b.write_text("b", encoding="utf-8")

    # Similar path segment under another root should not match relative pattern "input/**/*.txt".
    decoy = tmp_path / "other" / "input"
    decoy.mkdir(parents=True)
    (decoy / "c.txt").write_text("c", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    files, discovered_source = FileDiscoveryService().discover("input/**/*.txt")

    assert files == sorted([file_a.resolve(), file_b.resolve()])
    assert discovered_source == pattern_root.resolve()
