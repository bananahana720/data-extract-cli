"""Unit tests for base formatter module.

Tests for:
- FormattingResult dataclass creation and defaults
- BaseFormatter ABC interface and abstract method enforcement
- Subclass implementation requirements
"""

from pathlib import Path
from typing import Any, List

import pytest

from data_extract.core.models import Chunk
from data_extract.output.formatters.base import BaseFormatter, FormattingResult

# ============================================================================
# FORMATTINGRESULT DATACLASS TESTS
# ============================================================================


@pytest.mark.unit
def test_formatting_result_creation_with_all_fields() -> None:
    """Test FormattingResult creation with all fields specified."""
    result = FormattingResult(
        output_path=Path("/tmp/output.txt"),
        chunk_count=10,
        total_size=5000,
        metadata={"author": "test", "version": "1.0"},
        format_type="json",
        duration_seconds=2.5,
        errors=["Error 1", "Error 2"],
    )

    assert result.output_path == Path("/tmp/output.txt")
    assert result.chunk_count == 10
    assert result.total_size == 5000
    assert result.metadata == {"author": "test", "version": "1.0"}
    assert result.format_type == "json"
    assert result.duration_seconds == 2.5
    assert result.errors == ["Error 1", "Error 2"]


@pytest.mark.unit
def test_formatting_result_default_errors_empty_list() -> None:
    """Test FormattingResult initializes errors as empty list when None."""
    result = FormattingResult(
        output_path=Path("/tmp/output.txt"),
        chunk_count=5,
        total_size=2500,
        metadata={},
    )

    # errors should default to empty list via __post_init__
    assert result.errors == []
    assert isinstance(result.errors, list)


@pytest.mark.unit
def test_formatting_result_default_format_type() -> None:
    """Test FormattingResult default format_type is 'txt'."""
    result = FormattingResult(
        output_path=Path("/tmp/output.txt"),
        chunk_count=5,
        total_size=2500,
        metadata={},
    )

    assert result.format_type == "txt"


@pytest.mark.unit
def test_formatting_result_default_duration_seconds() -> None:
    """Test FormattingResult default duration_seconds is 0.0."""
    result = FormattingResult(
        output_path=Path("/tmp/output.txt"),
        chunk_count=5,
        total_size=2500,
        metadata={},
    )

    assert result.duration_seconds == 0.0


@pytest.mark.unit
def test_formatting_result_with_errors_list() -> None:
    """Test FormattingResult with explicit errors list."""
    errors = [
        "Failed to format chunk 3",
        "Invalid metadata for chunk 7",
    ]

    result = FormattingResult(
        output_path=Path("/tmp/output.txt"),
        chunk_count=10,
        total_size=5000,
        metadata={},
        errors=errors,
    )

    assert result.errors == errors
    assert len(result.errors) == 2


@pytest.mark.unit
def test_formatting_result_immutability() -> None:
    """Test FormattingResult is frozen (immutable)."""
    result = FormattingResult(
        output_path=Path("/tmp/output.txt"),
        chunk_count=5,
        total_size=2500,
        metadata={},
    )

    # Attempting to modify should raise AttributeError (dataclass frozen)
    with pytest.raises(AttributeError):
        result.chunk_count = 10  # type: ignore[misc]


# ============================================================================
# BASEFORMATTER ABC TESTS
# ============================================================================


@pytest.mark.unit
def test_base_formatter_cannot_be_instantiated() -> None:
    """Test BaseFormatter ABC cannot be instantiated directly."""
    # Attempting to instantiate abstract class should raise TypeError
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        BaseFormatter()  # type: ignore


@pytest.mark.unit
def test_base_formatter_subclass_without_implementation_fails() -> None:
    """Test subclass without format_chunks() implementation fails."""

    class IncompleteFormatter(BaseFormatter):
        """Incomplete formatter missing format_chunks() implementation."""

        pass

    # Attempting to instantiate should raise TypeError
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IncompleteFormatter()  # type: ignore


@pytest.mark.unit
def test_base_formatter_subclass_with_implementation_works(sample_chunk: Chunk) -> None:
    """Test subclass implementing format_chunks() can be instantiated."""

    class ConcreteFormatter(BaseFormatter):
        """Concrete formatter with format_chunks() implementation."""

        def format_chunks(
            self, chunks: List[Any], output_path: Path, **kwargs: Any
        ) -> FormattingResult:
            """Mock implementation of format_chunks()."""
            return FormattingResult(
                output_path=output_path,
                chunk_count=len(chunks),
                total_size=sum(len(c.text) for c in chunks),
                metadata={"formatter": "ConcreteFormatter"},
                format_type="txt",
            )

    # Should instantiate successfully
    formatter = ConcreteFormatter()
    assert isinstance(formatter, BaseFormatter)

    # Should be able to call format_chunks()
    result = formatter.format_chunks(
        chunks=[sample_chunk],
        output_path=Path("/tmp/test.txt"),
    )

    assert isinstance(result, FormattingResult)
    assert result.chunk_count == 1
    assert result.output_path == Path("/tmp/test.txt")


@pytest.mark.unit
def test_base_formatter_format_chunks_signature() -> None:
    """Test BaseFormatter.format_chunks() has correct signature."""

    class TestFormatter(BaseFormatter):
        """Test formatter for signature validation."""

        def format_chunks(
            self, chunks: List[Any], output_path: Path, **kwargs: Any
        ) -> FormattingResult:
            """Implementation for testing."""
            return FormattingResult(
                output_path=output_path,
                chunk_count=0,
                total_size=0,
                metadata={},
            )

    formatter = TestFormatter()

    # Verify method exists and has correct signature
    assert hasattr(formatter, "format_chunks")
    assert callable(formatter.format_chunks)

    # Test can be called with required parameters
    result = formatter.format_chunks(chunks=[], output_path=Path("/tmp/test.txt"))
    assert isinstance(result, FormattingResult)


@pytest.mark.unit
def test_base_formatter_format_chunks_kwargs_support(sample_chunk: Chunk) -> None:
    """Test BaseFormatter.format_chunks() supports **kwargs."""

    class KwargsFormatter(BaseFormatter):
        """Formatter that uses kwargs."""

        def format_chunks(
            self, chunks: List[Any], output_path: Path, **kwargs: Any
        ) -> FormattingResult:
            """Implementation that uses kwargs."""
            include_metadata = kwargs.get("include_metadata", False)
            metadata = {"include_metadata": include_metadata} if include_metadata else {}

            return FormattingResult(
                output_path=output_path,
                chunk_count=len(chunks),
                total_size=0,
                metadata=metadata,
            )

    formatter = KwargsFormatter()

    # Test without kwargs
    result1 = formatter.format_chunks(
        chunks=[sample_chunk],
        output_path=Path("/tmp/test1.txt"),
    )
    assert result1.metadata == {}

    # Test with kwargs
    result2 = formatter.format_chunks(
        chunks=[sample_chunk],
        output_path=Path("/tmp/test2.txt"),
        include_metadata=True,
    )
    assert result2.metadata == {"include_metadata": True}
