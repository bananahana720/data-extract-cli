"""
Unit tests for the documentation generator script.

Tests cover:
- AST parsing and docstring extraction
- Type hint analysis
- API documentation generation
- Coverage report generation
- README section updates
- Architecture diagram generation
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from scripts.generate_docs import DocumentationGenerator, parse_arguments


class TestDocumentationGenerator:
    """Test suite for DocumentationGenerator class."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            src_dir = temp_path / "src"
            output_dir = temp_path / "docs"
            src_dir.mkdir()
            output_dir.mkdir()
            yield src_dir, output_dir

    @pytest.fixture
    def sample_python_file(self, temp_dirs):
        """Create a sample Python file for testing."""
        src_dir, _ = temp_dirs
        test_file = src_dir / "test_module.py"
        test_file.write_text(
            '''
"""Module for testing documentation generation."""

from typing import List, Optional, Dict

class TestClass:
    """A test class with various methods."""

    class_var: int = 42

    def __init__(self, name: str):
        """Initialize the test class.

        Args:
            name: The name of the instance
        """
        self.name = name

    def process_data(self, data: List[str]) -> Dict[str, int]:
        """Process a list of data.

        Args:
            data: List of strings to process

        Returns:
            Dictionary mapping strings to counts
        """
        return {item: len(item) for item in data}

    async def async_method(self, value: Optional[int] = None) -> bool:
        """An async method example.

        Args:
            value: Optional integer value

        Returns:
            True if value is provided
        """
        return value is not None

def standalone_function(x: int, y: int = 10) -> int:
    """Add two numbers together.

    Args:
        x: First number
        y: Second number (default: 10)

    Returns:
        Sum of x and y
    """
    return x + y

async def async_function(items: List[str]) -> str:
    """Concatenate items asynchronously.

    Args:
        items: List of strings

    Returns:
        Concatenated string
    """
    return "".join(items)
'''
        )
        return test_file

    def test_initialization(self, temp_dirs):
        """Test generator initialization."""
        src_dir, output_dir = temp_dirs
        generator = DocumentationGenerator(src_dir, output_dir)

        assert generator.source_dir == src_dir
        assert generator.output_dir == output_dir
        assert generator.config == {}
        assert generator.modules_data == {}

    def test_load_config_yaml(self, temp_dirs):
        """Test loading YAML configuration."""
        src_dir, output_dir = temp_dirs
        config_file = output_dir / "config.yaml"
        config_data = {"api": {"format": "markdown"}, "coverage": {"enabled": True}}
        config_file.write_text(yaml.dump(config_data))

        generator = DocumentationGenerator(src_dir, output_dir, config_file)
        assert generator.config == config_data

    def test_load_config_json(self, temp_dirs):
        """Test loading JSON configuration."""
        src_dir, output_dir = temp_dirs
        config_file = output_dir / "config.json"
        config_data = {"api": {"format": "html"}, "coverage": {"enabled": False}}
        config_file.write_text(json.dumps(config_data))

        generator = DocumentationGenerator(src_dir, output_dir, config_file)
        assert generator.config == config_data

    def test_extract_docstrings(self, temp_dirs, sample_python_file):
        """Test docstring and type hint extraction (AC-1, AC-2)."""
        src_dir, output_dir = temp_dirs
        generator = DocumentationGenerator(src_dir, output_dir)

        module_info = generator.extract_docstrings(sample_python_file)

        # Check module-level info
        assert module_info["module_docstring"] == "Module for testing documentation generation."
        assert len(module_info["classes"]) == 1
        assert len(module_info["functions"]) == 2

        # Check class extraction
        test_class = module_info["classes"][0]
        assert test_class["name"] == "TestClass"
        assert test_class["docstring"] == "A test class with various methods."
        assert len(test_class["methods"]) == 3
        assert len(test_class["attributes"]) == 1

        # Check method extraction
        init_method = next(m for m in test_class["methods"] if m["name"] == "__init__")
        assert len(init_method["args"]) == 2  # self and name
        assert init_method["args"][1]["name"] == "name"
        assert init_method["args"][1]["type"] == "str"

        process_method = next(m for m in test_class["methods"] if m["name"] == "process_data")
        assert process_method["returns"] == "Dict[str, int]"
        assert process_method["args"][1]["type"] == "List[str]"

        async_method = next(m for m in test_class["methods"] if m["name"] == "async_method")
        assert async_method["async"] is True
        assert async_method["returns"] == "bool"

        # Check function extraction
        standalone = next(f for f in module_info["functions"] if f["name"] == "standalone_function")
        assert standalone["async"] is False
        assert standalone["returns"] == "int"
        assert standalone["args"][1]["default"] == 10

        async_func = next(f for f in module_info["functions"] if f["name"] == "async_function")
        assert async_func["async"] is True

    def test_generate_api_documentation(self, temp_dirs, sample_python_file):
        """Test API documentation generation (AC-3)."""
        src_dir, output_dir = temp_dirs
        generator = DocumentationGenerator(src_dir, output_dir)

        # Generate documentation
        generator.generate_api_documentation(format="markdown")

        # Check generated files
        api_dir = output_dir / "api"
        assert api_dir.exists()
        assert (api_dir / "modules.md").exists()
        assert (api_dir / "classes.md").exists()
        assert (api_dir / "functions.md").exists()

        # Check content
        modules_content = (api_dir / "modules.md").read_text()
        assert "# API Modules Overview" in modules_content
        assert "test_module" in modules_content

        classes_content = (api_dir / "classes.md").read_text()
        assert "# API Classes Documentation" in classes_content
        assert "TestClass" in classes_content
        assert "process_data" in classes_content

        functions_content = (api_dir / "functions.md").read_text()
        assert "# API Functions Documentation" in functions_content
        assert "standalone_function" in functions_content
        assert "async_function" in functions_content

    @patch("scripts.generate_docs.COVERAGE_FILE", Path("/fake/.coverage"))
    def test_generate_coverage_report(self, temp_dirs):
        """Test coverage report generation (AC-4)."""
        src_dir, output_dir = temp_dirs
        generator = DocumentationGenerator(src_dir, output_dir)

        with patch("scripts.generate_docs.Path.exists", return_value=True):
            with patch("coverage.Coverage") as mock_coverage:
                # Mock coverage data
                mock_cov = MagicMock()
                mock_cov.get_data().measured_files.return_value = ["module1.py", "module2.py"]
                mock_cov.analysis2.side_effect = [
                    ("module1.py", [1, 2, 3, 4, 5], [], [2, 4], ""),  # 2 missing lines
                    ("module2.py", [1, 2, 3], [], [], ""),  # No missing lines
                ]
                mock_coverage.return_value = mock_cov

                report = generator.generate_coverage_report()

                assert "overall_coverage" in report
                assert report["total_statements"] == 8
                assert report["total_missing"] == 2
                assert "module_breakdown" in report
                assert "html_report" in report

                # Check HTML report generation was called
                mock_cov.html_report.assert_called_once()

    def test_update_readme_sections(self, temp_dirs, sample_python_file):
        """Test README section updates (AC-5)."""
        src_dir, output_dir = temp_dirs
        readme_path = src_dir.parent / "README.md"

        # Create initial README
        initial_content = """# Project Title

## Overview
This is a test project.

## API Documentation
Old API content here.

## Test Coverage
Old coverage content.

## Other Section
This should not change.
"""
        readme_path.write_text(initial_content)

        generator = DocumentationGenerator(src_dir, output_dir)
        generator.modules_data = {
            "test_module": {"classes": [{"name": "TestClass"}], "functions": []}
        }

        # Update README
        generator.update_readme_sections(["API", "Coverage"], readme_path=readme_path)

        updated_content = readme_path.read_text()

        # Check that sections were updated
        assert "Old API content" not in updated_content
        assert "Old coverage content" not in updated_content
        assert "This should not change" in updated_content
        assert "## API Documentation" in updated_content
        assert "## Test Coverage" in updated_content

    def test_generate_architecture_diagram_mermaid(self, temp_dirs):
        """Test architecture diagram generation in Mermaid format (AC-6)."""
        src_dir, output_dir = temp_dirs

        # Create some Python files in different packages
        (src_dir / "package1").mkdir()
        (src_dir / "package1" / "module1.py").write_text("# Module 1")
        (src_dir / "package2").mkdir()
        (src_dir / "package2" / "module2.py").write_text("# Module 2")

        generator = DocumentationGenerator(src_dir, output_dir)
        generator.modules_data = {
            "package1/module1.py": {"classes": [], "functions": []},
            "package2/module2.py": {"classes": [], "functions": []},
        }

        diagram = generator.generate_architecture_diagram(format="mermaid")

        # Check diagram content
        assert "```mermaid" in diagram
        assert "graph TB" in diagram
        assert "package1" in diagram
        assert "package2" in diagram

        # Check file was created
        arch_file = output_dir / "architecture" / "system.mermaid"
        assert arch_file.exists()
        assert arch_file.read_text() == diagram

    def test_deterministic_output(self, temp_dirs, sample_python_file):
        """Test deterministic output (AC-11)."""
        src_dir, output_dir = temp_dirs
        generator = DocumentationGenerator(src_dir, output_dir)

        # Extract docstrings twice
        result1 = generator.extract_docstrings(sample_python_file)
        result2 = generator.extract_docstrings(sample_python_file)

        # Results should be identical
        assert result1 == result2

    def test_performance(self, temp_dirs):
        """Test performance requirement (AC-12)."""
        src_dir, output_dir = temp_dirs

        # Create 50 Python files
        for i in range(50):
            package_dir = src_dir / f"package_{i // 10}"
            package_dir.mkdir(exist_ok=True)
            file_path = package_dir / f"module_{i}.py"
            file_path.write_text(f'"""Module {i}."""\ndef func_{i}(): pass')

        generator = DocumentationGenerator(src_dir, output_dir)

        import time

        start = time.time()
        generator.generate_api_documentation()
        elapsed = time.time() - start

        # Should complete in less than 30 seconds
        assert elapsed < 30

    def test_config_customization(self, temp_dirs):
        """Test configuration file support (AC-13)."""
        src_dir, output_dir = temp_dirs
        config_file = output_dir / "config.yaml"

        config = {
            "api": {
                "format": "markdown",
                "include_private": False,
            },
            "coverage": {
                "min_threshold": 80,
            },
            "readme": {
                "sections": ["API", "Coverage", "Architecture"],
            },
        }

        config_file.write_text(yaml.dump(config))

        generator = DocumentationGenerator(src_dir, output_dir, config_file)
        assert generator.config == config


