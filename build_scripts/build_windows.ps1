# build_windows.ps1
# PowerShell build script for data-extract Windows executable
# Must be run ON Windows (not from WSL)

<#
.SYNOPSIS
    Builds data-extract.exe Windows executable using PyInstaller

.DESCRIPTION
    This script automates the build process for creating a standalone Windows executable:
    1. Validates prerequisites (Python 3.11+, PyInstaller, optional Inno Setup)
    2. Sets up or activates Python virtual environment
    3. Installs dependencies and downloads spaCy model
    4. Runs PyInstaller with spec file
    5. Verifies build output
    6. Optionally creates installer with Inno Setup

.PARAMETER Clean
    Clean build directories (dist/, build/) before building

.PARAMETER SkipInstaller
    Skip Inno Setup installer creation (only build executable)

.PARAMETER Full
    Include OCR dependencies (pytesseract, Tesseract binary)

.EXAMPLE
    .\build_windows.ps1
    # Basic build

.EXAMPLE
    .\build_windows.ps1 -Clean -Full
    # Clean build with OCR support

.EXAMPLE
    .\build_windows.ps1 -SkipInstaller
    # Build executable only, skip installer creation

.NOTES
    SECURITY NOTE: This script requires execution policy bypass for development builds.
    To run this script, use:
        powershell -ExecutionPolicy Bypass -File build_windows.ps1

    -ExecutionPolicy Bypass is used for DEVELOPMENT BUILDS ONLY.
    For PRODUCTION builds:
    1. Sign the script with a trusted certificate
    2. Remove the -ExecutionPolicy Bypass requirement
    3. Use proper execution policy settings (RemoteSigned or AllSigned)

    Reference: https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies
#>

param(
    [switch]$Clean,
    [switch]$SkipInstaller,
    [switch]$Full
)

# Error handling
$ErrorActionPreference = "Stop"

# Script configuration
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $ProjectRoot ".venv"
$DistPath = Join-Path $ProjectRoot "dist"
$BuildPath = Join-Path $ProjectRoot "build"
$SpecFile = Join-Path $PSScriptRoot "data_extract.spec"
$ExePath = Join-Path $DistPath "data_extract\data-extract.exe"

# Color output helpers
function Write-Success { Write-Host " $args" -ForegroundColor Green }
function Write-Info { Write-Host "� $args" -ForegroundColor Cyan }
function Write-Warning { Write-Host "� $args" -ForegroundColor Yellow }
function Write-Error { Write-Host " $args" -ForegroundColor Red }

# Banner
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Data Extract Windows Build Script" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check prerequisites
Write-Info "Checking prerequisites..."

# Check Python version (3.11+)
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
            Write-Error "Python 3.11+ required, found: $pythonVersion"
            exit 1
        }
        Write-Success "Python version: $pythonVersion"
    }
} catch {
    Write-Error "Python not found in PATH"
    exit 1
}

# Check if running on Windows
if ($PSVersionTable.Platform -ne $null -and $PSVersionTable.Platform -ne "Win32NT") {
    Write-Error "This script must run ON Windows (not WSL). Use build_orchestrator.py from WSL."
    exit 1
}

# Check Inno Setup (optional, for installer)
if (-not $SkipInstaller) {
    $InnoSetup = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
    if ($InnoSetup) {
        Write-Success "Inno Setup found: $($InnoSetup.Source)"
    } else {
        Write-Warning "Inno Setup not found - will skip installer creation"
        Write-Warning "Download from: https://jrsoftware.org/isdl.php"
        $SkipInstaller = $true
    }
}

# Step 2: Clean build directories if requested
if ($Clean) {
    Write-Info "Cleaning build directories..."
    try {
        if (Test-Path $DistPath) {
            Remove-Item -Recurse -Force $DistPath -ErrorAction Stop
            Write-Success "Removed dist/"
        }
        if (Test-Path $BuildPath) {
            Remove-Item -Recurse -Force $BuildPath -ErrorAction Stop
            Write-Success "Removed build/"
        }
    } catch {
        Write-Error "Failed to clean build directories: $_"
        Write-Warning "Try closing any programs that might have files open in dist/ or build/"
        exit 1
    }
}

# Step 3: Setup virtual environment
Write-Info "Setting up Python virtual environment..."

try {
    if (-not (Test-Path $VenvPath)) {
        Write-Info "Creating new virtual environment at $VenvPath"
        $venvOutput = python -m venv $VenvPath 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to create virtual environment"
            Write-Host $venvOutput -ForegroundColor Red
            exit 1
        }
        Write-Success "Virtual environment created"
    } else {
        Write-Success "Virtual environment already exists"
    }
} catch {
    Write-Error "Failed to setup virtual environment: $_"
    exit 1
}

# Activate virtual environment
try {
    $ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
    if (Test-Path $ActivateScript) {
        & $ActivateScript
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to activate virtual environment"
            exit 1
        }
        Write-Success "Virtual environment activated"
    } else {
        Write-Error "Could not find activation script at $ActivateScript"
        exit 1
    }
} catch {
    Write-Error "Failed to activate virtual environment: $_"
    exit 1
}

# Step 4: Install dependencies
Write-Info "Installing dependencies..."

