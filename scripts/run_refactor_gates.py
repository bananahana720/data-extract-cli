#!/usr/bin/env python3
"""Run milestone refactor gates for deterministic rollout."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GATES_DIR = PROJECT_ROOT / "scripts" / "gates"
DEFAULT_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"


def _resolve_python() -> str:
    if DEFAULT_PYTHON.exists():
        return str(DEFAULT_PYTHON)
    return sys.executable


PYTHON_EXE = _resolve_python()


def _read_manifest(path: Path) -> list[str]:
    entries: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        entries.append(value)
    return entries


def _run(command: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> bool:
    merged_env = dict(os.environ)
    if env:
        merged_env.update(env)
    merged_env["PYTHONPATH"] = str(PROJECT_ROOT / "src") + os.pathsep + merged_env.get("PYTHONPATH", "")
    print(f"$ {' '.join(command)}")
    completed = subprocess.run(command, cwd=cwd or PROJECT_ROOT, env=merged_env)
    return completed.returncode == 0


def gate_py_compile() -> bool:
    manifest = GATES_DIR / "refactor_py_compile_paths.txt"
    paths = _read_manifest(manifest)
    command = [PYTHON_EXE, "-m", "py_compile", *paths]
    return _run(command)


def gate_tests() -> bool:
    manifest = GATES_DIR / "refactor_test_targets.txt"
    targets = _read_manifest(manifest)
    command = [PYTHON_EXE, "-m", "pytest", "-q", *targets]
    return _run(command)


def gate_install_validation() -> bool:
    with tempfile.TemporaryDirectory(prefix="refactor-install-validation-") as tmp:
        temp_root = Path(tmp)
        ui_home = temp_root / "ui-home"
        legacy_root = temp_root / "legacy-sessions"
        legacy_root.mkdir(parents=True, exist_ok=True)

        env = dict(os.environ)
        env["DATA_EXTRACT_UI_HOME"] = str(ui_home)

        validation_ok = _run([PYTHON_EXE, "scripts/validate_installation.py"], env=env)
        migration_smoke_ok = _run(
            [
                PYTHON_EXE,
                "scripts/migrate_legacy_sessions.py",
                str(legacy_root),
                "--dry-run",
                "--report-json",
                str(temp_root / "migration-report.json"),
                "--report-md",
                str(temp_root / "migration-report.md"),
            ],
            env=env,
        )
        return validation_ok and migration_smoke_ok


def gate_ui_build() -> bool:
    ui_dir = PROJECT_ROOT / "ui"
    with tempfile.TemporaryDirectory(prefix="refactor-ui-gate-") as tmp:
        temp_root = Path(tmp)
        e2e_port = 47000 + (sum(ord(char) for char in temp_root.name) % 1000)
        env = dict(os.environ)
        env["DATA_EXTRACT_UI_HOME"] = str(temp_root / "ui-home")
        env["DATA_EXTRACT_E2E_UI_HOME"] = str(temp_root / "e2e-ui-home")
        env["DATA_EXTRACT_E2E_ARTIFACTS_DIR"] = str(temp_root / "e2e-artifacts")
        env["DATA_EXTRACT_E2E_PORT"] = str(e2e_port)

        build_ok = _run(["npm", "run", "build"], cwd=ui_dir, env=env)
        e2e_ok = _run(["npm", "run", "e2e:gui"], cwd=ui_dir, env=env)
        slo_ok = _run(["npm", "run", "e2e:gui:slo", "--", str(temp_root / "e2e-artifacts")], cwd=ui_dir, env=env)
        return build_ok and e2e_ok and slo_ok


def main() -> int:
    gates = [
        ("py_compile", gate_py_compile),
        ("tests", gate_tests),
        ("install_validation", gate_install_validation),
        ("ui_build", gate_ui_build),
    ]

    failures: list[str] = []
    for name, runner in gates:
        print(f"\n=== Gate: {name} ===")
        if runner():
            print(f"PASS {name}")
        else:
            print(f"FAIL {name}")
            failures.append(name)

    print("\n=== Summary ===")
    if failures:
        print(f"Failed gates: {', '.join(failures)}")
        return 1
    print("All four refactor gates passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
