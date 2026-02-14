#!/usr/bin/env python3
"""Import legacy filesystem sessions into canonical SQLite projections."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from data_extract.services.persistence_repository import PersistenceRepository


def _iter_session_files(root: Path) -> list[Path]:
    return sorted(root.rglob(".data-extract-session/session-*.json")) + sorted(
        root.rglob(".data-extract-session/archive/session-*.json")
    )


def _load_payload(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _normalized_path(value: Any) -> str:
    return str(value or "").replace("\\", "/").strip()


def _normalize_status(value: Any, failed_count: int) -> str:
    status = str(value or "").strip().lower()
    if status in {"success"}:
        status = "completed"
    if status == "completed" and failed_count > 0:
        return "partial"
    return status


def _summary_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    stats = payload.get("statistics", {})
    total_files = _safe_int(stats.get("total_files", payload.get("total_files", 0)))
    processed_count = _safe_int(
        stats.get("processed_count", len(payload.get("processed_files", [])))
    )
    failed_count = _safe_int(stats.get("failed_count", len(payload.get("failed_files", []))))
    return {
        "status": _normalize_status(payload.get("status", ""), failed_count),
        "total_files": total_files,
        "processed_count": processed_count,
        "failed_count": failed_count,
        "source_directory": str(payload.get("source_directory", "")),
    }


def _processed_path_set(items: list[dict[str, Any]]) -> set[str]:
    paths: set[str] = set()
    for item in items:
        source_path = item.get("source_path")
        fallback_path = item.get("path")
        path_value = _normalized_path(source_path or fallback_path)
        if path_value:
            paths.add(path_value)
    return paths


def _failed_path_set(items: list[dict[str, Any]]) -> set[str]:
    paths: set[str] = set()
    for item in items:
        path_value = _normalized_path(item.get("path"))
        if path_value:
            paths.add(path_value)
    return paths


def _failed_retry_map(items: list[dict[str, Any]]) -> dict[str, int]:
    retry: dict[str, int] = {}
    for item in items:
        path_value = _normalized_path(item.get("path"))
        if not path_value:
            continue
        retry[path_value] = _safe_int(item.get("retry_count", 0))
    return retry


def _session_projection(payload: dict[str, Any]) -> dict[str, Any]:
    processed_files = payload.get("processed_files", [])
    failed_files = payload.get("failed_files", [])
    if not isinstance(processed_files, list):
        processed_files = []
    if not isinstance(failed_files, list):
        failed_files = []

    return {
        "summary": _summary_from_payload(payload),
        "processed_paths": _processed_path_set(processed_files),
        "failed_paths": _failed_path_set(failed_files),
        "failed_retry_map": _failed_retry_map(failed_files),
    }


def _canonical_projection(session_id: str) -> dict[str, Any] | None:
    if not session_id:
        return None

    try:
        from sqlalchemy import select

        from data_extract.api.database import SessionLocal, init_database
        from data_extract.api.models import Job, SessionRecord
    except Exception:
        return None

    init_database()
    with SessionLocal() as db:
        session_row = db.get(SessionRecord, session_id)
        latest_job = db.scalar(
            select(Job).where(Job.session_id == session_id).order_by(Job.updated_at.desc())
        )

    if session_row is None and latest_job is None:
        return None

    result_payload: dict[str, Any] = {}
    if latest_job is not None:
        try:
            raw_payload = json.loads(latest_job.result_payload or "{}")
            if isinstance(raw_payload, dict):
                result_payload = raw_payload
        except Exception:
            result_payload = {}

    processed_files = result_payload.get("processed_files", [])
    failed_files = result_payload.get("failed_files", [])
    if not isinstance(processed_files, list):
        processed_files = []
    if not isinstance(failed_files, list):
        failed_files = []

    summary = {
        "status": _normalize_status(
            (
                session_row.status
                if session_row is not None
                else result_payload.get(
                    "status", latest_job.status if latest_job is not None else ""
                )
            ),
            _safe_int(
                session_row.failed_count
                if session_row is not None
                else result_payload.get("failed_count", len(failed_files))
            ),
        ),
        "total_files": _safe_int(
            session_row.total_files
            if session_row is not None
            else result_payload.get("total_files", 0)
        ),
        "processed_count": _safe_int(
            session_row.processed_count
            if session_row is not None
            else result_payload.get("processed_count", len(processed_files))
        ),
        "failed_count": _safe_int(
            session_row.failed_count
            if session_row is not None
            else result_payload.get("failed_count", len(failed_files))
        ),
        "source_directory": str(session_row.source_directory if session_row is not None else ""),
    }

    return {
        "summary": summary,
        "processed_paths": _processed_path_set(processed_files),
        "failed_paths": _failed_path_set(failed_files),
        "failed_retry_map": _failed_retry_map(failed_files),
    }


def _report_parity(legacy: dict[str, Any], canonical: dict[str, Any] | None) -> dict[str, Any]:
    if canonical is None:
        return {
            "status": "missing_canonical",
            "session_level": {
                "matches": False,
                "deltas": [{"field": "canonical", "legacy": "present", "canonical": "missing"}],
            },
            "file_level": {
                "matches": False,
                "deltas": [{"field": "canonical", "legacy": "present", "canonical": "missing"}],
            },
        }

    session_deltas: list[dict[str, Any]] = []
    for field in ["status", "total_files", "processed_count", "failed_count", "source_directory"]:
        legacy_value = legacy["summary"].get(field)
        canonical_value = canonical["summary"].get(field)
        if legacy_value != canonical_value:
            session_deltas.append(
                {"field": field, "legacy": legacy_value, "canonical": canonical_value}
            )

    processed_missing = sorted(legacy["processed_paths"] - canonical["processed_paths"])
    processed_extra = sorted(canonical["processed_paths"] - legacy["processed_paths"])
    failed_missing = sorted(legacy["failed_paths"] - canonical["failed_paths"])
    failed_extra = sorted(canonical["failed_paths"] - legacy["failed_paths"])

    retry_deltas: list[dict[str, Any]] = []
    retry_keys = sorted(set(legacy["failed_retry_map"]) | set(canonical["failed_retry_map"]))
    for key in retry_keys:
        legacy_value = _safe_int(legacy["failed_retry_map"].get(key, 0))
        canonical_value = _safe_int(canonical["failed_retry_map"].get(key, 0))
        if legacy_value != canonical_value:
            retry_deltas.append({"path": key, "legacy": legacy_value, "canonical": canonical_value})

    file_deltas: list[dict[str, Any]] = []
    if processed_missing:
        file_deltas.append(
            {"field": "processed_paths_missing_in_canonical", "paths": processed_missing}
        )
    if processed_extra:
        file_deltas.append(
            {"field": "processed_paths_extra_in_canonical", "paths": processed_extra}
        )
    if failed_missing:
        file_deltas.append({"field": "failed_paths_missing_in_canonical", "paths": failed_missing})
    if failed_extra:
        file_deltas.append({"field": "failed_paths_extra_in_canonical", "paths": failed_extra})
    if retry_deltas:
        file_deltas.append({"field": "failed_retry_count_deltas", "paths": retry_deltas})

    matches = not session_deltas and not file_deltas
    return {
        "status": "match" if matches else "mismatch",
        "session_level": {"matches": not session_deltas, "deltas": session_deltas},
        "file_level": {"matches": not file_deltas, "deltas": file_deltas},
    }


def _classify_mutation(legacy_summary: dict[str, Any], canonical: dict[str, Any] | None) -> str:
    if canonical is None:
        return "would_insert"
    if legacy_summary == canonical.get("summary"):
        return "unchanged"
    return "would_update"


def _write_json_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_markdown_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload.get("summary", {})
    lines: list[str] = [
        "# Legacy Session Migration Report",
        "",
        f"- Generated: {payload.get('generated_at')}",
        f"- Root: `{payload.get('root')}`",
        f"- Dry run: `{payload.get('dry_run')}`",
        f"- Audit parity: `{payload.get('audit_parity')}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]

    for key in [
        "discovered",
        "valid",
        "invalid",
        "would_insert",
        "would_update",
        "unchanged",
        "skipped",
    ]:
        lines.append(f"| {key} | {summary.get(key, 0)} |")

    lines.extend(["", "## Per-Session", ""])
    for session in payload.get("sessions", []):
        session_id = session.get("session_id") or "(missing)"
        decision = session.get("decision", "unknown")
        parity_status = (session.get("parity") or {}).get("status", "n/a")
        lines.append(f"- `{session_id}`: decision=`{decision}`, parity=`{parity_status}`")

    mismatch_details = payload.get("mismatch_details", [])
    lines.extend(["", "## Mismatch Details", ""])
    if not mismatch_details:
        lines.append("- none")
    else:
        for mismatch in mismatch_details:
            session_id = mismatch.get("session_id") or "(missing)"
            lines.append(f"- `{session_id}`")
            for detail in mismatch.get("details", []):
                lines.append(f"  - {json.dumps(detail, sort_keys=True)}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root", nargs="?", default=".", help="Search root (default: current directory)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Analyze and report without writing to canonical DB"
    )
    parser.add_argument(
        "--audit-parity",
        action="store_true",
        help="Compare legacy sessions against canonical dual-write projections",
    )
    parser.add_argument("--report-json", type=Path, help="Optional JSON report output path")
    parser.add_argument("--report-md", type=Path, help="Optional Markdown report output path")
    parser.add_argument(
        "--fail-on-parity-mismatch",
        action="store_true",
        help="Return non-zero when parity mismatches are detected",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    repository = PersistenceRepository()
    audit_parity = args.audit_parity or args.fail_on_parity_mismatch

    imported = 0
    skipped = 0
    summary = {
        "discovered": 0,
        "valid": 0,
        "invalid": 0,
        "would_insert": 0,
        "would_update": 0,
        "unchanged": 0,
        "skipped": 0,
    }
    per_session: list[dict[str, Any]] = []
    mismatch_details: list[dict[str, Any]] = []

    for session_file in _iter_session_files(root):
        summary["discovered"] += 1
        payload = _load_payload(session_file)
        if not payload:
            skipped += 1
            summary["invalid"] += 1
            summary["skipped"] += 1
            per_session.append(
                {
                    "session_file": str(session_file),
                    "session_id": "",
                    "decision": "skipped_invalid",
                    "parity": None,
                }
            )
            continue

        summary["valid"] += 1
        session_id = str(payload.get("session_id") or "")
        legacy = _session_projection(payload)
        canonical = _canonical_projection(session_id) if session_id else None

        decision = "skipped_missing_session_id"
        if session_id:
            decision = _classify_mutation(legacy["summary"], canonical)
            if decision in summary:
                summary[decision] += 1
        else:
            summary["skipped"] += 1

        parity = _report_parity(legacy, canonical) if audit_parity and session_id else None
        if parity and parity["status"] != "match":
            details = parity["session_level"]["deltas"] + parity["file_level"]["deltas"]
            mismatch_details.append(
                {
                    "session_id": session_id,
                    "status": parity["status"],
                    "details": details,
                }
            )

        is_archived = session_file.parent.name == "archive"
        artifact_dir = str(
            payload.get("output_directory")
            or payload.get("configuration", {}).get("output_path")
            or ""
        )
        archived_at = (
            datetime.fromtimestamp(session_file.stat().st_mtime, timezone.utc)
            if is_archived
            else None
        )

        if not args.dry_run:
            repository.upsert_session_record(
                payload,
                artifact_dir=artifact_dir or None,
                is_archived=is_archived,
                archived_at=archived_at,
            )
            imported += 1

        per_session.append(
            {
                "session_file": str(session_file),
                "session_id": session_id,
                "decision": decision,
                "legacy_summary": legacy["summary"],
                "canonical_summary": canonical["summary"] if canonical else None,
                "parity": parity,
            }
        )

    print(f"Imported sessions: {imported}")
    print(f"Skipped files: {skipped}")

    report_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "dry_run": bool(args.dry_run),
        "audit_parity": bool(audit_parity),
        "summary": summary,
        "sessions": per_session,
        "mismatch_details": mismatch_details,
    }

    if args.report_json:
        _write_json_report(args.report_json, report_payload)
    if args.report_md:
        _write_markdown_report(args.report_md, report_payload)

    if args.fail_on_parity_mismatch and mismatch_details:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
