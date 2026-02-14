# Build Documentation - Data Extraction Tool

Complete guide for building Windows executables and installers for the Data Extraction Tool.

## Prerequisites

### Required

- **Windows 10/11 (64-bit)**: The build process is designed for 64-bit Windows systems
- **Python 3.11+**: Must be installed from [python.org](https://www.python.org/downloads/), NOT Windows Store version
  - Windows Store Python has restricted file system access that breaks PyInstaller
  - Verify with: `python --version` (should show 3.11 or higher)

### Optional

- **Inno Setup 6.x**: Required for creating Windows installers
  - Download from [jrsoftware.org](https://jrsoftware.org/isdl.php)
  - If not installed, use `-SkipInstaller` flag to build executable only
- **Git**: For version control and automated version detection
  - Download from [git-scm.com](https://git-scm.com/download/win)

## Quick Start

### From Windows PowerShell

```powershell
# Basic build (clean rebuild)
.\build_scripts\build_windows.ps1 -Clean

# Build without installer
.\build_scripts\build_windows.ps1 -Clean -SkipInstaller

# Full build with OCR support
.\build_scripts\build_windows.ps1 -Clean -Full
```

### From WSL (Windows Subsystem for Linux)

```bash
# Basic build (clean rebuild)
python build_scripts/build_orchestrator.py --clean

# Build without installer
python build_scripts/build_orchestrator.py --clean --skip-installer

# Full build with OCR support
python build_scripts/build_orchestrator.py --clean --full
```

## Build Options

### PowerShell Flags (`build_windows.ps1`)

| Flag | Description |
|------|-------------|
| `-Clean` | Remove all previous build artifacts before building |
| `-SkipInstaller` | Build executable only, skip Inno Setup installer creation |
| `-Full` | Include OCR dependencies (Tesseract + Poppler) in the build |

### Python Flags (`build_orchestrator.py`)

| Flag | Description |
|------|-------------|
| `--clean` | Remove all previous build artifacts before building |
| `--skip-installer` | Build executable only, skip Inno Setup installer creation |
| `--full` | Include OCR dependencies (Tesseract + Poppler) in the build |

## Build Outputs

### Standard Build

- **`dist/data_extract/data-extract.exe`**: Standalone executable (~150MB)
  - Single-file bundle containing Python runtime, dependencies, and application code
  - Can be distributed as-is or via installer

- **`dist/DataExtractionTool-Setup-1.0.0.exe`**: Windows installer (~160MB)
  - Professional installer with Start Menu shortcuts
  - Uninstaller included
  - Registry integration for file associations (optional)

### Full Build (with OCR)

- **`dist/data_extract/data-extract.exe`**: Standalone executable (~230MB)
  - Includes Tesseract OCR and Poppler utilities

- **`dist/DataExtractionTool-Setup-1.0.0.exe`**: Windows installer (~240MB)

### Intermediate Artifacts

- **`build/`**: PyInstaller temporary build files (can be deleted)
- **`dist/data_extract/`**: Directory containing executable and dependencies

## OCR Dependencies (Full Build)

### Downloading OCR Dependencies

```bash
# Download and verify Tesseract + Poppler
python build_scripts/download_ocr_dependencies.py

# Override defaults for flaky networks or a specific Poppler release
python build_scripts/download_ocr_dependencies.py --max-retries 5 --backoff-ms 1500 --poppler-version 24.08.0

# Extracted dependencies default to build_scripts/vendor/
```

### OCR Downloader Flags (`download_ocr_dependencies.py`)

| Flag | Description |
|------|-------------|
| `--max-retries` | Number of retry attempts per network request after the first failure (default: `3`) |
| `--backoff-ms` | Initial exponential backoff delay between retries in milliseconds (default: `500`) |
| `--poppler-version` | Pinned Poppler version to download (default: `24.02.0`, not `latest`) |
| `--skip-verify` | Explicitly disables checksum verification (unsafe; use only in trusted dev/test environments) |

### What Gets Downloaded

- **Tesseract 5.3.3** (~50MB compressed)
  - OCR engine for image and PDF text extraction
  - Includes English language data

- **Poppler 24.02.0** (~30MB compressed)
  - PDF rendering utilities for preview generation
  - Includes pdftoppm, pdfinfo, and related tools

### Verification

- SHA256 checksums are verified automatically
- Download failures will abort the build process
- Poppler checksum key is version-specific (`poppler-<version>`)
- `--skip-verify` disables integrity checks and should only be used when you explicitly trust the source

## Troubleshooting

### "Python not found" or "python: command not found"

**Problem**: Python is not in your PATH or using Windows Store version

**Solutions**:
1. Install Python from [python.org](https://www.python.org/downloads/) (NOT Windows Store)
2. During installation, check "Add Python to PATH"
3. Restart PowerShell/terminal after installation
4. Verify: `python --version` should show 3.11+

### "spaCy model not found" Error

**Problem**: Required spaCy language model is not installed

**Solution**:
```bash
# Download and install the medium English model
python -m spacy download en_core_web_md

# Verify installation
python -m spacy validate
```

### "Inno Setup not found"

**Problem**: Inno Setup is not installed or not in PATH

**Solutions**:
1. Install Inno Setup from [jrsoftware.org](https://jrsoftware.org/isdl.php)
2. OR use `-SkipInstaller` flag to build executable only:
   ```powershell
   .\build_scripts\build_windows.ps1 -Clean -SkipInstaller
   ```

### Anti-virus Warnings

**Problem**: Windows Defender or other AV software flags the executable

**Why This Happens**:
- PyInstaller executables are self-extracting archives
- Self-signed executables trigger heuristic warnings
- New executables have no reputation score

**Solutions**:
1. **For Development**: Add `dist/` directory to AV exclusions
2. **For Distribution**:
   - Submit binary to AV vendors for whitelisting
   - Obtain Extended Validation (EV) code signing certificate
   - Sign executable with: `signtool sign /f certificate.pfx dist/data_extract/data-extract.exe`

### Build Fails with "Permission Denied"

**Problem**: Previous build artifacts are locked or in use

**Solutions**:
1. Close any running instances of the executable
2. Use `-Clean` flag to force removal:
   ```powershell
   .\build_scripts\build_windows.ps1 -Clean
   ```
3. Manually delete `build/` and `dist/` directories

### "Module not found" Errors During Build

**Problem**: Dependencies are not installed in the build environment

**Solution**:
```bash
# Reinstall all dependencies
pip install -e ".[dev]"

# Verify spaCy model
python -m spacy download en_core_web_md
```

## Security Notes

### Development Security

- **`-ExecutionPolicy Bypass`**: PowerShell script uses this for development convenience
- **Self-Signed Executables**: Built binaries are not code-signed by default
- **Checksum Verification**: OCR dependency downloads are verified via SHA256

### Production Security Recommendations

1. **Code Signing**:
   - Obtain code signing certificate (Standard or EV)
   - Sign all executables and installers before distribution
   - Example: `signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com data-extract.exe`

2. **PowerShell Script Signing**:
   - Sign `build_windows.ps1` with certificate for production use
   - Set execution policy to `AllSigned` instead of `Bypass`

3. **Integrity Verification**:
   - Generate SHA256 checksums for release artifacts
   - Publish checksums on official release page
   - Example: `certutil -hashfile data-extract.exe SHA256`

4. **Distribution Security**:
   - Host releases on HTTPS endpoints only
   - Use GitHub Releases or similar with integrity protection
   - Never distribute via email or untrusted file shares

## Testing the Build

### Basic Functionality Tests

```bash
# Verify executable runs and shows version
dist\data_extract\data-extract.exe --version

# Show help text (tests CLI framework)
dist\data_extract\data-extract.exe --help

# Process a sample document (tests core pipeline)
dist\data_extract\data-extract.exe process sample.pdf

# Process with output directory (tests file I/O)
dist\data_extract\data-extract.exe process sample.pdf --output-dir test_output
```

### OCR Functionality Tests (Full Build)

```bash
# Test OCR extraction on image-based PDF
dist\data_extract\data-extract.exe process scanned_document.pdf

# Verify Tesseract is bundled
dist\data_extract\data-extract.exe config show | findstr tesseract

# Verify Poppler is bundled
dist\data_extract\data-extract.exe config show | findstr poppler
```

### Installer Tests

1. **Installation Test**:
   - Run `dist\DataExtractionTool-Setup-1.0.0.exe`
   - Install to default location (`C:\Program Files\Data Extraction Tool\`)
   - Verify Start Menu shortcuts created

2. **Installed Executable Test**:
   ```bash
   "C:\Program Files\Data Extraction Tool\data-extract.exe" --version
   ```

3. **Uninstaller Test**:
   - Run uninstaller from Control Panel or Start Menu
   - Verify all files removed
   - Verify Start Menu shortcuts removed

### VM Testing for Releases

**Recommended**: Test installers on clean Windows VMs before public release

1. Create fresh Windows 10/11 VM (no Python or dependencies)
2. Run installer as regular user (not admin)
3. Test all core commands
4. Verify no missing dependencies
5. Test uninstaller

## Silent Installation (Enterprise)

For automated and enterprise deployments, the Inno Setup installer supports silent/unattended installation using command-line parameters.

### Basic Silent Install

```cmd
# Silent install with minimal output
DataExtractionTool-Setup-1.0.0.exe /VERYSILENT /NORESTART
```

### Silent Install with Logging

```cmd
# Silent install with installation log
DataExtractionTool-Setup-1.0.0.exe /VERYSILENT /NORESTART /LOG="install.log"

# Log will contain detailed installation steps and any errors
```

### Silent Install to Custom Directory

```cmd
# Silent install to custom installation path
DataExtractionTool-Setup-1.0.0.exe /VERYSILENT /DIR="C:\Tools\DataExtract" /NORESTART

# Useful for automated enterprise deployments with specific path requirements
```

### Silent Uninstall

```cmd
# Silent uninstall (remove all files and Start Menu items)
"C:\Program Files\DataExtractionTool\unins000.exe" /VERYSILENT

# Alternative: Use control panel uninstaller
"C:\Program Files\DataExtractionTool\unins000.exe" /VERYSILENT /NORESTART
```

### Common Parameters

| Parameter | Description |
|-----------|-------------|
| `/VERYSILENT` | Silent mode with no dialogs (ideal for automation) |
| `/SILENT` | Silent mode with progress bar |
| `/NORESTART` | Do not restart computer after installation |
| `/DIR="path"` | Custom installation directory |
| `/LOG="file"` | Write detailed log to specified file |
| `/TASKS="taskname"` | Select specific installation tasks |

### Enterprise Deployment Example

```batch
@echo off
REM Automated deployment script for Data Extraction Tool

set INSTALL_DIR=C:\Program Files\DataExtract
set LOG_FILE=C:\Logs\data-extract-install.log
set INSTALLER=DataExtractionTool-Setup-1.0.0.exe

REM Silent install to custom directory with logging
%INSTALLER% /VERYSILENT /DIR="%INSTALL_DIR%" /LOG="%LOG_FILE%" /NORESTART

REM Check installation success
if %ERRORLEVEL% EQU 0 (
    echo Installation successful
    exit /b 0
) else (
    echo Installation failed with error code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
```

### PowerShell Deployment Example

```powershell
# Silent installation via PowerShell
$installerPath = ".\DataExtractionTool-Setup-1.0.0.exe"
$installDir = "C:\Program Files\DataExtract"
$logFile = "C:\Logs\data-extract-install.log"

# Run installer silently
& $installerPath /VERYSILENT /DIR="$installDir" /LOG="$logFile" /NORESTART

# Verify installation
if ($LASTEXITCODE -eq 0) {
    Write-Host "Installation successful"
} else {
    Write-Error "Installation failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}
```

### Troubleshooting Silent Installations

**Installation fails with no feedback**:
- Add `/LOG="install.log"` to capture detailed error information
- Check the log file for specific error messages
- Ensure the installation path is writable and has sufficient disk space

**"Access denied" errors**:
- Ensure PowerShell/Command Prompt is running as Administrator
- Verify user has write permissions to target directory

**Custom directory installation fails**:
- Ensure the specified directory path exists or is creatable
- Use absolute paths (e.g., `C:\Tools\` not `%PROGRAMFILES%\`)
- Quote paths containing spaces

**Return codes**:
- `0` = Success
- Non-zero = Installation failed (check log file for details)

### See Also

- [Inno Setup Command-Line Documentation](https://jrsoftware.org/ishelp/)
- For additional parameters and advanced options, refer to the official Inno Setup documentation

## Creating Releases

### Step-by-Step Release Process

1. **Update Version Number**:
   ```bash
   # Edit version in version.py
   nano build_scripts/version.py

   # Update version string (follows semantic versioning)
   __version__ = "1.0.0"  # Change to new version
   ```

2. **Run Clean Build**:
   ```powershell
   # From Windows PowerShell
   .\build_scripts\build_windows.ps1 -Clean

   # OR for full build with OCR
   .\build_scripts\build_windows.ps1 -Clean -Full
   ```

3. **Test Executable**:
   ```bash
   # Run test suite on built executable
   dist\data_extract\data-extract.exe --version
   dist\data_extract\data-extract.exe process tests\fixtures\sample.pdf
   ```

4. **Test Installer on Fresh VM**:
   - Copy installer to clean Windows VM
   - Install as non-admin user
   - Run integration tests
   - Verify uninstaller works

5. **Sign Executable** (if certificate available):
   ```powershell
   # Sign with code signing certificate
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist\data_extract\data-extract.exe

   # Verify signature
   signtool verify /pa dist\data_extract\data-extract.exe
   ```

6. **Generate Checksums**:
   ```powershell
   # Generate SHA256 for executable
   certutil -hashfile dist\data_extract\data-extract.exe SHA256 > dist\SHA256SUMS.txt

   # Generate SHA256 for installer
   certutil -hashfile dist\DataExtractionTool-Setup-1.0.0.exe SHA256 >> dist\SHA256SUMS.txt
   ```

7. **Create GitHub Release**:
   - Tag version: `git tag v1.0.0`
   - Push tag: `git push origin v1.0.0`
   - Upload artifacts to GitHub Releases:
     - `data-extract.exe`
     - `DataExtractionTool-Setup-1.0.0.exe`
     - `SHA256SUMS.txt`
   - Include release notes with changelog

### Semantic Versioning Guidelines

- **Major (1.x.x)**: Breaking API changes, incompatible updates
- **Minor (x.1.x)**: New features, backward-compatible
- **Patch (x.x.1)**: Bug fixes, backward-compatible

## Advanced Configuration

### Custom PyInstaller Options

Edit `build_scripts/build_orchestrator.py` to modify PyInstaller behavior:

```python
# Add custom hidden imports
pyinstaller_args.extend(['--hidden-import', 'custom_module'])

# Exclude unnecessary packages
pyinstaller_args.extend(['--exclude-module', 'matplotlib'])

# Add data files
pyinstaller_args.extend(['--add-data', 'config.yaml:config'])
```

### Custom Installer Options

Edit `build_scripts/installer.iss` for Inno Setup customization:

- **Default Installation Directory**: Change `DefaultDirName`
- **File Associations**: Add to `[Registry]` section
- **Start Menu Items**: Modify `[Icons]` section
- **Custom Dialogs**: Add to `[Messages]` section

## Performance Optimization

### Reducing Executable Size

1. **Exclude Unused Modules**:
   ```bash
   # Add to PyInstaller args
   --exclude-module matplotlib
   --exclude-module pandas
   ```

2. **Use UPX Compression** (optional):
   ```bash
   # Install UPX
   choco install upx

   # PyInstaller will auto-detect and use UPX
   # Reduces size by ~30-40% but slower startup
   ```

3. **Remove Debug Symbols**:
   ```bash
   # Already included in build_orchestrator.py
   --strip
   ```

### Improving Startup Time

- **Lazy Imports**: Import heavy modules only when needed
- **Pre-compiled Bytecode**: PyInstaller handles automatically
- **Resource Caching**: Cache spaCy models and other resources

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build Windows Executable

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          python -m spacy download en_core_web_md
      - name: Build executable
        run: |
          .\build_scripts\build_windows.ps1 -Clean
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: windows-executable
          path: dist/DataExtractionTool-Setup-*.exe
```

## Additional Resources

- **PyInstaller Documentation**: [pyinstaller.org](https://pyinstaller.org/)
- **Inno Setup Documentation**: [jrsoftware.org/ishelp](https://jrsoftware.org/ishelp/)
- **spaCy Models**: [spacy.io/models](https://spacy.io/models)
- **Code Signing Guide**: [Microsoft Docs - SignTool](https://docs.microsoft.com/en-us/windows/win32/seccrypto/signtool)

## Getting Help

- **Build Issues**: Check `build_scripts/build.log` for detailed error messages
- **Runtime Issues**: Run with `--verbose` flag for detailed logging
- **GitHub Issues**: [github.com/your-repo/issues](https://github.com/your-repo/issues)

---

**Last Updated**: 2025-12-01
**Build System Version**: 1.0.0
**Minimum Python**: 3.11+
**Target Platform**: Windows 10/11 (64-bit)
