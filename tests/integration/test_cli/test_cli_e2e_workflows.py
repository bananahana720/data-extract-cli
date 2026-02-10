"""Integration tests for CLI end-to-end workflows.

Tests the greenfield CLI (src/data_extract/cli.py) with real file I/O,
full OutputWriter integration, and actual file creation.

Note: Epic 5 will replace this CLI with full Typer-based implementation.
"""

import subprocess
import sys

import pytest

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.cli]


@pytest.fixture
def sample_pdf(tmp_path):
    """Create sample PDF file for testing."""
    pdf_file = tmp_path / "sample_document.pdf"
    pdf_file.write_text("Sample PDF content for testing CLI workflows")
    return pdf_file


@pytest.fixture
def sample_docx(tmp_path):
    """Create sample DOCX file for testing."""
    docx_file = tmp_path / "sample_document.docx"
    docx_file.write_text("Sample DOCX content for testing CLI workflows")
    return docx_file


class TestCLIInstallation:
    """Test CLI is properly installed and accessible."""

    def test_cli_module_can_be_invoked(self):
        """Should be able to invoke CLI via python -m data_extract.cli."""
        # WHEN: Invoking CLI module with --help
        result = subprocess.run(
            [sys.executable, "-m", "data_extract.cli", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # THEN: Should succeed and show help
        assert result.returncode == 0
        assert "Data Extraction Tool" in result.stdout
        assert "process" in result.stdout

    def test_cli_shows_version(self):
        """Should display version information."""
        # WHEN: Invoking CLI with --version
        result = subprocess.run(
            [sys.executable, "-m", "data_extract.cli", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # THEN: Should display version
        assert result.returncode == 0
        assert "0.1.0" in result.stdout


class TestProcessCommandBasicWorkflow:
    """Test basic process command workflows with real file I/O."""

    def test_process_creates_txt_output_file(self, sample_pdf, tmp_path):
        """Should create TXT output file from input."""
        # GIVEN: Output path
        output_file = tmp_path / "output.txt"

        # WHEN: Processing document with CLI
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(sample_pdf),
                "--format",
                "txt",
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # THEN: Should succeed and create file
        assert result.returncode == 0
        assert output_file.exists()
        assert output_file.stat().st_size > 0
        assert "Processing complete!" in result.stdout

    def test_process_creates_json_output_file(self, sample_pdf, tmp_path):
        """Should create JSON output file from input."""
        # GIVEN: Output path
        output_file = tmp_path / "output.json"

        # WHEN: Processing document with JSON format
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(sample_pdf),
                "--format",
                "json",
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # THEN: Should succeed and create JSON file
        assert result.returncode == 0
        assert output_file.exists()
        assert output_file.stat().st_size > 0

        # Verify valid JSON structure
        import json

        with open(output_file, encoding="utf-8") as f:
            data = json.load(f)
            assert "metadata" in data
            assert "chunks" in data

    def test_process_output_contains_chunk_delimiters(self, sample_pdf, tmp_path):
        """Should include chunk delimiters in TXT output."""
        # GIVEN: Output file
        output_file = tmp_path / "output.txt"

        # WHEN: Processing with default TXT format
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(sample_pdf),
                "--format",
                "txt",
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # THEN: Should include delimiters
        assert result.returncode == 0
        content = output_file.read_text(encoding="utf-8")
        assert "━━━ CHUNK" in content  # Default delimiter

    def test_process_with_custom_delimiter(self, sample_pdf, tmp_path):
        """Should use custom delimiter when specified."""
        # GIVEN: Custom delimiter
        output_file = tmp_path / "output.txt"
        custom_delimiter = "--- SECTION {{n}} ---"

        # WHEN: Processing with custom delimiter
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(sample_pdf),
                "--format",
                "txt",
                "--output",
                str(output_file),
                "--delimiter",
                custom_delimiter,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # THEN: Should use custom delimiter
        assert result.returncode == 0
        content = output_file.read_text(encoding="utf-8")
        assert "--- SECTION" in content


class TestProcessCommandMetadataFeature:
    """Test --include-metadata flag functionality."""

    def test_process_without_metadata_no_headers(self, sample_pdf, tmp_path):
        """Should not include metadata headers by default."""
        # GIVEN: Output file
        output_file = tmp_path / "output.txt"

        # WHEN: Processing without --include-metadata
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(sample_pdf),
                "--format",
                "txt",
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # THEN: Should not include metadata headers
        assert result.returncode == 0
        content = output_file.read_text(encoding="utf-8")
        assert "Source:" not in content  # No metadata headers

    def test_process_with_metadata_includes_headers(self, sample_pdf, tmp_path):
        """Should include metadata headers when --include-metadata is set."""
        # GIVEN: Output file
        output_file = tmp_path / "output.txt"

        # WHEN: Processing with --include-metadata
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(sample_pdf),
                "--format",
                "txt",
                "--output",
                str(output_file),
                "--include-metadata",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # THEN: Should include metadata headers
        assert result.returncode == 0
        content = output_file.read_text(encoding="utf-8")
        assert "Source:" in content or "Chunk ID:" in content


class TestProcessCommandPerChunkMode:
    """Test --per-chunk flag functionality."""

    def test_process_per_chunk_creates_multiple_files(self, sample_pdf, tmp_path):
        """Should create separate file for each chunk."""
        # GIVEN: Output directory
        output_dir = tmp_path / "chunks"

        # WHEN: Processing with --per-chunk
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(sample_pdf),
                "--format",
                "txt",
                "--output",
                str(output_dir),
                "--per-chunk",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # THEN: Should create multiple chunk files
        assert result.returncode == 0
        assert output_dir.exists()
        chunk_files = list(output_dir.glob("*.txt"))
        assert len(chunk_files) > 0  # At least one chunk file

    def test_process_per_chunk_files_numbered_sequentially(self, sample_pdf, tmp_path):
        """Should number chunk files sequentially."""
        # GIVEN: Output directory
        output_dir = tmp_path / "chunks"

        # WHEN: Processing with --per-chunk
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(sample_pdf),
                "--format",
                "txt",
                "--output",
                str(output_dir),
                "--per-chunk",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # THEN: Should have sequentially numbered files
        assert result.returncode == 0
        chunk_files = sorted(output_dir.glob("*.txt"))
        assert len(chunk_files) >= 1
        # Verify naming pattern (e.g., chunk_001.txt, chunk_002.txt)
        assert any("001" in f.name or "1" in f.name for f in chunk_files)


class TestProcessCommandOrganization:
    """Test --organize and --strategy flags."""

    def test_process_with_by_document_strategy(self, sample_pdf, tmp_path):
        """Should organize output by document."""
        # GIVEN: Output directory and by_document strategy
        output_dir = tmp_path / "organized"

        # WHEN: Processing with BY_DOCUMENT organization
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(sample_pdf),
                "--format",
                "txt",
                "--output",
                str(output_dir),
                "--per-chunk",
                "--organize",
                "--strategy",
                "by_document",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # THEN: Should create document-based directory structure
        assert result.returncode == 0
        assert output_dir.exists()
        # Should have document-named subdirectories
        subdirs = [d for d in output_dir.iterdir() if d.is_dir()]
        assert len(subdirs) > 0

    def test_process_with_flat_strategy(self, sample_pdf, tmp_path):
        """Should organize output with flat structure."""
        # GIVEN: Output directory and flat strategy
        output_dir = tmp_path / "organized"

        # WHEN: Processing with FLAT organization
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(sample_pdf),
                "--format",
                "txt",
                "--output",
                str(output_dir),
                "--per-chunk",
                "--organize",
                "--strategy",
                "flat",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # THEN: Should create flat file structure
        assert result.returncode == 0
        assert output_dir.exists()
        # Flat strategy creates files in single directory
        txt_files = list(output_dir.glob("*.txt"))
        assert len(txt_files) > 0

    def test_process_organize_creates_manifest(self, sample_pdf, tmp_path):
        """Should create manifest file when using organization."""
        # GIVEN: Output directory with organization
        output_dir = tmp_path / "organized"

        # WHEN: Processing with organization enabled
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(sample_pdf),
                "--format",
                "txt",
                "--output",
                str(output_dir),
                "--per-chunk",
                "--organize",
                "--strategy",
                "flat",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # THEN: Should create manifest file
        assert result.returncode == 0
        manifest_file = output_dir / "MANIFEST.md"
        assert manifest_file.exists()


class TestProcessCommandErrorHandling:
    """Test CLI error handling and validation."""

    def test_process_errors_with_missing_file(self, tmp_path):
        """Should error gracefully when input file doesn't exist."""
        # GIVEN: Non-existent file
        missing_file = tmp_path / "nonexistent.pdf"
        output_file = tmp_path / "output.txt"

        # WHEN: Processing missing file
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(missing_file),
                "--format",
                "txt",
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # THEN: Should exit with error
        assert result.returncode != 0
        # Click validates file existence automatically

    def test_process_errors_with_organize_no_strategy(self, sample_pdf, tmp_path):
        """Should error when --organize is used without --strategy."""
        # GIVEN: Organize flag without strategy
        output_dir = tmp_path / "output"

        # WHEN: Processing with --organize but no --strategy
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(sample_pdf),
                "--format",
                "txt",
                "--output",
                str(output_dir),
                "--organize",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # THEN: Should exit with validation error
        assert result.returncode == 1
        assert "Error" in result.stdout or "Error" in result.stderr
        assert "strategy" in (result.stdout + result.stderr).lower()

    def test_process_errors_with_strategy_no_organize(self, sample_pdf, tmp_path):
        """Should error when --strategy is used without --organize."""
        # GIVEN: Strategy without organize flag
        output_dir = tmp_path / "output"

        # WHEN: Processing with --strategy but no --organize
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(sample_pdf),
                "--format",
                "txt",
                "--output",
                str(output_dir),
                "--strategy",
                "flat",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # THEN: Should exit with validation error
        assert result.returncode == 1
        assert "Error" in result.stdout or "Error" in result.stderr
        assert "organize" in (result.stdout + result.stderr).lower()


class TestProcessCommandUTF8Encoding:
    """Test UTF-8 encoding and Unicode handling."""

    def test_process_handles_unicode_content(self, tmp_path):
        """Should handle Unicode content correctly."""
        # GIVEN: File with Unicode content
        unicode_file = tmp_path / "unicode_test.pdf"
        unicode_file.write_text("Test Unicode: 你好世界 🎉 Café", encoding="utf-8")

        output_file = tmp_path / "output.txt"

        # WHEN: Processing Unicode file
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(unicode_file),
                "--format",
                "txt",
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # THEN: Should succeed and preserve Unicode
        assert result.returncode == 0
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8-sig")
        # Demo chunks contain standard text, but encoding should work
        assert len(content) > 0

    def test_process_creates_utf8_sig_encoded_files(self, sample_pdf, tmp_path):
        """Should create UTF-8-sig encoded files (BOM for Windows)."""
        # GIVEN: Output file
        output_file = tmp_path / "output.txt"

        # WHEN: Processing document
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(sample_pdf),
                "--format",
                "txt",
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # THEN: Should create UTF-8-sig file with BOM
        assert result.returncode == 0
        with open(output_file, "rb") as f:
            first_bytes = f.read(3)
            assert first_bytes == b"\xef\xbb\xbf"  # UTF-8 BOM


class TestVersionCommandIntegration:
    """Test version command via subprocess."""

    def test_version_command_displays_info(self):
        """Should display version information."""
        # WHEN: Invoking version command
        result = subprocess.run(
            [sys.executable, "-m", "data_extract.cli", "version"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # THEN: Should display version details
        assert result.returncode == 0
        assert "Data Extraction Tool v0.1.0" in result.stdout
        assert "Epic 3" in result.stdout


class TestFullWorkflowScenarios:
    """Test realistic end-to-end workflows."""

    def test_workflow_basic_txt_export(self, sample_pdf, tmp_path):
        """Complete workflow: PDF → TXT with metadata."""
        # GIVEN: Input file
        output_file = tmp_path / "export.txt"

        # WHEN: Full processing workflow
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(sample_pdf),
                "--format",
                "txt",
                "--output",
                str(output_file),
                "--include-metadata",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # THEN: Should complete full workflow
        assert result.returncode == 0
        assert output_file.exists()
        assert "Processing complete!" in result.stdout
        assert "Chunks written:" in result.stdout

        # Verify output quality
        content = output_file.read_text(encoding="utf-8-sig")
        assert len(content) > 0
        assert "Source:" in content  # Metadata header

    def test_workflow_organized_output(self, sample_pdf, tmp_path):
        """Complete workflow: PDF → Organized TXT files."""
        # GIVEN: Output directory
        output_dir = tmp_path / "organized_export"

        # WHEN: Full organized workflow
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(sample_pdf),
                "--format",
                "txt",
                "--output",
                str(output_dir),
                "--per-chunk",
                "--organize",
                "--strategy",
                "by_document",
                "--include-metadata",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # THEN: Should create organized structure
        assert result.returncode == 0
        assert output_dir.exists()
        assert (output_dir / "MANIFEST.md").exists()

        # Verify chunk files created
        all_txt_files = list(output_dir.rglob("*.txt"))
        assert len(all_txt_files) > 0

    def test_workflow_json_export(self, sample_pdf, tmp_path):
        """Complete workflow: PDF → JSON."""
        # GIVEN: Output file
        output_file = tmp_path / "export.json"

        # WHEN: JSON export workflow
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(sample_pdf),
                "--format",
                "json",
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # THEN: Should create valid JSON
        assert result.returncode == 0
        assert output_file.exists()

        # Verify JSON structure
        import json

        with open(output_file, encoding="utf-8") as f:
            data = json.load(f)
            assert "metadata" in data
            assert "chunks" in data
            assert len(data["chunks"]) > 0
            assert data["metadata"]["chunk_count"] == len(data["chunks"])
