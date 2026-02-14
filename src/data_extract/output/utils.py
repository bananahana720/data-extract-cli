"""Utility functions for output formatting."""

import re
from typing import Any


def clean_text_artifacts(text: str) -> str:
    """Remove markdown and formatting artifacts from text.

    Args:
        text: Text to clean

    Returns:
        Cleaned text without artifacts
    """
    # Remove markdown formatting
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # Bold
    text = re.sub(r"\*(.*?)\*", r"\1", text)  # Italic
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)  # Code blocks
    text = re.sub(r"`(.*?)`", r"\1", text)  # Inline code
    text = re.sub(r"#+\s+", "", text)  # Headers
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)  # Links

    return text.strip()


def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to maximum length with ellipsis.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def normalize_path(path: Any) -> str:
    """Normalize path to string format.

    Args:
        path: Path object or string

    Returns:
        Normalized path string
    """
    if hasattr(path, "as_posix"):
        as_posix = getattr(path, "as_posix", None)
        if callable(as_posix):
            return str(as_posix())
    return str(path)
