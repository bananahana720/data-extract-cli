#!/usr/bin/env python3
"""Refresh maintained performance baselines and prune legacy keys."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from performance_catalog import ACTIVE_BASELINE_KEYS, BASELINE_REFRESH_NODEIDS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASELINE_FILE = PROJECT_ROOT / "tests" / "performance" / "baselines.json"


def _run_refresh_tests(target_file: Path) -> None:
    env = os.environ.copy()
    existing_path = env.get("PYTHONPATH", "").strip()
    src_path = str(PROJECT_ROOT / "src")
    env["PYTHONPATH"] = f"{src_path}{os.pathsep}{existing_path}" if existing_path else src_path
    env["DATA_EXTRACT_BASELINE_WRITE_MODE"] = "1"
    env["DATA_EXTRACT_BASELINE_TARGET"] = str(target_file)

    command = [
        sys.executable,
        "-m",
        "pytest",
        *BASELINE_REFRESH_NODEIDS,
        "-q",
        "-s",
        "--tb=short",
    ]
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError("Baseline refresh tests failed")


def _load_baselines(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Baseline file was not created: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    baselines = payload.get("baselines")
    if not isinstance(baselines, dict):
        raise RuntimeError("Baseline file missing 'baselines' mapping")
    return baselines


def _prune_baselines(baselines: dict[str, Any]) -> dict[str, Any]:
    kept = {key: baselines[key] for key in ACTIVE_BASELINE_KEYS if key in baselines}
    missing = [key for key in ACTIVE_BASELINE_KEYS if key not in kept]
    if missing:
        raise RuntimeError(f"Missing refreshed baseline keys: {', '.join(missing)}")
    return kept


def _write_canonical_baselines(path: Path, baselines: dict[str, Any]) -> None:
    data = {
        "baselines": baselines,
        "updated_at": datetime.now().isoformat(),
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def main() -> int:
    print("=" * 70)
    print("Refreshing Performance Baselines")
    print("=" * 70)
    print(f"Target baseline file: {BASELINE_FILE}")
    print(f"Maintained keys: {len(ACTIVE_BASELINE_KEYS)}")

    with TemporaryDirectory(prefix="perf-baseline-refresh-") as temp_dir:
        temp_file = Path(temp_dir) / "baselines-refresh.json"
        _run_refresh_tests(temp_file)
        refreshed = _load_baselines(temp_file)
        canonical = _prune_baselines(refreshed)
        _write_canonical_baselines(BASELINE_FILE, canonical)

    print("Baseline refresh completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
