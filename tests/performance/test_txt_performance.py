"""Performance tests for TxtFormatter (Story 3.5 - ATDD RED PHASE).

Tests formatting latency baselines to ensure sub-second performance for typical documents.
Performance tests are non-blocking (won't block story completion if they fail).

Test Coverage:
    - Formatting latency for small documents (<1s target)
    - Formatting latency for large documents (<3s target)
    - Memory efficiency validation

These tests WILL FAIL until TxtFormatter is optimized (GREEN phase).
"""

import time
from datetime import datetime
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.P2,
    pytest.mark.performance,
    pytest.mark.output,
    pytest.mark.slow,
]

# These imports WILL FAIL in RED phase - this is expected
try:
    from data_extract.output.formatters.txt_formatter import TxtFormatter  # noqa: E402
except ImportError:
    TxtFormatter = None

from data_extract.chunk.models import Chunk, ChunkMetadata  # noqa: E402


@pytest.fixture
def txt_formatter():
    """Create TxtFormatter instance."""
    if TxtFormatter is None:
        pytest.skip("TxtFormatter not available yet (RED phase)")
    return TxtFormatter()


@pytest.fixture
def small_document_chunks() -> list[Chunk]:
    """Generate small document (10 chunks, ~500 words)."""
    chunks = []
    for i in range(10):
        chunk_metadata = ChunkMetadata(
            entity_tags=[],
            quality=None,
            source_hash=f"chunk_{i}",
            document_type="report",
            word_count=50,
            token_count=65,
            created_at=datetime(2025, 11, 15, 10, 0, 0),
            processing_version="1.0.0",
            source_file=Path(f"small_doc_{i}.txt"),
            config_snapshot={},
        )

        chunk = Chunk(
            id=f"chunk_{i:03d}",
            text=f"This is chunk {i} of a small test document. " * 10,
            document_id="small_doc",
            position_index=i,
            token_count=65,
            word_count=50,
            entities=[],
            quality_score=0.90,
            metadata=chunk_metadata,
        )
        chunks.append(chunk)

    return chunks


@pytest.fixture
def large_document_chunks() -> list[Chunk]:
    """Generate large document (100 chunks, ~5000 words)."""
    chunks = []
    for i in range(100):
        chunk_metadata = ChunkMetadata(
            entity_tags=[],
            quality=None,
            source_hash=f"chunk_{i}",
            document_type="report",
            word_count=50,
            token_count=65,
            created_at=datetime(2025, 11, 15, 10, 0, 0),
            processing_version="1.0.0",
            source_file=Path(f"large_doc_{i}.txt"),
            config_snapshot={},
        )

        chunk = Chunk(
            id=f"chunk_{i:03d}",
            text=f"This is chunk {i} of a large test document. " * 10,
            document_id="large_doc",
            position_index=i,
            token_count=65,
            word_count=50,
            entities=[],
            quality_score=0.90,
            metadata=chunk_metadata,
        )
        chunks.append(chunk)

    return chunks


class TestFormattingLatency:
    """Test formatting performance baselines."""

    def test_small_document_formatting_under_1_second(
        self, txt_formatter, small_document_chunks, tmp_path
    ):
        """Should format small document (10 chunks) in under 1 second."""
        # GIVEN: Small document (10 chunks)
        output_path = tmp_path / "small.txt"

        # WHEN: Formatting to TXT
        start = time.time()
        result = txt_formatter.format_chunks(iter(small_document_chunks), output_path)
        duration = time.time() - start

        # THEN: Should complete in under 1 second
        assert duration < 1.0, f"Formatting took {duration:.3f}s (target: <1.0s)"
        assert result.chunk_count == 10

    def test_large_document_formatting_under_3_seconds(
        self, txt_formatter, large_document_chunks, tmp_path
    ):
        """Should format large document (100 chunks) in under 3 seconds."""
        # GIVEN: Large document (100 chunks)
        output_path = tmp_path / "large.txt"

        # WHEN: Formatting to TXT
        start = time.time()
        result = txt_formatter.format_chunks(iter(large_document_chunks), output_path)
        duration = time.time() - start

        # THEN: Should complete in under 3 seconds
        assert duration < 3.0, f"Formatting took {duration:.3f}s (target: <3.0s)"
        assert result.chunk_count == 100
