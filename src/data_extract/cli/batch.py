"""Batch processing and incremental updates for data-extract CLI (Story 5-7).

Provides incremental processing capabilities with:
- SHA256 file hashing for change detection
- State file persistence for tracking processed files
- Glob pattern expansion for batch input
- Corpus sync status tracking

Reference: docs/stories/5-7-batch-processing-optimization-and-incremental-updates.md
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from data_extract.services.pipeline_service import PipelineService

# ==============================================================================
# Enums and Type Definitions
# ==============================================================================


class ChangeType(Enum):
    """Type of change detected for a file."""

    NEW = "new"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"
    DELETED = "deleted"


# ==============================================================================
# Data Models
# ==============================================================================


@dataclass(frozen=True)
class ProcessedFileEntry:
    """Information about a processed file.

    Attributes:
        path: Path to the source file
        hash: SHA256 hash of the file contents
        processed_at: Timestamp when file was processed
        output_path: Path to the generated output file
        size_bytes: Size of the source file in bytes
    """

    path: Path
    hash: str
    processed_at: datetime
    output_path: Path
    size_bytes: int


@dataclass(frozen=True)
class ChangeSummary:
    """Summary of detected changes in a corpus.

    Attributes:
        new_files: List of newly detected files
        modified_files: List of files that changed since last processing
        unchanged_files: List of files that are unchanged
        deleted_files: List of files that were deleted from source
    """

    new_files: list[Path]
    modified_files: list[Path]
    unchanged_files: list[Path]
    deleted_files: list[Path]

    @property
    def new_count(self) -> int:
        """Number of new files."""
        return len(self.new_files)

    @property
    def modified_count(self) -> int:
        """Number of modified files."""
        return len(self.modified_files)

    @property
    def unchanged_count(self) -> int:
        """Number of unchanged files."""
        return len(self.unchanged_files)

    @property
    def deleted_count(self) -> int:
        """Number of deleted files."""
        return len(self.deleted_files)

    @property
    def total_changes(self) -> int:
        """Total number of files that need processing (new + modified)."""
        return self.new_count + self.modified_count


@dataclass(frozen=True)
class ProcessingResult:
    """Result of a batch processing operation.

    Attributes:
        total_files: Total number of files attempted
        successful: Number of successfully processed files
        failed: Number of failed files
        skipped: Number of skipped files (incremental mode)
        time_saved_estimate: Estimated time saved by incremental processing (seconds)
    """

    total_files: int
    successful: int
    failed: int
    skipped: int = 0
    time_saved_estimate: float = 0.0


# ==============================================================================
# File Hashing
# ==============================================================================


class FileHasher:
    """Utility for computing file hashes.

    Uses SHA256 for cryptographically secure file identification.
    Reads files in chunks for memory efficiency.
    """

    CHUNK_SIZE = 8192  # 8KB chunks for efficient reading

    @staticmethod
    def compute_hash(file_path: Path) -> str:
        """Compute SHA256 hash of file contents.

        Args:
            file_path: Path to file to hash

        Returns:
            Hexadecimal SHA256 hash string

        Raises:
            FileNotFoundError: If file does not exist
            PermissionError: If file cannot be read
            OSError: For other I/O errors
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        hasher = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(FileHasher.CHUNK_SIZE):
                    hasher.update(chunk)
        except PermissionError as e:
            raise PermissionError(f"Permission denied reading file: {file_path}") from e
        except OSError as e:
            raise OSError(f"Error reading file {file_path}: {e}") from e

        return hasher.hexdigest()


# ==============================================================================
# State File Management
# ==============================================================================


