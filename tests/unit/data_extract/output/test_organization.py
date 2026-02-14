"""Tests for output organization module.

Organization module provides strategies for organizing output files
(BY_DOCUMENT, BY_ENTITY, FLAT) and the Organizer class that implements
the organization logic.
"""

from pathlib import Path
from typing import List

import pytest

from data_extract.core.models import Chunk
from data_extract.output.organization import (
    OrganizationResult,
    OrganizationStrategy,
    Organizer,
)

# ============================================================================
# TEST MARKERS
# ============================================================================

pytestmark = [pytest.mark.P0, pytest.mark.unit]


# ============================================================================
# ENUM TESTS
# ============================================================================


def test_organization_strategy_enum_values_exist() -> None:
    """OrganizationStrategy enum has BY_DOCUMENT, BY_ENTITY, and FLAT values."""
    assert hasattr(OrganizationStrategy, "BY_DOCUMENT")
    assert hasattr(OrganizationStrategy, "BY_ENTITY")
    assert hasattr(OrganizationStrategy, "FLAT")


def test_organization_strategy_is_string_enum() -> None:
    """OrganizationStrategy enum values are strings."""
    assert OrganizationStrategy.BY_DOCUMENT.value == "by_document"
    assert OrganizationStrategy.BY_ENTITY.value == "by_entity"
    assert OrganizationStrategy.FLAT.value == "flat"


# ============================================================================
# DATACLASS TESTS
# ============================================================================


def test_organization_result_dataclass_fields(tmp_path: Path) -> None:
    """OrganizationResult has expected fields with correct types."""
    result = OrganizationResult(
        strategy=OrganizationStrategy.FLAT,
        output_dir=tmp_path,
        files_created=[tmp_path / "output.txt"],
        manifest_path=tmp_path / "manifest.json",
        metadata={"key": "value"},
    )

    assert result.strategy == OrganizationStrategy.FLAT
    assert result.output_dir == tmp_path
    assert result.files_created == [tmp_path / "output.txt"]
    assert result.manifest_path == tmp_path / "manifest.json"
    assert result.metadata == {"key": "value"}


def test_organization_result_immutability(tmp_path: Path) -> None:
    """OrganizationResult is frozen and immutable."""
    result = OrganizationResult(
        strategy=OrganizationStrategy.FLAT,
        output_dir=tmp_path,
    )

    with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
        result.strategy = OrganizationStrategy.BY_DOCUMENT  # type: ignore[misc]


def test_organization_result_default_fields(tmp_path: Path) -> None:
    """OrganizationResult has proper default values for optional fields."""
    result = OrganizationResult(
        strategy=OrganizationStrategy.BY_DOCUMENT,
        output_dir=tmp_path,
    )

    assert result.files_created == []
    assert result.manifest_path is None
    assert result.metadata == {}


# ============================================================================
# ORGANIZER CLASS TESTS
# ============================================================================


def test_organizer_initialization() -> None:
    """Organizer can be instantiated with default constructor."""
    organizer = Organizer()
    assert organizer is not None


def test_organize_with_flat_strategy(sample_chunks: List[Chunk], tmp_path: Path) -> None:
    """Organizer.organize() with FLAT strategy returns OrganizationResult."""
    organizer = Organizer()
    output_dir = tmp_path / "flat_output"

    result = organizer.organize(
        chunks=sample_chunks,
        output_dir=output_dir,
        strategy=OrganizationStrategy.FLAT,
        format_type="txt",
    )

    assert isinstance(result, OrganizationResult)
    assert result.strategy == OrganizationStrategy.FLAT
    assert result.output_dir == output_dir


def test_organize_with_by_document_strategy(sample_chunks: List[Chunk], tmp_path: Path) -> None:
    """Organizer.organize() with BY_DOCUMENT strategy (placeholder implementation)."""
    organizer = Organizer()
    output_dir = tmp_path / "by_document_output"

    result = organizer.organize(
        chunks=sample_chunks,
        output_dir=output_dir,
        strategy=OrganizationStrategy.BY_DOCUMENT,
        format_type="json",
    )

    assert isinstance(result, OrganizationResult)
    assert result.strategy == OrganizationStrategy.BY_DOCUMENT
    assert result.output_dir == output_dir
    # Placeholder implementation returns empty files_created
    assert result.files_created == []


def test_organize_with_by_entity_strategy(sample_chunks: List[Chunk], tmp_path: Path) -> None:
    """Organizer.organize() with BY_ENTITY strategy (placeholder implementation)."""
    organizer = Organizer()
    output_dir = tmp_path / "by_entity_output"

    result = organizer.organize(
        chunks=sample_chunks,
        output_dir=output_dir,
        strategy=OrganizationStrategy.BY_ENTITY,
        format_type="csv",
    )

    assert isinstance(result, OrganizationResult)
    assert result.strategy == OrganizationStrategy.BY_ENTITY
    assert result.output_dir == output_dir
    # Placeholder implementation returns empty files_created
    assert result.files_created == []


def test_organize_creates_output_directory(sample_chunks: List[Chunk], tmp_path: Path) -> None:
    """Organizer.organize() creates output directory if it doesn't exist."""
    organizer = Organizer()
    output_dir = tmp_path / "nested" / "deep" / "output"

    # Verify directory doesn't exist
    assert not output_dir.exists()

    organizer.organize(
        chunks=sample_chunks,
        output_dir=output_dir,
        strategy=OrganizationStrategy.FLAT,
        format_type="txt",
    )

    # Verify directory was created
    assert output_dir.exists()
    assert output_dir.is_dir()


def test_organize_accepts_format_type_parameter(sample_chunks: List[Chunk], tmp_path: Path) -> None:
    """Organizer.organize() accepts format_type parameter for future use."""
    organizer = Organizer()
    output_dir = tmp_path / "output"

    # Should not raise error with different format types
    for format_type in ["txt", "json", "csv"]:
        result = organizer.organize(
            chunks=sample_chunks,
            output_dir=output_dir,
            strategy=OrganizationStrategy.FLAT,
            format_type=format_type,
        )
        assert isinstance(result, OrganizationResult)


def test_organize_accepts_kwargs(sample_chunks: List[Chunk], tmp_path: Path) -> None:
    """Organizer.organize() accepts additional kwargs for future use."""
    organizer = Organizer()
    output_dir = tmp_path / "output"

    # Should not raise error with additional kwargs
    result = organizer.organize(
        chunks=sample_chunks,
        output_dir=output_dir,
        strategy=OrganizationStrategy.FLAT,
        format_type="txt",
        validate=True,
        include_metadata=False,
        custom_option="value",
    )

    assert isinstance(result, OrganizationResult)
