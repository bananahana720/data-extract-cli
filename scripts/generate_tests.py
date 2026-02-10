#!/usr/bin/env python3
"""
Test Generator from Story Specifications

Parses story markdown files to extract acceptance criteria and generates
comprehensive test stubs, fixtures, and appropriate pytest markers.

This tool accelerates test-driven development by creating structured test
files directly from story specifications.

Usage:
    python scripts/generate_tests.py --story docs/stories/4-1-tf-idf.md
    python scripts/generate_tests.py --story docs/stories/4-1-tf-idf.md --output tests/unit/data_extract/semantic/
    python scripts/generate_tests.py --story docs/stories/4-1-tf-idf.md --markers auto
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import structlog  # type: ignore[import-not-found]

# Configure structured logging
logger = structlog.get_logger()

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
STORIES_DIR = PROJECT_ROOT / "docs" / "stories"
TESTS_DIR = PROJECT_ROOT / "tests"
FIXTURES_DIR = TESTS_DIR / "fixtures"

# Keywords that suggest test types
UNIT_KEYWORDS = {"function", "method", "class", "unit", "parse", "extract", "validate", "calculate"}
INTEGRATION_KEYWORDS = {"integration", "pipeline", "workflow", "end-to-end", "e2e", "system", "cli"}
PERFORMANCE_KEYWORDS = {
    "performance",
    "nfr",
    "throughput",
    "latency",
    "memory",
    "speed",
    "benchmark",
}


class StoryTestGenerator:
    """Generates test files from story specifications."""

    def __init__(self) -> None:
        """Initialize the test generator."""
        self.story_content = ""
        self.story_key = ""
        self.epic_number = ""
        self.story_number = ""
        self.acceptance_criteria: List[Dict[str, str]] = []
        self.tasks: List[str] = []
        self.has_performance_requirements = False
        logger.info("initialized_test_generator")

    def parse_story_file(self, story_path: Path) -> bool:
        """
        Parse story markdown file to extract ACs and metadata.

        Args:
            story_path: Path to story markdown file

        Returns:
            True if successfully parsed, False otherwise
        """
        logger.info("parsing_story_file", path=str(story_path))

        if not story_path.exists():
            logger.error("story_file_not_found", path=str(story_path))
            return False

        with open(story_path, "r", encoding="utf-8") as f:
            self.story_content = f.read()

        # Extract story key from filename or content
        self._extract_story_key(story_path)

        # Extract acceptance criteria
        self._extract_acceptance_criteria()

        # Extract tasks
        self._extract_tasks()

        # Check for performance requirements
        self._check_performance_requirements()

        logger.info(
            "story_parsed",
            story_key=self.story_key,
            ac_count=len(self.acceptance_criteria),
            has_performance=self.has_performance_requirements,
        )

        return True

    def _extract_story_key(self, story_path: Path) -> None:
        """
        Extract story key from filename or content.

        Args:
            story_path: Path to story file
        """
        # Try to extract from filename first
        filename = story_path.stem
        match = re.match(r"^(\d+(?:\.\d+)?)-(\d+)-(.+)$", filename)

        if match:
            self.epic_number = match.group(1)
            self.story_number = match.group(2)
            self.story_key = filename
        else:
            # Try to extract from content
            key_match = re.search(r"Story Key:\s*`?([^\s`]+)`?", self.story_content)
            if key_match:
                self.story_key = key_match.group(1)
                # Parse the key
                parts = self.story_key.split("-")
                if len(parts) >= 2:
                    self.epic_number = parts[0]
                    self.story_number = parts[1]
            else:
                # Fallback to filename
                self.story_key = filename

        logger.debug("extracted_story_key", key=self.story_key, epic=self.epic_number)

    def _extract_acceptance_criteria(self) -> None:
        """Extract acceptance criteria from story content."""
        self.acceptance_criteria = []

        # Find the Acceptance Criteria section
        ac_section = re.search(
            r"## Acceptance Criteria(.*?)(?=## |$)", self.story_content, re.DOTALL | re.IGNORECASE
        )

        if not ac_section:
            logger.warning("no_acceptance_criteria_section_found")
            return

        ac_text = ac_section.group(1)

        # Pattern for numbered ACs with optional AC- prefix
        ac_pattern = r"(?:^|\n)\s*(?:AC-)?(\d+)\.?\s*\*?\*?([^:]+?)[:*]?\*?\*?\s*(.+?)(?=\n\s*(?:AC-)?\d+\.|\Z)"

        for match in re.finditer(ac_pattern, ac_text, re.DOTALL | re.MULTILINE):
            ac_num = match.group(1)
            ac_title = match.group(2).strip()
            ac_description = match.group(3).strip()

            # Clean up the description
            ac_description = re.sub(r"\s+", " ", ac_description)
            ac_description = ac_description.split("[")[0].strip()  # Remove source references

            self.acceptance_criteria.append(
                {
                    "number": ac_num,
                    "title": ac_title,
                    "description": ac_description,
                    "id": f"AC-{ac_num}",
                }
            )

        logger.debug("extracted_acceptance_criteria", count=len(self.acceptance_criteria))

    def _extract_tasks(self) -> None:
        """Extract tasks from story content."""
        self.tasks = []

        # Find the Tasks section
        tasks_section = re.search(
            r"## Tasks[/\s]*Subtasks(.*?)(?=## |$)", self.story_content, re.DOTALL | re.IGNORECASE
        )

        if not tasks_section:
            return

        tasks_text = tasks_section.group(1)

        # Extract task descriptions
        task_pattern = r"- \[.\]\s*\*?\*?(.+?)[:*]?\*?\*?"

        for match in re.finditer(task_pattern, tasks_text):
            task = match.group(1).strip()
            self.tasks.append(task)

        logger.debug("extracted_tasks", count=len(self.tasks))

    def _check_performance_requirements(self) -> None:
        """Check if story has performance/NFR requirements."""
        content_lower = self.story_content.lower()

        # Check for performance-related keywords
        perf_indicators = [
            "nfr",
            "performance",
            "throughput",
            "latency",
            "memory",
            "benchmark",
            "speed",
            "optimization",
            "efficiency",
        ]

        self.has_performance_requirements = any(
            indicator in content_lower for indicator in perf_indicators
        )

    def generate_test_file(
        self, output_dir: Optional[Path] = None, marker_mode: str = "auto"
    ) -> Tuple[Path, str]:
        """
        Generate test file with stubs for each AC.

        Args:
            output_dir: Output directory for test file
            marker_mode: How to assign markers (auto, unit, integration, both)

        Returns:
            Tuple of (test_file_path, test_content)
        """
        logger.info("generating_test_file", marker_mode=marker_mode)

        # Determine output path
        if output_dir is None:
            # Default to appropriate test directory
            module_name = self._get_module_name()
            output_dir = TESTS_DIR / "unit" / f"test_{module_name}"

        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate test filename
        test_filename = f"test_{self.story_key.replace('-', '_')}.py"
        test_path = output_dir / test_filename

        # Generate test content
        test_content = self._generate_test_content(marker_mode)

        # Write test file
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(test_content)

        logger.info("test_file_generated", path=str(test_path))

        return test_path, test_content

    def _get_module_name(self) -> str:
        """
        Determine module name from story key.

        Returns:
            Module name for test organization
        """
        # Map epic numbers to module names
        epic_to_module = {
            "1": "infrastructure",
            "2": "normalize",
            "2.5": "infrastructure",
            "3": "chunk",
            "3.5": "scripts",
            "4": "semantic",
            "5": "cli",
        }

        return epic_to_module.get(self.epic_number, "misc")

    def _generate_test_content(self, marker_mode: str) -> str:
        """
        Generate test file content with proper structure.

        Args:
            marker_mode: How to assign markers

        Returns:
            Test file content as string
        """
        lines = [
            '"""',
            f"Test suite for Story {self.story_key}",
            "",
            "Generated from story specification.",
            f"Generated at: {datetime.now().isoformat()}",
            '"""',
            "",
            "import pytest",
            "from pathlib import Path",
            "from typing import Any, Dict",
            "",
        ]

        # Add imports based on module
        module = self._get_module_name()
        if module == "semantic":
            lines.extend(
                [
                    "import numpy as np",
                    "from sklearn.feature_extraction.text import TfidfVectorizer",
                    "",
                ]
            )
        elif module == "cli":
            lines.extend(
                [
                    "from typer.testing import CliRunner",
                    "from data_extract.cli import app",
                    "",
                ]
            )

        # Add fixture imports
        lines.extend(
            [
                f"from tests.fixtures.{self.story_key.replace('-', '_')}_fixtures import (",
                "    sample_data,",
                "    test_config,",
                "    mock_dependencies",
                ")",
                "",
                "",
            ]
        )

        # Generate test class
        class_name = self._generate_class_name()
        lines.extend(
            [
                f"class {class_name}:",
                f'    """Test cases for {self.story_key} acceptance criteria."""',
                "",
            ]
        )

        # Generate test methods for each AC
        for ac in self.acceptance_criteria:
            test_method = self._generate_test_method(ac, marker_mode)
            lines.extend(test_method)

        # Add performance test template if needed
        if self.has_performance_requirements:
            lines.extend(self._generate_performance_test_template())

        return "\n".join(lines)

    def _generate_class_name(self) -> str:
        """
        Generate test class name from story key.

        Returns:
            PascalCase class name
        """
        # Convert story key to class name
        parts = self.story_key.split("-")

        # Handle numeric parts
        class_parts = []
        for part in parts:
            if part.replace(".", "").isdigit():
                class_parts.append(f"Story{part.replace('.', '_')}")
            else:
                class_parts.append(part.title())

        return "Test" + "".join(class_parts)

    def _generate_test_method(self, ac: Dict[str, str], marker_mode: str) -> List[str]:
        """
        Generate test method for an acceptance criterion.

        Args:
            ac: Acceptance criterion dictionary
            marker_mode: How to assign markers

        Returns:
            List of code lines for test method
        """
        lines = []

        # Determine markers
        markers = self._determine_markers(ac, marker_mode)

        # Add markers
        for marker in markers:
            lines.append(f"    @pytest.mark.{marker}")

        # Generate method name
        method_name = f"test_ac_{ac['number']}_{self._slugify(ac['title'])}"

        # Add method definition
        lines.extend(
            [
                f"    def {method_name}(self, sample_data: Dict[str, Any], test_config: Dict[str, Any]):",
                '        """',
                f"        {ac['id']}: {ac['title']}",
                "        ",
                f"        {ac['description']}",
                '        """',
            ]
        )

        # Add test implementation stub
        lines.extend(
            [
                "        # Arrange",
                "        # TODO: Set up test data and expected results",
                "        test_input = sample_data.get('input')",
                "        expected = sample_data.get('expected')",
                "",
                "        # Act",
                "        # TODO: Execute the functionality being tested",
                "        result = None  # Replace with actual implementation",
                "",
                "        # Assert",
                "        # TODO: Verify the results meet acceptance criteria",
                '        assert result is not None, "Implementation not complete"',
                f'        # assert result == expected, "{ac["title"]} validation failed"',
                "",
            ]
        )

        return lines

    def _determine_markers(self, ac: Dict[str, str], marker_mode: str) -> List[str]:
        """
        Determine appropriate pytest markers for an AC.

        Args:
            ac: Acceptance criterion
            marker_mode: Marker assignment mode

        Returns:
            List of marker names
        """
        if marker_mode == "unit":
            return ["unit"]
        elif marker_mode == "integration":
            return ["integration"]
        elif marker_mode == "both":
            return ["unit", "integration"]
        elif marker_mode == "auto":
            # Analyze AC content to determine markers
            content = (ac["title"] + " " + ac["description"]).lower()

            markers = []

            # Check for integration keywords
            if any(kw in content for kw in INTEGRATION_KEYWORDS):
                markers.append("integration")
            # Check for unit keywords
            elif any(kw in content for kw in UNIT_KEYWORDS):
                markers.append("unit")
            else:
                # Default to unit
                markers.append("unit")

            # Check for performance keywords
            if any(kw in content for kw in PERFORMANCE_KEYWORDS):
                markers.append("performance")

            return markers

        return ["unit"]  # Default

    def _slugify(self, text: str) -> str:
        """
        Convert text to valid Python identifier.

        Args:
            text: Input text

        Returns:
            Slugified text
        """
        # Remove special characters and convert to snake_case
        text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
        text = re.sub(r"\s+", "_", text)
        text = text.lower()

        # Ensure it starts with a letter
        if text and text[0].isdigit():
            text = "n_" + text

        return text[:50]  # Limit length

    def _generate_performance_test_template(self) -> List[str]:
        """
        Generate performance test template.

        Returns:
            List of code lines for performance test
        """
        return [
            "",
            "    @pytest.mark.performance",
            "    @pytest.mark.slow",
            "    def test_performance_requirements(self, sample_data: Dict[str, Any]):",
            '        """',
            "        Validate performance and NFR requirements.",
            "        ",
            "        This test ensures the implementation meets specified performance targets.",
            '        """',
            "        import time",
            "        import psutil",
            "        ",
            "        # Arrange",
            "        process = psutil.Process()",
            "        start_memory = process.memory_info().rss / 1024 / 1024  # MB",
            "        test_input = sample_data.get('performance_input')",
            "        ",
            "        # Act",
            "        start_time = time.perf_counter()",
            "        # TODO: Execute performance-critical operation",
            "        result = None  # Replace with actual implementation",
            "        elapsed_time = time.perf_counter() - start_time",
            "        ",
            "        end_memory = process.memory_info().rss / 1024 / 1024  # MB",
            "        memory_used = end_memory - start_memory",
            "        ",
            "        # Assert",
            "        # TODO: Update thresholds based on NFR requirements",
            '        assert elapsed_time < 1.0, f"Operation took {elapsed_time:.2f}s (limit: 1.0s)"',
            '        assert memory_used < 100, f"Used {memory_used:.1f}MB memory (limit: 100MB)"',
            "",
        ]

    def generate_fixture_file(self, output_dir: Optional[Path] = None) -> Tuple[Path, str]:
        """
        Generate fixture file with sample data.

        Args:
            output_dir: Output directory for fixture file

        Returns:
            Tuple of (fixture_file_path, fixture_content)
        """
        logger.info("generating_fixture_file")

        # Determine output path
        if output_dir is None:
            output_dir = FIXTURES_DIR

        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate fixture filename
        fixture_filename = f"{self.story_key.replace('-', '_')}_fixtures.py"
        fixture_path = output_dir / fixture_filename

        # Generate fixture content
        fixture_content = self._generate_fixture_content()

        # Write fixture file
        with open(fixture_path, "w", encoding="utf-8") as f:
            f.write(fixture_content)

        logger.info("fixture_file_generated", path=str(fixture_path))

        return fixture_path, fixture_content

    def _generate_fixture_content(self) -> str:
        """
        Generate fixture file content.

        Returns:
            Fixture file content as string
        """
        lines = [
            '"""',
            f"Test fixtures for Story {self.story_key}",
            "",
            "Provides sample data and test configurations.",
            f"Generated at: {datetime.now().isoformat()}",
            '"""',
            "",
            "import pytest",
            "from pathlib import Path",
            "from typing import Any, Dict, List",
            "",
            "",
            "@pytest.fixture",
            "def sample_data() -> Dict[str, Any]:",
            '    """',
            "    Provide sample test data for story acceptance criteria.",
            "    ",
            "    Returns:",
            "        Dictionary containing test inputs and expected outputs",
            '    """',
            "    return {",
        ]

        # Generate sample data for each AC
        for ac in self.acceptance_criteria:
            lines.extend(
                [
                    f"        # {ac['id']}: {ac['title']}",
                    f"        'ac_{ac['number']}_input': {{",
                    "            # TODO: Add specific test input data",
                    f"            'description': '{ac['description'][:100]}...',",
                    "            'data': None,",
                    "        },",
                    f"        'ac_{ac['number']}_expected': {{",
                    "            # TODO: Add expected output",
                    "            'result': None,",
                    "        },",
                    "",
                ]
            )

        # Add performance test data if needed
        if self.has_performance_requirements:
            lines.extend(
                [
                    "        # Performance test data",
                    "        'performance_input': {",
                    "            'large_dataset': None,  # TODO: Add large test dataset",
                    "            'iterations': 1000,",
                    "        },",
                    "",
                ]
            )

        lines.extend(
            [
                "    }",
                "",
                "",
                "@pytest.fixture",
                "def test_config() -> Dict[str, Any]:",
                '    """',
                "    Provide test configuration settings.",
                "    ",
                "    Returns:",
                "        Dictionary containing test configuration",
                '    """',
                "    return {",
                f"        'story_key': '{self.story_key}',",
                f"        'epic_number': '{self.epic_number}',",
                "        'test_timeout': 30,  # seconds",
                "        'enable_debug': False,",
                "        'test_data_dir': Path('tests/data'),",
                "    }",
                "",
                "",
                "@pytest.fixture",
                "def mock_dependencies(monkeypatch):",
                '    """',
                "    Mock external dependencies for isolated testing.",
                "    ",
                "    Args:",
                "        monkeypatch: pytest monkeypatch fixture",
                "    ",
                "    Returns:",
                "        Dictionary of mocked dependencies",
                '    """',
                "    mocks = {}",
                "    ",
                "    # TODO: Add specific mocks based on story requirements",
                "    # Example:",
                "    # from unittest.mock import Mock",
                "    # mock_api = Mock()",
                "    # monkeypatch.setattr('module.api_client', mock_api)",
                "    # mocks['api'] = mock_api",
                "    ",
                "    return mocks",
                "",
            ]
        )

        # Add helper functions if needed
        if self.tasks:
            lines.extend(
                [
                    "",
                    "# Helper functions for test setup",
                    "",
                ]
            )

            for i, task in enumerate(self.tasks[:3], 1):  # First 3 tasks as examples
                func_name = f"setup_{self._slugify(task)}"[:50]
                lines.extend(
                    [
                        f"def {func_name}():",
                        f'    """Setup for: {task[:100]}"""',
                        "    # TODO: Implement setup logic",
                        "    pass",
                        "",
                    ]
                )

        return "\n".join(lines)


