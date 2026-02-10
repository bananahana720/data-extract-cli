"""
Runtime hook for Tesseract OCR and Poppler in PyInstaller bundles.

This hook configures paths for Tesseract tessdata and adds tesseract/poppler
binaries to PATH when running as a frozen executable.
"""

import os
import sys


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
        poppler_bin = os.path.join(bundle_dir, "poppler", "bin")

        current_path = os.environ.get("PATH", "")
        new_path = f"{tesseract_bin}{os.pathsep}{poppler_bin}{os.pathsep}{current_path}"
        os.environ["PATH"] = new_path

        print(f"[Runtime Hook] TESSDATA_PREFIX set to: {tessdata_path}")
        print(f"[Runtime Hook] Added to PATH: {tesseract_bin}, {poppler_bin}")


# Execute on import
setup_tesseract_and_poppler()
