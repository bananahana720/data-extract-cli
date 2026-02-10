#!/usr/bin/env python3
"""
Claude Code Session Initializer

Automated session setup for Claude Code on the web.
Sets up environment, syncs git, installs dependencies (via uv), and loads context.

Usage:
    python scripts/init_claude_session.py           # Run full initialization (uses uv)
    python scripts/init_claude_session.py --quick   # Skip dependency updates
    python scripts/init_claude_session.py --no-uv   # Use pip instead of uv
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
CLAUDE_MD = PROJECT_ROOT / ".claude" / "CLAUDE.md"
SPRINT_STATUS = PROJECT_ROOT / "docs" / "sprint-status.yaml"
PYPROJECT = PROJECT_ROOT / "pyproject.toml"


class SessionInitializer:
    """Initialize Claude Code session with project context."""

    def __init__(self, quick: bool = False, no_uv: bool = False):
        """
        Initialize the session initializer.

        Args:
            quick: If True, skip dependency updates
            no_uv: If True, use pip instead of uv
        """
        self.quick = quick
        self.no_uv = no_uv
        self.use_uv = self._check_uv_available() and not no_uv
        self.errors = []
        self.warnings = []

    def _check_uv_available(self) -> bool:
        """Check if uv is available."""
        try:
            result = subprocess.run(["uv", "--version"], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def print_header(self):
        """Print session initialization header."""
        print("=" * 60)
        print("🚀 Claude Code Session Initializer")
        print("=" * 60)
        pkg_mgr = "uv (fast mode)" if self.use_uv else "pip (standard mode)"
        print(f"📦 Package Manager: {pkg_mgr}")
        print()

    def sync_git_repository(self) -> bool:
        """
        Pull latest changes from git repository.

        Returns:
            True if successful
        """
        print("📦 Syncing Git Repository...")

        try:
            # Check git status
            result = subprocess.run(
                ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=PROJECT_ROOT
            )

            if result.stdout.strip():
                print("  ⚠️  You have uncommitted changes:")
                for line in result.stdout.strip().split("\n")[:5]:
                    print(f"    {line}")
                if len(result.stdout.strip().split("\n")) > 5:
                    print("    ...")
                self.warnings.append("Uncommitted changes present")

            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )
            current_branch = result.stdout.strip()
            print(f"  📍 Current branch: {current_branch}")

            # Pull latest changes
            print("  🔄 Pulling latest changes...")
            result = subprocess.run(
                ["git", "pull", "--rebase", "--autostash"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode == 0:
                print("  ✅ Repository synced successfully")
                if "Already up to date" in result.stdout:
                    print("  ℹ️  No new changes")
                return True
            else:
                print(f"  ❌ Git pull failed: {result.stderr}")
                self.errors.append("Git sync failed")
                return False

        except FileNotFoundError:
            print("  ❌ Git not found. Please install git.")
            self.errors.append("Git not installed")
            return False
        except Exception as e:
            print(f"  ❌ Error syncing repository: {e}")
            self.errors.append(f"Git sync error: {e}")
            return False

    def setup_virtual_environment(self) -> bool:
        """
        Set up and activate virtual environment.

        Returns:
            True if successful
        """
        print("\n🐍 Setting Up Python Environment...")

        venv_path = PROJECT_ROOT / "venv"

        # Check if venv exists
        if not venv_path.exists():
            print("  📦 Creating virtual environment...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "venv", "venv"],
                    check=True,
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                )
                print("  ✅ Virtual environment created")
            except subprocess.CalledProcessError as e:
                print(f"  ❌ Failed to create venv: {e}")
                self.errors.append("venv creation failed")
                return False
        else:
            print("  ✅ Virtual environment exists")

        # Set environment variables for this process
        if sys.platform == "win32":
            venv_python = venv_path / "Scripts" / "python.exe"
        else:
            venv_python = venv_path / "bin" / "python"

        # Check if venv is functional
        try:
            result = subprocess.run(
                [str(venv_python), "--version"], capture_output=True, text=True, check=True
            )
            print(f"  ℹ️  Using Python: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("  ⚠️  Virtual environment not functional, using system Python")
            self.warnings.append("venv not functional")
            return True  # Continue with system Python

    def install_dependencies(self) -> bool:
        """
        Install/update project dependencies from pyproject.toml.

        Returns:
            True if successful
        """
        if self.quick:
            print("\n📚 Skipping dependency installation (--quick mode)")
            return True

        print("\n📚 Installing Dependencies...")

        if not PYPROJECT.exists():
            print("  ⚠️  pyproject.toml not found")
            self.warnings.append("pyproject.toml missing")
            return True

        try:
            # Determine which package manager to use
            if self.use_uv:
                # Use uv (much faster)
                print("  📦 Installing dependencies with uv...")
                cmd = ["uv", "pip", "install", "-e", ".[dev]"]
            else:
                # Fallback to pip
                venv_pip = (
                    PROJECT_ROOT
                    / "venv"
                    / ("Scripts" if sys.platform == "win32" else "bin")
                    / "pip"
                )
                if venv_pip.exists():
                    pip_cmd = str(venv_pip)
                else:
                    pip_cmd = "pip"

                print("  📦 Installing dependencies with pip...")
                cmd = [pip_cmd, "install", "-e", ".[dev]"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode == 0:
                print("  ✅ Dependencies installed successfully")
            else:
                print("  ⚠️  Some dependencies failed to install")
                self.warnings.append("Some dependencies failed")

            return True

        except Exception as e:
            print(f"  ❌ Error installing dependencies: {e}")
            self.errors.append(f"Dependency installation error: {e}")
            return False

    def setup_spacy_model(self) -> bool:
        """
        Download spaCy en_core_web_md model if not present.

        Returns:
            True if successful
        """
        print("\n🧠 Setting Up spaCy Model...")

        try:
            import spacy

            # Check if model is already installed
            try:
                nlp = spacy.load("en_core_web_md")
                print(f"  ✅ spaCy model already installed: v{nlp.meta['version']}")
                return True
            except OSError:
                # Model not installed, download it
                print("  📥 Downloading en_core_web_md model (~43MB)...")

                # Try venv python first
                venv_python = (
                    PROJECT_ROOT
                    / "venv"
                    / ("Scripts" if sys.platform == "win32" else "bin")
                    / "python"
                )

                if venv_python.exists():
                    python_cmd = str(venv_python)
                else:
                    python_cmd = sys.executable

                result = subprocess.run(
                    [python_cmd, "-m", "spacy", "download", "en_core_web_md"],
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    print("  ✅ spaCy model downloaded successfully")
                    return True
                else:
                    print(f"  ❌ Failed to download model: {result.stderr}")
                    self.errors.append("spaCy model download failed")
                    return False

        except ImportError:
            print("  ⚠️  spaCy not installed. Run: pip install spacy")
            self.warnings.append("spaCy not installed")
            return True  # Non-critical, continue

    def load_context_from_claude_md(self) -> bool:
        """
        Load and display key sections from CLAUDE.md.

        Returns:
            True if successful
        """
        print("\n📋 Loading Project Context...")

        if not CLAUDE_MD.exists():
            print("  ⚠️  CLAUDE.md not found")
            self.warnings.append("CLAUDE.md missing")
            return True

        try:
            content = CLAUDE_MD.read_text(encoding="utf-8")
            lines = content.split("\n")

            # Extract key sections
            sections = {
                "Project Overview": [],
                "Current": [],
                "Development Commands": [],
            }

            current_section = None
            for line in lines:
                if line.startswith("## "):
                    section_name = line[3:].strip()
                    if any(key in section_name for key in sections.keys()):
                        for key in sections.keys():
                            if key in section_name:
                                current_section = key
                                break
                elif current_section and line.strip():
                    sections[current_section].append(line)

            # Display project overview
            if sections["Project Overview"]:
                print("\n  📌 Project Overview:")
                for line in sections["Project Overview"][:5]:
                    if line.strip():
                        print(f"    {line.strip()}")

            # Display current status
            for line in lines:
                if "**Status**:" in line:
                    print(f"\n  📊 {line.strip()}")
                    break

            print("\n  ✅ Context loaded from CLAUDE.md")
            return True

        except Exception as e:
            print(f"  ❌ Error reading CLAUDE.md: {e}")
            self.errors.append(f"CLAUDE.md read error: {e}")
            return False

    def display_sprint_status(self) -> bool:
        """
        Show current sprint status and active stories.

        Returns:
            True if successful
        """
        print("\n📊 Sprint Status Overview...")

        if not SPRINT_STATUS.exists():
            print("  ⚠️  sprint-status.yaml not found")
            self.warnings.append("sprint-status.yaml missing")
            return True

        try:
            import yaml

            with open(SPRINT_STATUS, "r") as f:
                sprint_data = yaml.safe_load(f)

            dev_status = sprint_data.get("development_status", {})

            # Count story statuses
            status_counts = {
                "done": 0,
                "in-progress": 0,
                "review": 0,
                "ready-for-dev": 0,
                "drafted": 0,
                "backlog": 0,
            }

            active_stories = []
            current_epics = set()

            for key, status in dev_status.items():
                if status in status_counts:
                    status_counts[status] += 1

                # Track active stories
                if status in ["in-progress", "review", "ready-for-dev"]:
                    active_stories.append((key, status))

                # Track current epics
                if key.startswith("epic-") and status == "contexted":
                    current_epics.add(key)

            # Display summary
            total = sum(status_counts.values())
            done_pct = (status_counts["done"] / total * 100) if total > 0 else 0

            print(f"\n  📈 Overall Progress: {done_pct:.1f}% complete")
            print(f"    ✅ Done: {status_counts['done']}")
            print(f"    🔄 In Progress: {status_counts['in-progress']}")
            print(f"    👀 In Review: {status_counts['review']}")
            print(f"    🚀 Ready for Dev: {status_counts['ready-for-dev']}")
            print(f"    📝 Drafted: {status_counts['drafted']}")
            print(f"    📋 Backlog: {status_counts['backlog']}")

            # Display active stories
            if active_stories:
                print("\n  🎯 Active Stories:")
                for story, status in active_stories[:5]:
                    status_emoji = {"in-progress": "🔄", "review": "👀", "ready-for-dev": "🚀"}.get(
                        status, "📍"
                    )
                    print(f"    {status_emoji} {story}: {status}")

            print("\n  ✅ Sprint status loaded")
            return True

        except ImportError:
            print("  ⚠️  PyYAML not installed. Run: pip install pyyaml")
            self.warnings.append("PyYAML not installed")
            return True
        except Exception as e:
            print(f"  ❌ Error reading sprint status: {e}")
            self.errors.append(f"Sprint status read error: {e}")
            return False

    def set_environment_variables(self) -> bool:
        """
        Set required environment variables.

        Returns:
            True if successful
        """
        print("\n⚙️  Setting Environment Variables...")

        env_vars = {
            "PYTHONPATH": str(PROJECT_ROOT),
            "DATA_EXTRACT_PROJECT_ROOT": str(PROJECT_ROOT),
        }

        for key, value in env_vars.items():
            os.environ[key] = value
            print(f"  ✅ {key} = {value}")

        return True

    def display_quick_commands(self):
        """Display helpful commands for the session."""
        print("\n📝 Quick Commands:")
        print("  • Run tests: pytest")
        print("  • Quality checks: python scripts/run_quality_gates.py")
        print("  • Generate story: python scripts/generate_story_template.py --help")
        print("  • Check sprint: cat docs/sprint-status.yaml | head -50")
        print("  • View CLAUDE.md: cat .claude/CLAUDE.md")

    def run_initialization(self) -> bool:
        """
        Run full initialization sequence.

        Returns:
            True if successful
        """
        self.print_header()

        steps = [
            ("Git Repository", self.sync_git_repository),
            ("Python Environment", self.setup_virtual_environment),
            ("Dependencies", self.install_dependencies),
            ("spaCy Model", self.setup_spacy_model),
            ("Project Context", self.load_context_from_claude_md),
            ("Sprint Status", self.display_sprint_status),
            ("Environment Variables", self.set_environment_variables),
        ]

        for name, func in steps:
            try:
                func()
            except Exception as e:
                print(f"\n❌ Error in {name}: {e}")
                self.errors.append(f"{name} error: {e}")

        # Summary
        print("\n" + "=" * 60)
        print("📊 Initialization Summary")
        print("=" * 60)

        if self.errors:
            print("\n❌ Errors encountered:")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  • {warning}")

        if not self.errors:
            print("\n✅ Session initialization completed successfully!")
            self.display_quick_commands()
            return True
        else:
            print("\n⚠️  Session initialized with errors - some features may not work")
            return False


def create_session_hook():
    """Create .claude/hooks/SessionStart hook file."""
    hooks_dir = PROJECT_ROOT / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    hook_file = hooks_dir / "SessionStart"
    hook_content = """#!/usr/bin/env python3
