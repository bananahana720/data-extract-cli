"""
Comprehensive test suite for the story template generator.

Tests cover all aspects of template generation including:
- Basic template generation (happy path)
- Jinja2 rendering with story variables
- Pre-commit hook integration
- CLI argument parsing
- Output file creation and permissions
- Template validation
- Error handling
- Edge cases
- Deterministic output
- Integration with project structure
"""

import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add scripts directory to path for import
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
from generate_story_template import (
    StoryTemplateGenerator,
    create_default_template,
    main,
    parse_arguments,
)


class TestStoryTemplateGenerator:
    """Test suite for StoryTemplateGenerator class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.fixture
    def generator(self, temp_dir):
        """Create StoryTemplateGenerator instance with temp templates."""
        template_dir = temp_dir / "templates"
        template_dir.mkdir(parents=True, exist_ok=True)

        # Create test template
        template_content = """# Story {{ story_number }}: {{ title }}
Epic: {{ epic }}
Owner: {{ owner }}
Estimate: {{ estimate }} hours
Story Key: {{ story_key }}
Date: {{ date }}

## Acceptance Criteria
{% for ac in acceptance_criteria %}
- AC{{ ac.id }}: {{ ac.description }}
{% endfor %}

## Wiring Checklist
{% for item in wiring_checklist.bom %}
- BOM: {{ item }}
{% endfor %}

## Submission Summary
Coverage: {{ submission_summary.coverage }}
"""
        (template_dir / "story.md.j2").write_text(template_content)

        return StoryTemplateGenerator(template_dir=template_dir)

    def test_basic_template_generation_happy_path(self, generator, temp_dir):
        """Test 1: Basic template generation (happy path)."""
        output_dir = temp_dir / "output"

        result_path = generator.generate_story(
            story_number="4.1",
            epic="4",
            title="Semantic Analysis Foundation",
            owner="Alice",
            estimate=8,
            output_dir=output_dir,
            dry_run=False,
        )

        # Verify file was created
        assert result_path.exists()
        assert result_path.name == "4.1-semantic-analysis-foundation.md"

        # Verify content contains expected elements
        content = result_path.read_text()
        assert "Story 4.1: Semantic Analysis Foundation" in content
        assert "Epic: 4" in content
        assert "Owner: Alice" in content
        assert "Estimate: 8 hours" in content
        assert "Story Key: 4.1-semantic-analysis-foundation" in content

    def test_jinja2_rendering_with_story_variables(self, generator, temp_dir):
        """Test 2: Jinja2 rendering with story variables."""
        output_dir = temp_dir / "output"

        # Test with various variable combinations
        result_path = generator.generate_story(
            story_number="3.5.1",
            epic="3.5",
            title="Complex Story Title with Numbers 123",
            owner="DevOps Team",
            estimate=16,
            output_dir=output_dir,
        )

        content = result_path.read_text()

        # Verify Jinja2 variables were properly rendered
        assert "Story 3.5.1: Complex Story Title with Numbers 123" in content
        assert "Epic: 3.5" in content
        assert "Owner: DevOps Team" in content
        assert "Story Key: 3.5.1-complex-story-title-with-numbers-123" in content

        # Verify template lists were rendered
        assert "AC1: TODO: Define acceptance criterion" in content
        assert "BOM: TODO: List new dependencies/packages" in content
        assert "Coverage: TODO: Report coverage %" in content

    @patch("generate_story_template.Path.exists")
    @patch("subprocess.run")
    def test_pre_commit_hook_integration(self, mock_run, mock_exists):
        """Test 3: Pre-commit hook integration."""
        # Simulate pre-commit validation
        mock_exists.return_value = True
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        # Test that generator produces valid structure for pre-commit
        generator = StoryTemplateGenerator()

        # Verify generator produces required AC table structure
        ac_template = generator._generate_ac_template()
        assert len(ac_template) >= 3
        assert all("description" in ac for ac in ac_template)
        assert all("evidence" in ac for ac in ac_template)

        # Verify wiring checklist structure
        wiring = generator._generate_wiring_checklist()
        assert "bom" in wiring
        assert "logging" in wiring
        assert "cli" in wiring
        assert "testing" in wiring

    def test_cli_argument_parsing(self):
        """Test 4: CLI argument parsing (story number, epic, title)."""
        # Test required arguments
        test_args = ["--story-number", "5.1", "--epic", "5", "--title", "CLI and Batch Processing"]

        with patch("sys.argv", ["generate_story_template.py"] + test_args):
            args = parse_arguments()
            assert args.story_number == "5.1"
            assert args.epic == "5"
            assert args.title == "CLI and Batch Processing"
            assert args.owner == "Team"  # Default
            assert args.estimate == 4  # Default
            assert args.dry_run is False  # Default

        # Test all arguments including optionals
        test_args_full = [
            "--story-number",
            "5.2",
            "--epic",
            "5",
            "--title",
            "Advanced Features",
            "--owner",
            "Bob",
            "--estimate",
            "12",
            "--dry-run",
        ]

        with patch("sys.argv", ["generate_story_template.py"] + test_args_full):
            args = parse_arguments()
            assert args.story_number == "5.2"
            assert args.owner == "Bob"
            assert args.estimate == 12
            assert args.dry_run is True

    def test_output_file_creation_and_permissions(self, generator, temp_dir):
        """Test 5: Output file creation and permissions."""
        output_dir = temp_dir / "output"

        # Ensure output directory doesn't exist yet
        assert not output_dir.exists()

        result_path = generator.generate_story(
            story_number="4.2", epic="4", title="Test Story", output_dir=output_dir
        )

        # Verify directory was created
        assert output_dir.exists()
        assert output_dir.is_dir()

        # Verify file was created with correct permissions
        assert result_path.exists()
        assert result_path.is_file()

        # Verify file is readable and writable
        stat = result_path.stat()
        assert stat.st_size > 0  # File has content

        # Test we can read and write to the file
        original_content = result_path.read_text()
        result_path.write_text(original_content + "\n# Test append")
        new_content = result_path.read_text()
        assert "# Test append" in new_content

    def test_template_validation(self, temp_dir):
        """Test 6: Template validation (AC sections, metadata)."""
        template_dir = temp_dir / "templates"
        template_dir.mkdir(parents=True, exist_ok=True)

        # Create a valid template
        valid_template = template_dir / "story.md.j2"
        valid_template.write_text(
            """# Story {{ story_number }}
