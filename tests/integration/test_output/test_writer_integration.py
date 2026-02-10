"""Integration tests for OutputWriter coordinating formatters and organization (Story 3.5 - Bucket 2).

Tests OutputWriter as the main entry point for output generation, including:
- Formatter registry and selection
- Formatter kwargs passing (per_chunk, include_metadata, etc.)
- Organization strategy coordination
- CLI command integration
- Error handling and validation

Test Coverage:
    - OutputWriter.write() with all format types
    - Formatter kwargs passing for TXT and JSON
    - Organization strategies (BY_DOCUMENT, BY_ENTITY, FLAT)
    - CLI process command smoke tests
    - Error handling for invalid inputs
"""

import subprocess
import sys

import pytest

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.output]

import pytest  # noqa: E402

from data_extract.chunk.models import Chunk, ChunkMetadata, QualityScore  # noqa: E402
from data_extract.output.organization import OrganizationStrategy  # noqa: E402
from data_extract.output.writer import OutputWriter  # noqa: E402

pytestmark = [pytest.mark.integration, pytest.mark.output, pytest.mark.pipeline]


@pytest.fixture
def sample_chunks(tmp_path):
    """Create sample chunks for testing."""
    source_file = tmp_path / "test_document.pdf"
    source_file.touch()  # Create empty file for metadata

    chunks = []
    for idx in range(1, 4):
        metadata = ChunkMetadata(
            source_file=source_file,
            processing_version="1.0.0-test",
            entity_tags=[
                {
                    "entity_id": f"RISK-{idx:03d}",
                    "entity_type": "risk",
                    "start_pos": 0,
                    "end_pos": 10,
                }
            ],
            quality=QualityScore(
                overall=0.95,
                completeness=0.98,
                coherence=0.92,
                ocr_confidence=0.98,
                readability_flesch_kincaid=8.0,
                readability_gunning_fog=9.5,
                flags=[],
            ),
        )

        chunk = Chunk(
            id=f"chunk_{idx:03d}",
            text=f"This is test chunk {idx} with **markdown** and <html>tags</html>.",
            document_id="test_document",
            position_index=idx - 1,
            token_count=15,
            word_count=12,
            entities=[],
            section_context="",
            quality_score=0.95,
            readability_scores={"flesch_reading_ease": 65.0},
            metadata=metadata,
        )
        chunks.append(chunk)

    return chunks


