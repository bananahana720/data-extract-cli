#!/usr/bin/env python3
"""
Story Template Generator

Generates standardized story templates with acceptance criteria tables,
wiring checklists, and submission summaries for the Data Extraction Tool project.

Usage:
    python scripts/generate_story_template.py --story-number 4.1 --epic 4 --title "Semantic Analysis Foundation"
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import structlog
import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

# Configure structured logging
logger = structlog.get_logger()

# Constants
TEMPLATE_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "stories"
DEFAULT_OWNER = "Team"
DEFAULT_ESTIMATE = 4


class StoryTemplateGenerator:
    """Generates story markdown files from Jinja2 templates."""

    def __init__(self, template_dir: Path = TEMPLATE_DIR):
        """
        Initialize the template generator.

        Args:
            template_dir: Directory containing Jinja2 templates
        """
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)), trim_blocks=True, lstrip_blocks=True
        )
        logger.info("initialized_template_generator", template_dir=str(template_dir))

    def generate_story(
        self,
        story_number: str,
        epic: str,
        title: str,
        owner: str = DEFAULT_OWNER,
        estimate: int = DEFAULT_ESTIMATE,
        output_dir: Path = OUTPUT_DIR,
        dry_run: bool = False,
        with_tests: bool = False,
        with_fixtures: bool = False,
        with_uat: bool = False,
        update_status: bool = False,
    ) -> Path:
        """
        Generate a story markdown file from template.

        Args:
            story_number: Story number (e.g., "4.1")
            epic: Epic number (e.g., "4")
            title: Story title
            owner: Story owner/assignee
            estimate: Estimated hours
            output_dir: Directory to write output file
            dry_run: If True, only preview without writing
            with_tests: If True, generate test file template
            with_fixtures: If True, generate fixture file
            with_uat: If True, generate UAT test cases
            update_status: If True, update sprint-status.yaml

        Returns:
            Path to generated file (or would-be path if dry_run)

        Raises:
            TemplateNotFound: If template file doesn't exist
            IOError: If file write fails
        """
        # Validate epic dependencies if not in dry-run mode and any enhanced features are enabled
        if not dry_run and (with_tests or with_fixtures or with_uat or update_status):
            is_valid, message = self.validate_epic_dependencies(epic, story_number)
            if not is_valid:
                logger.warning("epic_dependency_validation_failed", message=message)
                print(f"⚠️  Warning: {message}")
                # Continue but warn user

        # Prepare template variables
        title_slug = self._create_slug(title)
        story_key = f"{story_number}-{title_slug}"

        # Enhanced AC template with evidence placeholders if tests are being generated
        acceptance_criteria = self._generate_ac_template()
        if with_tests:
            # Add evidence placeholders linking to test files
            for i, ac in enumerate(acceptance_criteria):
                ac["evidence"] = (
                    f"See tests/unit/test_scripts/test_{story_key.replace('-', '_')}.py::test_acceptance_criterion_{i+1}"
                )

        variables = {
            "story_number": story_number,
            "epic": epic,
            "title": title,
            "title_slug": title_slug,
            "story_key": story_key,
            "owner": owner,
            "estimate": estimate,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "acceptance_criteria": acceptance_criteria,
            "wiring_checklist": self._generate_wiring_checklist(),
            "submission_summary": self._generate_submission_summary(),
        }

        # Render template
        try:
            template = self.env.get_template("story.md.j2")
            rendered = template.render(**variables)
            logger.info(
                "rendered_template", story_number=story_number, variables_count=len(variables)
            )
        except TemplateNotFound as e:
            logger.error("template_not_found", template=str(e))
            raise

        # Write or preview output
        output_path = output_dir / f"{story_key}.md"

        if dry_run:
            print("\n=== DRY RUN - Generated Story Preview ===\n")
            print(rendered)
            print(f"\n=== Would write to: {output_path} ===")
            if with_tests:
                print(
                    f"Would generate test file: tests/unit/test_scripts/test_{story_key.replace('-', '_')}.py"
                )
            if with_fixtures:
                print(
                    f"Would generate fixture file: tests/fixtures/{story_key.replace('-', '_')}_fixtures.py"
                )
            if with_uat:
                print(
                    f"Would generate UAT test cases: docs/uat/test-cases/{story_key}-test-cases.md"
                )
            if update_status:
                print(f"Would update sprint-status.yaml with story: {story_key}")
        else:
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered, encoding="utf-8")
            logger.info("wrote_story_file", path=str(output_path), size=len(rendered))

            # Generate additional files based on flags
            generated_files = [output_path]

            if with_tests:
                test_file = self.generate_test_file(story_key, title, output_dir)
                generated_files.append(test_file)
                print(f"✅ Generated test file: {test_file}")

            if with_fixtures:
                fixture_file = self.generate_fixture_file(story_key, output_dir)
                generated_files.append(fixture_file)
                print(f"✅ Generated fixture file: {fixture_file}")

            if with_uat:
                uat_file = self.generate_uat_test_case(story_key, title, output_dir)
                generated_files.append(uat_file)
                print(f"✅ Generated UAT test cases: {uat_file}")

            if update_status:
                if self.update_sprint_status(story_key, epic):
                    print(f"✅ Updated sprint-status.yaml with story: {story_key}")
                else:
                    print("⚠️  Failed to update sprint-status.yaml")

        return output_path

    def _create_slug(self, title: str) -> str:
        """
        Create URL-safe slug from title.

        Args:
            title: Story title

        Returns:
            Slugified title
        """
        # Replace spaces and special chars with hyphens
        slug = title.lower()
        slug = "".join(c if c.isalnum() or c == "-" else "-" for c in slug)
        # Remove consecutive hyphens and trim
        while "--" in slug:
            slug = slug.replace("--", "-")
        slug = slug.strip("-")
        return slug

    def _generate_ac_template(self) -> list:
        """Generate acceptance criteria template structure."""
        return [
            {
                "id": 1,
                "description": "TODO: Define acceptance criterion",
                "evidence": "TODO: Add evidence/implementation notes",
            },
            {
                "id": 2,
                "description": "TODO: Define acceptance criterion",
                "evidence": "TODO: Add evidence/implementation notes",
            },
            {
                "id": 3,
                "description": "TODO: Define acceptance criterion",
                "evidence": "TODO: Add evidence/implementation notes",
            },
        ]

    def _generate_wiring_checklist(self) -> dict:
        """Generate wiring checklist template."""
        return {
            "bom": [
                "TODO: List new dependencies/packages",
                "If adding dependencies, follow docs/processes/test-dependency-audit.md",
            ],
            "logging": ["TODO: Add structured logging points"],
            "cli": ["TODO: Define CLI flags/commands"],
            "testing": ["TODO: List test requirements"],
        }

    def _generate_submission_summary(self) -> dict:
        """Generate submission summary template."""
        return {
            "files_created": ["TODO: List new files"],
            "files_modified": ["TODO: List modified files"],
            "tests_added": ["TODO: List test files"],
            "coverage": "TODO: Report coverage %",
        }

    def validate_template(self, template_name: str = "story.md.j2") -> bool:
        """
        Validate that a template exists and is loadable.

        Args:
            template_name: Name of template file

        Returns:
            True if template is valid, False otherwise
        """
        try:
            self.env.get_template(template_name)
            return True
        except TemplateNotFound:
            return False

    def validate_epic_dependencies(self, epic: str, story_number: str) -> tuple[bool, str]:
        """
        Validate that prerequisite stories from same/previous epics are complete.

        Args:
            epic: Epic number
            story_number: Story number

        Returns:
            Tuple of (is_valid, message)
        """
        sprint_status_path = Path(__file__).parent.parent / "docs" / "sprint-status.yaml"

        if not sprint_status_path.exists():
            return True, "Sprint status file not found, skipping dependency validation"

        try:
            with open(sprint_status_path, "r") as f:
                sprint_data = yaml.safe_load(f)
        except Exception:
            # If we can't parse YAML, we'll skip validation
            return True, "Could not parse sprint status, skipping dependency validation"

        dev_status = sprint_data.get("development_status", {})

        # Check if previous stories in same epic are complete
        epic_stories = [k for k in dev_status.keys() if k.startswith(f"{epic}-")]
        for story_key in epic_stories:
            # Parse story number from key (e.g., "3.5-1-some-title" -> "3.5-1")
            parts = story_key.split("-")
            if len(parts) >= 2:
                other_story_num = f"{parts[0]}-{parts[1]}"
                if other_story_num < story_number:
                    status = dev_status.get(story_key)
                    if status not in ["done", "review"]:
                        return (
                            False,
                            f"Prerequisite story {other_story_num} is not complete (status: {status})",
                        )

        return True, "All dependencies satisfied"

    def generate_test_file(self, story_key: str, story_title: str, output_dir: Path) -> Path:
        """
        Generate test file template for the story.

        Args:
            story_key: Story key (e.g., "3.5-1-template-generator")
            story_title: Story title
            output_dir: Base output directory

        Returns:
            Path to generated test file
        """
        test_dir = output_dir.parent.parent / "tests" / "unit" / "test_scripts"
        test_dir.mkdir(parents=True, exist_ok=True)

        test_file_path = test_dir / f"test_{story_key.replace('-', '_')}.py"

        test_content = f'''"""
