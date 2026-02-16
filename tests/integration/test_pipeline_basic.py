"""Integration coverage for file discovery and basic pipeline behavior."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_extract.services.file_discovery_service import FileDiscoveryService
from data_extract.services.pipeline_service import PipelineService

pytestmark = [pytest.mark.P0, pytest.mark.integration]


def _write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_discover_filters_supported_extensions_non_recursive(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    _write_text(source_dir / "zeta.txt", "zeta")
    _write_text(source_dir / "alpha.md", "alpha")
    _write_text(source_dir / "nested" / "child.txt", "child")
    (source_dir / "ignored.bin").write_bytes(b"bin")

    files, discovered_root = FileDiscoveryService().discover(source_dir, recursive=False)

    assert discovered_root == source_dir
    assert [path.name for path in files] == ["alpha.md", "zeta.txt"]


def test_discover_glob_pattern_resolves_from_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    docs_dir = tmp_path / "docs"
    _write_text(docs_dir / "one.txt", "one")
    _write_text(docs_dir / "two.log", "two")
    _write_text(docs_dir / "three.csv", "col_a,col_b\n1,2\n")

    monkeypatch.chdir(tmp_path)
    files, discovered_root = FileDiscoveryService().discover("docs/*.txt")

    assert discovered_root == Path.cwd()
    assert files == [(docs_dir / "one.txt").resolve()]


def test_pipeline_process_file_writes_json_output(tmp_path: Path) -> None:
    source_file = _write_text(
        tmp_path / "input.txt",
        "one two three four five six seven",
    )
    output_dir = tmp_path / "output"

    run = PipelineService().process_files(
        files=[source_file],
        output_dir=output_dir,
        output_format="json",
        chunk_size=3,
        include_semantic=False,
        source_root=tmp_path,
        pipeline_profile="legacy",
    )

    assert len(run.processed) == 1
    assert run.failed == []

    output_file = output_dir / "input.json"
    assert output_file.exists()

    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["metadata"]["chunk_count"] == run.processed[0].chunk_count
    assert payload["metadata"]["source_documents"] == [str(source_file)]

    stage_keys = set(run.processed[0].stage_timings_ms)
    assert {"extract", "normalize", "chunk", "semantic", "output"}.issubset(stage_keys)