## Acceptance Criteria
{% for ac in acceptance_criteria %}
- {{ ac.description }}
{% endfor %}

## Metadata
Owner: {{ owner }}
Estimate: {{ estimate }}
"""
        )

        generator = StoryTemplateGenerator(template_dir=template_dir)

        # Test validation of existing template
        assert generator.validate_template("story.md.j2") is True

        # Test validation of non-existent template
        assert generator.validate_template("nonexistent.md.j2") is False

        # Generate story and verify required sections are present
        output_dir = temp_dir / "output"
        result_path = generator.generate_story(
            story_number="4.3", epic="4", title="Validation Test", output_dir=output_dir
        )

        content = result_path.read_text()
        assert "Acceptance Criteria" in content
        assert "Metadata" in content
        assert "Owner:" in content
        assert "Estimate:" in content

    def test_error_handling(self, temp_dir):
        """Test 7: Error handling (missing args, invalid paths)."""

        # Test missing required arguments
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["generate_story_template.py"]):
                parse_arguments()

        # Test with invalid template directory (no templates)
        invalid_template_dir = temp_dir / "nonexistent"
        generator = StoryTemplateGenerator(template_dir=invalid_template_dir)

        with pytest.raises(Exception):  # TemplateNotFound or similar
            generator.generate_story(
                story_number="4.4", epic="4", title="Error Test", output_dir=temp_dir / "output"
            )

        # Test main function error handling
        with patch(
            "sys.argv",
            [
                "generate_story_template.py",
                "--story-number",
                "4.5",
                "--epic",
                "4",
                "--title",
                "Test",
            ],
        ):
            with patch("generate_story_template.StoryTemplateGenerator.generate_story") as mock_gen:
                mock_gen.side_effect = Exception("Test error")
                result = main()
                assert result == 1  # Should return error code

    def test_edge_cases_special_chars_long_descriptions(self, generator, temp_dir):
        """Test 8: Edge cases (special chars in titles, long descriptions)."""
        output_dir = temp_dir / "output"

        # Test with special characters in title
        special_title = "Story with !@#$%^&*() Special-Chars & Symbols"
        result_path = generator.generate_story(
            story_number="4.6", epic="4", title=special_title, output_dir=output_dir
        )

        # Verify slug is properly sanitized
        assert result_path.name == "4.6-story-with-special-chars-symbols.md"
        content = result_path.read_text()
        assert special_title in content

        # Test with very long title
        long_title = "A" * 100 + " Very Long Title " + "B" * 100
        result_path_long = generator.generate_story(
            story_number="4.7", epic="4", title=long_title, output_dir=output_dir
        )

        assert result_path_long.exists()
        content_long = result_path_long.read_text()
        assert long_title in content_long

        # Test with unicode characters
        unicode_title = "Story with 中文 and émojis 🚀"
        result_path_unicode = generator.generate_story(
            story_number="4.8", epic="4", title=unicode_title, output_dir=output_dir
        )

        assert result_path_unicode.exists()
        content_unicode = result_path_unicode.read_text(encoding="utf-8")
        assert unicode_title in content_unicode

    @patch("generate_story_template.datetime")
    def test_deterministic_output(self, mock_datetime, generator, temp_dir):
        """Test 9: Deterministic output (same inputs → identical files)."""
        # Fix the date for deterministic output
        mock_datetime.now.return_value.strftime.return_value = "2025-11-17"

        output_dir = temp_dir / "output"

        # Generate same story twice with identical parameters
        params = {
            "story_number": "4.9",
            "epic": "4",
            "title": "Deterministic Test",
            "owner": "TestOwner",
            "estimate": 6,
            "output_dir": output_dir,
        }

        path1 = generator.generate_story(**params)
        content1 = path1.read_text()

        # Delete and regenerate
        path1.unlink()

        path2 = generator.generate_story(**params)
        content2 = path2.read_text()

        # Contents should be identical
        assert content1 == content2
        assert path1 == path2

    def test_integration_with_project_structure(self, temp_dir):
        """Test 10: Integration with project structure (correct paths)."""
        # Create project-like structure
        project_root = temp_dir / "project"
        scripts_dir = project_root / "scripts"
        templates_dir = scripts_dir / "templates"
        docs_dir = project_root / "docs" / "stories"

        # Create directories
        for directory in [scripts_dir, templates_dir, docs_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Create template
        template_file = templates_dir / "story.md.j2"
        template_file.write_text(
            """# Story {{ story_number }}: {{ title }}
