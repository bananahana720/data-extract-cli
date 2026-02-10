"""
Unit tests for the fixture data generator script.

Tests cover:
- Document generation (PDF, DOCX, XLSX)
- Semantic corpus generation
- PII-free data validation
- Edge case generation
- Deterministic output
- Configuration support
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from scripts.generate_fixtures import FixtureGenerator, parse_arguments


class TestFixtureGenerator:
    """Test suite for FixtureGenerator class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def generator(self, temp_dir):
        """Create a FixtureGenerator instance."""
        return FixtureGenerator(output_dir=temp_dir, seed=42)

    def test_initialization(self, temp_dir):
        """Test generator initialization."""
        generator = FixtureGenerator(output_dir=temp_dir, seed=123)

        assert generator.output_dir == temp_dir
        assert generator.seed == 123
        assert generator.config == {}

        # Check directories were created
        assert (temp_dir / "documents").exists()
        assert (temp_dir / "semantic").exists()
        assert (temp_dir / "edge_cases").exists()

    def test_load_config_yaml(self, temp_dir):
        """Test loading YAML configuration."""
        config_file = temp_dir / "config.yaml"
        config_data = {
            "documents": {"default_pages": 3},
            "corpus": {"topics": ["tech", "finance"]},
        }
        config_file.write_text(yaml.dump(config_data))

        generator = FixtureGenerator(output_dir=temp_dir, config_file=config_file)
        assert generator.config == config_data

    def test_load_config_json(self, temp_dir):
        """Test loading JSON configuration."""
        config_file = temp_dir / "config.json"
        config_data = {
            "documents": {"default_rows": 100},
            "edge_cases": {"include_unicode": True},
        }
        config_file.write_text(json.dumps(config_data))

        generator = FixtureGenerator(output_dir=temp_dir, config_file=config_file)
        assert generator.config == config_data

    @patch("scripts.generate_fixtures.REPORTLAB_AVAILABLE", True)
    @patch("scripts.generate_fixtures.canvas")
    def test_generate_pdf(self, mock_canvas, generator):
        """Test PDF generation (AC-7)."""
        # Setup mock
        mock_canvas_instance = MagicMock()
        mock_canvas.Canvas.return_value = mock_canvas_instance

        # Generate PDF
        result = generator.generate_pdf(
            filename="test.pdf",
            pages=2,
            content_type="financial",
        )

        # Verify
        assert result.name == "test.pdf"
        mock_canvas.Canvas.assert_called_once()
        mock_canvas_instance.save.assert_called_once()

        # Check that multiple pages were created
        assert mock_canvas_instance.showPage.call_count == 1  # Called between pages

    @patch("scripts.generate_fixtures.REPORTLAB_AVAILABLE", False)
    def test_generate_pdf_no_reportlab(self, generator):
        """Test PDF generation when reportlab is not available."""
        with pytest.raises(ImportError, match="reportlab is required"):
            generator.generate_pdf()

    @patch("scripts.generate_fixtures.DOCX_AVAILABLE", True)
    @patch("scripts.generate_fixtures.Document")
    def test_generate_docx(self, mock_document, generator):
        """Test DOCX generation (AC-7)."""
        # Setup mock
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc

        # Generate DOCX
        result = generator.generate_docx(
            filename="test.docx",
            paragraphs=5,
            content_type="technical",
            with_tables=True,
        )

        # Verify
        assert result.name == "test.docx"
        mock_document.assert_called_once()
        mock_doc.save.assert_called_once()
        assert mock_doc.add_paragraph.call_count >= 5
        mock_doc.add_table.assert_called_once_with(rows=5, cols=4)

    @patch("scripts.generate_fixtures.DOCX_AVAILABLE", False)
    def test_generate_docx_no_python_docx(self, generator):
        """Test DOCX generation when python-docx is not available."""
        with pytest.raises(ImportError, match="python-docx is required"):
            generator.generate_docx()

    @patch("scripts.generate_fixtures.OPENPYXL_AVAILABLE", True)
    @patch("scripts.generate_fixtures.Workbook")
    def test_generate_xlsx(self, mock_workbook, generator):
        """Test XLSX generation (AC-7)."""
        # Setup mock
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws
        mock_wb.create_sheet.return_value = MagicMock()
        mock_workbook.return_value = mock_wb

        # Generate XLSX
        result = generator.generate_xlsx(
            filename="test.xlsx",
            sheets=2,
            rows=50,
            content_type="inventory",
        )

        # Verify
        assert result.name == "test.xlsx"
        mock_workbook.assert_called_once()
        mock_wb.save.assert_called_once()
        mock_wb.create_sheet.assert_called_once()  # For second sheet
        # Check headers were written
        assert mock_ws.cell.called

    @patch("scripts.generate_fixtures.OPENPYXL_AVAILABLE", False)
    def test_generate_xlsx_no_openpyxl(self, generator):
        """Test XLSX generation when openpyxl is not available."""
        with pytest.raises(ImportError, match="openpyxl is required"):
            generator.generate_xlsx()

    def test_generate_semantic_corpus(self, generator):
        """Test semantic corpus generation (AC-8)."""
        files = generator.generate_semantic_corpus(
            count=5,
            topics=["technology", "finance"],
            min_words=50,
            max_words=100,
        )

        assert len(files) == 5

        # Check files were created with correct patterns
        for i, file_path in enumerate(files):
            assert file_path.exists()
            assert file_path.parent.name == "corpus"

            content = file_path.read_text()
            word_count = len(content.split())

            # Check word count is in range
            assert 40 <= word_count <= 120  # Allow some variance

            # Check filename pattern
            topic = "technology" if i % 2 == 0 else "finance"
            assert file_path.name.startswith(f"{topic}_{i:03d}_")

    def test_semantic_document_content(self, generator):
        """Test semantic document has appropriate vocabulary."""
        content = generator._generate_semantic_document("technology", 100)

        # Check that technology-related words appear
        tech_words = ["software", "algorithm", "data", "system", "cloud"]
        content_lower = content.lower()
        found_tech_words = any(word in content_lower for word in tech_words)
        assert found_tech_words

    def test_generate_edge_cases(self, generator):
        """Test edge case generation (AC-10)."""
        edge_cases = generator.generate_edge_cases()

        # Check all expected edge cases
        expected_cases = [
            "empty",
            "single_char",
            "large",
            "special_chars",
            "unicode",
            "long_line",
            "many_lines",
            "mixed_encoding",
            "whitespace",
            "null_bytes",
        ]

        for case in expected_cases:
            assert case in edge_cases
            assert edge_cases[case].exists()

        # Verify specific edge cases
        assert edge_cases["empty"].stat().st_size == 0
        assert edge_cases["single_char"].read_text() == "X"
        assert edge_cases["large"].stat().st_size == 1024 * 1024
        assert "€" in edge_cases["special_chars"].read_text()
        assert "世界" in edge_cases["unicode"].read_text()

    def test_pii_free_validation(self, generator):
        """Test PII-free data validation (AC-9)."""
        # Generate some fixtures
        generator.generate_docx(filename="test.docx")
        generator.generate_semantic_corpus(count=2)

        # Create a file with fake PII
        bad_file = generator.output_dir / "bad.txt"
        bad_file.write_text("SSN: 123-45-6789")

        # Validate
        results = generator.validate_fixtures()

        # Good files should pass
        good_file = generator.output_dir / "documents" / "test.docx"
        assert results.get(str(good_file), False) is True

        # Bad file should fail
        assert results[str(bad_file)] is False

    def test_deterministic_output(self, temp_dir):
        """Test deterministic output with same seed (AC-11)."""
        # Generate with seed 42
        gen1 = FixtureGenerator(output_dir=temp_dir / "gen1", seed=42)
        files1 = gen1.generate_semantic_corpus(count=3)

        # Generate again with same seed
        gen2 = FixtureGenerator(output_dir=temp_dir / "gen2", seed=42)
        files2 = gen2.generate_semantic_corpus(count=3)

        # Content should be identical
        for f1, f2 in zip(files1, files2):
            content1 = f1.read_text()
            content2 = f2.read_text()
            assert content1 == content2

            # Filenames should also be identical (hash-based)
            assert f1.name == f2.name

    def test_different_seeds_produce_different_output(self, temp_dir):
        """Test that different seeds produce different output."""
        gen1 = FixtureGenerator(output_dir=temp_dir / "gen1", seed=42)
        files1 = gen1.generate_semantic_corpus(count=1)

        gen2 = FixtureGenerator(output_dir=temp_dir / "gen2", seed=123)
        files2 = gen2.generate_semantic_corpus(count=1)

        # Content should be different
        content1 = files1[0].read_text()
        content2 = files2[0].read_text()
        assert content1 != content2

    def test_financial_content_generation(self, generator):
        """Test financial content has appropriate patterns."""
        content = generator._generate_financial_content()

        assert len(content) == 20
        # Check for financial keywords
        financial_terms = ["revenue", "margin", "assets", "income", "earnings", "dividend"]
        content_str = " ".join(content).lower()
        found_terms = sum(1 for term in financial_terms if term in content_str)
        assert found_terms >= 3

    def test_technical_content_generation(self, generator):
        """Test technical content has appropriate patterns."""
        content = generator._generate_technical_content()

        assert len(content) == 20
        # Check for technical keywords
        tech_terms = ["api", "latency", "database", "memory", "cpu", "throughput"]
        content_str = " ".join(content).lower()
        found_terms = sum(1 for term in tech_terms if term in content_str)
        assert found_terms >= 3

    def test_standard_row_generation(self, generator):
        """Test standard data row generation."""
        row = generator._generate_standard_row()

        assert len(row) == 6
        # Check email format
        assert "@example.com" in row[3]
        # Check phone format
        assert row[4].startswith("+1-555-")
        # Check date format (YYYY-MM-DD)
        assert len(row[5]) == 10 and row[5][4] == "-" and row[5][7] == "-"

    def test_configuration_support(self, temp_dir):
        """Test configuration file support (AC-13)."""
        config = {
            "seed": 100,
            "documents": {
                "default_pages": 5,
                "default_paragraphs": 10,
            },
            "corpus": {
                "default_topics": ["science", "art"],
                "min_words": 200,
                "max_words": 1000,
            },
        }

        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))

        generator = FixtureGenerator(
            output_dir=temp_dir,
            seed=42,
            config_file=config_file,
        )

        assert generator.config == config


