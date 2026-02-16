"""Integration tests for end-to-end JSON output pipeline (Story 3.4).

Tests complete pipeline from ProcessingResult → ChunkingEngine → JsonFormatter → JSON file,
including metadata accuracy and deterministic output.

Test Coverage:
    - AC-3.4-2: Valid parsable JSON
    - AC-3.4-6: Metadata accuracy (sources, chunk_count, configuration)
    - Deterministic output generation

Part 1 of 3: Basic pipeline and metadata.
"""

import json

import pytest

from data_extract.chunk.engine import ChunkingConfig, ChunkingEngine
from data_extract.output.formatters.json_formatter import JsonFormatter

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


class TestEndToEndPipeline:
    """Test complete pipeline: ProcessingResult → Chunks → JSON file (AC-3.4-2, AC-3.4-5)."""

    def test_complete_pipeline_processing_result_to_json(
        self, sample_processing_result, chunking_engine, json_formatter, tmp_path
    ):
        """Should process document from ProcessingResult through to JSON file."""
        # GIVEN: ProcessingResult from normalization stage
        output_path = tmp_path / "output.json"

        # WHEN: Chunking and formatting to JSON
        chunks = chunking_engine.chunk(sample_processing_result)
        json_formatter.format_chunks(chunks, output_path)

        # THEN: JSON file should exist and be parsable
        assert output_path.exists()

        with open(output_path, "r", encoding="utf-8-sig") as f:
            json_data = json.load(f)

        assert "metadata" in json_data
        assert "chunks" in json_data
        assert len(json_data["chunks"]) > 0

    def test_json_parsing_with_python_json_module(
        self, sample_processing_result, chunking_engine, json_formatter, tmp_path
    ):
        """Should parse JSON using Python's json.load() (AC-3.4-2)."""
        # GIVEN: Generated JSON file
        output_path = tmp_path / "output.json"
        chunks = chunking_engine.chunk(sample_processing_result)
        json_formatter.format_chunks(chunks, output_path)

        # WHEN: Parsing with json.load()
        with open(output_path, "r", encoding="utf-8-sig") as f:
            json_data = json.load(f)

        # THEN: Should parse successfully
        assert isinstance(json_data, dict)
        assert "chunks" in json_data


class TestMetadataAccuracy:
    """Test metadata header accuracy (AC-3.4-6)."""

    def test_source_documents_list_matches_input(
        self, sample_processing_result, chunking_engine, json_formatter, tmp_path
    ):
        """Should list source documents accurately in metadata."""
        # GIVEN: Generated JSON file
        output_path = tmp_path / "output.json"
        chunks = chunking_engine.chunk(sample_processing_result)
        json_formatter.format_chunks(chunks, output_path)

        # WHEN: Reading metadata
        with open(output_path, "r", encoding="utf-8-sig") as f:
            json_data = json.load(f)

        # THEN: Source documents should be listed
        assert "source_documents" in json_data["metadata"]
        assert isinstance(json_data["metadata"]["source_documents"], list)

    def test_chunk_count_matches_actual_chunks(
        self, sample_processing_result, chunking_engine, json_formatter, tmp_path
    ):
        """Should set chunk_count to actual number of chunks (AC-3.4-6)."""
        # GIVEN: Generated JSON file
        output_path = tmp_path / "output.json"
        chunks = chunking_engine.chunk(sample_processing_result)
        json_formatter.format_chunks(chunks, output_path)

        # WHEN: Reading metadata and chunks
        with open(output_path, "r", encoding="utf-8-sig") as f:
            json_data = json.load(f)

        # THEN: chunk_count should match actual chunks
        assert json_data["metadata"]["chunk_count"] == len(json_data["chunks"])

    def test_configuration_reflects_chunking_params(
        self, sample_processing_result, chunking_engine, json_formatter, tmp_path
    ):
        """Should reflect actual chunking configuration (AC-3.4-6)."""
        # GIVEN: ChunkingEngine with specific config
        output_path = tmp_path / "output.json"
        chunks = chunking_engine.chunk(sample_processing_result)
        json_formatter.format_chunks(chunks, output_path)

        # WHEN: Reading metadata configuration
        with open(output_path, "r", encoding="utf-8-sig") as f:
            json_data = json.load(f)

        config = json_data["metadata"]["configuration"]

        # THEN: Configuration should match ChunkingEngine settings
        assert config["chunk_size"] == 512
        assert config["overlap_pct"] == 0.15


class TestDeterminism:
    """Test deterministic output generation (AC-3.4-2)."""

    def test_same_input_produces_same_json(
        self, sample_processing_result, chunking_engine, json_formatter, tmp_path
    ):
        """Should produce identical JSON for same input (excluding timestamp)."""
        # GIVEN: Same ProcessingResult processed twice
        output_path_1 = tmp_path / "output1.json"
        output_path_2 = tmp_path / "output2.json"

        chunks_1 = chunking_engine.chunk(sample_processing_result)
        json_formatter.format_chunks(chunks_1, output_path_1)

        chunks_2 = chunking_engine.chunk(sample_processing_result)
        json_formatter.format_chunks(chunks_2, output_path_2)

        # WHEN: Loading both JSON files
        with open(output_path_1, "r", encoding="utf-8-sig") as f:
            json_data_1 = json.load(f)

        with open(output_path_2, "r", encoding="utf-8-sig") as f:
            json_data_2 = json.load(f)

        # THEN: Chunks should be identical (excluding processing_timestamp)
        # Remove timestamps for comparison
        del json_data_1["metadata"]["processing_timestamp"]
        del json_data_2["metadata"]["processing_timestamp"]

        # Chunk content should be identical
        assert len(json_data_1["chunks"]) == len(json_data_2["chunks"])

        for chunk1, chunk2 in zip(json_data_1["chunks"], json_data_2["chunks"]):
            assert chunk1["text"] == chunk2["text"]
            assert chunk1["chunk_id"] == chunk2["chunk_id"]