Test suite for Story {story_key}: {story_title}

Auto-generated test template with AC-based test stubs.
"""

import pytest
from pathlib import Path


class Test{story_key.replace("-", "").replace(".", "").title()}:
    """Test suite for {story_title}."""

    def test_acceptance_criterion_1(self):
        """Test AC-1: TODO: Add description."""
        # TODO: Implement test
        assert True  # Placeholder

    def test_acceptance_criterion_2(self):
        """Test AC-2: TODO: Add description."""
        # TODO: Implement test
        assert True  # Placeholder

    def test_acceptance_criterion_3(self):
        """Test AC-3: TODO: Add description."""
        # TODO: Implement test
        assert True  # Placeholder


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''

        test_file_path.write_text(test_content, encoding="utf-8")
        logger.info("generated_test_file", path=str(test_file_path))
        return test_file_path

    def generate_fixture_file(self, story_key: str, output_dir: Path) -> Path:
        """
        Generate fixture file for the story.

        Args:
            story_key: Story key
            output_dir: Base output directory

        Returns:
            Path to generated fixture file
        """
        fixture_dir = output_dir.parent.parent / "tests" / "fixtures"
        fixture_dir.mkdir(parents=True, exist_ok=True)

        fixture_file_path = fixture_dir / f"{story_key.replace('-', '_')}_fixtures.py"

        fixture_content = f'''"""
