from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "migrate_legacy_sessions.py"
SRC_PATH = PROJECT_ROOT / "src"


def _run_migration(tmp_ui_home: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["DATA_EXTRACT_UI_HOME"] = str(tmp_ui_home)
    env["PYTHONPATH"] = str(SRC_PATH) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def _run_python(tmp_ui_home: Path, code: str, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["DATA_EXTRACT_UI_HOME"] = str(tmp_ui_home)
    env["PYTHONPATH"] = str(SRC_PATH) + os.pathsep + env.get("PYTHONPATH", "")
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def _init_database(tmp_ui_home: Path) -> None:
    completed = _run_python(
        tmp_ui_home,
        "from data_extract.api.database import init_database; init_database()",
    )
    assert completed.returncode == 0, completed.stderr


def _session_payload(
    *,
    session_id: str,
    source_directory: Path,
    status: str,
    processed_paths: list[str],
    failed_paths: list[tuple[str, int]],
) -> dict[str, object]:
    now = datetime.now(timezone.utc).isoformat()
    output_directory = source_directory / "output"
    processed_files = [{"path": Path(path).name, "source_path": path} for path in processed_paths]
    failed_files = [{"path": path, "retry_count": retry_count} for path, retry_count in failed_paths]
    total_files = len(processed_files) + len(failed_files)
    return {
        "schema_version": "1.0",
        "session_id": session_id,
        "status": status,
        "source_directory": str(source_directory),
        "output_directory": str(output_directory),
        "total_files": total_files,
        "started_at": now,
        "updated_at": now,
        "configuration": {
            "output_path": str(output_directory),
            "format": "json",
            "chunk_size": 64,
        },
        "processed_files": processed_files,
        "failed_files": failed_files,
        "statistics": {
            "total_files": total_files,
            "processed_count": len(processed_files),
            "failed_count": len(failed_files),
            "skipped_count": 0,
        },
    }


def _write_legacy_session(root: Path, payload: dict[str, object], archived: bool = False) -> Path:
    session_id = str(payload.get("session_id", "missing"))
    session_dir = root / ".data-extract-session"
    if archived:
        session_dir = session_dir / "archive"
    session_dir.mkdir(parents=True, exist_ok=True)
    session_file = session_dir / f"session-{session_id}.json"
    session_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return session_file


def _insert_canonical_seed(
    *,
    db_path: Path,
    session_id: str,
    source_directory: Path,
    status: str,
    processed_paths: list[str],
    failed_paths: list[tuple[str, int]],
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    total_files = len(processed_paths) + len(failed_paths)
    result_payload = {
        "status": status,
        "total_files": total_files,
        "processed_count": len(processed_paths),
        "failed_count": len(failed_paths),
        "skipped_count": 0,
        "output_dir": str(source_directory / "output"),
        "session_id": session_id,
        "processed_files": [{"path": path, "output_path": str(source_directory / "output" / (Path(path).stem + ".json"))} for path in processed_paths],
        "failed_files": [{"path": path, "retry_count": retry} for path, retry in failed_paths],
        "started_at": now,
        "finished_at": now,
        "request_hash": "seed-hash",
    }

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO sessions (
                session_id, source_directory, status, total_files, processed_count, failed_count,
                artifact_dir, is_archived, archived_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                str(source_directory),
                status,
                total_files,
                len(processed_paths),
                len(failed_paths),
                str(source_directory / "output"),
                0,
                None,
                now,
            ),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO jobs (
                id, status, input_path, output_dir, requested_format, chunk_size,
                request_payload, result_payload, request_hash, idempotency_key,
                attempt, artifact_dir, session_id, created_at, started_at, finished_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"job-{session_id}",
                status,
                str(source_directory),
                str(source_directory / "output"),
                "json",
                64,
                "{}",
                json.dumps(result_payload),
                "seed-hash",
                None,
                1,
                str(source_directory / "output"),
                session_id,
                now,
                now,
                now,
                now,
            ),
        )
        conn.commit()


def test_migration_default_mode_keeps_legacy_output_contract(tmp_path: Path) -> None:
    ui_home = tmp_path / "ui-home"
    source_root = tmp_path / "source"
    source_root.mkdir(parents=True, exist_ok=True)

    payload = _session_payload(
        session_id="legacy-a1",
        source_directory=source_root,
        status="completed",
        processed_paths=[str(source_root / "good.txt")],
        failed_paths=[],
    )
    _write_legacy_session(source_root, payload)

    completed = _run_migration(ui_home, str(source_root))
    assert completed.returncode == 0, completed.stderr
    assert "Imported sessions: 1" in completed.stdout
    assert "Skipped files: 0" in completed.stdout


def test_migration_dry_run_writes_json_and_markdown_reports(tmp_path: Path) -> None:
    ui_home = tmp_path / "ui-home"
    source_root = tmp_path / "source"
    source_root.mkdir(parents=True, exist_ok=True)

    payload = _session_payload(
        session_id="legacy-b1",
        source_directory=source_root,
        status="completed",
        processed_paths=[str(source_root / "good.txt")],
        failed_paths=[],
    )
    _write_legacy_session(source_root, payload)

    report_json = tmp_path / "migration-report.json"
    report_md = tmp_path / "migration-report.md"
    completed = _run_migration(
        ui_home,
        str(source_root),
        "--dry-run",
        "--report-json",
        str(report_json),
        "--report-md",
        str(report_md),
    )
    assert completed.returncode == 0, completed.stderr
    assert "Imported sessions: 0" in completed.stdout

    report_payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert report_payload["summary"]["discovered"] == 1
    assert report_payload["summary"]["valid"] == 1
    assert report_payload["summary"]["invalid"] == 0
    assert report_md.exists()
    assert "## Summary" in report_md.read_text(encoding="utf-8")


def test_migration_audit_parity_matches_runtime_artifacts(tmp_path: Path) -> None:
    ui_home = tmp_path / "ui-home"
    source_root = tmp_path / "runtime-source"
    source_root.mkdir(parents=True, exist_ok=True)
    (source_root / "good.txt").write_text("alpha", encoding="utf-8")
    (source_root / "bad.pdf").write_text("not-a-real-pdf", encoding="utf-8")

    runtime_script = textwrap.dedent(
        """
        import json
        import os
        from pathlib import Path
        from data_extract.contracts import ProcessJobRequest
        from data_extract.services.job_service import JobService

        source = Path(os.environ["MIGRATION_SOURCE"]).resolve()
        result = JobService().run_process(
            ProcessJobRequest(
                input_path=str(source),
                output_path=str(source / "output"),
                output_format="json",
                chunk_size=64,
            ),
            work_dir=source,
        )
        print(json.dumps(result.model_dump(mode="json")))
        """
    )
    seeded = _run_python(ui_home, runtime_script, {"MIGRATION_SOURCE": str(source_root)})
    assert seeded.returncode == 0, seeded.stderr
    runtime_payload = json.loads(seeded.stdout.strip().splitlines()[-1])
    session_id = runtime_payload["session_id"]
    assert runtime_payload["failed_count"] >= 1

    db_path = ui_home / "app.db"
    _insert_canonical_seed(
        db_path=db_path,
        session_id=session_id,
        source_directory=source_root,
        status=runtime_payload["status"],
        processed_paths=[item.get("path") for item in runtime_payload.get("processed_files", []) if item.get("path")],
        failed_paths=[(item.get("path"), int(item.get("retry_count", 0))) for item in runtime_payload.get("failed_files", []) if item.get("path")],
    )

    report_json = tmp_path / "parity-report.json"
    completed = _run_migration(
        ui_home,
        str(source_root),
        "--dry-run",
        "--audit-parity",
        "--report-json",
        str(report_json),
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert payload["mismatch_details"] == []
    parity_statuses = [entry.get("parity", {}).get("status") for entry in payload["sessions"] if entry.get("session_id")]
    assert "match" in parity_statuses


def test_migration_fail_on_parity_mismatch(tmp_path: Path) -> None:
    ui_home = tmp_path / "ui-home"
    source_root = tmp_path / "source"
    source_root.mkdir(parents=True, exist_ok=True)
    _init_database(ui_home)

    payload = _session_payload(
        session_id="legacy-c1",
        source_directory=source_root,
        status="completed",
        processed_paths=[str(source_root / "good.txt")],
        failed_paths=[(str(source_root / "bad.txt"), 1)],
    )
    _write_legacy_session(source_root, payload)

    db_path = ui_home / "app.db"
    _insert_canonical_seed(
        db_path=db_path,
        session_id="legacy-c1",
        source_directory=source_root,
        status="failed",
        processed_paths=[str(source_root / "good.txt")],
        failed_paths=[(str(source_root / "bad.txt"), 3)],
    )

    report_json = tmp_path / "mismatch-report.json"
    completed = _run_migration(
        ui_home,
        str(source_root),
        "--dry-run",
        "--audit-parity",
        "--fail-on-parity-mismatch",
        "--report-json",
        str(report_json),
    )
    assert completed.returncode == 1
    report_payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert report_payload["mismatch_details"]
