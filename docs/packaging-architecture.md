# Windows Packaging Architecture

## Overview

### Goal
Package the Data Extraction Tool as a standalone Windows installer for non-technical users who need to process enterprise documents without Python knowledge or development environment setup.

### Target Users
- Enterprise audit teams processing corporate documents
- Business analysts extracting data from mixed-format document collections
- Non-technical Windows users requiring offline document processing

### Package Variants

| Variant | Installer Size | Installed Size | Features |
|---------|---------------|----------------|----------|
| **Core** (Step 1) | ~80 MB | ~190 MB | PDF, DOCX, XLSX, PPTX, CSV, TXT extraction |
| **Full + OCR** (Step 2) | ~120 MB | ~270 MB | Core + OCR for scanned documents/images |

### Entry Point
```
src/data_extract/app.py -> data_extract.app:app (Typer CLI)
```

Available commands: `process`, `extract`, `retry`, `validate`, `status`, `semantic`, `cache`, `config`, `session`

---

## Architecture Decisions

### ADR-P1: PyInstaller over Nuitka/cx_Freeze

**Status**: Accepted

**Context**: Need to bundle Python application with spaCy NLP models and scikit-learn into Windows executable.

**Decision**: Use PyInstaller

**Rationale**:
- Mature ecosystem with 15+ years of production use
- Built-in hooks for spaCy, scikit-learn, numpy, pydantic
- Extensive documentation and community support
- Proven track record with NLP/ML applications
- cx_Freeze lacks spaCy hooks; Nuitka compilation complexity with C extensions

**Consequences**:
- Requires runtime hooks for spaCy model paths
- Must manage hidden imports explicitly
- Cannot cross-compile (must build ON Windows)

---

### ADR-P2: One-Folder Mode over Onefile

**Status**: Accepted

**Context**: PyInstaller offers `--onefile` (single EXE) vs `--onedir` (folder with EXE + dependencies).

**Decision**: Use one-folder mode (COLLECT)

**Rationale**:
- Faster startup (no temp extraction on each launch)
- Easier debugging (can inspect bundled files)
- Better compatibility with antivirus software
- Simpler spaCy model integration (visible in `_internal/` folder)
- Smaller disk footprint (no duplicate extraction to temp)

**Consequences**:
- Installer distributes folder structure, not single file
- Users see `_internal/` folder alongside `data-extract.exe`
- Inno Setup handles folder packaging transparently

---

### ADR-P3: Pre-Bundle spaCy Model

**Status**: Accepted

**Context**: spaCy requires `en_core_web_md` model (~40MB) for sentence segmentation in chunking stage.

**Decision**: Bundle model during build, not download at runtime

**Rationale**:
- Offline installation (enterprise environments often have restricted internet)
- Deterministic builds (same model version across all installs)
- No first-run delays or download failures
- Model path resolved via `sys._MEIPASS` in frozen environment

**Consequences**:
- Increases installer size by ~40MB
- Build process must download model to staging directory
- Runtime hook required to set spaCy data path

---

### ADR-P4: Per-User Installation

**Status**: Accepted

**Context**: Enterprise environments often restrict admin privileges for end users.

**Decision**: Install to `%LOCALAPPDATA%` with `PrivilegesRequired=lowest`

**Rationale**:
- No admin rights required (enterprise-friendly)
- User-isolated installation (no system-wide conflicts)
- Standard pattern for modern Windows applications
- Avoids UAC prompts during installation

**Consequences**:
- Each user has separate installation
- Updates apply per-user, not system-wide
- Uninstall available through standard Windows mechanisms

---

### ADR-P5: Graceful OCR Degradation

**Status**: Accepted

**Context**: Full variant includes Tesseract OCR which requires additional system dependencies.

**Decision**: Core variant works without Tesseract; OCR features disabled gracefully

**Rationale**:
- Core users don't need OCR overhead
- Missing Tesseract produces clear warning, not crash
- OCR variant bundles Tesseract binaries and tessdata

**Consequences**:
- Two build configurations (core vs full)
- Runtime detection of Tesseract availability
- User-friendly error messages when OCR unavailable

---

## Build Workflow

### Critical Constraint
**PyInstaller cannot cross-compile.** Windows executables MUST be built ON Windows.