Test fixtures for Story {story_key}.

Auto-generated fixture file with sample data structures.
"""

import pytest
from pathlib import Path


# Sample fixture data
SAMPLE_DATA = {{
    "story_key": "{story_key}",
    "test_data": [
        {{"id": 1, "value": "test1"}},
        {{"id": 2, "value": "test2"}},
    ],
}}


@pytest.fixture
def sample_data():
    """Provide sample test data."""
    return SAMPLE_DATA.copy()


@pytest.fixture
def temp_dir(tmp_path):
    """Provide temporary directory for test files."""
    return tmp_path
'''

        fixture_file_path.write_text(fixture_content, encoding="utf-8")
        logger.info("generated_fixture_file", path=str(fixture_file_path))
        return fixture_file_path

    def update_sprint_status(self, story_key: str, epic: str) -> bool:
        """
        Update sprint-status.yaml with new story entry in 'drafted' status.

        Args:
            story_key: Story key
            epic: Epic number

        Returns:
            True if updated successfully
        """
        sprint_status_path = Path(__file__).parent.parent / "docs" / "sprint-status.yaml"

        try:
            # Read existing content
            content = sprint_status_path.read_text() if sprint_status_path.exists() else ""
            lines = content.splitlines()

            # Find the development_status section
            dev_status_index = -1
            for i, line in enumerate(lines):
                if "development_status:" in line:
                    dev_status_index = i
                    break

            if dev_status_index == -1:
                logger.warning(
                    "sprint_status_not_found", message="Could not find development_status section"
                )
                return False

            # Find the right place to insert the new story (after the epic line)
            epic_line_index = -1
            for i in range(dev_status_index, len(lines)):
                if f"epic-{epic}:" in lines[i]:
                    epic_line_index = i
                    break

            if epic_line_index != -1:
                # Find next epic or end of development_status section
                insert_index = epic_line_index + 1
                while insert_index < len(lines) and lines[insert_index].startswith("  "):
                    if "epic-" in lines[insert_index]:
                        break
                    insert_index += 1

                # Check if story already exists
                for line in lines:
                    if f"  {story_key}:" in line:
                        logger.info("story_already_in_sprint_status", story_key=story_key)
                        return True

                # Insert new story entry
                new_entry = (
                    f"  {story_key}: drafted  # Story created {datetime.now().strftime('%Y-%m-%d')}"
                )
                lines.insert(insert_index, new_entry)

                # Write back
                sprint_status_path.write_text("\n".join(lines) + "\n")
                logger.info("updated_sprint_status", story_key=story_key)
                return True

        except Exception as e:
            logger.error("failed_to_update_sprint_status", error=str(e))
            return False

    def generate_uat_test_case(self, story_key: str, story_title: str, output_dir: Path) -> Path:
        """
        Generate UAT test case file for the story.

        Args:
            story_key: Story key
            story_title: Story title
            output_dir: Base output directory

        Returns:
            Path to generated UAT test case file
        """
        uat_dir = output_dir.parent.parent / "docs" / "uat" / "test-cases"
        uat_dir.mkdir(parents=True, exist_ok=True)

        uat_file_path = uat_dir / f"{story_key}-test-cases.md"

        uat_content = f"""# UAT Test Cases: {story_title}