class TestCLIArguments:
    """Test command-line argument parsing."""

    def test_parse_arguments_defaults(self):
        """Test default argument values."""
        with patch("sys.argv", ["generate_docs.py"]):
            args = parse_arguments()
            assert args.api is False
            assert args.coverage is False
            assert args.architecture is False
            assert args.format == "markdown"
            assert args.dry_run is False
            assert args.verbose is False

    def test_parse_arguments_all_options(self):
        """Test parsing all arguments."""
        with patch(
            "sys.argv",
            [
                "generate_docs.py",
                "--api",
                "--coverage",
                "--update-readme",
                "API",
                "Coverage",
                "--architecture",
                "--format",
                "html",
                "--dry-run",
                "--verbose",
            ],
        ):
            args = parse_arguments()
            assert args.api is True
            assert args.coverage is True
            assert args.update_readme == ["API", "Coverage"]
            assert args.architecture is True
            assert args.format == "html"
            assert args.dry_run is True
            assert args.verbose is True

    def test_parse_arguments_paths(self):
        """Test path arguments."""
        with patch(
            "sys.argv",
            [
                "generate_docs.py",
                "--source-dir",
                "/custom/src",
                "--output-dir",
                "/custom/docs",
                "--config",
                "/custom/config.yaml",
            ],
        ):
            args = parse_arguments()
            assert args.source_dir == Path("/custom/src")
            assert args.output_dir == Path("/custom/docs")
            assert args.config == Path("/custom/config.yaml")


