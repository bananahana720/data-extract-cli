"""File discovery helpers shared by CLI and API."""

from __future__ import annotations

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
    ) -> Tuple[List[Path], Path]:
        """Resolve files and return (file_list, source_dir)."""
        input_str = str(input_path)
        if self.is_glob_pattern(input_str):
            files = self._discover_from_glob(input_str)
            return files, Path.cwd()

        resolved = Path(input_str)
        if not resolved.exists():
            raise FileNotFoundError(f"Source not found: {resolved}")

        if resolved.is_file():
            return self._filter_supported([resolved]), resolved.parent

        pattern = "**/*" if recursive else "*"
        files = [p for p in resolved.glob(pattern) if p.is_file()]
        return self._filter_supported(files), resolved

    def _discover_from_glob(self, pattern: str) -> List[Path]:
        """Expand glob pattern and filter to supported source files."""
        if "**" in pattern:
            sub_pattern = pattern.replace("**/", "")
            matches = list(Path.cwd().rglob(sub_pattern))
        else:
            matches = list(Path.cwd().glob(pattern))
        files = [p for p in matches if p.is_file()]
        return self._filter_supported(files)

    @staticmethod
    def _filter_supported(files: Iterable[Path]) -> List[Path]:
        """Keep only extensions currently supported by extractors."""
        filtered = [f.resolve() for f in files if f.suffix.lower() in SUPPORTED_EXTENSIONS]
        return sorted(set(filtered))
