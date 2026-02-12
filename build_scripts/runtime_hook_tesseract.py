"""
Runtime hook for Tesseract OCR and Poppler in PyInstaller bundles.

This hook configures paths for Tesseract tessdata and adds tesseract/poppler
binaries to PATH when running as a frozen executable.
"""

import os
import sys


def _resolve_poppler_bin(bundle_dir: str) -> str | None:
    candidates = (
        os.path.join(bundle_dir, "poppler", "Library", "bin"),
        os.path.join(bundle_dir, "poppler", "bin"),
    )
    for candidate in candidates:
        if os.path.isdir(candidate):
            return candidate
    return None


def setup_tesseract_and_poppler():
    """Configure Tesseract and Poppler paths for frozen executables."""
    # Check if running as a PyInstaller bundle
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Running in a PyInstaller bundle
        bundle_dir = sys._MEIPASS

        # Set Tesseract data directory
        tessdata_path = os.path.join(bundle_dir, "tesseract", "tessdata")
        os.environ["TESSDATA_PREFIX"] = tessdata_path

        # Add tesseract and poppler to PATH
        tesseract_bin = os.path.join(bundle_dir, "tesseract")
        poppler_bin = _resolve_poppler_bin(bundle_dir)

        current_path = os.environ.get("PATH", "")
        path_parts = [tesseract_bin]
        if poppler_bin:
            path_parts.append(poppler_bin)
        path_parts.append(current_path)
        new_path = os.pathsep.join(path_parts)
        os.environ["PATH"] = new_path

        print(f"[Runtime Hook] TESSDATA_PREFIX set to: {tessdata_path}")
        print(f"[Runtime Hook] Added to PATH: {tesseract_bin}, {poppler_bin or 'poppler missing'}")


# Execute on import
setup_tesseract_and_poppler()
