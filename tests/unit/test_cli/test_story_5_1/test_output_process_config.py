"""TDD RED Phase Tests: OutputConfig and ProcessConfig Models (AC-5.1-4).

These tests verify:
- OutputConfig model exists with format field
- ProcessConfig model exists with input_path field
- Both are Pydantic BaseModel subclasses

Domain: OutputConfig and ProcessConfig models
"""

import pytest

# P0: Critical path - always run
pytestmark = [
    pytest.mark.P0,
    pytest.mark.story_5_1,
    pytest.mark.unit,
    pytest.mark.cli,
]


@pytest.mark.unit
@pytest.mark.story_5_1
class TestOutputConfigModel:
    """Test OutputConfig model exists and validates correctly."""

    @pytest.mark.test_id("5.1-UNIT-001")
    def test_output_config_exists(self):
        """
        RED: Verify OutputConfig model can be imported.

        Given: The CLI models module
        When: We import OutputConfig
        Then: It should be a Pydantic model

        Expected RED failure: ImportError
        """
        # Given/When
        try:
            from pydantic import BaseModel

            from data_extract.cli.models import OutputConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # Then
        assert issubclass(OutputConfig, BaseModel)

    @pytest.mark.test_id("5.1-UNIT-002")
    def test_output_config_has_format_field(self):
        """
        RED: Verify OutputConfig has format field with validation.

        Given: OutputConfig model
        When: We create with format field
        Then: It should validate allowed formats

        Expected RED failure: format field missing
        """
        # Given
        try:
            from data_extract.cli.models import OutputConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        config = OutputConfig(format="json")

        # Then
        assert hasattr(config, "format")
        assert config.format == "json"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestProcessConfigModel:
    """Test ProcessConfig model for process command configuration."""

    @pytest.mark.test_id("5.1-UNIT-003")
    def test_process_config_exists(self):
        """
        RED: Verify ProcessConfig model can be imported.

        Given: The CLI models module
        When: We import ProcessConfig
        Then: It should be a Pydantic model

        Expected RED failure: ImportError
        """
        # Given/When
        try:
            from pydantic import BaseModel

            from data_extract.cli.models import ProcessConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # Then
        assert issubclass(ProcessConfig, BaseModel)

    @pytest.mark.test_id("5.1-UNIT-004")
    def test_process_config_has_input_path(self):
        """
        RED: Verify ProcessConfig has input_path field.

        Given: ProcessConfig model
        When: We create with input_path
        Then: It should store the path

        Expected RED failure: input_path field missing
        """
        # Given
        try:
            from pathlib import Path

            from data_extract.cli.models import ProcessConfig
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # When
        config = ProcessConfig(input_path=Path("/tmp/input"))

        # Then
        assert hasattr(config, "input_path")
