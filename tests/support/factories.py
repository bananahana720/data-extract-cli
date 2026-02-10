"""
Test factories for creating test data.

Provides factory functions for creating test chunks, documents, and metadata
with configurable parameters.
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from data_extract.chunk.models import Chunk
from data_extract.core.models import Metadata


def chunks_factory(
    count: int = 1,
    source_file: Optional[Path] = None,
    quality_score: float = 0.85,
    document_id: str = "test_doc_001",
) -> List[Chunk]:
    """
    Factory function for creating test chunks.

    Args:
        count: Number of chunks to create
        source_file: Source file path (defaults to test.pdf)
        quality_score: Quality score for chunks (0.0-1.0)
        document_id: Document ID for chunks

    Returns:
        List of Chunk objects with realistic test data
    """
    if source_file is None:
        source_file = Path("/data/test.pdf")

    chunks = []
    for i in range(count):
        # Generate realistic content
        text = (
            f"This is test chunk {i+1} of {count}. "
            f"It contains sample content for testing purposes. "
            f"The chunk includes entities like RISK-{i+1:03d} and CTRL-{i+1:03d}. "
            "This text is long enough to simulate real document chunks "
            "while remaining simple enough for test assertions."
        )

        # Calculate word and token counts
        word_count = len(text.split())
        token_count = len(text) // 4  # Simple estimation

        # Create metadata
        metadata = Metadata(
            source_file=source_file,
            file_hash=hashlib.sha256(text.encode()).hexdigest(),
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0.0",
            entity_tags=[f"RISK-{i+1:03d}", f"CTRL-{i+1:03d}"],
        )

        # Create chunk
        chunk = Chunk(
            id=f"{document_id}_chunk_{i:03d}",
            text=text,
            document_id=document_id,
            position_index=i,
            word_count=word_count,
            token_count=token_count,
            quality_score=quality_score,
            entities=[],
            metadata=metadata,
            section_context=f"Section {i // 3 + 1}",
            readability_scores={
                "flesch_reading_ease": 60.0 + (i % 20),
                "flesch_kincaid_grade": 10.0 + (i % 5),
            },
        )

        chunks.append(chunk)

    return chunks
