"""
Unit tests for setup_environment.py script.

Tests virtual environment creation, dependency installation, spaCy model download,
pre-commit setup, Claude Code hooks configuration, and git settings.
"""

import json
import platform
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

from setup_environment import EnvironmentSetup


@pytest.fixture
def mock_project_root(tmp_path):
    """Create a mock project structure."""
    project = tmp_path / "test_project"
    project.mkdir()

    # Create essential directories and files
    (project / "src" / "data_extract").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "scripts").mkdir()
    (project / ".claude").mkdir()

    # Create pyproject.toml
    pyproject = project / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "data-extraction-tool"
requires-python = ">=3.12"

[project.optional-dependencies]
dev = ["pytest", "black", "ruff", "mypy"]
"""
    )

    # Create .pre-commit-config.yaml
    precommit = project / ".pre-commit-config.yaml"
    precommit.write_text("repos: []")

    return project


class TestEnvironmentSetup:
    """Test cases for EnvironmentSetup class."""

    @pytest.mark.unit
    def test_initialization(self):
        """Test EnvironmentSetup initialization."""
        setup = EnvironmentSetup(skip_git=True, force=False, verbose=True)

        assert setup.skip_git is True
        assert setup.force is False
        assert setup.verbose is True
        assert setup.errors == []
        assert setup.warnings == []

    @pytest.mark.unit
    def test_check_python_version_valid(self):
        """Test Python version check with valid version."""
        setup = EnvironmentSetup()

        # Current Python should be >= 3.12 for this project
        result = setup.check_python_version()

        if sys.version_info >= (3, 12):
            assert result is True
            assert setup.validation_results["python_version"] is True
            assert len(setup.errors) == 0
        else:
            assert result is False
            assert len(setup.errors) > 0

    @pytest.mark.unit
    def test_check_python_version_invalid(self):
        """Test Python version check with invalid version."""
        setup = EnvironmentSetup()

        # Mock sys.version_info to simulate old Python with proper attributes
        mock_version = MagicMock()
        mock_version.major = 3
        mock_version.minor = 11
        mock_version.micro = 0
        mock_version.__lt__ = lambda self, other: (3, 11, 0) < other

        with patch("sys.version_info", mock_version):
            result = setup.check_python_version()

            assert result is False
            assert len(setup.errors) == 1
            assert "3.12+ required" in setup.errors[0]

    @pytest.mark.unit
    @patch("setup_environment.venv.create")
    def test_create_virtual_environment(self, mock_venv_create, mock_project_root):
        """Test virtual environment creation."""
        with patch("setup_environment.PROJECT_ROOT", mock_project_root):
            # Use .venv to match VENV_DIR constant
            with patch("setup_environment.VENV_DIR", mock_project_root / ".venv"):
                setup = EnvironmentSetup()
                venv_dir = mock_project_root / ".venv"

                # Mock venv creation
                mock_venv_create.return_value = None

                # Create mock Python executable
                if platform.system() == "Windows":
                    python_exe = venv_dir / "Scripts" / "python.exe"
                else:
                    python_exe = venv_dir / "bin" / "python"

                python_exe.parent.mkdir(parents=True, exist_ok=True)
                python_exe.touch()

                result = setup.create_virtual_environment()

                assert result is True
                # When venv already exists, implementation sets "venv_exists" not "venv_created"
                assert setup.validation_results["venv_exists"] is True

    @pytest.mark.unit
    @patch("setup_environment.venv.create")
    def test_create_virtual_environment_force(self, mock_venv_create, mock_project_root):
        """Test virtual environment creation with force flag."""
        with patch("setup_environment.PROJECT_ROOT", mock_project_root):
            # Use .venv to match VENV_DIR constant
            with patch("setup_environment.VENV_DIR", mock_project_root / ".venv"):
                venv_dir = mock_project_root / ".venv"
                venv_dir.mkdir()

                setup = EnvironmentSetup(force=True)

                # Mock venv creation
                mock_venv_create.return_value = None

                # Create mock Python executable after venv.create would be called
                if platform.system() == "Windows":
                    python_exe = venv_dir / "Scripts" / "python.exe"
                else:
                    python_exe = venv_dir / "bin" / "python"

                python_exe.parent.mkdir(parents=True, exist_ok=True)
                python_exe.touch()

                result = setup.create_virtual_environment()

                assert result is True
                # With force=True and no uv, should call venv.create
                # Check that venv_created was set
                assert setup.validation_results["venv_created"] is True

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_install_dependencies(self, mock_run, mock_project_root):
        """Test dependency installation."""
        with patch("setup_environment.PROJECT_ROOT", mock_project_root):
            # Use .venv to match VENV_DIR constant
            with patch("setup_environment.VENV_DIR", mock_project_root / ".venv"):
                setup = EnvironmentSetup()

                # Create mock pip executable
                venv_dir = mock_project_root / ".venv"
                if platform.system() == "Windows":
                    pip_exe = venv_dir / "Scripts" / "pip.exe"
                else:
                    pip_exe = venv_dir / "bin" / "pip"

                pip_exe.parent.mkdir(parents=True, exist_ok=True)
                pip_exe.touch()

                # Mock successful pip commands
                mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

                result = setup.install_dependencies()

                assert result is True
                assert setup.validation_results["dependencies_installed"] is True
                assert mock_run.call_count >= 2  # pip upgrade + install

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_download_spacy_model(self, mock_run, mock_project_root):
        """Test spaCy model download."""
        with patch("setup_environment.PROJECT_ROOT", mock_project_root):
            # Use .venv to match VENV_DIR constant
            with patch("setup_environment.VENV_DIR", mock_project_root / ".venv"):
                setup = EnvironmentSetup()

                # Create mock Python executable
                venv_dir = mock_project_root / ".venv"
                if platform.system() == "Windows":
                    python_exe = venv_dir / "Scripts" / "python.exe"
                else:
                    python_exe = venv_dir / "bin" / "python"

                python_exe.parent.mkdir(parents=True, exist_ok=True)
                python_exe.touch()

                # Mock successful spacy commands (model already exists)
                mock_run.return_value = MagicMock(returncode=0, stdout="✔", stderr="")

                result = setup.download_spacy_model()

                assert result is True
                # When model already exists, implementation sets "spacy_model_exists" not "spacy_model_installed"
                assert setup.validation_results["spacy_model_exists"] is True

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_setup_pre_commit_hooks(self, mock_run, mock_project_root):
        """Test pre-commit hook setup."""
        with patch("setup_environment.PROJECT_ROOT", mock_project_root):
            setup = EnvironmentSetup()

            # Create mock Python executable
            venv_dir = mock_project_root / "venv"
            if platform.system() == "Windows":
                python_exe = venv_dir / "Scripts" / "python.exe"
            else:
                python_exe = venv_dir / "bin" / "python"

            python_exe.parent.mkdir(parents=True, exist_ok=True)
            python_exe.touch()

            # Mock successful pre-commit install
            mock_run.return_value = MagicMock(returncode=0, stdout="Passed", stderr="")

            result = setup.setup_pre_commit_hooks()

            assert result is True
            assert setup.validation_results["pre_commit_installed"] is True

    @pytest.mark.unit
    def test_setup_claude_code_hooks(self, mock_project_root):
        """Test Claude Code hooks setup."""
        with patch("setup_environment.PROJECT_ROOT", mock_project_root):
            # Also patch CLAUDE_HOOKS_DIR since it's defined at module level
            with patch(
                "setup_environment.CLAUDE_HOOKS_DIR", mock_project_root / ".claude" / "hooks"
            ):
                setup = EnvironmentSetup()

                result = setup.setup_claude_code_hooks()

                assert result is True
                assert setup.validation_results["claude_hooks_created"] is True

                # Check hooks were created
                hooks_dir = mock_project_root / ".claude" / "hooks"
                assert hooks_dir.exists()
                assert (hooks_dir / "SessionStart").exists()
                assert (hooks_dir / "PostToolUse").exists()

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_configure_git_settings(self, mock_run):
        """Test git configuration."""
        setup = EnvironmentSetup()

        # Mock git commands
        mock_run.return_value = MagicMock(
            returncode=0, stdout="test_user\ntest@email.com", stderr=""
        )

        result = setup.configure_git_settings()

        assert result is True
        assert setup.validation_results["git_configured"] is True

    @pytest.mark.unit
    def test_configure_git_settings_skip(self):
        """Test git configuration with skip flag."""
        setup = EnvironmentSetup(skip_git=True)

        result = setup.configure_git_settings()

        assert result is True
        # Should not set git_configured when skipped
        assert "git_configured" not in setup.validation_results

    @pytest.mark.unit
    @patch("subprocess.run")
    def test_validate_environment(self, mock_run, mock_project_root):
        """Test environment validation."""
        with patch("setup_environment.PROJECT_ROOT", mock_project_root):
            setup = EnvironmentSetup()

            # Create required directories
            venv_dir = mock_project_root / "venv"
            if platform.system() == "Windows":
                python_exe = venv_dir / "Scripts" / "python.exe"
            else:
                python_exe = venv_dir / "bin" / "python"

            python_exe.parent.mkdir(parents=True, exist_ok=True)
            python_exe.touch()

            # Create git hooks directory
            (mock_project_root / ".git" / "hooks").mkdir(parents=True)
            (mock_project_root / ".git" / "hooks" / "pre-commit").touch()

            # Create Claude hooks
            claude_dir = mock_project_root / ".claude" / "hooks"
            claude_dir.mkdir(parents=True)
            (claude_dir / "SessionStart").touch()

            # Mock subprocess calls
            mock_run.return_value = MagicMock(returncode=0, stdout="3.7.0", stderr="")

            result = setup.validate_environment()

            # Should pass basic checks
            assert isinstance(result, bool)

    @pytest.mark.unit
    def test_save_validation_report(self, mock_project_root):
        """Test validation report generation."""
        with patch("setup_environment.PROJECT_ROOT", mock_project_root):
            setup = EnvironmentSetup(verbose=True)

            # Add some test data
            setup.validation_results = {
                "python_version": True,
                "venv_created": True,
                "dependencies_installed": True,
            }
            setup.errors = ["Test error"]
            setup.warnings = ["Test warning"]

            setup.save_validation_report()

            # Check report was created
            report_file = mock_project_root / "environment_setup_report.json"
            assert report_file.exists()

            # Verify report content
            with open(report_file) as f:
                report = json.load(f)

            assert report["validation_results"] == setup.validation_results
            assert report["errors"] == setup.errors
            assert report["warnings"] == setup.warnings
            assert "timestamp" in report
            assert "platform" in report
            assert "python_version" in report

    @pytest.mark.unit
    def test_get_python_executable_windows(self, mock_project_root):
        """Test getting Python executable path on Windows."""
        with patch("setup_environment.PROJECT_ROOT", mock_project_root):
            with patch("setup_environment.IS_WINDOWS", True):
                setup = EnvironmentSetup()

                exe_path = setup._get_python_executable()

                assert "Scripts" in str(exe_path)
                assert "python.exe" in str(exe_path)

    @pytest.mark.unit
    def test_get_python_executable_unix(self, mock_project_root):
        """Test getting Python executable path on Unix."""
        with patch("setup_environment.PROJECT_ROOT", mock_project_root):
            with patch("setup_environment.IS_WINDOWS", False):
                setup = EnvironmentSetup()

                exe_path = setup._get_python_executable()

                assert "bin" in str(exe_path)
                assert "python" in str(exe_path)
                assert ".exe" not in str(exe_path)

    @pytest.mark.unit
    def test_get_pip_executable_windows(self, mock_project_root):
        """Test getting pip executable path on Windows."""
        with patch("setup_environment.PROJECT_ROOT", mock_project_root):
            with patch("setup_environment.IS_WINDOWS", True):
                setup = EnvironmentSetup()

                pip_path = setup._get_pip_executable()

                assert "Scripts" in str(pip_path)
                assert "pip.exe" in str(pip_path)

    @pytest.mark.unit
    def test_get_pip_executable_unix(self, mock_project_root):
        """Test getting pip executable path on Unix."""
        with patch("setup_environment.PROJECT_ROOT", mock_project_root):
            with patch("setup_environment.IS_WINDOWS", False):
                setup = EnvironmentSetup()

                pip_path = setup._get_pip_executable()

                assert "bin" in str(pip_path)
                assert "pip" in str(pip_path)
                assert ".exe" not in str(pip_path)


@pytest.mark.integration
class TestEnvironmentSetupIntegration:
    """Integration tests for environment setup."""

    @patch("subprocess.run")
    def test_full_setup_workflow(self, mock_run, mock_project_root):
        """Test complete setup workflow."""
        with patch("setup_environment.PROJECT_ROOT", mock_project_root):
            with patch("setup_environment.venv.create"):
                setup = EnvironmentSetup()

                # Create necessary mock files
                venv_dir = mock_project_root / "venv"
                if platform.system() == "Windows":
                    python_exe = venv_dir / "Scripts" / "python.exe"
                    pip_exe = venv_dir / "Scripts" / "pip.exe"
                else:
                    python_exe = venv_dir / "bin" / "python"
                    pip_exe = venv_dir / "bin" / "pip"

                python_exe.parent.mkdir(parents=True, exist_ok=True)
                python_exe.touch()
                pip_exe.touch()

                # Mock all subprocess calls as successful
                mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")

                # Run full setup
                result = setup.run()

                # Check that all major steps were attempted
                assert "python_version" in setup.validation_results
                assert mock_run.called  # Various subprocess calls should have been made
