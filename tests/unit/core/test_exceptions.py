"""Unit tests for exception hierarchy.

Tests cover:
- Exception hierarchy (inheritance relationships)
- Raising and catching each exception type
- Base exception catches all subclasses
- Exception messages and documentation
"""

import pytest

from src.data_extract.core.exceptions import (
    ConfigurationError,
    CriticalError,
    DataExtractError,
    ExtractionError,
    ProcessingError,
    ValidationError,
)


class TestDataExtractError:
    """Test DataExtractError base exception."""

    def test_can_raise_and_catch(self):
        """Test DataExtractError can be raised and caught."""
        with pytest.raises(DataExtractError) as exc_info:
            raise DataExtractError("Base error message")
        assert "Base error message" in str(exc_info.value)

    def test_inherits_from_exception(self):
        """Test DataExtractError inherits from Exception."""
        assert issubclass(DataExtractError, Exception)

    def test_catches_all_subclasses(self):
        """Test DataExtractError catches all tool-specific exceptions."""
        # Should catch ProcessingError
        with pytest.raises(DataExtractError):
            raise ProcessingError("Processing failed")

        # Should catch CriticalError
        with pytest.raises(DataExtractError):
            raise CriticalError("Critical failure")

        # Should catch ConfigurationError
        with pytest.raises(DataExtractError):
            raise ConfigurationError("Config error")

        # Should catch ExtractionError
        with pytest.raises(DataExtractError):
            raise ExtractionError("Extraction failed")

        # Should catch ValidationError
        with pytest.raises(DataExtractError):
            raise ValidationError("Validation failed")


class TestProcessingError:
    """Test ProcessingError (recoverable) exception."""

    def test_can_raise_and_catch(self):
        """Test ProcessingError can be raised and caught."""
        with pytest.raises(ProcessingError) as exc_info:
            raise ProcessingError("Processing failed for file.pdf")
        assert "Processing failed for file.pdf" in str(exc_info.value)

    def test_inherits_from_data_extract_error(self):
        """Test ProcessingError extends DataExtractError."""
        assert issubclass(ProcessingError, DataExtractError)

    def test_catch_specific_exception(self):
        """Test catching ProcessingError specifically."""
        with pytest.raises(ProcessingError):
            raise ProcessingError("File corrupted")

    def test_catches_subclasses(self):
        """Test ProcessingError catches ExtractionError and ValidationError."""
        # Should catch ExtractionError
        with pytest.raises(ProcessingError):
            raise ExtractionError("Extraction failed")

        # Should catch ValidationError
        with pytest.raises(ProcessingError):
            raise ValidationError("Validation failed")


class TestCriticalError:
    """Test CriticalError (unrecoverable) exception."""

    def test_can_raise_and_catch(self):
        """Test CriticalError can be raised and caught."""
        with pytest.raises(CriticalError) as exc_info:
            raise CriticalError("System failure")
        assert "System failure" in str(exc_info.value)

    def test_inherits_from_data_extract_error(self):
        """Test CriticalError extends DataExtractError."""
        assert issubclass(CriticalError, DataExtractError)

    def test_catch_specific_exception(self):
        """Test catching CriticalError specifically."""
        with pytest.raises(CriticalError):
            raise CriticalError("Out of memory")

    def test_catches_configuration_error(self):
        """Test CriticalError catches ConfigurationError subclass."""
        with pytest.raises(CriticalError):
            raise ConfigurationError("Config missing")


