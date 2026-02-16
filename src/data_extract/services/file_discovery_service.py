"""File discovery helpers shared by CLI and API."""

from __future__ import annotations

import glob
from pathlib import Path
from typing import Iterable, List, Tuple

from data_extract.extract import SUPPORTED_EXTENSIONS


class FileDiscoveryService:
    """Discover source files from paths, directories, and glob patterns."""

    GLOB_CHARS = {"*", "?", "[", "]"}

    def is_glob_pattern(self, value: str) -> bool:
        """Return True when input contains shell-style glob characters."""
        return any(char in value for char in self.GLOB_CHARS)

    def discover(
        self,
        input_path: str | Path,
        recursive: bool = False,
        exclude_paths: Iterable[Path] | None = None,
    ) -> Tuple[List[Path], Path]:
        """Resolve files and return (file_list, source_dir)."""
        excludes = [path.resolve() for path in (exclude_paths or [])]
        input_str = str(input_path)
        if self.is_glob_pattern(input_str):
            files = self._discover_from_glob(input_str, excludes)
            return files, self._glob_source_dir(input_str)

        resolved = Path(input_str)
        if not resolved.exists():
            raise FileNotFoundError(f"Source not found: {resolved}")

        if resolved.is_file():
            return self._filter_supported([resolved], excludes), resolved.parent

        pattern = "**/*" if recursive else "*"
        files = [p for p in resolved.glob(pattern) if p.is_file()]
        return self._filter_supported(files, excludes), resolved

    def _discover_from_glob(self, pattern: str, excludes: Iterable[Path]) -> List[Path]:
        """Expand glob pattern and filter to supported source files."""
        expanded_pattern = str(Path(pattern).expanduser())
        matches = glob.glob(expanded_pattern, recursive=True)
        files = [Path(match) for match in matches if Path(match).is_file()]
        return self._filter_supported(files, excludes)

    def _glob_source_dir(self, pattern: str) -> Path:
        """Return deterministic source root for a glob pattern."""
        expanded = Path(pattern).expanduser()
        static_parts: list[str] = []
        for part in expanded.parts:
            if self.is_glob_pattern(part):
                break
            static_parts.append(part)

        if not static_parts:
            return Path.cwd().resolve()

        source_dir = Path(*static_parts)
        if not source_dir.is_absolute():
            source_dir = Path.cwd() / source_dir
        return source_dir.resolve()

    @staticmethod
    def _filter_supported(
        files: Iterable[Path], excludes: Iterable[Path] | None = None
    ) -> List[Path]:
        """Keep only extensions currently supported by extractors."""
        excluded_roots = [path.resolve() for path in (excludes or [])]
        filtered = []
        for file_path in files:
            resolved = file_path.resolve()
            if resolved.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            if any(
                excluded == resolved or excluded in resolved.parents for excluded in excluded_roots
            ):
                continue
            filtered.append(resolved)
        return sorted(set(filtered))
