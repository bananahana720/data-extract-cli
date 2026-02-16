"""Tests for OutputWriter coordinator module.

OutputWriter coordinates formatter selection and output organization.
Tests cover format selection, options passthrough, per-chunk mode, and
directory creation behavior.
"""

from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from data_extract.core.models import Chunk
from data_extract.output.formatters.base import FormattingResult
from data_extract.output.organization import OrganizationResult, OrganizationStrategy
from data_extract.output.writer import OutputWriter

# ============================================================================
# TEST MARKERS
# ============================================================================

pytestmark = [pytest.mark.P0, pytest.mark.unit]


# ============================================================================
# FORMAT SELECTION TESTS
# ============================================================================


def test_json_format_selection(sample_chunk: Chunk, tmp_path: Path) -> None:
    """OutputWriter selects JsonFormatter for format_type='json'."""
    writer = OutputWriter()
    output_path = tmp_path / "output.json"

    with patch("data_extract.output.writer.JsonFormatter") as mock_json_formatter:
        mock_formatter_instance = MagicMock()
        mock_json_formatter.return_value = mock_formatter_instance
        mock_formatter_instance.format_chunks.return_value = FormattingResult(
            output_path=output_path,
            chunk_count=1,
            total_size=100,
            metadata={},
            format_type="json",
        )

        writer.write([sample_chunk], output_path, format_type="json")

        # Verify JsonFormatter was instantiated
        mock_json_formatter.assert_called_once_with(validate=True)
        # Verify format_chunks was called
        mock_formatter_instance.format_chunks.assert_called_once()


def test_txt_format_selection(sample_chunk: Chunk, tmp_path: Path) -> None:
    """OutputWriter selects TxtFormatter for format_type='txt'."""
    writer = OutputWriter()
    output_path = tmp_path / "output.txt"

    with patch("data_extract.output.writer.TxtFormatter") as mock_txt_formatter:
        mock_formatter_instance = MagicMock()
        mock_txt_formatter.return_value = mock_formatter_instance
        mock_formatter_instance.format_chunks.return_value = FormattingResult(
            output_path=output_path,
            chunk_count=1,
            total_size=100,
            metadata={},
            format_type="txt",
        )

        writer.write([sample_chunk], output_path, format_type="txt")

        # Verify TxtFormatter was instantiated with defaults
        mock_txt_formatter.assert_called_once_with(
            include_metadata=False, delimiter="━━━ CHUNK {{n}} ━━━"
        )
        mock_formatter_instance.format_chunks.assert_called_once()


def test_csv_format_selection(sample_chunk: Chunk, tmp_path: Path) -> None:
    """OutputWriter selects CsvFormatter for format_type='csv'."""
    writer = OutputWriter()
    output_path = tmp_path / "output.csv"

    with patch("data_extract.output.writer.CsvFormatter") as mock_csv_formatter:
        mock_formatter_instance = MagicMock()
        mock_csv_formatter.return_value = mock_formatter_instance
        mock_formatter_instance.format_chunks.return_value = FormattingResult(
            output_path=output_path,
            chunk_count=1,
            total_size=100,
            metadata={},
            format_type="csv",
        )

        writer.write([sample_chunk], output_path, format_type="csv")

        # Verify CsvFormatter was instantiated
        mock_csv_formatter.assert_called_once_with(max_text_length=None, validate=True)
        mock_formatter_instance.format_chunks.assert_called_once()


def test_invalid_format_raises_value_error(sample_chunk: Chunk, tmp_path: Path) -> None:
    """OutputWriter raises ValueError for unsupported format type."""
    writer = OutputWriter()
    output_path = tmp_path / "output.xml"

    with pytest.raises(ValueError) as exc_info:
        writer.write([sample_chunk], output_path, format_type="xml")

    assert "Unsupported format type: xml" in str(exc_info.value)


# ============================================================================
# OPTIONS PASSTHROUGH TESTS
# ============================================================================


def test_options_passthrough_validate_true(sample_chunk: Chunk, tmp_path: Path) -> None:
    """OutputWriter passes validate=True option to JsonFormatter."""
    writer = OutputWriter()
    output_path = tmp_path / "output.json"

    with patch("data_extract.output.writer.JsonFormatter") as mock_json_formatter:
        mock_formatter_instance = MagicMock()
        mock_json_formatter.return_value = mock_formatter_instance
        mock_formatter_instance.format_chunks.return_value = FormattingResult(
            output_path=output_path,
            chunk_count=1,
            total_size=100,
            metadata={},
            format_type="json",
        )

        writer.write([sample_chunk], output_path, format_type="json", validate=True)

        # Verify validate=True was passed to constructor
        mock_json_formatter.assert_called_once_with(validate=True)


