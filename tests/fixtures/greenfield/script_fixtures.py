"""
Script Fixtures - Reusable Components for Script Development

Provides BMAD-approved script scaffolding, patterns, and mocks to ensure
deterministic quality and reduce AI decision overhead.
"""

from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest


@pytest.fixture
def standard_script_scaffold() -> Dict[str, Any]:
    """
    Provides BMAD-approved script structure with embedded quality checks.

    Returns:
        Dictionary containing standard script components and validation rules
    """
    return {
        "imports": [
            "#!/usr/bin/env python3",
            '"""Module docstring."""',
            "",
            "import argparse",
            "import sys",
            "from pathlib import Path",
            "from typing import Dict, Any, Optional, List",
            "import structlog",
            "",
            "# Configure structured logging",
            "logger = structlog.get_logger()",
        ],
        "class_template": '''class ScriptProcessor:
    """Main script processing class."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize processor with configuration."""
        self.config = config
        logger.info("initialized_processor", config=config)

    def process(self, input_path: Path) -> Any:
        """Process input file."""
        try:
            # Implementation here
            result = self._process_internal(input_path)
            logger.info("processing_complete", path=str(input_path))
            return result
        except Exception as e:
            logger.error("processing_failed", error=str(e))
            raise

    def _process_internal(self, input_path: Path) -> Any:
        """Internal processing logic."""
        # Implement core logic here
        pass''',
        "main_template": '''def main() -> int:
    """Main entry point."""
    try:
        args = parse_arguments()

        # Configure logging
        if args.verbose:
            structlog.configure(
                wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
            )

        # Initialize and run
        processor = ScriptProcessor(vars(args))
        result = processor.process(args.input)

        print(f"✅ Success: {result}")
        return 0

    except Exception as e:
        logger.error("script_failed", error=str(e))
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())''',
        "argparse_template": '''def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Script description here",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Input file path"
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path.cwd(),
        help="Output directory"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without making changes"
    )

    return parser.parse_args()''',
        "validation_rules": {
            "must_have_type_hints": True,
            "must_have_docstrings": True,
            "must_handle_errors": True,
            "must_use_pathlib": True,
            "must_use_structlog": True,
            "max_line_length": 100,
            "max_complexity": 10,
        },
        "quality_checks": [
            "black --check",
            "ruff check",
            "mypy --strict",
            "pytest --cov",
        ],
    }


@pytest.fixture
def mock_filesystem():
    """
    Provides pre-configured filesystem mocks for testing scripts.

    Returns:
        Dictionary of commonly needed filesystem mocks
    """
    return {
        "path_exists": Mock(return_value=True),
        "path_is_file": Mock(return_value=True),
        "path_is_dir": Mock(return_value=False),
        "path_read_text": Mock(return_value="test content"),
        "path_write_text": Mock(),
        "path_mkdir": Mock(),
        "path_unlink": Mock(),
        "pathlib_patch": patch.object(Path, "exists", return_value=True),
    }


@pytest.fixture
def mock_subprocess():
    """
    Provides subprocess mocks for testing external command execution.

    Returns:
        Mock subprocess.run with success configuration
    """
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "Success output"
    mock_result.stderr = ""

    return Mock(return_value=mock_result)


@pytest.fixture
def mock_logger():
    """
    Provides a mock structlog logger for testing.

    Returns:
        MagicMock configured as structlog logger
    """
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    logger.debug = MagicMock()

    return logger


@pytest.fixture
def error_scenarios():
    """
    Provides common error scenarios for comprehensive testing.

    Returns:
        List of exception scenarios to test
    """
    return [
        FileNotFoundError("File not found"),
        PermissionError("Permission denied"),
        ValueError("Invalid value"),
        IOError("I/O operation failed"),
        RuntimeError("Runtime error occurred"),
        KeyError("Missing key"),
        TypeError("Type mismatch"),
        AttributeError("Attribute not found"),
    ]


@pytest.fixture
def performance_benchmarks():
    """
    Provides performance benchmarks for scripts.

    Returns:
        Dictionary of performance targets
    """
    return {
        "small_file_processing": 0.1,  # 100ms for files < 1MB
        "medium_file_processing": 0.5,  # 500ms for files < 10MB
        "large_file_processing": 2.0,  # 2s for files < 100MB
        "batch_processing_per_item": 0.05,  # 50ms per item in batch
        "startup_time": 0.1,  # 100ms script startup
        "memory_limit_mb": 500,  # 500MB memory limit
    }


@pytest.fixture
def script_test_template():
    """
    Provides a template for testing scripts comprehensively.

    Returns:
        String template for test file structure
    """
    return '''"""
Tests for {script_name} script.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import {script_module}


class Test{ScriptClass}:
    """Test suite for {ScriptClass}."""

    @pytest.fixture
    def instance(self):
        """Create instance for testing."""
        config = {{"test": True}}
        return {script_module}.{ScriptClass}(config)

    def test_initialization(self, instance):
        """Test proper initialization."""
        assert instance.config["test"] is True

    def test_process_success(self, instance, tmp_path):
        """Test successful processing."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        result = instance.process(test_file)
        assert result is not None

    def test_process_error_handling(self, instance):
        """Test error handling."""
        with pytest.raises(FileNotFoundError):
            instance.process(Path("/nonexistent"))

    @patch("{script_module}.logger")
    def test_logging(self, mock_logger, instance, tmp_path):
        """Test logging behavior."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        instance.process(test_file)
        mock_logger.info.assert_called()


class TestCLI:
    """Test suite for CLI functionality."""

    def test_parse_arguments(self):
        """Test argument parsing."""
        with patch("sys.argv", ["script", "input.txt"]):
            args = {script_module}.parse_arguments()
            assert args.input == Path("input.txt")

    @patch("{script_module}.ScriptProcessor")
    def test_main_success(self, mock_processor):
        """Test successful execution."""
        with patch("sys.argv", ["script", "input.txt"]):
            result = {script_module}.main()
            assert result == 0

    def test_main_error(self):
        """Test error handling in main."""
        with patch("sys.argv", ["script", "/nonexistent"]):
            result = {script_module}.main()
            assert result == 1
'''


@pytest.fixture
def validation_helpers():
    """
    Provides helper functions for validating script structure.

    Returns:
        Dictionary of validation functions
    """

    def has_type_hints(source: str) -> bool:
        """Check if source has type hints."""
        return "->" in source and ":" in source

    def has_docstrings(source: str) -> bool:
        """Check if source has docstrings."""
        return '"""' in source or "'''" in source

    def has_error_handling(source: str) -> bool:
        """Check if source has error handling."""
        return "try:" in source and "except" in source

    def uses_pathlib(source: str) -> bool:
        """Check if source uses pathlib."""
        return "from pathlib import Path" in source or "import pathlib" in source

    def uses_structlog(source: str) -> bool:
        """Check if source uses structlog."""
        return "import structlog" in source

    return {
        "has_type_hints": has_type_hints,
        "has_docstrings": has_docstrings,
        "has_error_handling": has_error_handling,
        "uses_pathlib": uses_pathlib,
        "uses_structlog": uses_structlog,
    }


# Export commonly used components
__all__ = [
    "standard_script_scaffold",
    "mock_filesystem",
    "mock_subprocess",
    "mock_logger",
    "error_scenarios",
    "performance_benchmarks",
    "script_test_template",
    "validation_helpers",
]
