"""OCR availability detection and user messaging.

Provides graceful degradation messaging when OCR (Tesseract) is unavailable:
- Detects frozen executable (Core Edition) vs source installation
- Checks Tesseract availability at runtime
- Displays user-friendly panels with installation guidance
- Integrates with CLI error handling for scanned PDFs

This module supports the "Core Edition" (frozen executable without OCR)
and "Full Edition" (source installation with OCR support) deployment model.

Example:
    >>> from data_extract.cli.ocr_status import check_ocr_available, show_ocr_unavailable_panel
    >>> from rich.console import Console
    >>>
    >>> available, message = check_ocr_available()
    >>> if not available:
    ...     console = Console()
    ...     show_ocr_unavailable_panel(console)
"""

from __future__ import annotations

import sys
from typing import Tuple

from rich.console import Console
from rich.panel import Panel

# ==============================================================================
# Runtime Environment Detection
# ==============================================================================


def is_frozen() -> bool:
    """Check if running as frozen executable (PyInstaller bundle).

    Frozen executables are typically "Core Edition" without OCR dependencies
    to minimize bundle size and deployment complexity.

    Returns:
        True if running as frozen executable, False if running from source

    Example:
        >>> if is_frozen():
        ...     print("Running as Core Edition")
        ... else:
        ...     print("Running as Full Edition (source)")
    """
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


# ==============================================================================
# OCR Availability Detection
# ==============================================================================


def check_ocr_available() -> Tuple[bool, str]:
    """Check if OCR (Tesseract) is available at runtime.

    Attempts to import pytesseract and verify Tesseract is installed.
    Provides context-aware messaging based on deployment model:
    - Core Edition (frozen): Suggests upgrading to Full Edition
    - Full Edition (source): Provides installation instructions

    Returns:
        Tuple of (available: bool, message: str)
            - available: True if OCR is ready to use
            - message: Success message or installation guidance

    Example:
        >>> available, message = check_ocr_available()
        >>> if not available:
        ...     print(f"OCR unavailable: {message}")
    """
    try:
        import pytesseract  # type: ignore[import-not-found,import-untyped]

        # Attempt to get version to verify Tesseract is actually installed
        # (not just pytesseract package)
        pytesseract.get_tesseract_version()
        return True, "OCR available"
    except Exception:
        # Provide context-aware guidance based on deployment model
        if is_frozen():
            return False, (
                "OCR is not available in Core Edition.\n"
                "To process scanned documents, install Full Edition with OCR support."
            )
        else:
            return False, (
                "Tesseract OCR not found.\n"
                "Install Tesseract and ensure it's in your PATH:\n"
                "  Windows: https://github.com/UB-Mannheim/tesseract/wiki\n"
                "  Linux: sudo apt install tesseract-ocr\n"
                "  macOS: brew install tesseract"
            )


# ==============================================================================
# User-Facing UI Components
# ==============================================================================


def show_ocr_unavailable_panel(console: Console) -> None:
    """Display a friendly panel when OCR is needed but unavailable.

    Shows a yellow-bordered informational panel with:
    - Clear explanation of OCR unavailability
    - Context-aware installation/upgrade guidance
    - Non-blocking (informational, not error)

    Args:
        console: Rich Console for output

    Example:
        >>> from rich.console import Console
        >>> console = Console()
        >>> show_ocr_unavailable_panel(console)
        # Displays:
        # ╭─ OCR Not Available ────────────────────╮
        # │ Tesseract OCR not found.               │
        # │ Install Tesseract and ensure it's in   │
        # │ your PATH:                             │
        # │   Windows: https://...                 │
        # │   Linux: sudo apt install tesseract... │
        # │   macOS: brew install tesseract        │
        # ╰────────────────────────────────────────╯
    """
    available, message = check_ocr_available()
    if not available:
        console.print(
            Panel(
                message,
                title="[yellow]OCR Not Available[/yellow]",
                border_style="yellow",
            )
        )


def get_ocr_unavailable_suggestion() -> str:
    """Get a brief OCR unavailable suggestion for error prompts.

    Provides a concise one-line suggestion suitable for error handling
    contexts (e.g., error_prompts.py suggestions dictionary).

    Returns:
        Brief suggestion string (no newlines)

    Example:
        >>> suggestion = get_ocr_unavailable_suggestion()
        >>> print(suggestion)
        Install Tesseract OCR or upgrade to Full Edition
    """
    if is_frozen():
        return "Install Full Edition with OCR support for scanned documents"
    else:
        return "Install Tesseract OCR (see docs for platform-specific instructions)"