class TestMainFunction:
    """Test the main entry point."""

    @patch("scripts.generate_docs.DocumentationGenerator")
    def test_main_api_generation(self, mock_generator_class):
        """Test main function with API generation."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        with patch("sys.argv", ["generate_docs.py", "--api"]):
            from scripts.generate_docs import main

            result = main()

            assert result == 0
            mock_generator.generate_api_documentation.assert_called_once_with(format="markdown")

    @patch("scripts.generate_docs.DocumentationGenerator")
    def test_main_coverage_generation(self, mock_generator_class):
        """Test main function with coverage generation."""
        mock_generator = MagicMock()
        mock_generator.generate_coverage_report.return_value = {
            "overall_coverage": "85.5%",
            "html_report": "/docs/coverage/index.html",
        }
        mock_generator_class.return_value = mock_generator

        with patch("sys.argv", ["generate_docs.py", "--coverage"]):
            from scripts.generate_docs import main

            result = main()

            assert result == 0
            mock_generator.generate_coverage_report.assert_called_once()

    @patch("scripts.generate_docs.DocumentationGenerator")
    def test_main_error_handling(self, mock_generator_class):
        """Test main function error handling."""
        mock_generator_class.side_effect = Exception("Test error")

        with patch("sys.argv", ["generate_docs.py", "--api"]):
            from scripts.generate_docs import main

            result = main()

            assert result == 1