class TestCLIArguments:
    """Test command-line argument parsing."""

    def test_parse_arguments_defaults(self):
        """Test default argument values."""
        with patch("sys.argv", ["generate_fixtures.py"]):
            args = parse_arguments()
            assert args.seed == 42
            assert args.count == 1
            assert args.content_type == "standard"
            assert args.corpus_count == 10
            assert args.semantic_corpus is False
            assert args.edge_cases is False
            assert args.validate is False
            assert args.dry_run is False
            assert args.verbose is False

    def test_parse_arguments_document_types(self):
        """Test document type arguments."""
        with patch(
            "sys.argv",
            [
                "generate_fixtures.py",
                "--types",
                "pdf",
                "docx",
                "xlsx",
                "--count",
                "5",
                "--content-type",
                "financial",
            ],
        ):
            args = parse_arguments()
            assert args.types == ["pdf", "docx", "xlsx"]
            assert args.count == 5
            assert args.content_type == "financial"

    def test_parse_arguments_semantic_corpus(self):
        """Test semantic corpus arguments."""
        with patch(
            "sys.argv",
            [
                "generate_fixtures.py",
                "--semantic-corpus",
                "--corpus-count",
                "20",
                "--topics",
                "tech",
                "health",
                "edu",
            ],
        ):
            args = parse_arguments()
            assert args.semantic_corpus is True
            assert args.corpus_count == 20
            assert args.topics == ["tech", "health", "edu"]

    def test_parse_arguments_all_options(self):
        """Test parsing all arguments."""
        with patch(
            "sys.argv",
            [
                "generate_fixtures.py",
                "--output-dir",
                "/custom/fixtures",
                "--config",
                "/custom/config.yaml",
                "--seed",
                "100",
                "--types",
                "all",
                "--edge-cases",
                "--validate",
                "--dry-run",
                "--verbose",
            ],
        ):
            args = parse_arguments()
            assert args.output_dir == Path("/custom/fixtures")
            assert args.config == Path("/custom/config.yaml")
            assert args.seed == 100
            assert args.types == ["all"]
            assert args.edge_cases is True
            assert args.validate is True
            assert args.dry_run is True
            assert args.verbose is True


