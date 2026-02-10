"""
Test Fixtures - Reusable Test Patterns and Components

Provides BMAD-approved test patterns, fixtures, and utilities to ensure
comprehensive test coverage with minimal boilerplate.
"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator, List
from unittest.mock import Mock

import pytest
import yaml


@pytest.fixture
def standard_test_structure() -> Dict[str, Any]:
    """
    Provides BMAD-approved test structure patterns.

    Returns:
        Dictionary containing test organization patterns
    """
    return {
        "class_organization": {
            "unit_tests": "TestUnit{ComponentName}",
            "integration_tests": "TestIntegration{ComponentName}",
            "performance_tests": "TestPerformance{ComponentName}",
            "edge_cases": "TestEdgeCases{ComponentName}",
        },
        "test_naming": {
            "success_case": "test_{method}_success",
            "error_case": "test_{method}_error_{error_type}",
            "edge_case": "test_{method}_edge_{scenario}",
            "performance": "test_{method}_performance_{metric}",
        },
        "assertion_patterns": [
            "assert result == expected",
            "assert isinstance(result, ExpectedType)",
            "assert len(result) > 0",
            "assert error_message in str(exc_info.value)",
            "assert mock_method.called_once_with(expected_args)",
        ],
        "coverage_targets": {
            "unit": 90,
            "integration": 80,
            "overall": 85,
        },
    }


@pytest.fixture
def temp_workspace() -> Generator[Path, None, None]:
    """
    Provides a temporary workspace that's automatically cleaned up.

    Yields:
        Path to temporary directory
    """
    temp_path = Path(tempfile.mkdtemp(prefix="test_workspace_"))
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_files(temp_workspace: Path) -> Dict[str, Path]:
    """
    Creates sample files for testing in temporary workspace.

    Args:
        temp_workspace: Temporary directory path

    Returns:
        Dictionary mapping file types to paths
    """
    files = {}

    # Text file
    text_file = temp_workspace / "sample.txt"
    text_file.write_text("Sample text content\nLine 2\nLine 3")
    files["text"] = text_file

    # JSON file
    json_file = temp_workspace / "sample.json"
    json_file.write_text(json.dumps({"key": "value", "number": 42}))
    files["json"] = json_file

    # YAML file
    yaml_file = temp_workspace / "sample.yaml"
    yaml_file.write_text(yaml.dump({"config": {"enabled": True, "value": 100}}))
    files["yaml"] = yaml_file

    # Python file
    py_file = temp_workspace / "sample.py"
    py_file.write_text('def hello():\n    return "Hello, World!"')
    files["python"] = py_file

    # Markdown file
    md_file = temp_workspace / "sample.md"
    md_file.write_text("# Title\n\n## Section\n\nContent here.")
    files["markdown"] = md_file

    # CSV file
    csv_file = temp_workspace / "sample.csv"
    csv_file.write_text("header1,header2,header3\nvalue1,value2,value3")
    files["csv"] = csv_file

    return files


@pytest.fixture
def mock_data_generators():
    """
    Provides functions to generate mock data for testing.

    Returns:
        Dictionary of data generator functions
    """

    def generate_dict(size: int = 10) -> Dict[str, Any]:
        """Generate dictionary with specified number of keys."""
        return {f"key_{i}": f"value_{i}" for i in range(size)}

    def generate_list(size: int = 10) -> List[Any]:
        """Generate list with specified number of items."""
        return [f"item_{i}" for i in range(size)]

    def generate_nested_structure(depth: int = 3) -> Dict[str, Any]:
        """Generate nested dictionary structure."""
        if depth <= 0:
            return {"leaf": "value"}
        return {
            f"level_{depth}": {
                "data": f"data_{depth}",
                "nested": generate_nested_structure(depth - 1),
            }
        }

    def generate_test_cases(count: int = 5) -> List[Dict[str, Any]]:
        """Generate parameterized test cases."""
        return [
            {"input": f"input_{i}", "expected": f"output_{i}", "description": f"Test case {i}"}
            for i in range(count)
        ]

    return {
        "dict": generate_dict,
        "list": generate_list,
        "nested": generate_nested_structure,
        "test_cases": generate_test_cases,
    }


@pytest.fixture
def assertion_helpers():
    """
    Provides helper functions for common assertions.

    Returns:
        Dictionary of assertion helper functions
    """

    def assert_files_equal(file1: Path, file2: Path):
        """Assert two files have identical content."""
        content1 = file1.read_text() if file1.exists() else ""
        content2 = file2.read_text() if file2.exists() else ""
        assert content1 == content2, f"Files differ: {file1} vs {file2}"

    def assert_json_equal(obj1: Any, obj2: Any):
        """Assert two objects are equal when serialized to JSON."""
        json1 = json.dumps(obj1, sort_keys=True, indent=2)
        json2 = json.dumps(obj2, sort_keys=True, indent=2)
        assert json1 == json2, "JSON representations differ"

    def assert_contains_all(container: Any, items: List[Any]):
        """Assert container contains all specified items."""
        for item in items:
            assert item in container, f"Missing item: {item}"

    def assert_called_with_subset(mock_obj: Mock, **kwargs):
        """Assert mock was called with at least the specified kwargs."""
        assert mock_obj.called, "Mock was not called"
        call_kwargs = mock_obj.call_args.kwargs
        for key, value in kwargs.items():
            assert key in call_kwargs, f"Missing key: {key}"
            assert call_kwargs[key] == value, f"Value mismatch for {key}"

    def assert_performance(func, max_time: float):
        """Assert function completes within time limit."""
        import time

        start = time.time()
        func()
        elapsed = time.time() - start
        assert elapsed < max_time, f"Too slow: {elapsed:.2f}s > {max_time}s"

    return {
        "files_equal": assert_files_equal,
        "json_equal": assert_json_equal,
        "contains_all": assert_contains_all,
        "called_with_subset": assert_called_with_subset,
        "performance": assert_performance,
    }


@pytest.fixture
def parametrize_cases():
    """
    Provides common parameterization cases for tests.

    Returns:
        Dictionary of parameterization scenarios
    """
    return {
        "edge_numbers": [0, 1, -1, 999999, -999999, 0.0, 0.1, -0.1],
        "edge_strings": ["", " ", "a", "A" * 1000, "unicode: 中文 émoji 🚀"],
        "special_chars": ["!@#$%^&*()", "\\n\\r\\t", "\"'`", "<>|;:", "null\0"],
        "file_paths": [
            Path("/"),
            Path("."),
            Path(".."),
            Path("/tmp/test.txt"),
            Path("C:\\Windows\\test.txt"),
            Path("~/test.txt"),
        ],
        "boolean_combos": [
            (True, True),
            (True, False),
            (False, True),
            (False, False),
        ],
        "error_types": [
            ValueError,
            TypeError,
            KeyError,
            FileNotFoundError,
            PermissionError,
            RuntimeError,
        ],
    }


@pytest.fixture
def mock_context_managers():
    """
    Provides mock context managers for testing.

    Returns:
        Dictionary of context manager mocks
    """

    class MockOpen:
        """Mock for open() context manager."""

        def __init__(self, content=""):
            self.content = content
            self.file = Mock()
            self.file.read.return_value = content
            self.file.write = Mock()

        def __enter__(self):
            return self.file

        def __exit__(self, *args):
            pass

    class MockTempFile:
        """Mock for temporary file context manager."""

        def __init__(self, path="/tmp/mockfile"):
            self.path = Path(path)

        def __enter__(self):
            return self.path

        def __exit__(self, *args):
            pass

    class MockLock:
        """Mock for threading lock context manager."""

        def __init__(self):
            self.acquired = False

        def __enter__(self):
            self.acquired = True
            return self

        def __exit__(self, *args):
            self.acquired = False

    return {
        "open": MockOpen,
        "tempfile": MockTempFile,
        "lock": MockLock,
    }


@pytest.fixture
def test_report_template():
    """
    Provides template for test execution reports.

    Returns:
        String template for test reports
    """
    return """
