"""Tests for core.exceptions module."""

import pytest

from src.data_extract.core.exceptions import (
    ConfigurationError,
    CriticalError,
    DataExtractError,
    ExtractionError,
    ProcessingError,
    ValidationError,
)

pytestmark = [pytest.mark.P0, pytest.mark.unit]


# ============================================================================
# Inheritance Tests - Verify exception hierarchy structure
# ============================================================================


def test_data_extract_error_inherits_from_exception():
    """Verify DataExtractError is a subclass of Exception."""
    assert issubclass(DataExtractError, Exception)


def test_processing_error_inherits_from_data_extract_error():
    """Verify ProcessingError inherits from DataExtractError."""
    assert issubclass(ProcessingError, DataExtractError)


def test_critical_error_inherits_from_data_extract_error():
    """Verify CriticalError inherits from DataExtractError."""
    assert issubclass(CriticalError, DataExtractError)


def test_configuration_error_inherits_from_critical_error():
    """Verify ConfigurationError inherits from CriticalError."""
    assert issubclass(ConfigurationError, CriticalError)


def test_extraction_error_inherits_from_processing_error():
    """Verify ExtractionError inherits from ProcessingError."""
    assert issubclass(ExtractionError, ProcessingError)


def test_validation_error_inherits_from_processing_error():
    """Verify ValidationError inherits from ProcessingError."""
    assert issubclass(ValidationError, ProcessingError)


# ============================================================================
# Exception Message Tests - Verify messages are passed correctly
# ============================================================================


def test_data_extract_error_message():
    """Verify DataExtractError preserves exception message."""
    message = "Test error message"
    with pytest.raises(DataExtractError, match=message):
        raise DataExtractError(message)


def test_processing_error_message():
    """Verify ProcessingError preserves exception message."""
    message = "Failed to process document"
    with pytest.raises(ProcessingError, match=message):
        raise ProcessingError(message)


def test_critical_error_message():
    """Verify CriticalError preserves exception message."""
    message = "Critical system failure"
    with pytest.raises(CriticalError, match=message):
        raise CriticalError(message)


def test_configuration_error_message():
    """Verify ConfigurationError preserves exception message."""
    message = "Invalid configuration: batch_size must be positive"
    with pytest.raises(ConfigurationError, match=message):
        raise ConfigurationError(message)


def test_extraction_error_message():
    """Verify ExtractionError preserves exception message."""
    message = "Failed to extract PDF: corrupted file"
    with pytest.raises(ExtractionError, match=message):
        raise ExtractionError(message)


def test_validation_error_message():
    """Verify ValidationError preserves exception message."""
    message = "Chunk quality 0.3 below threshold 0.5"
    with pytest.raises(ValidationError, match=message):
        raise ValidationError(message)


# ============================================================================
# Catch-All Pattern Tests - Verify base class catches all subclasses
# ============================================================================


def test_data_extract_error_catches_processing_error():
    """Verify DataExtractError catches ProcessingError."""
    with pytest.raises(DataExtractError):
        raise ProcessingError("Processing failed")


def test_data_extract_error_catches_critical_error():
    """Verify DataExtractError catches CriticalError."""
    with pytest.raises(DataExtractError):
        raise CriticalError("Critical failure")


def test_data_extract_error_catches_configuration_error():
    """Verify DataExtractError catches ConfigurationError."""
    with pytest.raises(DataExtractError):
        raise ConfigurationError("Invalid config")


def test_data_extract_error_catches_extraction_error():
    """Verify DataExtractError catches ExtractionError."""
    with pytest.raises(DataExtractError):
        raise ExtractionError("Extraction failed")


def test_data_extract_error_catches_validation_error():
    """Verify DataExtractError catches ValidationError."""
    with pytest.raises(DataExtractError):
        raise ValidationError("Validation failed")


def test_processing_error_catches_extraction_error():
    """Verify ProcessingError catches ExtractionError."""
    with pytest.raises(ProcessingError):
        raise ExtractionError("Extraction failed")