### Orchestration Architecture

```
WSL/Linux (Orchestration)          Windows (Execution)
    |                                    |
    | 1. Prepare sources                 |
    | 2. Generate build scripts          |
    |-------------------------------->   |
    |    (PowerShell via pwsh.exe)       |
    |                                    | 3. Create venv
    |                                    | 4. Install deps
    |                                    | 5. Download spaCy model
    |                                    | 6. Run PyInstaller
    |                                    | 7. Run Inno Setup
    |    <--------------------------------|
    | 8. Retrieve installer              |
    |                                    |
```

### Build Steps

1. **Environment Setup** (Windows PowerShell)
   ```powershell
   python -m venv .venv-build
   .\.venv-build\Scripts\Activate.ps1
   pip install -e ".[dev]"
   python -m spacy download en_core_web_md
   ```

2. **PyInstaller Execution**
   ```powershell
   pyinstaller build_scripts/data-extract.spec --clean --noconfirm
   ```

3. **Inno Setup Compilation**
   ```powershell
   & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" build_scripts\installer.iss
   ```

4. **Output**: `dist/DataExtractionTool-Setup-1.0.0.exe`

---

## Hidden Imports

PyInstaller's dependency analysis misses dynamically-imported modules. The following must be explicitly declared in the spec file:

### spaCy Ecosystem
```python
hiddenimports = [
    'spacy',
    'spacy.lang.en',
    'thinc',
    'thinc.api',
    'cymem',
    'cymem.cymem',
    'preshed',
    'preshed.maps',
    'murmurhash',
    'murmurhash.mrmr',
    'blis',
    'blis.py',
    'srsly',
    'srsly.msgpack',
    'wasabi',
    'catalogue',
    'confection',
]
```

### scikit-learn Components
```python
hiddenimports += [
    'sklearn',
    'sklearn.utils._typedefs',
    'sklearn.utils._heap',
    'sklearn.utils._sorting',
    'sklearn.utils._vector_sentinel',
    'sklearn.tree._utils',
    'sklearn.neighbors._partition_nodes',
    'sklearn.feature_extraction.text',
    'sklearn.decomposition',
    'sklearn.metrics.pairwise',
]
```

### Pydantic v2
```python
hiddenimports += [
    'pydantic',
    'pydantic_core',
    'pydantic_core._pydantic_core',
    'annotated_types',
]
```

### Application Modules
```python
hiddenimports += [
    'data_extract',
    'data_extract.app',
    'data_extract.cli',
    'data_extract.cli.base',
    'data_extract.extract',
    'data_extract.normalize',
    'data_extract.chunk',
    'data_extract.semantic',
    'data_extract.output',
]
```

---

## Runtime Hooks

### spaCy Model Path Resolution

**File**: `build_scripts/hooks/hook-spacy.py`

```python
"""Runtime hook for spaCy model path resolution in frozen environment."""
import os
import sys

def _setup_spacy_data():
    """Configure spaCy to find bundled model data."""
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        bundle_dir = sys._MEIPASS
        spacy_data = os.path.join(bundle_dir, 'spacy_data')
        if os.path.exists(spacy_data):
            os.environ['SPACY_DATA'] = spacy_data

_setup_spacy_data()
```

### Tesseract OCR Path (Full Variant Only)

**File**: `build_scripts/hooks/hook-tesseract.py`

```python
"""Runtime hook for Tesseract OCR path resolution."""
import os
import sys

def _setup_tesseract():
    """Configure Tesseract paths in frozen environment."""
    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS
        tesseract_dir = os.path.join(bundle_dir, 'tesseract')
        tessdata_dir = os.path.join(tesseract_dir, 'tessdata')

        if os.path.exists(tesseract_dir):
            # Set Tesseract executable path
            os.environ['TESSERACT_CMD'] = os.path.join(tesseract_dir, 'tesseract.exe')
            # Set tessdata path
            os.environ['TESSDATA_PREFIX'] = tessdata_dir

_setup_tesseract()
```

---

## File Structure

```
build_scripts/
    data-extract.spec          # PyInstaller spec file
    installer.iss              # Inno Setup script
    build.ps1                  # PowerShell build orchestration
    hooks/
        hook-spacy.py          # spaCy runtime hook
        hook-tesseract.py      # Tesseract runtime hook (full variant)
    resources/
        icon.ico               # Application icon (256x256)
        license.txt            # License for installer display
        readme.txt             # Post-install readme
```

