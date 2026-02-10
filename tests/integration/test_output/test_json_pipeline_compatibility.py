"""Integration tests for JSON output cross-library compatibility (Story 3.4).

Tests JSON parsing with multiple libraries and schema validation.

Test Coverage:
    - AC-3.4-2: Valid parsable JSON (cross-library compatibility)
    - AC-3.4-7: Schema validation integration

Part 2 of 3: Cross-library compatibility and validation.
"""

import json
import subprocess
from pathlib import Path

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


class TestCrossLibraryCompatibility:
    """Test JSON parsing with multiple libraries (AC-3.4-2)."""

    def test_pandas_read_json_compatibility(
        self, sample_processing_result, chunking_engine, json_formatter, tmp_path
    ):
        """Should parse JSON using pandas.read_json() (AC-3.4-2)."""
        if pd is None:
            pytest.skip("pandas not installed")

        # GIVEN: Generated JSON file
        output_path = tmp_path / "output.json"
        chunks = chunking_engine.chunk(sample_processing_result)
        json_formatter.format_chunks(chunks, output_path)

        # WHEN: Reading with pandas by normalizing chunks array
        with open(output_path, "r", encoding="utf-8-sig") as f:
            json_data = json.load(f)
        df = pd.json_normalize(json_data["chunks"])

        # THEN: Should create DataFrame with chunk rows
        assert not df.empty
        assert "text" in df.columns

    def test_jq_command_line_parsing(
        self, sample_processing_result, chunking_engine, json_formatter, tmp_path
    ):
        """Should parse JSON using jq command-line tool (AC-3.4-2)."""
        # GIVEN: Generated JSON file
        output_path = tmp_path / "output.json"
        chunks = chunking_engine.chunk(sample_processing_result)
        json_formatter.format_chunks(chunks, output_path)

        # WHEN: Parsing with jq (if available)
        try:
            result = subprocess.run(
                ["jq", ".", str(output_path)],
                capture_output=True,
                text=True,
                check=True,
            )
        except FileNotFoundError:
            pytest.skip("jq not installed on system")

        # THEN: jq should parse successfully
        assert result.returncode == 0
        assert len(result.stdout) > 0

    def test_nodejs_json_parse_compatibility(
        self, sample_processing_result, chunking_engine, json_formatter, tmp_path
    ):
        """Should parse JSON using Node.js JSON.parse() (AC-3.4-2)."""
        # GIVEN: Generated JSON file
        output_path = tmp_path / "output.json"
        chunks = chunking_engine.chunk(sample_processing_result)
        json_formatter.format_chunks(chunks, output_path)

        # WHEN: Parsing with Node.js (if available)
        # Convert Windows backslashes to forward slashes for Node.js
        node_path = str(output_path).replace("\\", "/")
        node_code = f"""
        const fs = require('fs');
        // Strip BOM (UTF-8 signature) that JsonFormatter writes for Windows compatibility
        const content = fs.readFileSync('{node_path}', 'utf8').replace(/^\\uFEFF/, '');
        const data = JSON.parse(content);
        console.log(JSON.stringify({{ chunks: data.chunks.length }}));
        """

        try:
            result = subprocess.run(
                ["node", "-e", node_code],
                capture_output=True,
                text=True,
                check=True,
            )
        except FileNotFoundError:
            pytest.skip("Node.js not installed on system")

        # THEN: Node.js should parse successfully
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert "chunks" in parsed


class TestSchemaValidationIntegration:
    """Test schema validation on real pipeline output (AC-3.4-7)."""

    def test_pipeline_output_validates_against_schema(
        self, sample_processing_result, chunking_engine, json_formatter, tmp_path
    ):
        """Should produce output that validates against JSON schema."""
        try:
            from jsonschema import validate
        except ImportError:
            pytest.skip("jsonschema library not installed")

        # GIVEN: Generated JSON file
        output_path = tmp_path / "output.json"
        chunks = chunking_engine.chunk(sample_processing_result)
        json_formatter.format_chunks(chunks, output_path)

        # Load schema
        project_root = Path(__file__).resolve().parents[3]
        schema_path = (
            project_root
            / "src"
            / "data_extract"
            / "output"
            / "schemas"
            / "data-extract-chunk.schema.json"
        )

        if not schema_path.exists():
            pytest.skip("Schema file not created yet")

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        # WHEN: Validating output
        with open(output_path, "r", encoding="utf-8-sig") as f:
            json_data = json.load(f)

        # THEN: Should validate without errors
        validate(instance=json_data, schema=schema)
