#!/usr/bin/env python3
"""
Environment Setup Script

One-command development environment setup for the Data Extraction Tool project.
Creates virtual environment using uv (or falls back to venv), installs dependencies,
downloads spaCy models, sets up pre-commit hooks, configures git, and validates environment.

Usage:
    python scripts/setup_environment.py                    # Full setup (uses uv)
    python scripts/setup_environment.py --skip-git         # Skip git configuration
    python scripts/setup_environment.py --force            # Force reinstall everything
    python scripts/setup_environment.py --verbose          # Verbose output
    python scripts/setup_environment.py --no-uv            # Use pip/venv instead of uv
"""

import argparse
import json
import platform
import subprocess
import sys
import time
import venv
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import structlog  # type: ignore[import-not-found]

# Configure structured logging
logger = structlog.get_logger()

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
VENV_DIR = PROJECT_ROOT / ".venv"  # Changed from "venv" to ".venv" for uv compatibility
PYPROJECT_TOML = PROJECT_ROOT / "pyproject.toml"
PRE_COMMIT_CONFIG = PROJECT_ROOT / ".pre-commit-config.yaml"
CLAUDE_HOOKS_DIR = PROJECT_ROOT / ".claude" / "hooks"
SPACY_MODEL = "en_core_web_md"

# Platform detection
IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"