# Claude Code SessionStart Hook
# Auto-generated by init_claude_session.py

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Run session initializer
from scripts.init_claude_session import SessionInitializer

if __name__ == "__main__":
    initializer = SessionInitializer(quick=True)
    initializer.run_initialization()
"""

    hook_file.write_text(hook_content)
    hook_file.chmod(0o755)  # Make executable
    print(f"✅ Created SessionStart hook: {hook_file}")


def create_template_files():
    """Create template files for Claude Code configuration."""
    templates_dir = PROJECT_ROOT / ".claude" / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    # SessionStart template
    session_template = templates_dir / "SessionStart.template"
    session_content = """#!/usr/bin/env python3
# Claude Code SessionStart Hook Template
# Copy to .claude/hooks/SessionStart and customize

import subprocess
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent.parent

    # Run initialization script
    init_script = project_root / "scripts" / "init_claude_session.py"
    if init_script.exists():
        subprocess.run(["python3", str(init_script), "--quick"])
    else:
        print("Session initializer not found")

if __name__ == "__main__":
    main()
"""
    session_template.write_text(session_content)
    print(f"✅ Created template: {session_template}")

    # Config template
    config_template = templates_dir / "config.yaml.template"
    config_content = """# Claude Code Configuration Template
# Copy to .claude/config.yaml and customize

# Project settings
project_name: data-extraction-tool
python_version: "3.12"

# Session initialization
auto_init: true
quick_mode: false

# Quality gates
run_quality_checks: true
quality_tools:
  - black
  - ruff
  - mypy
  - pytest

# Sprint tracking
track_sprint_status: true
sprint_file: docs/sprint-status.yaml
"""
    config_template.write_text(config_content)
    print(f"✅ Created template: {config_template}")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Initialize Claude Code session")

    parser.add_argument(
        "--quick", action="store_true", help="Skip dependency updates for faster init"
    )

    parser.add_argument(
        "--no-uv", action="store_true", help="Use pip instead of uv for package management"
    )

    parser.add_argument("--create-hook", action="store_true", help="Create SessionStart hook file")

    parser.add_argument("--create-templates", action="store_true", help="Create template files")

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_arguments()

    # Create hook or templates if requested
    if args.create_hook:
        create_session_hook()
        return 0

    if args.create_templates:
        create_template_files()
        return 0

    # Run initialization
    initializer = SessionInitializer(quick=args.quick, no_uv=args.no_uv)
    success = initializer.run_initialization()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