### PyInstaller Spec File Template

**File**: `build_scripts/data-extract.spec`

```python
# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Data Extraction Tool."""

import os
import sys
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(SPECPATH).parent
SRC_DIR = PROJECT_ROOT / 'src'

# Determine variant
VARIANT = os.environ.get('BUILD_VARIANT', 'core')  # 'core' or 'full'

# Hidden imports (see section above for complete list)
hiddenimports = [
    # spaCy ecosystem
    'spacy', 'spacy.lang.en', 'thinc', 'thinc.api',
    'cymem', 'cymem.cymem', 'preshed', 'preshed.maps',
    'murmurhash', 'murmurhash.mrmr', 'blis', 'blis.py',
    'srsly', 'srsly.msgpack', 'wasabi', 'catalogue', 'confection',
    # scikit-learn
    'sklearn', 'sklearn.utils._typedefs', 'sklearn.utils._heap',
    'sklearn.utils._sorting', 'sklearn.utils._vector_sentinel',
    'sklearn.tree._utils', 'sklearn.neighbors._partition_nodes',
    'sklearn.feature_extraction.text', 'sklearn.decomposition',
    'sklearn.metrics.pairwise',
    # Pydantic v2
    'pydantic', 'pydantic_core', 'pydantic_core._pydantic_core',
    'annotated_types',
    # Application
    'data_extract', 'data_extract.app', 'data_extract.cli',
    'data_extract.cli.base', 'data_extract.extract',
    'data_extract.normalize', 'data_extract.chunk',
    'data_extract.semantic', 'data_extract.output',
]

# Data files to bundle
datas = [
    # spaCy model (downloaded during build)
    ('.venv-build/Lib/site-packages/en_core_web_md', 'spacy_data/en_core_web_md'),
]

# Runtime hooks
runtime_hooks = [
    'build_scripts/hooks/hook-spacy.py',
]

if VARIANT == 'full':
    # Add Tesseract binaries for OCR variant
    datas.append(('tesseract/', 'tesseract/'))
    runtime_hooks.append('build_scripts/hooks/hook-tesseract.py')

# Analysis
a = Analysis(
    ['src/data_extract/app.py'],
    pathex=[str(SRC_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['build_scripts/hooks'],
    hooksconfig={},
    runtime_hooks=runtime_hooks,
    excludes=[
        'tkinter', 'matplotlib', 'PIL.ImageTk',
        'pytest', 'black', 'ruff', 'mypy',
    ],
    noarchive=False,
)

# Remove unnecessary files
a.binaries = [x for x in a.binaries if not x[0].startswith('api-ms-win-')]

# PYZ archive
pyz = PYZ(a.pure)

# Executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='data-extract',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # CRITICAL: UPX breaks numpy/scipy
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='build_scripts/resources/icon.ico',
)

# Collect into folder
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,  # CRITICAL: UPX breaks numpy/scipy
    upx_exclude=[],
    name='data-extract',
)
```

### Inno Setup Script Template

**File**: `build_scripts/installer.iss`

```iss
; Inno Setup Script for Data Extraction Tool
; Per-user installation (no admin required)

#define MyAppName "Data Extraction Tool"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Organization"
#define MyAppExeName "data-extract.exe"
#define MyAppAssocName "Document Processor"

[Setup]
AppId={{GUID-GENERATE-NEW}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\DataExtractionTool
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=DataExtractionTool-Setup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
LicenseFile=resources\license.txt
SetupIconFile=resources\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "addtopath"; Description: "Add to PATH (recommended)"; GroupDescription: "System Integration:"; Flags: checkedonce

[Files]
; Main application folder (PyInstaller one-folder output)
Source: "..\dist\data-extract\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Add to user PATH if selected
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Tasks: addtopath; Check: NeedsAddPath(ExpandConstant('{app}'))

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--version"; Description: "Verify installation"; Flags: nowait postinstall skipifsilent shellexec

[Code]
// Check if path needs to be added
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER,
    'Environment',
    'Path', OrigPath)
  then begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;
```

---

