"""
Runtime hook for spaCy model loading in PyInstaller bundles.

This hook ensures spaCy can locate the bundled en_core_web_md model
when running as a frozen executable.
"""

import os
import sys


def setup_spacy_model_path():
    """Configure spaCy model path for frozen executables."""
    # Check if running as a PyInstaller bundle
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Running in a PyInstaller bundle
        bundle_dir = sys._MEIPASS
        model_path = os.path.join(bundle_dir, "en_core_web_md", "en_core_web_md")

        # Set environment variable to override spaCy's model search
        os.environ["SPACY_MODEL_PATH_OVERRIDE"] = model_path

        print(f"[Runtime Hook] spaCy model path set to: {model_path}")


# Execute on import
setup_spacy_model_path()