# Test Execution Report

## Summary
- **Total Tests**: {total_tests}
- **Passed**: {passed_tests}
- **Failed**: {failed_tests}
- **Skipped**: {skipped_tests}
- **Coverage**: {coverage_percent}%

## Test Categories
- **Unit Tests**: {unit_count} tests, {unit_coverage}% coverage
- **Integration Tests**: {integration_count} tests, {integration_coverage}% coverage
- **Performance Tests**: {performance_count} tests

## Performance Metrics
- **Total Execution Time**: {total_time}s
- **Average Test Time**: {avg_time}s
- **Slowest Test**: {slowest_test} ({slowest_time}s)

## Failed Tests
{failed_test_details}

## Coverage Gaps
{coverage_gaps}

## Recommendations
{recommendations}
"""


@pytest.fixture
def quality_validators():
    """
    Provides validators for test quality checks.

    Returns:
        Dictionary of validation functions
    """

    def validate_test_naming(test_name: str) -> bool:
        """Validate test follows naming convention."""
        return test_name.startswith("test_")

    def validate_test_docstring(test_func) -> bool:
        """Validate test has proper docstring."""
        return test_func.__doc__ is not None and len(test_func.__doc__) > 10

    def validate_assertions(test_source: str) -> bool:
        """Validate test contains assertions."""
        return "assert" in test_source or "self.assert" in test_source

    def validate_fixtures_usage(test_source: str) -> bool:
        """Validate test uses fixtures appropriately."""
        # Check for fixture usage patterns
        return any(
            pattern in test_source
            for pattern in [
                "@pytest.fixture",
                "def test_",
                "pytest.mark",
                "tmp_path",
                "monkeypatch",
            ]
        )

    return {
        "naming": validate_test_naming,
        "docstring": validate_test_docstring,
        "assertions": validate_assertions,
        "fixtures": validate_fixtures_usage,
    }


# Export commonly used components
__all__ = [
    "standard_test_structure",
    "temp_workspace",
    "sample_files",
    "mock_data_generators",
    "assertion_helpers",
    "parametrize_cases",
    "mock_context_managers",
    "test_report_template",
    "quality_validators",
]
