"""
Test suite for the dependency auditor script.

Tests import scanning, pyproject.toml parsing, cross-referencing,
report generation, and caching functionality.
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Mock structlog and toml before importing the script
sys.modules["structlog"] = MagicMock()
sys.modules["toml"] = MagicMock()

from scripts.audit_dependencies import DependencyAuditor, main  # noqa: E402


class TestDependencyAuditor:
    """Test cases for the DependencyAuditor class."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Provide temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def auditor(self, temp_cache_dir):
        """Create DependencyAuditor instance with temp cache."""
        return DependencyAuditor(cache_dir=temp_cache_dir)

    @pytest.fixture
    def sample_test_file(self):
        """Create a sample test file content."""
        return """
import pytest
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from data_extract.semantic.vectorizer import SemanticVectorizer
import json
import sys
"""

    @pytest.fixture
    def sample_pyproject(self):
        """Create a sample pyproject.toml content."""
        return """
[project]
dependencies = [
    "numpy>=1.20.0",
    "scikit-learn>=1.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=22.0.0",
    "mypy>=1.0.0",
]
"""

    @pytest.mark.unit
    def test_init(self, temp_cache_dir):
        """Test DependencyAuditor initialization."""
        auditor = DependencyAuditor(cache_dir=temp_cache_dir)

        assert auditor.cache_dir == temp_cache_dir
        assert temp_cache_dir.exists()
        assert auditor.test_imports == {}
        assert auditor.declared_deps == set()
        assert auditor.missing_deps == set()
        assert auditor.unused_deps == set()

    @pytest.mark.unit
    def test_extract_imports(self, auditor, tmp_path, sample_test_file):
        """Test import extraction from Python file."""
        # Create test file
        test_file = tmp_path / "test_sample.py"
        test_file.write_text(sample_test_file)

        # Extract imports
        imports = auditor._extract_imports(test_file)

        # Verify extracted imports (excluding stdlib and project modules)
        assert "numpy" in imports
        assert "sklearn" in imports
        assert "pytest" in imports
        # These should be filtered out
        assert "json" not in imports  # stdlib
        assert "sys" not in imports  # stdlib
        assert "data_extract" not in imports  # project module

    @pytest.mark.unit
    def test_extract_imports_with_syntax_error(self, auditor, tmp_path):
        """Test import extraction handles syntax errors gracefully."""
        # Create file with syntax error
        bad_file = tmp_path / "bad_syntax.py"
        bad_file.write_text("import numpy\nthis is not valid python")

        # Should handle error without crashing
        imports = auditor._extract_imports(bad_file)

        # Should return empty set on parse error
        assert imports == set()

    @pytest.mark.unit
    def test_normalize_import_name(self, auditor):
        """Test import name normalization."""
        # Test common mappings
        assert auditor._normalize_import_name("PIL") == "pillow"
        assert auditor._normalize_import_name("cv2") == "opencv_python"
        assert auditor._normalize_import_name("sklearn") == "scikit_learn"
        assert auditor._normalize_import_name("yaml") == "pyyaml"
        assert auditor._normalize_import_name("bs4") == "beautifulsoup4"

        # Test normalization rules
        assert auditor._normalize_import_name("Some-Package") == "some_package"
        assert auditor._normalize_import_name("CamelCase") == "camelcase"

    @pytest.mark.unit
    def test_extract_package_name(self, auditor):
        """Test package name extraction from dependency specs."""
        assert auditor._extract_package_name("numpy>=1.20.0") == "numpy"
        assert auditor._extract_package_name("scikit-learn>=1.0.0,<2.0") == "scikit_learn"
        assert auditor._extract_package_name("pytest") == "pytest"
        assert auditor._extract_package_name("package[extra]>=1.0") == "package"

        # Test edge cases
        assert auditor._extract_package_name("") is None
        assert auditor._extract_package_name(">=1.0.0") is None

    @pytest.mark.unit
    def test_parse_pyproject_manually(self, auditor, tmp_path, sample_pyproject):
        """Test manual pyproject.toml parsing."""
        # Create pyproject file
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(sample_pyproject)

        # Parse manually
        deps = auditor._parse_pyproject_manually(pyproject_file)

        # Verify dependencies found
        assert "numpy" in deps
        assert "scikit_learn" in deps
        assert "pydantic" in deps
        assert "pytest" in deps
        assert "black" in deps
        assert "mypy" in deps

    @pytest.mark.unit
    def test_load_declared_dependencies_with_toml(self, auditor, tmp_path):
        """Test loading dependencies with toml library available."""
        # Create a test pyproject.toml file with content
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
dependencies = ["numpy>=1.20.0", "pandas>=1.3.0"]