class StateFile:
    """Manages incremental state persistence.

    State file schema:
    {
        "version": "1.0",
        "source_dir": "/path/to/docs",
        "output_dir": "/path/to/output",
        "config_hash": "sha256...",
        "processed_at": "2025-11-25T15:42:00Z",
        "files": {
            "/path/to/doc1.pdf": {
                "hash": "sha256...",
                "processed_at": "2025-11-25T15:40:00Z",
                "output_path": "/path/to/output/doc1.json",
                "size_bytes": 102400
            }
        }
    }

    Attributes:
        STATE_FILE_NAME: Name of the state file
        SCHEMA_VERSION: Current schema version for compatibility
    """

    STATE_FILE_NAME = "incremental-state.json"
    SCHEMA_VERSION = "1.0"

    def __init__(self, work_dir: Path) -> None:
        """Initialize state file manager.

        Args:
            work_dir: Working directory (state file stored in .data-extract-session subdirectory)
        """
        self.work_dir = work_dir
        self.session_dir = work_dir / ".data-extract-session"
        self.state_path = self.session_dir / self.STATE_FILE_NAME

    def load(self) -> dict[str, Any] | None:
        """Load state from file.

        Returns:
            State dictionary or None if file doesn't exist or is corrupted
        """
        if not self.state_path.exists():
            return None

        try:
            content = self.state_path.read_text(encoding="utf-8")
            state: dict[str, Any] = json.loads(content)
            return state
        except (json.JSONDecodeError, OSError):
            # Corrupted or unreadable state - treat as missing
            return None

    def save(self, state: dict[str, Any]) -> None:
        """Save state to file using atomic write.

        Uses atomic write pattern:
        1. Write to temporary file
        2. Rename to final location
        3. Cleanup temp file on success

        Args:
            state: State dictionary to persist

        Raises:
            OSError: If write fails
        """
        # Ensure directory exists
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Convert to JSON
        json_content = json.dumps(state, indent=2, ensure_ascii=False)

        # Atomic write using temp file
        fd, temp_path = tempfile.mkstemp(
            suffix=".tmp",
            prefix="incremental-state-",
            dir=self.session_dir,
        )
        try:
            os.write(fd, json_content.encode("utf-8"))
            os.close(fd)
            # Atomic rename
            shutil.move(temp_path, self.state_path)
        except Exception:
            # Clean up temp file on failure
            try:
                os.close(fd)
            except OSError:
                pass
            if Path(temp_path).exists():
                Path(temp_path).unlink()
            raise

    def exists(self) -> bool:
        """Check if state file exists.

        Returns:
            True if state file exists, False otherwise
        """
        return self.state_path.exists()

    def get_path(self) -> Path:
        """Get path to state file.

        Returns:
            Path to state file (may not exist)
        """
        return self.state_path


# ==============================================================================
# Change Detection
# ==============================================================================


class ChangeDetector:
    """Detects file changes by comparing hashes.

    Attributes:
        state: Previously loaded state dictionary
        hasher: FileHasher instance for computing hashes
    """

    def __init__(self, state: dict[str, Any] | None, hasher: FileHasher) -> None:
        """Initialize change detector.

        Args:
            state: Previously loaded state (None if no state exists)
            hasher: FileHasher instance
        """
        self.state = state or {}
        self.hasher = hasher

    def detect_changes(self, files: list[Path]) -> ChangeSummary:
        """Compare current files against saved state.

        For each file:
        - Not in state → NEW
        - In state but hash differs → MODIFIED
        - In state and hash matches → UNCHANGED

        For each state entry:
        - Path not in files → DELETED

        Args:
            files: List of current files to check

        Returns:
            ChangeSummary with categorized files
        """
        new_files: list[Path] = []
        modified_files: list[Path] = []
        unchanged_files: list[Path] = []

        # Get previous file records
        previous_files = self.state.get("files", {})

        # Check current files against state
        for file_path in files:
            file_path_str = str(file_path)

            if file_path_str not in previous_files:
                # New file
                new_files.append(file_path)
            else:
                # File exists in state - check hash
                try:
                    current_hash = self.hasher.compute_hash(file_path)
                    previous_hash = previous_files[file_path_str].get("hash", "")

                    if current_hash != previous_hash:
                        modified_files.append(file_path)
                    else:
                        unchanged_files.append(file_path)
                except (FileNotFoundError, PermissionError, OSError):
                    # File became inaccessible - treat as modified to retry
                    modified_files.append(file_path)

        # Check for deleted files (in state but not in current files)
        current_paths = {str(f) for f in files}
        deleted_files: list[Path] = []

        for previous_path in previous_files.keys():
            if previous_path not in current_paths:
                deleted_files.append(Path(previous_path))

        return ChangeSummary(
            new_files=new_files,
            modified_files=modified_files,
            unchanged_files=unchanged_files,
            deleted_files=deleted_files,
        )