class TestMainFunction:
    """Test the main entry point."""

    @patch("scripts.generate_fixtures.FixtureGenerator")
    def test_main_dry_run(self, mock_generator_class):
        """Test main function in dry-run mode."""
        with patch(
            "sys.argv",
            [
                "generate_fixtures.py",
                "--dry-run",
                "--types",
                "pdf",
                "--semantic-corpus",
            ],
        ):
            from scripts.generate_fixtures import main

            result = main()

            assert result == 0
            # Generator should not be instantiated in dry-run
            mock_generator_class.assert_not_called()

    @patch("scripts.generate_fixtures.FixtureGenerator")
    def test_main_document_generation(self, mock_generator_class):
        """Test main function with document generation."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_pdf.return_value = Path("test.pdf")
        mock_generator.generate_docx.return_value = Path("test.docx")
        mock_generator.generate_xlsx.return_value = Path("test.xlsx")

        with patch(
            "sys.argv",
            [
                "generate_fixtures.py",
                "--types",
                "pdf",
                "docx",
                "xlsx",
                "--count",
                "2",
            ],
        ):
            from scripts.generate_fixtures import main

            result = main()

            assert result == 0
            assert mock_generator.generate_pdf.call_count == 2
            assert mock_generator.generate_docx.call_count == 2
            assert mock_generator.generate_xlsx.call_count == 2

    @patch("scripts.generate_fixtures.FixtureGenerator")
    def test_main_semantic_corpus(self, mock_generator_class):
        """Test main function with semantic corpus generation."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_semantic_corpus.return_value = [Path("doc1.txt"), Path("doc2.txt")]

        with patch(
            "sys.argv",
            [
                "generate_fixtures.py",
                "--semantic-corpus",
                "--corpus-count",
                "2",
            ],
        ):
            from scripts.generate_fixtures import main

            result = main()

            assert result == 0
            mock_generator.generate_semantic_corpus.assert_called_once_with(
                count=2,
                topics=None,
            )

    @patch("scripts.generate_fixtures.FixtureGenerator")
    def test_main_edge_cases(self, mock_generator_class):
        """Test main function with edge case generation."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_edge_cases.return_value = {
            "empty": Path("empty.txt"),
            "large": Path("large.txt"),
        }

        with patch("sys.argv", ["generate_fixtures.py", "--edge-cases"]):
            from scripts.generate_fixtures import main

            result = main()

            assert result == 0
            mock_generator.generate_edge_cases.assert_called_once()

    @patch("scripts.generate_fixtures.FixtureGenerator")
    def test_main_validation(self, mock_generator_class):
        """Test main function with validation."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.validate_fixtures.return_value = {
            "file1.txt": True,
            "file2.txt": False,
        }

        with patch("sys.argv", ["generate_fixtures.py", "--validate"]):
            from scripts.generate_fixtures import main

            result = main()

            assert result == 0
            mock_generator.validate_fixtures.assert_called_once()

    @patch("scripts.generate_fixtures.FixtureGenerator")
    def test_main_error_handling(self, mock_generator_class):
        """Test main function error handling."""
        mock_generator_class.side_effect = Exception("Test error")

        with patch("sys.argv", ["generate_fixtures.py", "--types", "pdf"]):
            from scripts.generate_fixtures import main

            result = main()

            assert result == 1
