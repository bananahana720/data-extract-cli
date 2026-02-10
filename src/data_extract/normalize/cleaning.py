"""Text cleaning and artifact removal.

This module implements the TextCleaner class for removing OCR artifacts,
normalizing whitespace, and detecting/removing headers and footers.

Key classes:
- CleaningResult: Audit log model for transformations (AC-2.1.7)
- TextCleaner: Main text cleaning engine (AC-2.1.1 through AC-2.1.5)
"""

import re
from typing import Any, Dict, List, Optional, Tuple

import yaml
from pydantic import BaseModel, ConfigDict, Field

from data_extract.normalize.config import NormalizationConfig


class CleaningResult(BaseModel):
    """Audit log of text cleaning transformations (AC-2.1.7).

    Captures all cleaning decisions for audit trail and debugging.

    Attributes:
        original_length: Length of text before cleaning
        cleaned_length: Length of text after cleaning
        artifacts_removed: Count of OCR artifacts removed
        headers_footers_removed: Count of headers/footers removed
        whitespace_normalized: Whether whitespace was normalized
        transformations: List of transformation log entries
    """

    model_config = ConfigDict(frozen=False)

    original_length: int = Field(..., ge=0, description="Length of text before cleaning")
    cleaned_length: int = Field(..., ge=0, description="Length of text after cleaning")
    artifacts_removed: int = Field(default=0, ge=0, description="Count of OCR artifacts removed")
    headers_footers_removed: int = Field(
        default=0, ge=0, description="Count of headers/footers removed"
    )
    whitespace_normalized: bool = Field(
        default=False, description="Whether whitespace was normalized"
    )
    transformations: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of transformation log entries"
    )