# ==============================================================================
# Glob Pattern Expansion
# ==============================================================================


class GlobPatternExpander:
    """Expands glob patterns to file lists.

    Supports patterns like:
    - *.pdf
    - **/*.pdf
    - **/*.{pdf,docx}

    Attributes:
        base_dir: Base directory for glob expansion
    """

    def __init__(self, base_dir: Path) -> None:
        """Initialize glob pattern expander.

        Args:
            base_dir: Base directory for relative patterns
        """
        self.base_dir = base_dir

    def expand(self, pattern: str) -> list[Path]:
        """Expand glob pattern to matching files.

        Args:
            pattern: Glob pattern (e.g., "**/*.pdf")

        Returns:
            List of matching file paths (sorted)

        Raises:
            ValueError: If pattern is invalid
        """
        try:
            # Use rglob for ** patterns, glob otherwise
            if "**" in pattern:
                # Remove ** from pattern for rglob
                sub_pattern = pattern.replace("**/", "")
                matches = list(self.base_dir.rglob(sub_pattern))
            else:
                matches = list(self.base_dir.glob(pattern))

            # Filter to files only (exclude directories)
            files = [p for p in matches if p.is_file()]

            # Sort for deterministic order
            return sorted(files)

        except (ValueError, OSError) as e:
            raise ValueError(f"Invalid glob pattern '{pattern}': {e}") from e


# ==============================================================================
# Incremental Processor
# ==============================================================================


