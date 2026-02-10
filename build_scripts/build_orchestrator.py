#!/usr/bin/env python3
"""Build orchestrator for data-extract Windows executable.

This script can be run from both WSL and Windows environments. It detects the
current platform and orchestrates the build process accordingly:

- From WSL: Translates paths and executes PowerShell script on Windows
- From Windows: Executes PowerShell script directly

Usage:
    python build_scripts/build_orchestrator.py [--clean] [--skip-installer] [--full]

Requirements:
    - Python 3.11+
    - When run from WSL: Access to Windows filesystem and powershell.exe
    - When run on Windows: PowerShell 5.1+ or PowerShell Core
"""

import argparse
import logging
import platform
import subprocess
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("build_orchestrator")


def is_wsl() -> bool:
    """Detect if running in Windows Subsystem for Linux."""
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except FileNotFoundError:
        return False


def wsl_to_windows_path(wsl_path: Path) -> str:
    """Convert WSL path to Windows path using wslpath.

    Args:
        wsl_path: Path in WSL filesystem

    Returns:
        Windows-style path (e.g., C:\\Users\\...)

    Example:
        /home/user/project -> C:\\Users\\user\\project
        /mnt/c/dev/project -> C:\\dev\\project
    """
    try:
        result = subprocess.run(
            ["wslpath", "-w", str(wsl_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error converting WSL path: {e}")
        sys.exit(1)


def run_windows_build(script_path: str, clean: bool, skip_installer: bool, full: bool) -> int:
    """Execute PowerShell build script on Windows.

    Args:
        script_path: Path to build_windows.ps1 (Windows-style if from WSL)
        clean: Pass -Clean flag
        skip_installer: Pass -SkipInstaller flag
        full: Pass -Full flag (include OCR)

    Returns:
        Exit code from PowerShell script
    """
    # Build PowerShell command
    ps_args = []
    if clean:
        ps_args.append("-Clean")
    if skip_installer:
        ps_args.append("-SkipInstaller")
    if full:
        ps_args.append("-Full")

    ps_command = f"& '{script_path}' {' '.join(ps_args)}"

    # Detect PowerShell executable
    if is_wsl():
        # From WSL, call Windows PowerShell
        ps_executable = "powershell.exe"
        logger.info("Running from WSL - using Windows PowerShell")
    else:
        # On Windows, prefer PowerShell Core if available
        if subprocess.run(["where", "pwsh"], capture_output=True, shell=True).returncode == 0:
            ps_executable = "pwsh"
            logger.info("Using PowerShell Core")
        else:
            ps_executable = "powershell"
            logger.info("Using Windows PowerShell")

    # Execute build script
    logger.info(f'Executing: {ps_executable} -ExecutionPolicy Bypass -Command "{ps_command}"')

    try:
        result = subprocess.run(
            [ps_executable, "-ExecutionPolicy", "Bypass", "-NoProfile", "-Command", ps_command],
            cwd=Path.cwd() if not is_wsl() else None,
            check=False,  # Let script return its own exit code
        )
        return result.returncode
    except FileNotFoundError:
        logger.error(f"{ps_executable} not found in PATH")
        logger.error("Make sure PowerShell is installed and accessible")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


def main() -> int:
    """Main entry point for build orchestrator."""
    parser = argparse.ArgumentParser(
        description="Build orchestrator for data-extract Windows executable",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_orchestrator.py                    # Basic build
  python build_orchestrator.py --clean --full     # Clean build with OCR
  python build_orchestrator.py --skip-installer   # Build exe only

Platform Detection:
  Automatically detects WSL vs Windows and uses appropriate PowerShell
  executable and path translation.
        """,
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build directories (dist/, build/) before building",
    )
    parser.add_argument(
        "--skip-installer",
        action="store_true",
        help="Skip Inno Setup installer creation (build executable only)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Include OCR dependencies (pytesseract, Tesseract)",
    )

    args = parser.parse_args()

    # Banner
    logger.info("=" * 50)
    logger.info("Data Extract Build Orchestrator")
    logger.info("=" * 50)

    # Detect platform
    if is_wsl():
        logger.info("Platform: WSL (Windows Subsystem for Linux)")
    elif platform.system() == "Windows":
        logger.info("Platform: Windows")
    else:
        logger.error(f"Unsupported platform: {platform.system()}")
        logger.error("This script only supports Windows and WSL")
        return 1

    # Locate build script
    script_dir = Path(__file__).parent.resolve()
    build_script = script_dir / "build_windows.ps1"

    if not build_script.exists():
        logger.error(f"Build script not found: {build_script}")
        return 1

    logger.info(f"Build script: {build_script}")

    # Convert path if running from WSL
    if is_wsl():
        windows_script_path = wsl_to_windows_path(build_script)
        logger.info(f"Windows path: {windows_script_path}")
    else:
        windows_script_path = str(build_script)

    # Execute build
    logger.info("Starting Windows build process...")
    exit_code = run_windows_build(
        windows_script_path,
        args.clean,
        args.skip_installer,
        args.full,
    )

    # Report result
    if exit_code == 0:
        logger.info("=" * 50)
        logger.info("Build Orchestration Complete!")
        logger.info("=" * 50)
        logger.info("Check dist/data_extract/ for executable")
        if not args.skip_installer:
            logger.info("Check dist/ for installer (if Inno Setup available)")
    else:
        logger.error("=" * 50)
        logger.error("Build Failed")
        logger.error("=" * 50)
        logger.error(f"Exit code: {exit_code}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