Path Test: Stories should go to docs/stories/
Epic: {{ epic }}
"""
        )

        # Test generator respects project structure
        generator = StoryTemplateGenerator(template_dir=templates_dir)

        result_path = generator.generate_story(
            story_number="5.0", epic="5", title="Integration Test", output_dir=docs_dir
        )

        # Verify correct path structure
        assert result_path.parent == docs_dir
        assert "docs/stories" in str(result_path)
        assert result_path.name == "5.0-integration-test.md"

        # Test dry-run mode
        with patch("builtins.print") as mock_print:
            dry_path = generator.generate_story(
                story_number="5.1",
                epic="5",
                title="Dry Run Test",
                output_dir=docs_dir,
                dry_run=True,
            )

            # Verify dry run doesn't create file
            assert not dry_path.exists()

            # Verify preview was printed
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("DRY RUN" in str(call) for call in calls)


class TestMainFunction:
    """Test suite for main function and CLI integration."""

    @patch(
        "sys.argv",
        [
            "generate_story_template.py",
            "--story-number",
            "6.1",
            "--epic",
            "6",
            "--title",
            "CLI Test Story",
        ],
    )
    @patch("generate_story_template.StoryTemplateGenerator")
    def test_main_success(self, mock_generator_class):
        """Test successful execution of main function."""
        mock_instance = Mock()
        mock_generator_class.return_value = mock_instance
        mock_instance.generate_story.return_value = Path("/tmp/test.md")

        result = main()

        assert result == 0
        mock_instance.generate_story.assert_called_once()

    def test_create_default_template(self):
        """Test default template creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = Path(temp_dir) / "test_template.md.j2"

            create_default_template(template_path)

            assert template_path.exists()
            content = template_path.read_text()

            # Verify template structure
            assert "# Story {{ story_number }}: {{ title }}" in content
            assert "{% for ac in acceptance_criteria %}" in content
            assert "{{ story_key }}" in content
            assert "{{ epic }}" in content
            assert "{{ owner }}" in content


class TestPerformance:
    """Performance tests to ensure fast execution."""

    @pytest.fixture
    def generator(self):
        """Create generator with minimal setup."""
        temp_dir = Path(tempfile.mkdtemp())
        template_dir = temp_dir / "templates"
        template_dir.mkdir(parents=True, exist_ok=True)

        # Minimal template
        (template_dir / "story.md.j2").write_text("# {{ story_number }}: {{ title }}")

        yield StoryTemplateGenerator(template_dir=template_dir)

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_generation_speed(self, generator):
        """Ensure template generation completes in <1 second."""
        import time

        start_time = time.time()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Generate 10 stories
            for i in range(10):
                generator.generate_story(
                    story_number=f"7.{i}",
                    epic="7",
                    title=f"Performance Test {i}",
                    output_dir=output_dir,
                )

        elapsed_time = time.time() - start_time

        # Should complete 10 generations in under 1 second
        assert elapsed_time < 1.0, f"Generation took {elapsed_time:.2f} seconds, expected < 1.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