class TestConfigurationError:
    """Test ConfigurationError exception."""

    def test_can_raise_and_catch(self):
        """Test ConfigurationError can be raised and caught."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("Config file not found")
        assert "Config file not found" in str(exc_info.value)

    def test_inherits_from_critical_error(self):
        """Test ConfigurationError extends CriticalError."""
        assert issubclass(ConfigurationError, CriticalError)

    def test_inherits_from_data_extract_error(self):
        """Test ConfigurationError ultimately extends DataExtractError."""
        assert issubclass(ConfigurationError, DataExtractError)

    def test_catch_as_critical_error(self):
        """Test ConfigurationError can be caught as CriticalError."""
        with pytest.raises(CriticalError):
            raise ConfigurationError("Invalid config value")

    def test_catch_as_data_extract_error(self):
        """Test ConfigurationError can be caught as DataExtractError."""
        with pytest.raises(DataExtractError):
            raise ConfigurationError("Missing required key")


class TestExtractionError:
    """Test ExtractionError exception."""

    def test_can_raise_and_catch(self):
        """Test ExtractionError can be raised and caught."""
        with pytest.raises(ExtractionError) as exc_info:
            raise ExtractionError("Failed to extract PDF")
        assert "Failed to extract PDF" in str(exc_info.value)

    def test_inherits_from_processing_error(self):
        """Test ExtractionError extends ProcessingError."""
        assert issubclass(ExtractionError, ProcessingError)

    def test_inherits_from_data_extract_error(self):
        """Test ExtractionError ultimately extends DataExtractError."""
        assert issubclass(ExtractionError, DataExtractError)

    def test_catch_as_processing_error(self):
        """Test ExtractionError can be caught as ProcessingError."""
        with pytest.raises(ProcessingError):
            raise ExtractionError("Corrupted document")

    def test_catch_as_data_extract_error(self):
        """Test ExtractionError can be caught as DataExtractError."""
        with pytest.raises(DataExtractError):
            raise ExtractionError("Unsupported format")


class TestValidationError:
    """Test ValidationError exception."""

    def test_can_raise_and_catch(self):
        """Test ValidationError can be raised and caught."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Schema validation failed")
        assert "Schema validation failed" in str(exc_info.value)

    def test_inherits_from_processing_error(self):
        """Test ValidationError extends ProcessingError."""
        assert issubclass(ValidationError, ProcessingError)

    def test_inherits_from_data_extract_error(self):
        """Test ValidationError ultimately extends DataExtractError."""
        assert issubclass(ValidationError, DataExtractError)

    def test_catch_as_processing_error(self):
        """Test ValidationError can be caught as ProcessingError."""
        with pytest.raises(ProcessingError):
            raise ValidationError("Quality too low")

    def test_catch_as_data_extract_error(self):
        """Test ValidationError can be caught as DataExtractError."""
        with pytest.raises(DataExtractError):
            raise ValidationError("Missing required field")


class TestExceptionHierarchy:
    """Test overall exception hierarchy relationships."""

    def test_hierarchy_structure(self):
        """Test complete exception hierarchy structure."""
        # DataExtractError is base
        assert issubclass(ProcessingError, DataExtractError)
        assert issubclass(CriticalError, DataExtractError)

        # ProcessingError branch
        assert issubclass(ExtractionError, ProcessingError)
        assert issubclass(ValidationError, ProcessingError)

        # CriticalError branch
        assert issubclass(ConfigurationError, CriticalError)

    def test_catch_all_with_base_exception(self):
        """Test DataExtractError catches all custom exceptions."""
        exceptions_to_test = [
            ProcessingError("test"),
            CriticalError("test"),
            ConfigurationError("test"),
            ExtractionError("test"),
            ValidationError("test"),
        ]

        for exc in exceptions_to_test:
            with pytest.raises(DataExtractError):
                raise exc

    def test_processing_error_branch(self):
        """Test ProcessingError catches recoverable errors."""
        recoverable_errors = [
            ExtractionError("test"),
            ValidationError("test"),
        ]

        for exc in recoverable_errors:
            with pytest.raises(ProcessingError):
                raise exc

    def test_critical_error_branch(self):
        """Test CriticalError catches unrecoverable errors."""
        unrecoverable_errors = [
            ConfigurationError("test"),
        ]

        for exc in unrecoverable_errors:
            with pytest.raises(CriticalError):
                raise exc

    def test_exception_messages_preserved(self):
        """Test exception messages are preserved when raised."""
        test_message = "Specific error details for debugging"

        with pytest.raises(ExtractionError) as exc_info:
            raise ExtractionError(test_message)
        assert test_message in str(exc_info.value)

        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError(test_message)
        assert test_message in str(exc_info.value)