class IncrementalProcessor:
    """Orchestrates incremental batch processing.

    Handles:
    - Loading and saving state
    - Change detection
    - Incremental processing logic
    - Status reporting

    Attributes:
        source_dir: Source directory containing documents
        output_dir: Output directory for processed files
        config_hash: Hash of configuration (for cache invalidation)
    """

    def __init__(
        self,
        source_dir: Path,
        output_dir: Path,
        config_hash: str | None = None,
        output_format: str = "json",
        chunk_size: int = 512,
        include_semantic: bool = False,
    ) -> None:
        """Initialize incremental processor.

        Args:
            source_dir: Source directory path
            output_dir: Output directory path
            config_hash: Optional configuration hash for invalidation
        """
        self.source_dir = source_dir.resolve()
        self.output_dir = output_dir.resolve()
        self.config_hash = config_hash
        self.output_format = output_format
        self.chunk_size = chunk_size
        self.include_semantic = include_semantic

        # Initialize components
        self.state_file = StateFile(self.source_dir.parent)
        self.hasher = FileHasher()
        self.pipeline = PipelineService()

        # Load existing state
        self._state = self.state_file.load()

        # Initialize change detector
        self.change_detector = ChangeDetector(self._state, self.hasher)

    def analyze(self) -> ChangeSummary:
        """Analyze changes without processing.

        Returns:
            ChangeSummary showing new/modified/unchanged/deleted files
        """
        # Get all files in source directory
        files = self._get_all_files()

        # Detect changes
        return self.change_detector.detect_changes(files)

    def process(
        self,
        force: bool = False,
        files: list[Path] | None = None,
    ) -> ProcessingResult:
        """Process files, respecting incremental state.

        Args:
            force: If True, reprocess all files regardless of state
            files: Optional list of specific files to process (overrides auto-detection)

        Returns:
            ProcessingResult with statistics
        """
        # Get files to check
        if files is None:
            files = self._get_all_files()

        # Detect changes
        changes = self.change_detector.detect_changes(files)

        # Determine files to process
        if force:
            # Process all files
            to_process = files
            skipped = 0
        else:
            # Process only new and modified files
            to_process = changes.new_files + changes.modified_files
            skipped = changes.unchanged_count

        run = self.pipeline.process_files(
            files=to_process,
            output_dir=self.output_dir,
            output_format=self.output_format,
            chunk_size=self.chunk_size,
            include_semantic=self.include_semantic,
            continue_on_error=True,
            source_root=self.source_dir,
        )
        successful = len(run.processed)
        failed = len(run.failed)

        # Update state using successfully processed files only.
        self._update_state([item.source_path for item in run.processed])

        total_runtime_s = sum(run.stage_totals_ms.values()) / 1000.0
        avg_time_per_file = (total_runtime_s / successful) if successful else 0.0
        time_saved = skipped * avg_time_per_file

        return ProcessingResult(
            total_files=len(files),
            successful=successful,
            failed=failed,
            skipped=skipped,
            time_saved_estimate=time_saved,
        )

    def get_status(self) -> dict[str, Any]:
        """Get current corpus sync status.

        Returns:
            Dictionary with status information:
            - total_files: Total files in state
            - last_updated: Last processing timestamp
            - source_dir: Source directory path
            - output_dir: Output directory path
            - sync_state: Current sync state (up-to-date or changes detected)
        """
        if not self._state:
            return {
                "total_files": 0,
                "last_updated": None,
                "source_dir": str(self.source_dir),
                "output_dir": str(self.output_dir),
                "sync_state": "not processed",
            }

        # Analyze current changes
        changes = self.analyze()

        # Determine sync state
        if changes.total_changes > 0:
            sync_state = f"{changes.total_changes} changes detected"
        else:
            sync_state = "up to date"

        return {
            "total_files": len(self._state.get("files", {})),
            "last_updated": self._state.get("processed_at"),
            "source_dir": str(self.source_dir),
            "output_dir": str(self.output_dir),
            "sync_state": sync_state,
            "changes": {
                "new": changes.new_count,
                "modified": changes.modified_count,
                "unchanged": changes.unchanged_count,
                "deleted": changes.deleted_count,
            },
        }

    def _get_all_files(self) -> list[Path]:
        """Get all files in source directory.

        Returns:
            List of all files (recursively)
        """
        files: list[Path] = []

        for item in self.source_dir.rglob("*"):
            if item.is_file():
                files.append(item)

        return sorted(files)

    def _update_state(self, processed_files: list[Path]) -> None:
        """Update state file with newly processed files.

        Args:
            processed_files: List of files that were processed
        """
        # Create or update state
        if not self._state:
            self._state = {
                "version": StateFile.SCHEMA_VERSION,
                "source_dir": str(self.source_dir),
                "output_dir": str(self.output_dir),
                "files": {},
            }

        # Update timestamp
        now = datetime.now().isoformat()
        self._state["processed_at"] = now

        # Update config hash
        if self.config_hash:
            self._state["config_hash"] = self.config_hash

        # Update file records
        files_dict = self._state.setdefault("files", {})

        for file_path in processed_files:
            try:
                file_hash = self.hasher.compute_hash(file_path)
                file_size = file_path.stat().st_size

                try:
                    relative = file_path.relative_to(self.source_dir)
                except ValueError:
                    relative = Path(file_path.name)
                output_path = self.output_dir / relative.with_suffix(f".{self.output_format}")

                files_dict[str(file_path)] = {
                    "hash": file_hash,
                    "processed_at": now,
                    "output_path": str(output_path),
                    "size_bytes": file_size,
                }
            except (FileNotFoundError, PermissionError, OSError):
                # Skip files that can't be hashed
                continue

        # Save state
        self.state_file.save(self._state)
