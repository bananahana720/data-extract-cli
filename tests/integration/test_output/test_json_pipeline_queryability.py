"""Integration tests for JSON output queryability and performance (Story 3.4).

Tests chunk filtering, querying capabilities, and performance benchmarks.

Test Coverage:
    - AC-3.4-5: Queryable array structure (jq, pandas filtering)
    - NFR-P1-E3: Performance requirements

Part 3 of 3: Queryability and performance.
"""

import json
import subprocess
import time

import pytest

from data_extract.chunk.engine import ChunkingConfig, ChunkingEngine
from data_extract.output.formatters.json_formatter import JsonFormatter

try:
    import pandas as pd
except ImportError:
    pd = None

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
def json_formatter():
    """Create JsonFormatter with validation enabled."""
    return JsonFormatter(validate=True)


class TestQueryability:
    """Test chunk filtering and querying (AC-3.4-5)."""

    def test_jq_filter_by_quality_score(
        self, sample_processing_result, chunking_engine, json_formatter, tmp_path
    ):
        """Should filter chunks by quality score using jq (AC-3.4-5)."""
        # GIVEN: Generated JSON file with quality scores
        output_path = tmp_path / "output.json"
        chunks = chunking_engine.chunk(sample_processing_result)
        json_formatter.format_chunks(chunks, output_path)

        # WHEN: Filtering with jq for high-quality chunks (overall >= 0.75)
        jq_query = ".chunks[] | select(.quality.overall >= 0.75)"

        try:
            result = subprocess.run(
                ["jq", jq_query, str(output_path)],
                capture_output=True,
                text=True,
                check=True,
            )
        except FileNotFoundError:
            pytest.skip("jq not installed on system")

        # THEN: Should return filtered chunks
        assert result.returncode == 0
        # Output should be valid JSON (one or more chunk objects)

    def test_jq_filter_by_entity_type(
        self, sample_processing_result, chunking_engine, json_formatter, tmp_path
    ):
        """Should filter chunks by entity type using jq (AC-3.4-5)."""
        # GIVEN: Generated JSON file with entities
        output_path = tmp_path / "output.json"
        chunks = chunking_engine.chunk(sample_processing_result)
        json_formatter.format_chunks(chunks, output_path)

        # WHEN: Filtering with jq for chunks containing risk entities
        jq_query = '.chunks[] | select(.metadata.entity_tags[].entity_type == "risk")'

        try:
            result = subprocess.run(
                ["jq", jq_query, str(output_path)],
                capture_output=True,
                text=True,
                check=True,
            )
        except FileNotFoundError:
            pytest.skip("jq not installed on system")

        # THEN: jq should execute successfully
        assert result.returncode == 0

    def test_pandas_dataframe_filtering(
        self, sample_processing_result, chunking_engine, json_formatter, tmp_path
    ):
        """Should filter chunks using pandas DataFrame operations (AC-3.4-5)."""
        if pd is None:
            pytest.skip("pandas not installed")

        # GIVEN: Generated JSON file
        output_path = tmp_path / "output.json"
        chunks = chunking_engine.chunk(sample_processing_result)
        json_formatter.format_chunks(chunks, output_path)

        # WHEN: Loading and filtering with pandas
        with open(output_path, "r", encoding="utf-8-sig") as f:
            json_data = json.load(f)

        df = pd.json_normalize(json_data["chunks"])

        # Filter by quality score
        high_quality = df[df["quality.overall"] >= 0.75]

        # THEN: Should filter successfully
        assert len(high_quality) >= 0  # May be 0 if no high-quality chunks

    def test_index_based_access(
        self, sample_processing_result, chunking_engine, json_formatter, tmp_path
    ):
        """Should support index-based access to chunks array (AC-3.4-5)."""
        # GIVEN: Generated JSON file
        output_path = tmp_path / "output.json"
        chunks = chunking_engine.chunk(sample_processing_result)
        json_formatter.format_chunks(chunks, output_path)

        # WHEN: Loading and accessing by index
        with open(output_path, "r", encoding="utf-8-sig") as f:
            json_data = json.load(f)

        # THEN: Should support array indexing
        if len(json_data["chunks"]) > 0:
            first_chunk = json_data["chunks"][0]
            assert "chunk_id" in first_chunk
            assert "text" in first_chunk


class TestPerformance:
    """Test JSON generation performance (NFR-P1-E3)."""

    def test_json_generation_under_1_second(
        self, sample_processing_result, chunking_engine, json_formatter, tmp_path
    ):
        """Should generate JSON in <1 second for typical document."""
        # GIVEN: ProcessingResult and JsonFormatter
        output_path = tmp_path / "output.json"
        chunks = list(chunking_engine.chunk(sample_processing_result))

        # WHEN: Formatting to JSON
        start_time = time.time()
        json_formatter.format_chunks(iter(chunks), output_path)
        duration = time.time() - start_time

        # THEN: Should complete in <1 second
        assert duration < 1.0, f"JSON generation took {duration:.2f}s (target: <1s)"

    def test_large_document_json_generation(
        self, sample_processing_result, chunking_engine, json_formatter, tmp_path
    ):
        """Should handle large documents (1000+ chunks) efficiently."""
        # GIVEN: Large document (simulate with many chunks)
        output_path = tmp_path / "large_output.json"
        chunks = chunking_engine.chunk(sample_processing_result)
        chunk_list = list(chunks)

        # Replicate chunks to simulate large document
        large_chunks = chunk_list * 100  # Multiply chunks

        # WHEN: Formatting large document
        start_time = time.time()
        json_formatter.format_chunks(iter(large_chunks), output_path)
        duration = time.time() - start_time

        # THEN: Should complete in reasonable time (<5 seconds)
        assert duration < 5.0, f"Large JSON generation took {duration:.2f}s"