# Upgrade pip
try {
    $pipOutput = python -m pip install --upgrade pip setuptools wheel 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to upgrade pip/setuptools/wheel"
        Write-Host $pipOutput -ForegroundColor Red
        exit 1
    }
    Write-Success "pip, setuptools, wheel upgraded"
} catch {
    Write-Error "Failed to upgrade pip: $_"
    exit 1
}

# Install PyInstaller
try {
    $pyinstallerOutput = python -m pip install pyinstaller 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install PyInstaller"
        Write-Host $pyinstallerOutput -ForegroundColor Red
        exit 1
    }
    Write-Success "PyInstaller installed"
} catch {
    Write-Error "Failed to install PyInstaller: $_"
    exit 1
}

# Install project dependencies
Push-Location $ProjectRoot
try {
    if ($Full) {
        $depsOutput = python -m pip install -e ".[dev,ocr]" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to install dependencies with OCR support"
            Write-Host $depsOutput -ForegroundColor Red
            Pop-Location
            exit 1
        }
        Write-Success "Installed with OCR support"
    } else {
        $depsOutput = python -m pip install -e ".[dev]" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to install dependencies"
            Write-Host $depsOutput -ForegroundColor Red
            Pop-Location
            exit 1
        }
        Write-Success "Installed dependencies"
    }
} catch {
    Write-Error "Failed to install dependencies: $_"
    Pop-Location
    exit 1
}
Pop-Location

# Step 5: Download OCR binary dependencies for Full builds
if ($Full) {
    Write-Info "Downloading OCR binary dependencies (Tesseract + Poppler)..."
    Push-Location $ProjectRoot
    try {
        $ocrDepsOutput = python build_scripts/download_ocr_dependencies.py 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to download OCR dependencies"
            Write-Host $ocrDepsOutput -ForegroundColor Red
            Pop-Location
            exit 1
        }
        Write-Success "OCR binary dependencies downloaded"
    } catch {
        Write-Error "Failed to download OCR dependencies: $_"
        Pop-Location
        exit 1
    }
    Pop-Location
}

# Step 6: Download spaCy model
Write-Info "Downloading spaCy model en_core_web_md..."

try {
    $spaCyCheck = python -c "import en_core_web_md; print('installed')" 2>&1
    if ($spaCyCheck -match "installed") {
        Write-Success "spaCy model already installed"
    } else {
        $spaCyDownload = python -m spacy download en_core_web_md 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to download spaCy model"
            Write-Host $spaCyDownload -ForegroundColor Red
            exit 1
        }
        Write-Success "spaCy model downloaded"
    }
} catch {
    Write-Error "Failed to check/download spaCy model: $_"
    exit 1
}

# Validate model
try {
    $validateOutput = python -m spacy validate 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "spaCy model validation returned warnings (non-critical)"
        # Don't exit on validation warnings - they're often informational
    } else {
        Write-Success "spaCy model validated"
    }
} catch {
    Write-Warning "spaCy validation check failed (non-critical): $_"
}

# Step 7: Run PyInstaller
Write-Info "Running PyInstaller..."

Push-Location $ProjectRoot
try {
    pyinstaller $SpecFile --clean --noconfirm
    Write-Success "PyInstaller build completed"
} catch {
    Write-Error "PyInstaller build failed: $_"
    Pop-Location
    exit 1
}
Pop-Location

# Step 8: Verify build output
Write-Info "Verifying build output..."

if (-not (Test-Path $ExePath)) {
    Write-Error "Executable not found at: $ExePath"
    exit 1
}

Write-Success "Executable found: $ExePath"

# Test executable
Write-Info "Testing executable..."
try {
    $versionOutput = & $ExePath --version 2>&1
    Write-Success "Executable test passed: $versionOutput"
} catch {
    Write-Error "Executable test failed: $_"
    exit 1
}

# Step 9: Create installer (if not skipped)
if (-not $SkipInstaller) {
    Write-Info "Creating Windows installer with Inno Setup..."

    $InnoScript = Join-Path $PSScriptRoot "installer.iss"
    if (Test-Path $InnoScript) {
        try {
            $innoOutput = ISCC.exe $InnoScript 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "Installer creation failed with exit code $LASTEXITCODE"
                Write-Host $innoOutput -ForegroundColor Yellow
            } else {
                Write-Success "Installer created successfully"
            }
        } catch {
            Write-Warning "Installer creation failed: $_"
        }
    } else {
        Write-Warning "Inno Setup script not found: $InnoScript"
    }
}

# Final summary
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Build Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Info "Executable location:"
Write-Host "  $ExePath" -ForegroundColor White
Write-Host ""

if (-not $SkipInstaller -and (Test-Path (Join-Path $DistPath "data-extract-setup.exe"))) {
    Write-Info "Installer location:"
    Write-Host "  $(Join-Path $DistPath 'data-extract-setup.exe')" -ForegroundColor White
    Write-Host ""
}

Write-Info "Next steps:"
Write-Host "  1. Test the executable: $ExePath --help" -ForegroundColor White
Write-Host "  2. Verify on clean Windows machine" -ForegroundColor White
Write-Host "  3. Distribute dist/data_extract/ folder or installer" -ForegroundColor White
Write-Host ""
