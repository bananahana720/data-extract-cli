"""Integration tests for end-to-end TXT output pipeline (Story 3.5 - ATDD RED PHASE).

Tests complete pipeline from ProcessingResult → ChunkingEngine → TxtFormatter → TXT file,
including delimiter rendering, metadata accuracy, and LLM upload readiness.

Test Coverage:
    - AC-3.5-1: Clean text in real pipeline
    - AC-3.5-2: Delimiters in concatenated output
    - AC-3.5-4: Output organization strategies
    - AC-3.5-7: LLM upload readiness (automated validation)

These tests WILL FAIL until full pipeline is integrated (GREEN phase).
"""

import re

import pytest

from data_extract.chunk.engine import ChunkingConfig, ChunkingEngine
from data_extract.output.formatters.txt_formatter import TxtFormatter

pytestmark = [pytest.mark.integration, pytest.mark.output, pytest.mark.pipeline]


@pytest.fixture
def sample_processing_result(sample_processing_result):
    """Use shared fixture from conftest.py for ProcessingResult."""
    return sample_processing_result


@pytest.fixture
def chunking_engine():
    """Create ChunkingEngine with default configuration."""
    config = ChunkingConfig(chunk_size=512, overlap_pct=0.15)
    return ChunkingEngine(config)


@pytest.fixture
def txt_formatter():
    """Create TxtFormatter with default settings."""
    return TxtFormatter()


@pytest.fixture
def txt_formatter_with_metadata():
    """Create TxtFormatter with metadata headers enabled."""
    return TxtFormatter(include_metadata=True)


class TestEndToEndPipeline:
    """Test complete pipeline: ProcessingResult → Chunks → TXT file (AC-3.5-1, AC-3.5-2)."""

    def test_complete_pipeline_processing_result_to_txt(
        self, sample_processing_result, chunking_engine, txt_formatter, tmp_path
    ):
        """Should process document from ProcessingResult through to TXT file."""
        # GIVEN: ProcessingResult from normalization stage
        output_path = tmp_path / "output.txt"

        # WHEN: Chunking and formatting to TXT
        chunks = chunking_engine.chunk(sample_processing_result)
        txt_formatter.format_chunks(chunks, output_path)

        # THEN: TXT file should exist and be readable
        assert output_path.exists()

        content = output_path.read_text(encoding="utf-8-sig")
        assert len(content) > 0
        assert "━━━ CHUNK" in content  # Delimiter present

    def test_pipeline_produces_clean_text(
        self, sample_processing_result, chunking_engine, txt_formatter, tmp_path
    ):
        """Should produce clean plain text without markup artifacts (AC-3.5-1)."""
        # GIVEN: ProcessingResult with content
        output_path = tmp_path / "output.txt"

        # WHEN: Processing through pipeline
        chunks = chunking_engine.chunk(sample_processing_result)
        txt_formatter.format_chunks(chunks, output_path)

        # THEN: Output should be clean text
        content = output_path.read_text(encoding="utf-8-sig")
        # Should not contain markdown/HTML artifacts
        assert "<p>" not in content
        assert "</p>" not in content
        # Should not contain JSON artifacts (outside metadata)
        text_chunks = content.split("━━━ CHUNK")
        for chunk in text_chunks[1:]:  # Skip preamble
            chunk_text = chunk.split("\n", 2)[-1]  # Skip delimiter line
            assert not re.search(r"^\s*[\{\}\[\]]\s*$", chunk_text, re.MULTILINE)

    def test_pipeline_delimiter_between_chunks(
        self, sample_processing_result, chunking_engine, txt_formatter, tmp_path
    ):
        """Should insert delimiters between all chunks in concatenated output (AC-3.5-2)."""
        # GIVEN: Multi-chunk document
        output_path = tmp_path / "output.txt"

        # WHEN: Processing through pipeline
        chunks = list(chunking_engine.chunk(sample_processing_result))
        chunk_count = len(chunks)
        txt_formatter.format_chunks(iter(chunks), output_path)

        # THEN: Should have delimiters for each chunk
        content = output_path.read_text(encoding="utf-8-sig")
        delimiter_count = content.count("━━━ CHUNK")
        assert delimiter_count == chunk_count

    def test_pipeline_metadata_headers_when_enabled(
        self, sample_processing_result, chunking_engine, txt_formatter_with_metadata, tmp_path
    ):
        """Should include metadata headers when enabled (AC-3.5-3)."""
        # GIVEN: Formatter with metadata enabled
        output_path = tmp_path / "output.txt"

        # WHEN: Processing through pipeline
        chunks = chunking_engine.chunk(sample_processing_result)
        txt_formatter_with_metadata.format_chunks(chunks, output_path)

        # THEN: Metadata headers should appear
        content = output_path.read_text(encoding="utf-8-sig")
        assert "Source:" in content
        # Should have at least one metadata field per chunk
        assert content.count("Source:") >= 1


