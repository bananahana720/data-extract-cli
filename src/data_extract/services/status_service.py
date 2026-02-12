"""Corpus status service for incremental processing sync information."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from data_extract.cli.batch import IncrementalProcessor


class StatusService:
    """Provide source/output sync and orphaned-output status."""

    def get_status(
        self,
        source_dir: Path,
        output_dir: Path,
        cleanup: bool = False,
    ) -> Dict[str, Any]:
        """Return status payload consumed by CLI and API."""
        source_dir = source_dir.resolve()
        output_dir = output_dir.resolve()

        processor = IncrementalProcessor(source_dir=source_dir, output_dir=output_dir)
        status = processor.get_status()
        changes = processor.analyze()
        orphaned_outputs = self._find_orphaned_outputs(source_dir, output_dir)

        cleaned_count = 0
        if cleanup:
            for orphan in orphaned_outputs:
                try:
                    orphan.unlink()
                    cleaned_count += 1
                except OSError:
                    continue
            orphaned_outputs = [o for o in orphaned_outputs if o.exists()]

        return {
            "source_dir": str(source_dir),
            "output_dir": str(output_dir),
            "total_files": status.get("total_files", 0),
            "last_updated": status.get("last_updated"),
            "sync_state": status.get("sync_state", "unknown"),
            "state_file_present": bool(status.get("state_file_present", False)),
            "tracked_files": status.get("tracked_files", []),
            "changes": {
                "new": changes.new_count,
                "modified": changes.modified_count,
                "unchanged": changes.unchanged_count,
                "deleted": changes.deleted_count,
            },
            "orphaned_outputs": [str(path) for path in orphaned_outputs],
            "orphaned_count": len(orphaned_outputs),
            "cleaned_count": cleaned_count,
        }

    @staticmethod
    def _find_orphaned_outputs(source_dir: Path, output_dir: Path) -> List[Path]:
        """Find output files that no longer map to source-relative paths."""
        if not output_dir.exists():
            return []

        source_relative_keys = {
            str(file_path.relative_to(source_dir).with_suffix(""))
            for file_path in source_dir.rglob("*")
            if file_path.is_file() and output_dir not in file_path.resolve().parents
        }

        tracked_suffixes = {".json", ".txt", ".csv"}
        ignored_output_files = {"incremental-state.json", "summary.json", "session.json"}
        orphans: List[Path] = []
        for output_file in output_dir.rglob("*"):
            if not output_file.is_file():
                continue
            if output_file.suffix.lower() not in tracked_suffixes:
                continue
            if output_file.name in ignored_output_files:
                continue
            output_key = str(output_file.relative_to(output_dir).with_suffix(""))
            if output_key not in source_relative_keys:
                orphans.append(output_file)

        return sorted(orphans)