class TextCleaner:
    """Text cleaning engine for normalization pipeline.

    Implements AC-2.1.1 through AC-2.1.5:
    - OCR artifact removal (AC-2.1.1)
    - Whitespace normalization (AC-2.1.2)
    - Header/footer removal (AC-2.1.3, AC-2.1.4)
    - Formatting preservation (AC-2.1.5)

    Design:
    - Deterministic: Same input + config → same output (AC-2.1.6)
    - Auditable: All transformations logged in CleaningResult (AC-2.1.7)
    - Modular: Each cleaning stage is separate method
    """

    def __init__(self, config: NormalizationConfig):
        """Initialize TextCleaner with configuration.

        Args:
            config: Normalization configuration
        """
        self.config = config
        self._ocr_patterns: List[Tuple[re.Pattern[str], str]] = []
        self._header_footer_patterns: List[Tuple[re.Pattern[str], str]] = []
        self._load_cleaning_patterns()

    def _load_cleaning_patterns(self) -> None:
        """Load cleaning patterns from YAML configuration file.

        Loads OCR artifact patterns and header/footer patterns.
        Patterns are compiled into regex objects for performance.
        """
        # Load OCR artifact patterns
        if (
            self.config.ocr_artifact_patterns_file
            and self.config.ocr_artifact_patterns_file.exists()
        ):
            with open(self.config.ocr_artifact_patterns_file, "r", encoding="utf-8") as f:
                rules = yaml.safe_load(f) or {}

            ocr_artifacts = rules.get("ocr_artifacts", [])
            for artifact in ocr_artifacts:
                pattern = artifact.get("pattern")
                replacement = artifact.get("replacement", "")
                if pattern:
                    try:
                        compiled_pattern = re.compile(pattern)
                        self._ocr_patterns.append((compiled_pattern, replacement))
                    except re.error:
                        # Skip invalid patterns
                        pass

            # Load header/footer patterns
            headers_footers = rules.get("headers_footers", [])
            for hf in headers_footers:
                pattern = hf.get("pattern")
                case_insensitive = hf.get("case_insensitive", False)
                if pattern:
                    try:
                        flags = re.IGNORECASE if case_insensitive else 0
                        compiled_pattern = re.compile(pattern, flags)
                        self._header_footer_patterns.append((compiled_pattern, ""))
                    except re.error:
                        # Skip invalid patterns
                        pass

        # Fallback: Default patterns if no file or empty file
        if not self._ocr_patterns:
            self._ocr_patterns = [
                (re.compile(r"\^{3,}"), ""),  # Multiple carets
                (re.compile(r"■{3,}"), ""),  # Multiple filled squares
                (re.compile(r"~{3,}"), ""),  # Multiple tildes
                (re.compile(r"_{10,}"), ""),  # Long underscores
                (re.compile(r"-{10,}"), ""),  # Long dashes
                (re.compile(r"={10,}"), ""),  # Long equals
                (re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]"), ""),  # Control characters
            ]

        if not self._header_footer_patterns:
            self._header_footer_patterns = [
                (re.compile(r"Page\s+\d+(\s+of\s+\d+)?", re.IGNORECASE), ""),
                (re.compile(r"^\d+\s*$"), ""),
                (re.compile(r"Confidential", re.IGNORECASE), ""),
                (re.compile(r"DRAFT", re.IGNORECASE), ""),
            ]

    def clean_text(self, text: str, doc_type: Optional[str] = None) -> Tuple[str, CleaningResult]:
        """Clean text through all configured stages.

        Main entry point for text cleaning. Applies transformations
        in deterministic order: OCR artifacts → whitespace → headers/footers.

        Args:
            text: Raw extracted text
            doc_type: Document type for type-specific rules (optional)

        Returns:
            Tuple of (cleaned_text, cleaning_result_audit_log)

        Examples:
            >>> cleaner = TextCleaner(config)
            >>> cleaned, result = cleaner.clean_text("Text with ^^^^^ noise")
            >>> assert "^^^^^" not in cleaned
            >>> assert result.artifacts_removed > 0
        """
        cleaned = text
        result = CleaningResult(original_length=len(text), cleaned_length=len(text))

        # Stage 1: OCR artifact removal (AC-2.1.1)
        if self.config.remove_ocr_artifacts:
            cleaned, artifacts_count = self.remove_ocr_artifacts(cleaned)
            result.artifacts_removed = artifacts_count

        # Stage 2: Whitespace normalization (AC-2.1.2, AC-2.1.5)
        if self.config.normalize_whitespace:
            cleaned, normalized = self.normalize_whitespace(cleaned)
            result.whitespace_normalized = normalized

        # Stage 3: Header/footer removal for single-block text (AC-2.1.3)
        # Note: Multi-page header/footer detection (AC-2.1.4) handled by Normalizer

        result.cleaned_length = len(cleaned)
        return cleaned, result

    def remove_ocr_artifacts(self, text: str) -> Tuple[str, int]:
        """Remove OCR artifacts from text (AC-2.1.1).

        Detects and removes:
        - Garbled characters (^^^^^, ■■■■, ~~~)
        - Repeated symbols (long underscores, dashes)
        - Random character sequences
        - Control characters

        Args:
            text: Text to clean

        Returns:
            Tuple of (cleaned_text, artifacts_removed_count)

        Examples:
            >>> cleaned, count = cleaner.remove_ocr_artifacts("Text ^^^^^ noise")
            >>> assert "^^^^^" not in cleaned
            >>> assert count == 1
        """
        cleaned = text
        artifacts_removed = 0

        for pattern, replacement in self._ocr_patterns:
            matches = pattern.findall(cleaned)
            if matches:
                artifacts_removed += len(matches)
                cleaned = pattern.sub(replacement, cleaned)

        return cleaned, artifacts_removed

    def normalize_whitespace(self, text: str) -> Tuple[str, bool]:
        """Normalize whitespace while preserving formatting (AC-2.1.2, AC-2.1.5).

        Normalization rules:
        - Multiple spaces → single space (within lines)
        - Multiple newlines → max 2 newlines (preserve paragraph breaks)
        - Tabs normalized to spaces
        - Leading/trailing whitespace trimmed per block

        Preserves:
        - Paragraph breaks (double newlines)
        - Intentional indentation (code blocks, lists)
        - Markdown formatting

        Args:
            text: Text to normalize

        Returns:
            Tuple of (normalized_text, was_normalized)

        Examples:
            >>> normalized, changed = cleaner.normalize_whitespace("Text   with\\n\\n\\n\\nspaces")
            >>> assert "  " not in normalized  # Multiple spaces removed
            >>> assert "\\n\\n" in normalized  # Paragraph breaks preserved
        """
        original = text
        cleaned = text

        # Normalize tabs to spaces
        cleaned = cleaned.replace("\t", " " * 4)

        # Normalize multiple spaces to single space (within lines)
        # But preserve intentional indentation at start of lines
        lines = cleaned.split("\n")
        normalized_lines = []
        for line in lines:
            # Preserve leading whitespace (for code blocks, lists)
            leading_space = len(line) - len(line.lstrip(" "))
            content = line.lstrip(" ")

            # Normalize multiple spaces within content
            content = re.sub(r" {2,}", " ", content)

            # Reconstruct line with preserved leading space
            normalized_line = (" " * leading_space) + content if leading_space > 0 else content
            normalized_lines.append(normalized_line)

        cleaned = "\n".join(normalized_lines)

        # Normalize multiple newlines (max 2 consecutive = paragraph break)
        max_newlines = self.config.whitespace_max_consecutive_newlines
        cleaned = re.sub(r"\n{3,}", "\n" * max_newlines, cleaned)

        # Trim leading/trailing whitespace from entire block
        cleaned = cleaned.strip()

        was_normalized = cleaned != original
        return cleaned, was_normalized

    def detect_headers_footers(self, pages: List[str]) -> Tuple[Optional[str], Optional[str]]:
        """Detect repeated headers/footers across pages (AC-2.1.4).

        Multi-page repetition analysis:
        - Extracts top 10% of each page (potential header)
        - Extracts bottom 10% of each page (potential footer)
        - Finds common substrings across >= header_repetition_threshold pages
        - Returns most common patterns

        Args:
            pages: List of page texts (one per page)

        Returns:
            Tuple of (header_pattern, footer_pattern) or (None, None)

        Algorithm:
        - Extract top/bottom regions from each page
        - Find longest common substring across pages
        - Require threshold minimum (default: 3 pages)
        - Return patterns if found, else None

        Examples:
            >>> pages = ["Page 1\\nContent", "Page 2\\nContent", "Page 3\\nContent"]
            >>> header, footer = cleaner.detect_headers_footers(pages)
            >>> assert "Page" in header  # Repeated header detected
        """
        if len(pages) < self.config.header_repetition_threshold:
            return None, None

        # Extract header regions (top 10% of each page)
        header_regions = []
        for page in pages:
            lines = page.split("\n")
            header_line_count = max(1, len(lines) // 10)
            header_text = "\n".join(lines[:header_line_count])
            header_regions.append(header_text.strip())

        # Extract footer regions (bottom 10% of each page)
        footer_regions = []
        for page in pages:
            lines = page.split("\n")
            footer_line_count = max(1, len(lines) // 10)
            footer_text = "\n".join(lines[-footer_line_count:])
            footer_regions.append(footer_text.strip())

        # Find common header pattern
        header_pattern = self._find_common_pattern(header_regions)

        # Find common footer pattern
        footer_pattern = self._find_common_pattern(footer_regions)

        return header_pattern, footer_pattern

    def _find_common_pattern(self, regions: List[str]) -> Optional[str]:
        """Find common substring across regions.

        Args:
            regions: List of text regions

        Returns:
            Common pattern if found, else None
        """
        if not regions:
            return None

        # Simple approach: Find exact matches
        # More sophisticated: Use longest common substring algorithm
        first_region = regions[0]

        # Check if first region appears in threshold number of pages
        match_count = sum(1 for region in regions if first_region in region)

        if match_count >= self.config.header_repetition_threshold:
            return first_region

        # Try line-by-line matching (more flexible)
        first_lines = first_region.split("\n")
        for line in first_lines:
            if len(line.strip()) > 5:  # Ignore very short lines
                match_count = sum(1 for region in regions if line in region)
                if match_count >= self.config.header_repetition_threshold:
                    return line

        return None

    def remove_headers_footers(
        self, pages: List[str], header: Optional[str], footer: Optional[str]
    ) -> List[str]:
        """Remove detected headers/footers from pages (AC-2.1.3).

        Args:
            pages: List of page texts
            header: Header pattern to remove
            footer: Footer pattern to remove

        Returns:
            List of cleaned pages

        Examples:
            >>> pages = ["Header\\nContent\\nFooter"] * 3
            >>> cleaned = cleaner.remove_headers_footers(pages, "Header", "Footer")
            >>> assert all("Header" not in p for p in cleaned)
        """
        cleaned_pages = []

        for page in pages:
            cleaned_page = page

            # Remove header
            if header:
                cleaned_page = cleaned_page.replace(header, "")

            # Remove footer
            if footer:
                cleaned_page = cleaned_page.replace(footer, "")

            # Also apply pattern-based header/footer removal
            if self.config.remove_headers_footers:
                for pattern, replacement in self._header_footer_patterns:
                    cleaned_page = pattern.sub(replacement, cleaned_page)

            cleaned_pages.append(cleaned_page.strip())

        return cleaned_pages