[project.optional-dependencies]
dev = ["pytest>=7.0.0", "black>=22.0.0"]
"""
        )

        # Mock toml.load to return expected data
        with patch("builtins.__import__") as mock_import:
            mock_toml = MagicMock()
            mock_toml.load.return_value = {
                "project": {
                    "dependencies": ["numpy>=1.20.0", "pandas>=1.3.0"],
                    "optional-dependencies": {"dev": ["pytest>=7.0.0", "black>=22.0.0"]},
                }
            }

            def import_side_effect(name, *args, **kwargs):
                if name == "toml":
                    return mock_toml
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            # Load dependencies
            deps = auditor.load_declared_dependencies(pyproject)

        # Verify
        assert "numpy" in deps
        assert "pandas" in deps
        assert "pytest" in deps
        assert "black" in deps

    @pytest.mark.unit
    def test_load_declared_dependencies_without_toml(self, auditor, tmp_path, sample_pyproject):
        """Test loading dependencies when toml library is not available."""
        # Create pyproject file
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(sample_pyproject)

        # Mock the import to fail for toml
        with patch("builtins.__import__") as mock_import:

            def import_side_effect(name, *args, **kwargs):
                if name == "toml":
                    raise ImportError("No module named 'toml'")
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            # Load dependencies (should fall back to manual parsing)
            deps = auditor.load_declared_dependencies(pyproject)

        # Verify dependencies still found
        assert "numpy" in deps
        assert "scikit_learn" in deps
        assert "pytest" in deps

    @pytest.mark.unit
    def test_cross_reference(self, auditor):
        """Test cross-referencing imports with declared dependencies."""
        # Setup test data
        auditor.test_imports = {
            "tests/test_1.py": {"numpy", "pytest", "requests"},
            "tests/test_2.py": {"pandas", "sklearn"},
        }
        auditor.declared_deps = {"numpy", "pytest", "pandas", "black", "mypy"}

        # Cross-reference
        missing, unused = auditor.cross_reference()

        # Verify results
        assert "requests" in missing  # Used but not declared
        assert "scikit_learn" in missing  # sklearn -> scikit_learn normalization
        assert "black" in unused  # Declared but not used
        assert "mypy" in unused  # Declared but not used

    @pytest.mark.unit
    def test_generate_recommendations(self, auditor):
        """Test recommendation generation."""
        # Test with missing dependencies
        auditor.missing_deps = {"requests", "flask", "django"}
        recommendations = auditor._generate_recommendations()

        assert any("Add 3 missing dependencies" in r for r in recommendations)
        assert any("requests" in r for r in recommendations)

        # Test with no issues
        auditor.missing_deps = set()
        auditor.unused_deps = set()
        recommendations = auditor._generate_recommendations()

        assert any("All test dependencies are properly declared" in r for r in recommendations)

    @pytest.mark.unit
    def test_generate_json_report(self, auditor):
        """Test JSON report generation."""
        # Setup test data
        auditor.test_imports = {"tests/test.py": {"numpy", "pytest"}}
        auditor.declared_deps = {"numpy", "pytest", "black"}
        auditor.missing_deps = {"requests"}
        auditor.unused_deps = {"black"}

        # Generate JSON report
        report = auditor.generate_report(output_format="json")
        report_data = json.loads(report)

        # Verify report structure
        assert "timestamp" in report_data
        assert "summary" in report_data
        assert report_data["summary"]["total_test_files"] == 1
        assert report_data["summary"]["missing_dependencies"] == 1
        assert report_data["summary"]["potentially_unused"] == 1
        assert "requests" in report_data["missing_dependencies"]
        assert "black" in report_data["potentially_unused"]

    @pytest.mark.unit
    def test_generate_markdown_report(self, auditor):
        """Test markdown report generation."""
        # Setup test data
        auditor.test_imports = {"tests/test.py": {"numpy"}}
        auditor.declared_deps = {"numpy", "black"}
        auditor.missing_deps = {"requests"}
        auditor.unused_deps = {"black"}

        # Generate markdown report
        report = auditor.generate_report(output_format="markdown")

        # Verify report content
        assert "# Test Dependency Audit Report" in report
        assert "## Summary" in report
        assert "## ⚠️ Missing Dependencies" in report
        assert "`requests`" in report
        assert "## 📋 Potentially Unused Test Dependencies" in report
        assert "`black`" in report
        assert "## 💡 Recommendations" in report

    @pytest.mark.unit
    def test_cache_operations(self, auditor, tmp_path):
        """Test cache save and load operations."""
        # Setup cache data
        auditor.cache = {"test_file.py": {"mtime": 12345.67, "imports": ["numpy", "pytest"]}}

        # Save cache
        auditor._save_cache()
        cache_file = auditor.cache_dir / "import_cache.json"
        assert cache_file.exists()

        # Create new auditor and load cache
        new_auditor = DependencyAuditor(cache_dir=auditor.cache_dir)
        new_auditor._load_cache()

        # Verify cache loaded correctly
        assert "test_file.py" in new_auditor.cache
        assert new_auditor.cache["test_file.py"]["mtime"] == 12345.67

    @pytest.mark.unit
    def test_scan_test_files_with_cache(self, auditor, tmp_path):
        """Test test file scanning with cache hit."""
        # Create test directory and file
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        test_file = test_dir / "test_sample.py"
        test_file.write_text("import numpy\nimport pytest")

        # Pre-populate cache
        file_mtime = test_file.stat().st_mtime
        auditor.cache[str(test_file)] = {"mtime": file_mtime, "imports": {"numpy", "pytest"}}

        # Scan with cache hit
        with patch.object(auditor, "_extract_imports") as mock_extract:
            test_imports = auditor.scan_test_files(test_dir)

            # Should not call extract_imports due to cache hit
            mock_extract.assert_not_called()

            # Should still return correct imports
            assert len(test_imports) == 1

    @pytest.mark.unit
    def test_update_documentation(self, auditor, tmp_path):
        """Test documentation update functionality."""
        docs_dir = tmp_path / "docs"
        report = "# Test Report\n\nSample content"

        # Update documentation
        auditor.update_documentation(report, docs_dir)

        # Verify file created
        report_file = docs_dir / "processes" / "test-dependency-audit-report.md"
        assert report_file.exists()
        assert report_file.read_text() == report

    @pytest.mark.integration
    @pytest.mark.skip(reason="P2 automation - test fixture doesn't declare all dependencies")
    @patch("sys.argv", ["audit_dependencies.py", "--output", "markdown"])
    def test_main_success(self, tmp_path, monkeypatch):
        """Test main function with successful execution."""
        monkeypatch.chdir(tmp_path)

        # Create minimal project structure
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_sample.py").write_text("import pytest")
        (tmp_path / "pyproject.toml").write_text('[project]\ndependencies = ["pytest>=7.0"]')

        # Patch PROJECT_ROOT and related constants to use tmp_path
        import scripts.audit_dependencies as audit_module

        monkeypatch.setattr(audit_module, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(audit_module, "TEST_DIR", tmp_path / "tests")
        monkeypatch.setattr(audit_module, "PYPROJECT_PATH", tmp_path / "pyproject.toml")
        monkeypatch.setattr(audit_module, "CACHE_DIR", tmp_path / ".cache" / "dependency_audit")
        monkeypatch.setattr(audit_module, "DOCS_DIR", tmp_path / "docs")

        # Run main
        with patch("sys.exit") as mock_exit:
            main()
            mock_exit.assert_called_with(0)

    @pytest.mark.integration
    @patch("sys.argv", ["audit_dependencies.py"])
    def test_main_with_missing_deps(self, tmp_path, monkeypatch):
        """Test main function with missing dependencies."""
        monkeypatch.chdir(tmp_path)

        # Create project with missing dependency
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test.py").write_text("import requests")  # Not declared
        (tmp_path / "pyproject.toml").write_text("[project]\ndependencies = []")

        # Patch PROJECT_ROOT and related constants to use tmp_path
        import scripts.audit_dependencies as audit_module

        monkeypatch.setattr(audit_module, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(audit_module, "TEST_DIR", tmp_path / "tests")
        monkeypatch.setattr(audit_module, "PYPROJECT_PATH", tmp_path / "pyproject.toml")
        monkeypatch.setattr(audit_module, "CACHE_DIR", tmp_path / ".cache" / "dependency_audit")
        monkeypatch.setattr(audit_module, "DOCS_DIR", tmp_path / "docs")

        # Run main - should exit with error
        with patch("sys.exit") as mock_exit:
            main()
            mock_exit.assert_called_with(1)