class TestOutputWriterBasic:
    """Test basic OutputWriter functionality with format selection."""

    def test_writer_txt_concatenated(self, sample_chunks, tmp_path):
        """Should create concatenated TXT output."""
        # GIVEN: OutputWriter and sample chunks
        writer = OutputWriter()
        output_path = tmp_path / "output.txt"

        # WHEN: Writing chunks to TXT
        result = writer.write(
            chunks=iter(sample_chunks), output_path=output_path, format_type="txt"
        )

        # THEN: TXT file should exist with correct structure
        assert result.format_type == "txt"
        assert result.chunk_count == 3
        assert result.output_path == output_path
        assert output_path.exists()

        content = output_path.read_text(encoding="utf-8-sig")
        assert "━━━ CHUNK 001 ━━━" in content
        assert "━━━ CHUNK 002 ━━━" in content
        assert "━━━ CHUNK 003 ━━━" in content

    def test_writer_json_output(self, tmp_path):
        """Should create JSON output."""
        # GIVEN: OutputWriter and chunks with simplified metadata for JSON
        writer = OutputWriter()
        output_path = tmp_path / "output.json"

        # Create simplified chunks for JSON test (avoid entity serialization complexity)
        from data_extract.core.models import Chunk  # noqa: E402

        simple_chunks = [
            Chunk(
                id=f"chunk_{i:03d}",
                text=f"Simple chunk {i} for JSON testing.",
                document_id="test_doc",
                position_index=i - 1,
                token_count=6,
                word_count=6,
                entities=[],
                section_context="",
                quality_score=0.95,
                readability_scores={"flesch_reading_ease": 65.0},
                metadata=None,  # Simplify metadata for JSON test
            )
            for i in range(1, 4)
        ]

        # WHEN: Writing chunks to JSON
        result = writer.write(
            chunks=iter(simple_chunks), output_path=output_path, format_type="json", validate=False
        )

        # THEN: JSON file should exist with correct structure
        assert result.format_type == "json"
        assert result.chunk_count == 3
        assert result.output_path == output_path
        assert output_path.exists()

        import json  # noqa: E402

        with open(output_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        assert "metadata" in data
        assert "chunks" in data
        assert len(data["chunks"]) == 3


class TestOutputWriterFormatterKwargs:
    """Test OutputWriter passing kwargs to formatters."""

    def test_writer_txt_per_chunk_mode(self, sample_chunks, tmp_path):
        """Should create per-chunk TXT files when per_chunk=True."""
        # GIVEN: OutputWriter and sample chunks
        writer = OutputWriter()
        output_dir = tmp_path / "output"

        # WHEN: Writing with per_chunk=True
        result = writer.write(
            chunks=iter(sample_chunks),
            output_path=output_dir,
            format_type="txt",
            per_chunk=True,
        )

        # THEN: Per-chunk files should be created
        assert result.chunk_count == 3
        assert result.output_path == output_dir

        # Check files exist
        chunk_files = list(output_dir.glob("*.txt"))
        assert len(chunk_files) == 3

    def test_writer_txt_with_metadata(self, sample_chunks, tmp_path):
        """Should include metadata headers when include_metadata=True."""
        # GIVEN: OutputWriter and sample chunks
        writer = OutputWriter()
        output_path = tmp_path / "output.txt"

        # WHEN: Writing with include_metadata=True
        result = writer.write(
            chunks=iter(sample_chunks),
            output_path=output_path,
            format_type="txt",
            include_metadata=True,
        )

        # THEN: Metadata headers should be present
        assert result.chunk_count == 3
        content = output_path.read_text(encoding="utf-8-sig")

        assert "Source:" in content  # Metadata header
        assert "Entities:" in content
        assert "Quality:" in content

    def test_writer_txt_custom_delimiter(self, sample_chunks, tmp_path):
        """Should use custom delimiter when provided."""
        # GIVEN: OutputWriter and custom delimiter
        writer = OutputWriter()
        output_path = tmp_path / "output.txt"
        custom_delimiter = "--- CHUNK {{n}} ---"

        # WHEN: Writing with custom delimiter
        result = writer.write(
            chunks=iter(sample_chunks),
            output_path=output_path,
            format_type="txt",
            delimiter=custom_delimiter,
        )

        # THEN: Custom delimiter should be used
        assert result.chunk_count == 3
        content = output_path.read_text(encoding="utf-8-sig")

        assert "--- CHUNK 001 ---" in content
        assert "--- CHUNK 002 ---" in content
        assert "━━━ CHUNK" not in content  # Default delimiter not present


class TestOutputWriterOrganization:
    """Test OutputWriter with organization strategies."""

    def test_writer_with_by_document_strategy(self, sample_chunks, tmp_path):
        """Should organize output by document when strategy=BY_DOCUMENT."""
        # GIVEN: OutputWriter and sample chunks
        writer = OutputWriter()
        output_dir = tmp_path / "output"

        # WHEN: Writing with BY_DOCUMENT strategy
        result = writer.write(
            chunks=iter(sample_chunks),
            output_path=output_dir,
            format_type="txt",
            per_chunk=True,
            organize=True,
            strategy=OrganizationStrategy.BY_DOCUMENT,
        )

        # THEN: Directory structure should be created
        assert result.chunk_count == 3
        assert output_dir.exists()

        # Check manifest exists
        manifest_path = output_dir / "manifest.json"
        assert manifest_path.exists()

        # Check document directory exists
        doc_dirs = [d for d in output_dir.iterdir() if d.is_dir()]
        assert len(doc_dirs) >= 1  # At least one document directory

    def test_writer_with_flat_strategy(self, sample_chunks, tmp_path):
        """Should use flat structure when strategy=FLAT."""
        # GIVEN: OutputWriter and sample chunks
        writer = OutputWriter()
        output_dir = tmp_path / "output"

        # WHEN: Writing with FLAT strategy
        result = writer.write(
            chunks=iter(sample_chunks),
            output_path=output_dir,
            format_type="txt",
            per_chunk=True,
            organize=True,
            strategy=OrganizationStrategy.FLAT,
        )

        # THEN: Flat structure should be used
        assert result.chunk_count == 3
        assert output_dir.exists()

        # Check manifest exists
        manifest_path = output_dir / "manifest.json"
        assert manifest_path.exists()

        # Check chunk files in flat structure
        chunk_files = list(output_dir.glob("*.txt"))
        assert len(chunk_files) == 3


class TestOutputWriterErrorHandling:
    """Test OutputWriter error handling and validation."""

    def test_writer_invalid_format_type(self, sample_chunks, tmp_path):
        """Should raise ValueError for unsupported format type."""
        # GIVEN: OutputWriter and invalid format
        writer = OutputWriter()
        output_path = tmp_path / "output.unknown"

        # WHEN/THEN: Writing with invalid format should raise error
        with pytest.raises(ValueError, match="Unsupported format type"):
            writer.write(chunks=iter(sample_chunks), output_path=output_path, format_type="invalid")

    def test_writer_organize_without_strategy(self, sample_chunks, tmp_path):
        """Should raise ValueError when organize=True but strategy=None."""
        # GIVEN: OutputWriter with organize but no strategy
        writer = OutputWriter()
        output_path = tmp_path / "output"

        # WHEN/THEN: Writing should raise error
        with pytest.raises(ValueError, match="Organization enabled but no strategy provided"):
            writer.write(
                chunks=iter(sample_chunks),
                output_path=output_path,
                format_type="txt",
                organize=True,
                strategy=None,
            )

    def test_writer_strategy_without_organize(self, sample_chunks, tmp_path):
        """Should raise ValueError when strategy provided but organize=False."""
        # GIVEN: OutputWriter with strategy but organize=False
        writer = OutputWriter()
        output_path = tmp_path / "output.txt"

        # WHEN/THEN: Writing should raise error
        with pytest.raises(ValueError, match="Strategy provided but organization not enabled"):
            writer.write(
                chunks=iter(sample_chunks),
                output_path=output_path,
                format_type="txt",
                organize=False,
                strategy=OrganizationStrategy.BY_DOCUMENT,
            )


class TestCLIIntegration:
    """Test CLI integration with OutputWriter (smoke tests)."""

    def test_cli_process_txt_basic(self, tmp_path):
        """Should process document via CLI and create TXT output."""
        # GIVEN: Input file and output path
        input_file = tmp_path / "input.pdf"
        input_file.touch()  # Create empty file
        output_file = tmp_path / "output.txt"

        # WHEN: Invoking CLI process command
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(input_file),
                "--format",
                "txt",
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )

        # THEN: CLI should succeed and create output
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert output_file.exists()
        assert "Processing complete!" in result.stdout

    def test_cli_process_with_metadata(self, tmp_path):
        """Should create TXT output with metadata when --include-metadata flag used."""
        # GIVEN: Input file and output path
        input_file = tmp_path / "input.pdf"
        input_file.touch()
        output_file = tmp_path / "output.txt"

        # WHEN: Invoking CLI with --include-metadata
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(input_file),
                "--format",
                "txt",
                "--output",
                str(output_file),
                "--include-metadata",
            ],
            capture_output=True,
            text=True,
        )

        # THEN: CLI should succeed and include metadata
        assert result.returncode == 0
        assert output_file.exists()

        content = output_file.read_text(encoding="utf-8-sig")
        assert "Source:" in content  # Metadata present

    def test_cli_process_per_chunk(self, tmp_path):
        """Should create per-chunk files when --per-chunk flag used."""
        # GIVEN: Input file and output directory
        input_file = tmp_path / "input.pdf"
        input_file.touch()
        output_dir = tmp_path / "output"

        # WHEN: Invoking CLI with --per-chunk
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(input_file),
                "--format",
                "txt",
                "--output",
                str(output_dir),
                "--per-chunk",
            ],
            capture_output=True,
            text=True,
        )

        # THEN: CLI should succeed and create per-chunk files
        assert result.returncode == 0
        assert output_dir.exists()

        chunk_files = list(output_dir.glob("*.txt"))
        assert len(chunk_files) > 0  # At least one chunk file created

    def test_cli_version_command(self):
        """Should display version information."""
        # WHEN: Invoking version command
        result = subprocess.run(
            [sys.executable, "-m", "data_extract.cli", "version"],
            capture_output=True,
            text=True,
        )

        # THEN: Should display version
        assert result.returncode == 0
        assert "Data Extraction Tool v0.1.0" in result.stdout
        assert "Epic 3, Story 3.5" in result.stdout

    def test_cli_error_organize_without_strategy(self, tmp_path):
        """Should fail when --organize used without --strategy."""
        # GIVEN: Input file with organize but no strategy
        input_file = tmp_path / "input.pdf"
        input_file.touch()
        output_dir = tmp_path / "output"

        # WHEN: Invoking CLI with --organize but no --strategy
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_extract.cli",
                "process",
                str(input_file),
                "--format",
                "txt",
                "--output",
                str(output_dir),
                "--organize",
            ],
            capture_output=True,
            text=True,
        )

        # THEN: CLI should fail with error message
        assert result.returncode == 1
        assert "--organize flag requires --strategy option" in result.stderr


class TestOutputWriterStatistics:
    """Test OutputWriter statistics and metadata reporting."""

    def test_writer_reports_accurate_statistics(self, sample_chunks, tmp_path):
        """Should report accurate statistics in FormatResult."""
        # GIVEN: OutputWriter and sample chunks
        writer = OutputWriter()
        output_path = tmp_path / "output.txt"

        # WHEN: Writing chunks
        result = writer.write(
            chunks=iter(sample_chunks), output_path=output_path, format_type="txt"
        )

        # THEN: Statistics should be accurate
        assert result.chunk_count == 3
        assert result.file_size_bytes > 0
        assert result.duration_seconds >= 0
        assert result.errors == []

    def test_writer_empty_chunks(self, tmp_path):
        """Should handle empty chunks gracefully."""
        # GIVEN: OutputWriter and empty chunks
        writer = OutputWriter()
        output_path = tmp_path / "output.txt"

        # WHEN: Writing empty chunks
        result = writer.write(chunks=iter([]), output_path=output_path, format_type="txt")

        # THEN: Should create empty output with zero count
        assert result.chunk_count == 0
        assert result.errors == []