class EnvironmentSetup:
    """Automated environment setup for Data Extraction Tool."""

    def __init__(
        self,
        skip_git: bool = False,
        force: bool = False,
        verbose: bool = False,
        no_uv: bool = False,
    ):
        """
        Initialize the environment setup.

        Args:
            skip_git: Skip git configuration
            force: Force reinstall everything
            verbose: Enable verbose output
            no_uv: Use pip/venv instead of uv
        """
        self.skip_git = skip_git
        self.force = force
        self.verbose = verbose
        self.no_uv = no_uv
        self.use_uv = self._check_uv_available() and not no_uv
        self.start_time = time.time()
        self.validation_results: Dict[str, bool] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        logger.info(
            "initialized_environment_setup",
            skip_git=skip_git,
            force=force,
            verbose=verbose,
            use_uv=self.use_uv,
            platform=platform.system(),
            python_version=sys.version,
        )

    def _check_uv_available(self) -> bool:
        """
        Check if uv is available on the system.

        Returns:
            True if uv is installed and available
        """
        try:
            result = subprocess.run(["uv", "--version"], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def print_header(self) -> None:
        """Print setup header."""
        print("=" * 70)
        print("🚀 Data Extraction Tool - Environment Setup")
        print("=" * 70)
        print(f"Platform: {platform.system()} {platform.release()}")
        print(f"Python: {sys.version.split()[0]}")
        print(f"Project: {PROJECT_ROOT}")
        if self.use_uv:
            print("📦 Package Manager: uv (fast mode)")
        else:
            print("📦 Package Manager: pip (fallback mode)")
        print()

    def check_python_version(self) -> bool:
        """
        Check if Python version meets requirements (3.12+).

        Returns:
            True if Python version is valid
        """
        print("🐍 Checking Python version...")
        version_info = sys.version_info

        if version_info < (3, 12):
            error_msg = f"Python 3.12+ required, found {version_info.major}.{version_info.minor}.{version_info.micro}"
            print(f"  ❌ {error_msg}")
            self.errors.append(error_msg)
            return False

        print(
            f"  ✅ Python {version_info.major}.{version_info.minor}.{version_info.micro} meets requirements"
        )
        self.validation_results["python_version"] = True
        return True

    def create_virtual_environment(self) -> bool:
        """
        Create Python virtual environment using uv (or fallback to venv).

        Returns:
            True if successful
        """
        print("📦 Setting up virtual environment...")

        # Check if venv already exists
        if VENV_DIR.exists() and not self.force:
            print(f"  ℹ️  Virtual environment already exists at {VENV_DIR}")
            self.validation_results["venv_exists"] = True
            return True

        if self.force and VENV_DIR.exists():
            print("  🔄 Recreating virtual environment (--force enabled)...")

        try:
            if self.use_uv:
                # Use uv to create virtual environment (much faster)
                print(f"  🔨 Creating virtual environment with uv at {VENV_DIR}...")
                uv_cmd = ["uv", "venv", str(VENV_DIR)]
                if self.force:
                    uv_cmd.append("--clear")
                result = subprocess.run(
                    uv_cmd,
                    capture_output=True,
                    text=True,
                    cwd=PROJECT_ROOT,
                )

                if result.returncode != 0:
                    print("  ⚠️  uv venv failed, falling back to python venv")
                    if self.verbose:
                        print(f"      Error: {result.stderr}")
                    self.use_uv = False  # Fallback for subsequent operations
                    venv.create(VENV_DIR, with_pip=True, clear=self.force)
            else:
                # Fallback to standard venv module
                print(f"  🔨 Creating virtual environment with venv at {VENV_DIR}...")
                venv.create(VENV_DIR, with_pip=True, clear=self.force)

            # Verify venv was created
            python_exe = self._get_python_executable()
            if not python_exe.exists():
                alt_python = (
                    VENV_DIR / "Scripts" / "python3.exe"
                    if IS_WINDOWS
                    else VENV_DIR / "bin" / "python3"
                )
                if alt_python.exists():
                    python_exe = alt_python
                else:
                    raise FileNotFoundError(f"Python executable not found at {python_exe}")

            mode = "uv" if self.use_uv else "venv"
            print(f"  ✅ Virtual environment created successfully ({mode})")
            self.validation_results["venv_created"] = True
            return True

        except Exception as e:
            error_msg = f"Failed to create virtual environment: {e}"
            print(f"  ❌ {error_msg}")
            self.errors.append(error_msg)
            return False

    def _get_python_executable(self) -> Path:
        """
        Get the path to the Python executable in the virtual environment.

        Returns:
            Path to Python executable
        """
        if IS_WINDOWS:
            return VENV_DIR / "Scripts" / "python.exe"
        else:
            return VENV_DIR / "bin" / "python"

    def _get_pip_executable(self) -> Path:
        """
        Get the path to the pip executable in the virtual environment.

        Returns:
            Path to pip executable
        """
        if IS_WINDOWS:
            return VENV_DIR / "Scripts" / "pip.exe"
        else:
            return VENV_DIR / "bin" / "pip"

    def install_dependencies(self) -> bool:
        """
        Install all dependencies from pyproject.toml including [dev] extras.
        Uses uv if available, falls back to pip.

        Returns:
            True if successful
        """
        print("📚 Installing dependencies...")

        try:
            if self.use_uv:
                # Use uv (much faster)
                print("  📦 Installing dependencies with uv (fast mode)...")
                cmd = ["uv", "pip", "install", "-e", ".[dev]"]

                if self.force:
                    cmd.append("--reinstall")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=PROJECT_ROOT,
                )

                if result.returncode == 0:
                    print("  ✅ All dependencies installed successfully (uv)")
                    self.validation_results["dependencies_installed"] = True
                    return True
                else:
                    print("  ⚠️  uv install failed, falling back to pip")
                    if self.verbose:
                        print(f"      Error: {result.stderr}")
                    self.use_uv = False  # Fallback to pip

            # Fallback to pip
            pip_exe = self._get_pip_executable()

            if not pip_exe.exists():
                error_msg = f"pip not found at {pip_exe}. Please create virtual environment first."
                print(f"  ❌ {error_msg}")
                self.errors.append(error_msg)
                return False

            # Upgrade pip first
            print("  ⬆️  Upgrading pip...")
            result = subprocess.run(
                [str(pip_exe), "install", "--upgrade", "pip"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode != 0 and self.verbose:
                print(f"  ⚠️  pip upgrade warning: {result.stderr}")

            # Install project with dev dependencies
            print("  📦 Installing project dependencies with pip...")
            cmd = [str(pip_exe), "install", "-e", ".[dev]"]

            if self.force:
                cmd.append("--force-reinstall")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode == 0:
                print("  ✅ All dependencies installed successfully (pip)")
                self.validation_results["dependencies_installed"] = True
                return True
            else:
                error_msg = f"Dependency installation failed: {result.stderr}"
                print(f"  ❌ {error_msg}")
                self.errors.append(error_msg)
                return False

        except Exception as e:
            error_msg = f"Failed to install dependencies: {e}"
            print(f"  ❌ {error_msg}")
            self.errors.append(error_msg)
            return False

    def download_spacy_model(self) -> bool:
        """
        Download and validate en_core_web_md spaCy model installation.

        Returns:
            True if successful
        """
        print(f"🧠 Setting up spaCy model ({SPACY_MODEL})...")

        python_exe = self._get_python_executable()

        try:
            # Check if model is already installed
            if not self.force:
                result = subprocess.run(
                    [str(python_exe), "-m", "spacy", "info", SPACY_MODEL],
                    capture_output=True,
                    text=True,
                    cwd=PROJECT_ROOT,
                )

                if result.returncode == 0:
                    print(f"  ℹ️  spaCy model {SPACY_MODEL} already installed")
                    self.validation_results["spacy_model_exists"] = True
                    return True

            # Download the model
            print(f"  📥 Downloading {SPACY_MODEL} (this may take a minute)...")
            result = subprocess.run(
                [str(python_exe), "-m", "spacy", "download", SPACY_MODEL],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode != 0:
                error_msg = f"spaCy model download failed: {result.stderr}"
                print(f"  ❌ {error_msg}")
                self.errors.append(error_msg)
                return False

            # Validate the model
            print("  🔍 Validating spaCy model...")
            result = subprocess.run(
                [str(python_exe), "-m", "spacy", "validate"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if "✔" in result.stdout or result.returncode == 0:
                print(f"  ✅ spaCy model {SPACY_MODEL} installed and validated")
                self.validation_results["spacy_model_installed"] = True
                return True
            else:
                warning_msg = f"spaCy validation warning: {result.stdout}"
                print(f"  ⚠️  {warning_msg}")
                self.warnings.append(warning_msg)
                return True  # Non-critical warning

        except FileNotFoundError:
            error_msg = "spaCy not found. Please ensure dependencies are installed."
            print(f"  ❌ {error_msg}")
            self.errors.append(error_msg)
            return False
        except Exception as e:
            error_msg = f"Failed to setup spaCy model: {e}"
            print(f"  ❌ {error_msg}")
            self.errors.append(error_msg)
            return False

    def setup_pre_commit_hooks(self) -> bool:
        """
        Install pre-commit hooks automatically with proper configuration.

        Returns:
            True if successful
        """
        print("🔗 Setting up pre-commit hooks...")

        python_exe = self._get_python_executable()

        try:
            # Check if pre-commit config exists
            if not PRE_COMMIT_CONFIG.exists():
                warning_msg = ".pre-commit-config.yaml not found, skipping hook setup"
                print(f"  ⚠️  {warning_msg}")
                self.warnings.append(warning_msg)
                return True

            # Install pre-commit hooks
            print("  🔧 Installing pre-commit hooks...")
            result = subprocess.run(
                [str(python_exe), "-m", "pre_commit", "install"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode != 0:
                error_msg = f"Pre-commit hook installation failed: {result.stderr}"
                print(f"  ❌ {error_msg}")
                self.errors.append(error_msg)
                return False

            # Run pre-commit once to download hook dependencies
            if self.force:
                print("  📥 Downloading pre-commit hook dependencies...")
                result = subprocess.run(
                    [str(python_exe), "-m", "pre_commit", "run", "--all-files"],
                    capture_output=True,
                    text=True,
                    cwd=PROJECT_ROOT,
                    timeout=120,  # 2 minute timeout
                )

                # Pre-commit may "fail" on first run if files need formatting
                if "Passed" in result.stdout or "Fixed" in result.stdout:
                    print("  ✅ Pre-commit hooks installed and ready")
                elif self.verbose:
                    print(f"  ℹ️  Pre-commit initial run output: {result.stdout[:500]}")

            print("  ✅ Pre-commit hooks installed successfully")
            self.validation_results["pre_commit_installed"] = True
            return True

        except subprocess.TimeoutExpired:
            warning_msg = "Pre-commit initial run timed out (non-critical)"
            print(f"  ⚠️  {warning_msg}")
            self.warnings.append(warning_msg)
            return True
        except Exception as e:
            error_msg = f"Failed to setup pre-commit hooks: {e}"
            print(f"  ❌ {error_msg}")
            self.errors.append(error_msg)
            return False

    def setup_claude_code_hooks(self) -> bool:
        """
        Set up .claude/hooks/ directory with templates and configuration.

        Returns:
            True if successful
        """
        print("🤖 Setting up Claude Code hooks...")

        try:
            # Create hooks directory
            CLAUDE_HOOKS_DIR.mkdir(parents=True, exist_ok=True)

            # Create SessionStart hook
            session_start_hook = CLAUDE_HOOKS_DIR / "SessionStart"
            session_start_content = """#!/bin/bash
# Claude Code Session Start Hook for Data Extraction Tool
# Auto-generated by setup_environment.py

echo "🚀 Initializing Data Extraction Tool environment..."

# Run session initializer if it exists
if [ -f "scripts/init_claude_session.py" ]; then
    python scripts/init_claude_session.py --quick
fi

echo "✅ Environment ready for development"
"""

            session_start_hook.write_text(session_start_content)

            # Make executable on Unix-like systems
            if not IS_WINDOWS:
                session_start_hook.chmod(0o755)

            # Create PostToolUse hook
            post_tool_hook = CLAUDE_HOOKS_DIR / "PostToolUse"
            post_tool_content = """#!/bin/bash
# Claude Code Post Tool Use Hook
# Auto-generated by setup_environment.py

# Run quality checks after file modifications
if [[ "$1" == *"Edit"* ]] || [[ "$1" == *"Write"* ]]; then
    if [ -f "scripts/run_quality_gates.py" ]; then
        echo "🔍 Running quick quality checks..."
        python scripts/run_quality_gates.py --quick --changed-only 2>/dev/null || true
    fi
fi
"""

            post_tool_hook.write_text(post_tool_content)

            # Make executable on Unix-like systems
            if not IS_WINDOWS:
                post_tool_hook.chmod(0o755)

            print(f"  ✅ Claude Code hooks created at {CLAUDE_HOOKS_DIR}")
            self.validation_results["claude_hooks_created"] = True
            return True

        except Exception as e:
            error_msg = f"Failed to setup Claude Code hooks: {e}"
            print(f"  ❌ {error_msg}")
            self.errors.append(error_msg)
            return False

    def configure_git_settings(self) -> bool:
        """
        Configure git user settings and recommended aliases for the project.

        Returns:
            True if successful
        """
        if self.skip_git:
            print("⏭️  Skipping git configuration (--skip-git flag)")
            return True

        print("📝 Configuring git settings...")

        try:
            # Check if git is installed
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                warning_msg = "Git not found. Skipping git configuration."
                print(f"  ⚠️  {warning_msg}")
                self.warnings.append(warning_msg)
                return True

            # Check current git user configuration
            result = subprocess.run(
                ["git", "config", "user.name"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            git_user_name = result.stdout.strip()

            result = subprocess.run(
                ["git", "config", "user.email"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            git_user_email = result.stdout.strip()

            # Only configure if not already set
            if not git_user_name:
                print("  📝 Git user.name not configured.")
                print("  💡 Run: git config user.name 'Your Name'")
                self.warnings.append("Git user.name not configured")

            if not git_user_email:
                print("  📝 Git user.email not configured.")
                print("  💡 Run: git config user.email 'your.email@example.com'")
                self.warnings.append("Git user.email not configured")

            # Set up recommended aliases
            aliases = {
                "st": "status",
                "co": "checkout",
                "br": "branch",
                "ci": "commit",
                "unstage": "reset HEAD --",
                "last": "log -1 HEAD",
                "visual": "log --graph --oneline --decorate",
            }

            print("  🔧 Setting up recommended git aliases...")
            for alias, command in aliases.items():
                subprocess.run(
                    ["git", "config", f"alias.{alias}", command],
                    capture_output=True,
                    text=True,
                    cwd=PROJECT_ROOT,
                )

            print("  ✅ Git configuration complete")
            self.validation_results["git_configured"] = True
            return True

        except Exception as e:
            warning_msg = f"Git configuration warning: {e}"
            print(f"  ⚠️  {warning_msg}")
            self.warnings.append(warning_msg)
            return True  # Non-critical

    def validate_environment(self) -> bool:
        """
        Validate complete setup with checklist and diagnostic output.

        Returns:
            True if all critical checks pass
        """
        print("\n" + "=" * 70)
        print("🔍 Environment Validation")
        print("=" * 70)

        validation_checks = []

        # Check Python version
        check_python = sys.version_info >= (3, 12)
        validation_checks.append(("Python 3.12+", check_python))

        # Check virtual environment
        check_venv = VENV_DIR.exists() and self._get_python_executable().exists()
        validation_checks.append(("Virtual environment", check_venv))

        # Check key dependencies
        python_exe = self._get_python_executable()

        # Check spaCy
        try:
            result = subprocess.run(
                [str(python_exe), "-c", "import spacy; print(spacy.__version__)"],
                capture_output=True,
                text=True,
            )
            check_spacy = result.returncode == 0
        except Exception:
            check_spacy = False
        validation_checks.append(("spaCy installed", check_spacy))

        # Check spaCy model
        try:
            result = subprocess.run(
                [str(python_exe), "-m", "spacy", "info", SPACY_MODEL],
                capture_output=True,
                text=True,
            )
            check_model = result.returncode == 0
        except Exception:
            check_model = False
        validation_checks.append((f"spaCy model ({SPACY_MODEL})", check_model))

        # Check pre-commit
        pre_commit_installed = (PROJECT_ROOT / ".git" / "hooks" / "pre-commit").exists()
        validation_checks.append(("Pre-commit hooks", pre_commit_installed))

        # Check Claude hooks
        claude_hooks = CLAUDE_HOOKS_DIR.exists() and (CLAUDE_HOOKS_DIR / "SessionStart").exists()
        validation_checks.append(("Claude Code hooks", claude_hooks))

        # Check project structure
        check_src = (PROJECT_ROOT / "src" / "data_extract").exists()
        validation_checks.append(("Source code structure", check_src))

        check_tests = (PROJECT_ROOT / "tests").exists()
        validation_checks.append(("Test directory", check_tests))

        # Display results
        all_passed = True
        for check_name, passed in validation_checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
            if not passed and check_name in [
                "Python 3.12+",
                "Virtual environment",
                "Source code structure",
            ]:
                all_passed = False

        # Diagnostic information
        print("\n📊 Diagnostic Information:")
        print(f"  • Platform: {platform.system()} {platform.release()}")
        print(f"  • Python: {sys.version.split()[0]}")
        print(f"  • Project root: {PROJECT_ROOT}")
        print(f"  • Virtual env: {VENV_DIR}")

        # Performance metrics
        elapsed = time.time() - self.start_time
        print(f"\n⏱️  Setup completed in {elapsed:.1f} seconds")

        # Summary
        if all_passed and not self.errors:
            print("\n✅ Environment setup successful! You're ready to develop.")
            print("\n💡 Next steps:")
            print("  1. Activate the virtual environment:")
            if IS_WINDOWS:
                print(f"     {VENV_DIR}\\Scripts\\activate")
            else:
                print(f"     source {VENV_DIR}/bin/activate")
            print("  2. Run tests to verify:")
            print("     pytest")
            print("  3. Check quality gates:")
            print("     python scripts/run_quality_gates.py")

            self.validation_results["environment_valid"] = True
            return True
        else:
            print("\n⚠️  Environment setup completed with issues.")

            if self.errors:
                print("\n❌ Errors encountered:")
                for error in self.errors:
                    print(f"  • {error}")

            if self.warnings:
                print("\n⚠️  Warnings:")
                for warning in self.warnings:
                    print(f"  • {warning}")

            print("\n💡 Troubleshooting:")
            print("  • Ensure Python 3.12+ is installed")
            print("  • Check file permissions in project directory")
            print("  • Try running with --force flag to reinstall")
            print("  • Run with --verbose for detailed output")

            return not self.errors  # Return False if there are errors

    def save_validation_report(self) -> None:
        """Save validation results to a JSON file for CI/CD integration."""
        report_path = PROJECT_ROOT / "environment_setup_report.json"

        report = {
            "timestamp": datetime.now().isoformat(),
            "platform": platform.system(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "validation_results": self.validation_results,
            "errors": self.errors,
            "warnings": self.warnings,
            "elapsed_time": time.time() - self.start_time,
        }

        try:
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2)

            if self.verbose:
                print(f"\n📄 Validation report saved to {report_path}")
        except Exception as e:
            logger.error("failed_to_save_report", error=str(e))

    def run(self) -> bool:
        """
        Run the complete environment setup process.

        Returns:
            True if setup completed successfully
        """
        self.print_header()

        # Check Python version first
        if not self.check_python_version():
            return False

        # Create virtual environment
        if not self.create_virtual_environment():
            return False

        # Install dependencies
        if not self.install_dependencies():
            return False

        # Download spaCy model
        if not self.download_spacy_model():
            return False

        # Setup pre-commit hooks
        if not self.setup_pre_commit_hooks():
            pass  # Non-critical, continue

        # Setup Claude Code hooks
        if not self.setup_claude_code_hooks():
            pass  # Non-critical, continue

        # Configure git
        if not self.configure_git_settings():
            pass  # Non-critical, continue

        # Validate environment
        success = self.validate_environment()

        # Save validation report
        self.save_validation_report()

        return success


def main() -> None:
    """Main entry point for the environment setup script."""
    parser = argparse.ArgumentParser(
        description="One-command development environment setup for Data Extraction Tool"
    )
    parser.add_argument(
        "--skip-git",
        action="store_true",
        help="Skip git configuration",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reinstall everything (removes existing venv)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--no-uv",
        action="store_true",
        help="Use pip/venv instead of uv (fallback mode)",
    )

    args = parser.parse_args()

    # Run setup
    setup = EnvironmentSetup(
        skip_git=args.skip_git,
        force=args.force,
        verbose=args.verbose,
        no_uv=args.no_uv,
    )

    success = setup.run()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