def test_processing_error_catches_validation_error():
    """Verify ProcessingError catches ValidationError."""
    with pytest.raises(ProcessingError):
        raise ValidationError("Validation failed")


def test_critical_error_catches_configuration_error():
    """Verify CriticalError catches ConfigurationError."""
    with pytest.raises(CriticalError):
        raise ConfigurationError("Invalid config")


# ============================================================================
# Exception Chaining Tests - Verify cause is preserved
# ============================================================================


def test_extraction_error_preserves_cause():
    """Verify ExtractionError preserves the original exception cause."""
    original_error = ValueError("Corrupted PDF structure")
    try:
        raise ExtractionError("Failed to extract PDF") from original_error
    except ExtractionError as e:
        assert e.__cause__ is original_error
        assert isinstance(e.__cause__, ValueError)


def test_configuration_error_preserves_cause():
    """Verify ConfigurationError preserves the original exception cause."""
    original_error = FileNotFoundError("config.yaml not found")
    try:
        raise ConfigurationError("Missing configuration file") from original_error
    except ConfigurationError as e:
        assert e.__cause__ is original_error
        assert isinstance(e.__cause__, FileNotFoundError)


def test_validation_error_preserves_cause():
    """Verify ValidationError preserves the original exception cause."""
    original_error = KeyError("required_field")
    try:
        raise ValidationError("Missing required field") from original_error
    except ValidationError as e:
        assert e.__cause__ is original_error
        assert isinstance(e.__cause__, KeyError)


# ============================================================================
# Isinstance Tests - Verify type relationships
# ============================================================================


def test_extraction_error_isinstance_checks():
    """Verify ExtractionError isinstance relationships."""
    error = ExtractionError("Test error")
    assert isinstance(error, ExtractionError)
    assert isinstance(error, ProcessingError)
    assert isinstance(error, DataExtractError)
    assert isinstance(error, Exception)
    # Negative checks
    assert not isinstance(error, CriticalError)
    assert not isinstance(error, ConfigurationError)
    assert not isinstance(error, ValidationError)


def test_validation_error_isinstance_checks():
    """Verify ValidationError isinstance relationships."""
    error = ValidationError("Test error")
    assert isinstance(error, ValidationError)
    assert isinstance(error, ProcessingError)
    assert isinstance(error, DataExtractError)
    assert isinstance(error, Exception)
    # Negative checks
    assert not isinstance(error, CriticalError)
    assert not isinstance(error, ConfigurationError)
    assert not isinstance(error, ExtractionError)


def test_configuration_error_isinstance_checks():
    """Verify ConfigurationError isinstance relationships."""
    error = ConfigurationError("Test error")
    assert isinstance(error, ConfigurationError)
    assert isinstance(error, CriticalError)
    assert isinstance(error, DataExtractError)
    assert isinstance(error, Exception)
    # Negative checks
    assert not isinstance(error, ProcessingError)
    assert not isinstance(error, ExtractionError)
    assert not isinstance(error, ValidationError)


def test_processing_error_isinstance_checks():
    """Verify ProcessingError isinstance relationships."""
    error = ProcessingError("Test error")
    assert isinstance(error, ProcessingError)
    assert isinstance(error, DataExtractError)
    assert isinstance(error, Exception)
    # Negative checks
    assert not isinstance(error, CriticalError)
    assert not isinstance(error, ConfigurationError)
    assert not isinstance(error, ExtractionError)
    assert not isinstance(error, ValidationError)


def test_critical_error_isinstance_checks():
    """Verify CriticalError isinstance relationships."""
    error = CriticalError("Test error")
    assert isinstance(error, CriticalError)
    assert isinstance(error, DataExtractError)
    assert isinstance(error, Exception)
    # Negative checks
    assert not isinstance(error, ProcessingError)
    assert not isinstance(error, ConfigurationError)
    assert not isinstance(error, ExtractionError)
    assert not isinstance(error, ValidationError)