**Story Key:** {story_key}
**Generated:** {datetime.now().strftime("%Y-%m-%d")}

## Test Case 1: Basic Functionality

### Preconditions
- [ ] Environment setup complete
- [ ] Test data prepared

### Test Steps
1. TODO: Add step 1
2. TODO: Add step 2
3. TODO: Add step 3

### Expected Results
- TODO: Define expected outcome

### Actual Results
- [ ] Pass
- [ ] Fail

### Notes
_Space for tester notes_

---

## Test Case 2: Edge Cases

### Preconditions
- [ ] TODO: Define preconditions

### Test Steps
1. TODO: Add edge case test steps

### Expected Results
- TODO: Define expected behavior for edge cases

### Actual Results
- [ ] Pass
- [ ] Fail

### Notes
_Space for tester notes_

---

## Test Case 3: Error Handling

### Preconditions
- [ ] TODO: Define error scenario setup

### Test Steps
1. TODO: Add error handling test steps

### Expected Results
- TODO: Define expected error handling

### Actual Results
- [ ] Pass
- [ ] Fail

### Notes
_Space for tester notes_

---

## Approval

- **Tester:** _________________
- **Date:** _________________
- **Status:** [ ] Approved [ ] Rejected
- **Comments:** _________________
"""

        uat_file_path.write_text(uat_content, encoding="utf-8")
        logger.info("generated_uat_test_case", path=str(uat_file_path))
        return uat_file_path


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate story template for Data Extraction Tool")

    parser.add_argument("--story-number", required=True, help="Story number (e.g., 4.1)")

    parser.add_argument("--epic", required=True, help="Epic number (e.g., 4)")

    parser.add_argument("--title", required=True, help="Story title")

    parser.add_argument(
        "--owner", default=DEFAULT_OWNER, help=f"Story owner (default: {DEFAULT_OWNER})"
    )

    parser.add_argument(
        "--estimate",
        type=int,
        default=DEFAULT_ESTIMATE,
        help=f"Estimated hours (default: {DEFAULT_ESTIMATE})",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help=f"Output directory (default: {OUTPUT_DIR})",
    )

    parser.add_argument("--dry-run", action="store_true", help="Preview without writing file")

    # Enhanced feature flags
    parser.add_argument(
        "--with-tests", action="store_true", help="Generate test file template with AC-based stubs"
    )

    parser.add_argument(
        "--with-fixtures", action="store_true", help="Generate fixture file with sample data"
    )

    parser.add_argument("--with-uat", action="store_true", help="Generate UAT test case file")

    parser.add_argument(
        "--update-status",
        action="store_true",
        help="Update sprint-status.yaml with new story entry",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    try:
        args = parse_arguments()

        # Ensure templates directory exists
        if not TEMPLATE_DIR.exists():
            TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
            # Create default template if it doesn't exist
            default_template = TEMPLATE_DIR / "story.md.j2"
            if not default_template.exists():
                create_default_template(default_template)

        generator = StoryTemplateGenerator()

        output_path = generator.generate_story(
            story_number=args.story_number,
            epic=args.epic,
            title=args.title,
            owner=args.owner,
            estimate=args.estimate,
            output_dir=args.output_dir,
            dry_run=args.dry_run,
            with_tests=args.with_tests,
            with_fixtures=args.with_fixtures,
            with_uat=args.with_uat,
            update_status=args.update_status,
        )

        if not args.dry_run:
            print(f"✅ Generated story template: {output_path}")

        return 0

    except Exception as e:
        logger.error("generation_failed", error=str(e))
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


def create_default_template(path: Path):
    """Create a default story template if none exists."""
    template_content = """# Story {{ story_number }}: {{ title }}