## Self-Signed Certificate

For code signing during development/testing (production should use EV certificate):

### Generate Certificate (PowerShell - Run Once)

```powershell
# Generate self-signed code signing certificate
$cert = New-SelfSignedCertificate `
    -Type CodeSigningCert `
    -Subject "CN=Data Extraction Tool Dev, O=YourOrg, C=US" `
    -KeyAlgorithm RSA `
    -KeyLength 2048 `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -NotAfter (Get-Date).AddYears(3) `
    -FriendlyName "Data Extraction Tool Code Signing"

# Export to PFX (with password)
$pwd = ConvertTo-SecureString -String "YourSecurePassword" -Force -AsPlainText
Export-PfxCertificate -Cert $cert -FilePath ".\build_scripts\codesign.pfx" -Password $pwd

# Display thumbprint for reference
Write-Host "Certificate thumbprint: $($cert.Thumbprint)"
```

### Sign Executable (During Build)

```powershell
# Sign the executable
$cert = Get-ChildItem -Path Cert:\CurrentUser\My -CodeSigningCert |
    Where-Object { $_.FriendlyName -eq "Data Extraction Tool Code Signing" }

Set-AuthenticodeSignature `
    -FilePath ".\dist\data-extract\data-extract.exe" `
    -Certificate $cert `
    -TimestampServer "http://timestamp.digicert.com"
```

---

## Success Criteria

### Core Variant (Step 1) Verification

| Check | Command/Action | Expected Result |
|-------|---------------|-----------------|
| Install completes | Run `DataExtractionTool-Setup-1.0.0.exe` | No errors, installs to `%LOCALAPPDATA%` |
| No admin prompt | Observe UAC behavior | No elevation requested |
| Version check | `data-extract --version` | Shows "v1.0.0" |
| Help displays | `data-extract --help` | Shows all 9 commands |
| PDF extraction | `data-extract process test.pdf -o output/` | Produces JSON/TXT output |
| DOCX extraction | `data-extract process test.docx -o output/` | Produces JSON/TXT output |
| XLSX extraction | `data-extract process test.xlsx -o output/` | Produces JSON/TXT output |
| Semantic analysis | `data-extract semantic analyze output/` | TF-IDF/LSA metrics generated |
| Config management | `data-extract config show` | Displays current configuration |
| Uninstall clean | Windows Settings > Uninstall | Removes all files |

### Full + OCR Variant (Step 2) Verification

| Check | Command/Action | Expected Result |
|-------|---------------|-----------------|
| All Core checks | (see above) | Pass |
| OCR available | `data-extract process scanned.pdf -o output/` | Text extracted from images |
| OCR graceful | Remove Tesseract, run OCR | Warning message, no crash |
| Installer size | Check file size | ~120 MB |
| Installed size | Check folder size | ~270 MB |

### Build Verification Checklist

- [ ] PyInstaller runs without errors
- [ ] No UPX compression applied (verify `upx=False`)
- [ ] spaCy model bundled in `_internal/spacy_data/`
- [ ] All hidden imports resolved (no runtime import errors)
- [ ] Inno Setup compiles successfully
- [ ] Installer runs on clean Windows 10/11 VM
- [ ] All 9 CLI commands functional
- [ ] Processing pipeline completes end-to-end
- [ ] Semantic analysis generates valid reports

---

## Appendix: Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'sklearn.utils._typedefs'` | Missing hidden import | Add to `hiddenimports` in spec |
| spaCy model not found | Path not resolved | Verify runtime hook sets `SPACY_DATA` |
| DLL load failed | UPX compression | Ensure `upx=False` for numpy/scipy |
| "Windows protected your PC" | Unsigned executable | Sign with certificate or dismiss SmartScreen |
| Slow startup | Onefile mode extraction | Use onedir mode (COLLECT) |

### Debug Mode Build

```powershell
# Build with debug output
pyinstaller build_scripts/data-extract.spec --clean --noconfirm --log-level DEBUG 2>&1 | Tee-Object build.log
```

### Inspect Bundle Contents

```powershell
# List bundled files
Get-ChildItem -Path .\dist\data-extract\_internal\ -Recurse |
    Select-Object FullName, Length |
    Sort-Object Length -Descending |
    Select-Object -First 50
```
