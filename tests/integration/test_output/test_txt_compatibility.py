"""Compatibility tests for TXT formatter (Story 3.5 - ATDD RED PHASE).

Tests cross-platform compatibility, path handling, and encoding edge cases.

Test Coverage:
    - AC-3.5-4: Path handling across platforms
    - AC-3.5-5: UTF-8 encoding with special characters
    - AC-3.5-6: Artifact-free output validation

These tests WILL FAIL until TxtFormatter is fully implemented (GREEN phase).
"""

from pathlib import Path

import pytest

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.output]

# These imports WILL FAIL in RED phase - this is expected
try:
    from data_extract.output.formatters.txt_formatter import TxtFormatter  # noqa: E402
except ImportError:
    TxtFormatter = None

from datetime import datetime  # noqa: E402

from data_extract.chunk.models import Chunk, ChunkMetadata  # noqa: E402

pytestmark = [pytest.mark.integration, pytest.mark.compatibility, pytest.mark.output]


@pytest.fixture
def txt_formatter():
    """Create TxtFormatter instance."""
    if TxtFormatter is None:
        pytest.skip("TxtFormatter not available yet (RED phase)")
    return TxtFormatter()


@pytest.fixture
def chunk_with_unicode() -> Chunk:
    """Create chunk with diverse Unicode characters."""
    chunk_metadata = ChunkMetadata(
        entity_tags=[],
        quality=None,
        source_hash="unicode_test",
        document_type="text",
        word_count=20,
        token_count=25,
        created_at=datetime(2025, 11, 15, 10, 0, 0),
        processing_version="1.0.0",
        source_file=Path("tests/fixtures/unicode_test.txt"),
        config_snapshot={},
    )

    return Chunk(
        id="unicode_chunk",
        text="Español: ñ, á, é, í, ó, ú. Français: é, è, ê, ë, ç. Deutsch: ä, ö, ü, ß. Chinese: 你好. Arabic: مرحبا. Emoji: 🚀🎉💻",
        document_id="unicode_doc",
        position_index=0,
        token_count=25,
        word_count=20,
        entities=[],
        quality_score=0.92,
        metadata=chunk_metadata,
    )


class TestPathCompatibility:
    """Test path handling across platforms (AC-3.5-4)."""

    def test_windows_path_handling(self, txt_formatter, tmp_path):
        """Should handle Windows-style paths correctly."""
        # GIVEN: Chunk with Windows path metadata
        chunk_metadata = ChunkMetadata(
            entity_tags=[],
            quality=None,
            source_hash="test",
            document_type="text",
            word_count=10,
            token_count=12,
            created_at=datetime(2025, 11, 15, 10, 0, 0),
            processing_version="1.0.0",
            source_file=Path("C:/Users/test/documents/report.pdf"),
            config_snapshot={},
        )

        chunk = Chunk(
            id="test",
            text="Test content",
            document_id="test",
            position_index=0,
            token_count=12,
            word_count=10,
            entities=[],
            quality_score=0.90,
            metadata=chunk_metadata,
        )

        output_path = tmp_path / "output.txt"

        # WHEN: Formatting chunk
        result = txt_formatter.format_chunks(iter([chunk]), output_path)

        # THEN: Should handle path without errors
        assert result.chunk_count == 1
        assert output_path.exists()

    def test_unicode_filename_support(self, txt_formatter, chunk_with_unicode, tmp_path):
        """Should support Unicode characters in output filename (AC-3.5-5)."""
        # GIVEN: Output path with Unicode characters
        output_path = tmp_path / "résumé_output_🚀.txt"

        # WHEN: Formatting to Unicode filename
        txt_formatter.format_chunks(iter([chunk_with_unicode]), output_path)

        # THEN: File should be created successfully
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8-sig")
        assert len(content) > 0


class TestUnicodeCompatibility:
    """Test Unicode character handling (AC-3.5-5)."""

    def test_multilingual_text_preservation(self, txt_formatter, chunk_with_unicode, tmp_path):
        """Should preserve multilingual Unicode text correctly."""
        # GIVEN: Chunk with multiple languages
        output_path = tmp_path / "multilingual.txt"

        # WHEN: Formatting to TXT
        txt_formatter.format_chunks(iter([chunk_with_unicode]), output_path)

        # THEN: All Unicode characters should be preserved
        content = output_path.read_text(encoding="utf-8-sig")
        assert "ñ" in content  # Spanish
        assert "ç" in content  # French
        assert "ß" in content  # German
        assert "你好" in content  # Chinese
        assert "مرحبا" in content  # Arabic
        assert "🚀" in content  # Emoji

    def test_emoji_preservation(self, txt_formatter, tmp_path):
        """Should preserve emoji characters correctly (AC-3.5-5)."""
        # GIVEN: Chunk with various emojis
        chunk_metadata = ChunkMetadata(
            entity_tags=[],
            quality=None,
            source_hash="emoji",
            document_type="text",
            word_count=5,
            token_count=8,
            created_at=datetime(2025, 11, 15, 10, 0, 0),
            processing_version="1.0.0",
            source_file=Path("emoji.txt"),
            config_snapshot={},
        )

        chunk = Chunk(
            id="emoji",
            text="Status: ✅ Success | ❌ Failed | ⚠️ Warning | 📊 Analytics | 🔒 Secure",
            document_id="emoji",
            position_index=0,
            token_count=8,
            word_count=5,
            entities=[],
            quality_score=0.88,
            metadata=chunk_metadata,
        )

        output_path = tmp_path / "emoji.txt"

        # WHEN: Formatting chunk
        txt_formatter.format_chunks(iter([chunk]), output_path)

        # THEN: Emojis should be preserved
        content = output_path.read_text(encoding="utf-8-sig")
        assert "✅" in content
        assert "❌" in content
        assert "⚠️" in content
        assert "📊" in content
        assert "🔒" in content


class TestArtifactValidation:
    """Test comprehensive artifact-free output (AC-3.5-6)."""

    def test_no_formatting_artifacts_comprehensive(
        self, txt_formatter, chunk_with_unicode, tmp_path
    ):
        """Should produce artifact-free output suitable for QA lint validation (AC-3.5-6)."""
        # GIVEN: Chunk with diverse content
        output_path = tmp_path / "artifact_check.txt"

        # WHEN: Formatting to TXT
        txt_formatter.format_chunks(iter([chunk_with_unicode]), output_path)

        # THEN: Should have no formatting artifacts
        content = output_path.read_text(encoding="utf-8-sig")

        # No BOM duplication (only at start)
        raw_bytes = output_path.read_bytes()
        assert raw_bytes.count(b"\xef\xbb\xbf") == 1

        # No JSON artifacts (except in metadata headers if enabled)
        text_only = content.split("━━━ CHUNK")[-1]  # Get last chunk
        assert "{" not in text_only
        assert "[" not in text_only

        # No ANSI codes
        assert "\x1b[" not in content
        assert "\033[" not in content

        # No HTML tags (unless in actual content)
        assert "<p>" not in content
        assert "</div>" not in content