def main() -> None:
    """Main entry point for the test generator."""
    parser = argparse.ArgumentParser(
        description="Generate test files from story specifications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate test from story
  python scripts/generate_tests.py --story docs/stories/4-1-tf-idf.md

  # Specify output directory
  python scripts/generate_tests.py --story docs/stories/4-1-tf-idf.md \\
    --output tests/integration/

  # Auto-detect test markers
  python scripts/generate_tests.py --story docs/stories/4-1-tf-idf.md \\
    --markers auto

  # Generate only fixtures
  python scripts/generate_tests.py --story docs/stories/4-1-tf-idf.md \\
    --fixtures-only
        """,
    )

    parser.add_argument("--story", type=Path, required=True, help="Path to story markdown file")

    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory for test file (auto-determined if not specified)",
    )

    parser.add_argument(
        "--markers",
        choices=["auto", "unit", "integration", "both"],
        default="auto",
        help="How to assign pytest markers (default: auto)",
    )

    parser.add_argument(
        "--fixtures-only", action="store_true", help="Only generate fixtures file, skip test file"
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        import logging

        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        )

    try:
        # Initialize generator
        generator = StoryTestGenerator()

        # Parse story file
        if not generator.parse_story_file(args.story):
            print(f"❌ Failed to parse story file: {args.story}", file=sys.stderr)
            sys.exit(1)

        # Generate fixture file
        fixture_path, _ = generator.generate_fixture_file()
        print(f"✅ Generated fixture file: {fixture_path}")

        # Generate test file unless fixtures-only
        if not args.fixtures_only:
            test_path, _ = generator.generate_test_file(
                output_dir=args.output, marker_mode=args.markers
            )
            print(f"✅ Generated test file: {test_path}")

        # Summary
        print("\n📊 Summary:")
        print(f"  - Story: {generator.story_key}")
        print(f"  - Acceptance Criteria: {len(generator.acceptance_criteria)}")
        print(f"  - Performance Tests: {'Yes' if generator.has_performance_requirements else 'No'}")

        if generator.acceptance_criteria:
            print("\n📋 Test Coverage:")
            for ac in generator.acceptance_criteria[:5]:  # Show first 5
                print(f"  - {ac['id']}: {ac['title']}")
            if len(generator.acceptance_criteria) > 5:
                print(f"  ... and {len(generator.acceptance_criteria) - 5} more")

    except Exception as e:
        logger.error("test_generation_failed", error=str(e))
        print(f"❌ Test generation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