def test_options_passthrough_include_metadata_true(sample_chunk: Chunk, tmp_path: Path) -> None:
    """OutputWriter passes include_metadata=True option to TxtFormatter."""
    writer = OutputWriter()
    output_path = tmp_path / "output.txt"

    with patch("data_extract.output.writer.TxtFormatter") as mock_txt_formatter:
        mock_formatter_instance = MagicMock()
        mock_txt_formatter.return_value = mock_formatter_instance
        mock_formatter_instance.format_chunks.return_value = FormattingResult(
            output_path=output_path,
            chunk_count=1,
            total_size=100,
            metadata={},
            format_type="txt",
        )

        writer.write([sample_chunk], output_path, format_type="txt", include_metadata=True)

        # Verify include_metadata=True was passed to constructor
        mock_txt_formatter.assert_called_once_with(
            include_metadata=True, delimiter="━━━ CHUNK {{n}} ━━━"
        )


# ============================================================================
# PER-CHUNK MODE TESTS
# ============================================================================


def test_per_chunk_mode_creates_multiple_files(sample_chunks: List[Chunk], tmp_path: Path) -> None:
    """OutputWriter creates separate files per chunk in per_chunk mode."""
    writer = OutputWriter()
    output_dir = tmp_path / "chunks"

    with patch("data_extract.output.writer.TxtFormatter") as mock_txt_formatter:
        mock_formatter_instance = MagicMock()
        mock_txt_formatter.return_value = mock_formatter_instance
        mock_formatter_instance.format_chunks.return_value = FormattingResult(
            output_path=output_dir / "batch_001.txt",
            chunk_count=1,
            total_size=200,
            metadata={},
            format_type="txt",
        )

        result = writer.write(sample_chunks, output_dir, format_type="txt", per_chunk=True)

        # Verify formatter was called once per chunk
        assert mock_formatter_instance.format_chunks.call_count == len(sample_chunks)

        # Verify result is a FormattingResult
        assert isinstance(result, FormattingResult)
        assert result.chunk_count == len(sample_chunks)
        assert result.output_path == output_dir


def test_per_chunk_file_naming(sample_chunks: List[Chunk], tmp_path: Path) -> None:
    """OutputWriter names per-chunk files using chunk.id attribute."""
    writer = OutputWriter()
    output_dir = tmp_path / "chunks"

    with patch("data_extract.output.writer.JsonFormatter") as mock_json_formatter:
        mock_formatter_instance = MagicMock()
        mock_json_formatter.return_value = mock_formatter_instance
        mock_formatter_instance.format_chunks.return_value = FormattingResult(
            output_path=output_dir / "batch_001.json",
            chunk_count=1,
            total_size=150,
            metadata={},
            format_type="json",
        )

        writer.write(sample_chunks, output_dir, format_type="json", per_chunk=True)

        # Extract all calls to format_chunks
        calls = mock_formatter_instance.format_chunks.call_args_list

        # Verify file paths match chunk IDs
        expected_filenames = [f"{chunk.id}.json" for chunk in sample_chunks]
        actual_filenames = [call[0][1].name for call in calls]

        assert actual_filenames == expected_filenames


def test_per_chunk_creates_output_directory(sample_chunks: List[Chunk], tmp_path: Path) -> None:
    """OutputWriter creates output directory if it doesn't exist in per_chunk mode."""
    writer = OutputWriter()
    output_dir = tmp_path / "nested" / "output" / "chunks"

    # Verify directory doesn't exist
    assert not output_dir.exists()

    with patch("data_extract.output.writer.TxtFormatter") as mock_txt_formatter:
        mock_formatter_instance = MagicMock()
        mock_txt_formatter.return_value = mock_formatter_instance
        mock_formatter_instance.format_chunks.return_value = FormattingResult(
            output_path=output_dir / "batch_001.txt",
            chunk_count=1,
            total_size=100,
            metadata={},
            format_type="txt",
        )

        writer.write(sample_chunks, output_dir, format_type="txt", per_chunk=True)

        # Verify directory was created
        assert output_dir.exists()
        assert output_dir.is_dir()


