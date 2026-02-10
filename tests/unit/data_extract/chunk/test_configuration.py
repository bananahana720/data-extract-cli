"""Configuration validation tests (AC-3.1-3, AC-3.1-4)."""

from unittest.mock import Mock, patch

import pytest

try:
    from data_extract.chunk.engine import ChunkingEngine
except ImportError:
    ChunkingEngine = None

pytestmark = [pytest.mark.P0, pytest.mark.unit, pytest.mark.chunking]


class TestChunkSizeValidation:
    """Test chunk_size configuration validation."""

    @pytest.mark.parametrize(
        "size,should_warn",
        [(1, True), (64, True), (128, False), (512, False), (2048, False), (10000, True)],
    )
    def test_chunk_size_validation(self, size, should_warn):
        """Should validate chunk_size range and warn on extremes."""
        mock_segmenter = Mock()

        # Capture structlog warnings
        with patch("data_extract.chunk.engine.logger") as mock_logger:
            engine = ChunkingEngine(segmenter=mock_segmenter, chunk_size=size)

            if should_warn:
                # Verify warning was logged via structlog
                mock_logger.warning.assert_called()
                warning_call = mock_logger.warning.call_args
                assert "chunk_size" in str(warning_call).lower()
            assert engine.chunk_size == size


class TestOverlapValidation:
    """Test overlap_pct configuration validation."""

    @pytest.mark.parametrize(
        "overlap,should_warn", [(0.0, False), (0.15, False), (0.5, False), (0.6, True), (1.0, True)]
    )
    def test_overlap_validation(self, overlap, should_warn):
        """Should validate overlap_pct range and warn when > 0.5."""
        mock_segmenter = Mock()

        # Capture structlog warnings
        with patch("data_extract.chunk.engine.logger") as mock_logger:
            engine = ChunkingEngine(segmenter=mock_segmenter, overlap_pct=overlap)

            if should_warn:
                # Verify warning was logged via structlog
                mock_logger.warning.assert_called()
                warning_call = mock_logger.warning.call_args
                assert "overlap" in str(warning_call).lower()
            assert engine.overlap_pct == overlap

    def test_overlap_tokens_calculation(self):
        """Should calculate overlap_tokens = int(chunk_size * overlap_pct)."""
        mock_segmenter = Mock()
        engine = ChunkingEngine(segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.15)

        expected_overlap = int(512 * 0.15)  # 76 tokens
        assert engine.overlap_tokens == expected_overlap


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
