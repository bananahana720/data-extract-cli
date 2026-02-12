# -*- mode: python ; coding: utf-8 -*-
# ruff: noqa: F821
"""
PyInstaller spec file for data-extraction-tool.

Usage:
    pyinstaller build_scripts/data_extract.spec

Output:
    dist/data_extract/ - Distributable folder with executable

Note:
    Analysis, PYZ, EXE, and COLLECT are PyInstaller globals injected at runtime.
"""

import datetime
import platform
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, copy_metadata

# Get absolute paths
SPEC_ROOT = Path(__file__).parent.resolve()
PROJECT_ROOT = SPEC_ROOT.parent
SRC_DIR = PROJECT_ROOT / "src"
ENTRY_POINT = SRC_DIR / "data_extract" / "app.py"
ASSETS_DIR = SPEC_ROOT / "assets"
ICON_PATH = ASSETS_DIR / "icon.ico"
VENDOR_DIR = SPEC_ROOT / "vendor"

# Import version information from centralized version.py
sys.path.insert(0, str(SPEC_ROOT))
from version import __app_name__, __version__  # noqa: E402, F401

# Build metadata
BUILD_METADATA = {
    "build_date": datetime.datetime.now().isoformat(),
    "python_version": platform.python_version(),
    "platform": platform.platform(),
    "app_version": __version__,
    "app_name": __app_name__,
}

# Log build metadata
print(f"Build metadata: {BUILD_METADATA}")

block_cipher = None

# Collect hidden imports for critical dependencies
hidden_imports = [
    # spaCy and its dependencies
    "spacy",
    "spacy.lang.en",
    "thinc",
    "thinc.backends",
    "cymem",
    "preshed",
    "murmurhash",
    "blis",
    "srsly",
    "wasabi",
    "catalogue",
    "confection",
    # scikit-learn and dependencies
    "sklearn",
    "sklearn.feature_extraction.text",
    "sklearn.decomposition",
    "sklearn.utils._typedefs",
    "sklearn.utils._heap",
    "sklearn.tree._utils",
    "sklearn.metrics.pairwise",
    # Pydantic v2
    "pydantic",
    "pydantic_core",
    "annotated_types",
    "pydantic.deprecated",
    "pydantic.deprecated.decorator",
    # scikit-learn hidden dependencies
    "sklearn.neighbors._partition_nodes",
    "sklearn.utils._weight_vector",
    "sklearn.utils._typedefs",
    # joblib hidden dependencies
    "joblib.externals.loky",
    "joblib.externals.cloudpickle",
    # CLI dependencies
    "typer",
    "typer.core",
    "rich",
    "InquirerPy",
    "click._bashcomplete",
    # Additional core dependencies
    "textstat",
    "joblib",
]

# Collect data files for key packages
datas = []

# Collect spaCy model data
datas += collect_data_files("en_core_web_md")

# Collect package data from data_extract
datas += collect_data_files("data_extract")

# Copy package metadata (required for version detection)
datas += copy_metadata("pydantic")
datas += copy_metadata("pydantic_core")
datas += copy_metadata("spacy")
datas += copy_metadata("scikit-learn")
datas += copy_metadata("typer")

# Include OCR binaries when available (Full build).
tesseract_vendor = VENDOR_DIR / "tesseract"
if tesseract_vendor.exists():
    print(f"Including bundled Tesseract: {tesseract_vendor}")
    datas.append((str(tesseract_vendor), "tesseract"))

poppler_vendor = VENDOR_DIR / "poppler"
if poppler_vendor.exists():
    print(f"Including bundled Poppler: {poppler_vendor}")
    datas.append((str(poppler_vendor), "poppler"))

# Analysis configuration
a = Analysis(
    [str(ENTRY_POINT)],  # Entry point
    pathex=[str(SRC_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=["hooks"],  # Custom hooks directory
    hooksconfig={},
    runtime_hooks=[
        "runtime_hook_spacy.py",
        "runtime_hook_tesseract.py",
    ],
    excludes=[
        # Exclude unnecessary GUI/dev dependencies
        "matplotlib",
        "tkinter",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "jupyter",
        "IPython",
        "pytest",
        "black",
        "ruff",
        "mypy",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="data-extract",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX compression (causes issues with large binaries)
    console=True,  # CLI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON_PATH) if ICON_PATH.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="data_extract",
)