def test_per_chunk_rolls_back_created_files_on_later_failure(
    sample_chunks: List[Chunk], tmp_path: Path
) -> None:
    """Per-chunk mode removes prior outputs if a later chunk write fails."""
    writer = OutputWriter()
    output_dir = tmp_path / "chunks"
    call_state = {"count": 0}

    def failing_format_chunks(chunks, output_path, **kwargs):
        del kwargs  # Not used in this test double.
        call_state["count"] += 1
        if call_state["count"] == 1:
            output_path.write_text("first chunk", encoding="utf-8")
            return FormattingResult(
                output_path=output_path,
                chunk_count=1,
                total_size=output_path.stat().st_size,
                metadata={},
                format_type="json",
            )

        output_path.write_text("partial second", encoding="utf-8")
        raise RuntimeError("chunk write failed")

    with patch("data_extract.output.writer.JsonFormatter") as mock_json_formatter:
        mock_formatter_instance = MagicMock()
        mock_json_formatter.return_value = mock_formatter_instance
        mock_formatter_instance.format_chunks.side_effect = failing_format_chunks

        with pytest.raises(RuntimeError, match="chunk write failed"):
            writer.write(sample_chunks[:2], output_dir, format_type="json", per_chunk=True)

    first_file = output_dir / f"{sample_chunks[0].id}.json"
    second_file = output_dir / f"{sample_chunks[1].id}.json"
    assert not first_file.exists()
    assert not second_file.exists()


# ============================================================================
# RETURN VALUE TESTS
# ============================================================================


def test_returns_formatting_result(sample_chunk: Chunk, tmp_path: Path) -> None:
    """OutputWriter returns FormattingResult from formatter."""
    writer = OutputWriter()
    output_path = tmp_path / "output.json"

    with patch("data_extract.output.writer.JsonFormatter") as mock_json_formatter:
        mock_formatter_instance = MagicMock()
        mock_json_formatter.return_value = mock_formatter_instance
        expected_result = FormattingResult(
            output_path=output_path,
            chunk_count=1,
            total_size=256,
            metadata={"test": "data"},
            format_type="json",
        )
        mock_formatter_instance.format_chunks.return_value = expected_result

        result = writer.write([sample_chunk], output_path, format_type="json")

        assert result == expected_result


# ============================================================================
# ORGANIZATION MODE TESTS
# ============================================================================


def test_organization_mode_delegates_to_organizer(
    sample_chunks: List[Chunk], tmp_path: Path
) -> None:
    """OutputWriter delegates to Organizer when organize=True."""
    writer = OutputWriter()
    output_dir = tmp_path / "organized"

    with patch.object(writer.organizer, "organize") as mock_organize:
        mock_organize.return_value = OrganizationResult(
            strategy=OrganizationStrategy.FLAT,
            output_dir=output_dir,
            files_created=[],
            metadata={},
        )

        result = writer.write(
            sample_chunks,
            output_dir,
            format_type="json",
            organize=True,
            strategy=OrganizationStrategy.FLAT,
        )

        # Verify organizer.organize was called
        mock_organize.assert_called_once_with(
            chunks=sample_chunks,
            output_dir=output_dir,
            strategy=OrganizationStrategy.FLAT,
            format_type="json",
        )

        # Verify result is OrganizationResult
        assert isinstance(result, OrganizationResult)


def test_organized_mode_rolls_back_chunks_and_manifests_on_failure(
    sample_chunks: List[Chunk], tmp_path: Path
) -> None:
    """Organized writes remove created chunks/manifests when manifest creation fails."""
    writer = OutputWriter()
    output_dir = tmp_path / "organized"
    manifest_calls = {"count": 0}

    def failing_manifest_write(output_path: Path, content: str, encoding: str = "utf-8") -> None:
        manifest_calls["count"] += 1
        output_path.write_text(content, encoding=encoding)
        if manifest_calls["count"] == 2:
            raise RuntimeError("manifest write failed")

    with patch.object(writer, "_write_text_atomic", side_effect=failing_manifest_write):
        with pytest.raises(RuntimeError, match="manifest write failed"):
            writer.write(
                sample_chunks[:2],
                output_dir,
                format_type="txt",
                organize=True,
                strategy=OrganizationStrategy.FLAT,
            )

    for chunk in sample_chunks[:2]:
        assert not (output_dir / f"{chunk.id}.txt").exists()
    assert not (output_dir / "manifest.json").exists()
    assert not (output_dir / "MANIFEST.md").exists()