Status: backlog

## Story

As a [role],
I want [feature/capability],
So that [benefit/value].

### Story Header

- **Story Key:** `{{ story_key }}` (Epic {{ epic }}, Story ID {{ story_number }})
- **Dependencies:** None
- **Estimate:** {{ estimate }} hours
- **Owner:** {{ owner }}

### Story Body

[Implementation details]

## Acceptance Criteria

{% for ac in acceptance_criteria %}
{{ ac.id }}. **{{ ac.description }}**
   - Evidence: {{ ac.evidence }}
{% endfor %}

## Tasks / Subtasks

{% for item in wiring_checklist.bom %}
- [ ] BOM: {{ item }}
{% endfor %}
{% for item in wiring_checklist.logging %}
- [ ] Logging: {{ item }}
{% endfor %}
{% for item in wiring_checklist.cli %}
- [ ] CLI: {{ item }}
{% endfor %}
{% for item in wiring_checklist.testing %}
- [ ] Testing: {{ item }}
{% endfor %}

## Dev Notes

### Submission Summary

**Files Created:**
{% for file in submission_summary.files_created %}
- {{ file }}
{% endfor %}

**Files Modified:**
{% for file in submission_summary.files_modified %}
- {{ file }}
{% endfor %}

**Tests Added:**
{% for test in submission_summary.tests_added %}
- {{ test }}
{% endfor %}

**Coverage:** {{ submission_summary.coverage }}

### Completion Notes

- **{{ date }}:** Story created with template generator
"""
    path.write_text(template_content, encoding="utf-8")
    logger.info("created_default_template", path=str(path))


if __name__ == "__main__":
    sys.exit(main())