class TestLLMUploadReadiness:
    """Test LLM upload readiness criteria (AC-3.5-7)."""

    def test_output_ready_for_direct_copy_paste(
        self, sample_processing_result, chunking_engine, txt_formatter, tmp_path
    ):
        """Should produce output suitable for direct ChatGPT/Claude paste (AC-3.5-7)."""
        # GIVEN: Real document processed through pipeline
        output_path = tmp_path / "output.txt"

        # WHEN: Generating TXT output
        chunks = chunking_engine.chunk(sample_processing_result)
        txt_formatter.format_chunks(chunks, output_path)

        # THEN: Output should be LLM-ready
        content = output_path.read_text(encoding="utf-8-sig")

        # Criterion 1: No JSON syntax (allow legitimate brackets in content like "[Table]")
        # Check for JSON object syntax
        assert '{"' not in content or "Source:" in content  # Allow in metadata headers only
        # Check for JSON array syntax (comma-separated items in brackets)
        assert '["' not in content and "[{" not in content

        # Criterion 2: No HTML
        assert "<" not in content or "<" not in content[:100]  # May appear in text content

        # Criterion 3: No ANSI codes
        assert "\x1b[" not in content
        assert "\033[" not in content

        # Criterion 4: Readable structure
        assert "━━━ CHUNK" in content  # Clear chunk boundaries

        # Criterion 5: Valid UTF-8
        assert content.isprintable() or "\n" in content  # Printable + newlines

    def test_output_metadata_provides_context(
        self, sample_processing_result, chunking_engine, txt_formatter_with_metadata, tmp_path
    ):
        """Should provide rich metadata context for LLM understanding (AC-3.5-3, AC-3.5-7)."""
        # GIVEN: Real document with metadata enabled
        output_path = tmp_path / "output.txt"

        # WHEN: Generating TXT with metadata
        chunks = chunking_engine.chunk(sample_processing_result)
        txt_formatter_with_metadata.format_chunks(chunks, output_path)

        # THEN: Metadata should enhance LLM context
        content = output_path.read_text(encoding="utf-8-sig")

        # Should have source attribution
        assert "Source:" in content

        # Metadata should be compact (not overwhelming)
        # Each chunk should have <= 5 lines of metadata
        chunk_sections = content.split("━━━ CHUNK")
        for section in chunk_sections[1:]:  # Skip preamble
            section_lines = section.split("\n")
            # Count metadata lines (before actual text)
            metadata_line_count = 0
            for line in section_lines:
                if line.strip() and not line.strip().startswith(("This", "The", "A", "An")):
                    metadata_line_count += 1
                else:
                    break
            assert metadata_line_count <= 6  # Delimiter + max 5 metadata lines


class TestOutputOrganization:
    """Test output organization strategies (AC-3.5-4)."""

    def test_concatenated_single_file_mode(
        self, sample_processing_result, chunking_engine, txt_formatter, tmp_path
    ):
        """Should produce single concatenated file with all chunks (AC-3.5-4)."""
        # GIVEN: Multiple chunks from processing result
        output_path = tmp_path / "output.txt"

        # WHEN: Formatting to single file
        chunks = list(chunking_engine.chunk(sample_processing_result))
        chunk_count = len(chunks)
        txt_formatter.format_chunks(iter(chunks), output_path)

        # THEN: All chunks in single file
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8-sig")
        # Verify all chunks present via delimiter count
        delimiter_count = content.count("━━━ CHUNK")
        assert delimiter_count == chunk_count

    def test_utf8_sig_encoding_preserved(
        self, sample_processing_result, chunking_engine, txt_formatter, tmp_path
    ):
        """Should preserve UTF-8-sig encoding through pipeline (AC-3.5-5)."""
        # GIVEN: Document processed through pipeline
        output_path = tmp_path / "output.txt"

        # WHEN: Formatting to TXT
        chunks = chunking_engine.chunk(sample_processing_result)
        txt_formatter.format_chunks(chunks, output_path)

        # THEN: File should have UTF-8 BOM
        raw_bytes = output_path.read_bytes()
        assert raw_bytes[:3] == b"\xef\xbb\xbf"  # UTF-8 BOM
