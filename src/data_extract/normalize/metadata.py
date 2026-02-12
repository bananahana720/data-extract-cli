"""Metadata enrichment module for Story 2.6.

This module provides metadata enrichment functionality for the normalization pipeline:
- calculate_file_hash(): SHA-256 file hashing with chunked reading for memory efficiency
- aggregate_entity_tags(): Extract and count entities by type
- aggregate_quality_scores(): Aggregate quality metrics from validation
- serialize_config_snapshot(): Serialize configuration for reproducibility
- MetadataEnricher: Main enrichment orchestrator class

All functions support the continue-on-error pattern (ADR-006) and structured logging.
"""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from ..core.exceptions import ProcessingError
from ..core.models import (
    Entity,
    Metadata,
    ValidationReport,
)
from .config import NormalizationConfig


def calculate_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
    """Calculate SHA-256 hash of a file using chunked reading.

    Uses chunked reading (default 8KB chunks) for memory efficiency with large files.
    Ensures deterministic hashing for audit trail integrity.

    Args:
        file_path: Path to file to hash
        chunk_size: Size of chunks to read (default 8192 bytes = 8KB)

    Returns:
        SHA-256 hash as 64-character hexadecimal string

    Raises:
        ProcessingError: If file cannot be read (missing, permission denied, I/O error)

    Examples:
        >>> file_hash = calculate_file_hash(Path("document.pdf"))
        >>> assert len(file_hash) == 64  # SHA-256 produces 64 hex characters
        >>> # Same file always produces same hash (determinism)
        >>> hash1 = calculate_file_hash(Path("document.pdf"))
        >>> hash2 = calculate_file_hash(Path("document.pdf"))
        >>> assert hash1 == hash2

    Story: 2.6 - Metadata Enrichment Framework
    AC: 2.6.1 (file hash), 2.6.8 (audit trail)
    """
    if not file_path.exists():
        raise ProcessingError(f"File not found for hashing: {file_path}")

    if not file_path.is_file():
        raise ProcessingError(f"Path is not a file: {file_path}")

    try:
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read file in chunks for memory efficiency
            while chunk := f.read(chunk_size):
                sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    except PermissionError as e:
        raise ProcessingError(f"Permission denied reading file: {file_path}") from e
    except OSError as e:
        raise ProcessingError(f"I/O error reading file: {file_path}") from e
    except Exception as e:
        raise ProcessingError(f"Unexpected error hashing file: {file_path}") from e


def aggregate_entity_tags(entities: List[Entity]) -> Tuple[List[str], Dict[str, int]]:
    """Aggregate entity tags and counts by entity type.

    Extracts entity type and ID from Entity objects, formats as "EntityType-ID"
    (e.g., "Risk-123", "Control-456"), and counts entities by EntityType.

    Args:
        entities: List of Entity objects to aggregate

    Returns:
        Tuple of (entity_tags, entity_counts):
            - entity_tags: List of formatted entity IDs (e.g., ["Risk-123", "Control-456"])
            - entity_counts: Dict mapping entity type to count (e.g., {"risk": 2, "control": 1})

    Examples:
        >>> entities = [
        ...     Entity(type=EntityType.RISK, id="Risk-123", text="...", confidence=0.9, location={}),
        ...     Entity(type=EntityType.CONTROL, id="Control-456", text="...", confidence=0.9, location={}),
        ... ]
        >>> tags, counts = aggregate_entity_tags(entities)
        >>> assert tags == ["Risk-123", "Control-456"]
        >>> assert counts == {"risk": 1, "control": 1}

    Story: 2.6 - Metadata Enrichment Framework
    AC: 2.6.4 (entity tags)
    """
    entity_tags: List[str] = []
    entity_counts: Dict[str, int] = {}

    for entity in entities:
        # Format entity tag as "EntityType-ID" (e.g., "Risk-123")
        entity_tags.append(entity.id)

        # Count entities by type (use lowercase enum value)
        entity_type_str = entity.type.value  # Get string value from enum
        entity_counts[entity_type_str] = entity_counts.get(entity_type_str, 0) + 1

    return entity_tags, entity_counts


def aggregate_quality_scores(
    validation_report: ValidationReport,
    readability_scores: Dict[str, float] | None = None,
) -> Tuple[Dict[str, float], List[str]]:
    """Aggregate quality scores from validation report and readability metrics.

    Collects OCR confidence, completeness ratio, and optional readability scores
    into a unified quality_scores dict. Also aggregates quality_flags from validation.

    Args:
        validation_report: ValidationReport from Story 2.5 with quality metrics
        readability_scores: Optional dict of readability metrics (e.g., flesch_reading_ease)

    Returns:
        Tuple of (quality_scores, quality_flags):
            - quality_scores: Dict with ocr_confidence, completeness_ratio, readability metrics
            - quality_flags: List of quality flag strings from ValidationReport

    Examples:
        >>> report = ValidationReport(
        ...     quarantine_recommended=False,
        ...     document_average_confidence=0.95,
        ...     completeness_passed=True,
        ...     quality_flags=[],
        ... )
        >>> scores, flags = aggregate_quality_scores(report)
        >>> assert scores["ocr_confidence"] == 0.95

    Story: 2.6 - Metadata Enrichment Framework
    AC: 2.6.5 (quality scores aggregation)
    """
    quality_scores: Dict[str, float] = {}

    # Aggregate OCR confidence (from Story 2.4)
    if validation_report.document_average_confidence is not None:
        quality_scores["ocr_confidence"] = validation_report.document_average_confidence

    # Aggregate completeness ratio (from Story 2.5)
    # Calculate from validation report if completeness_passed available
    if hasattr(validation_report, "completeness_ratio"):
        quality_scores["completeness_ratio"] = validation_report.completeness_ratio
    elif validation_report.completeness_passed:
        # If only pass/fail, assume 1.0 if passed (conservative estimate)
        quality_scores["completeness_ratio"] = 1.0

    # Add readability scores if provided
    if readability_scores:
        quality_scores.update(readability_scores)

    # Convert quality_flags from enum to string list
    quality_flags = [flag.value for flag in validation_report.quality_flags]

    return quality_scores, quality_flags


def serialize_config_snapshot(config: NormalizationConfig) -> Dict[str, Any]:
    """Serialize NormalizationConfig to dict for reproducibility.

    Converts Pydantic config model to JSON-serializable dict using model_dump().
    Includes all configuration fields for full reproducibility.

    Args:
        config: NormalizationConfig instance to serialize

    Returns:
        Dict with all configuration fields (JSON-serializable)

    Examples:
        >>> from data_extract.normalize.config import NormalizationConfig
        >>> config = NormalizationConfig(
        ...     tool_version="2.0.0",
        ...     ocr_confidence_threshold=0.95,
        ...     completeness_threshold=0.90,
        ... )
        >>> snapshot = serialize_config_snapshot(config)
        >>> assert snapshot["tool_version"] == "2.0.0"
        >>> assert snapshot["ocr_confidence_threshold"] == 0.95

    Story: 2.6 - Metadata Enrichment Framework
    AC: 2.6.6 (configuration snapshot for reproducibility)
    """
    # Use Pydantic's model_dump() to serialize config
    # mode='json' ensures Path objects are converted to strings
    return config.model_dump(mode="json")


class MetadataEnricher:
    """Metadata enrichment orchestrator for Story 2.6.

    Coordinates all metadata enrichment operations:
    - File hashing (SHA-256)
    - Entity aggregation (tags and counts)
    - Quality score aggregation (OCR, completeness, readability)
    - Configuration snapshot serialization
    - Timestamp and tool version recording

    Integrates as Step 8 in the Normalizer pipeline after QualityValidator (Step 7).

    Examples:
        >>> from pathlib import Path
        >>> enricher = MetadataEnricher()
        >>> enriched_metadata = enricher.enrich_metadata(
        ...     source_file=Path("document.pdf"),
        ...     entities=entity_list,
        ...     validation_report=validation_report,
        ...     config=normalization_config,
        ... )

    Story: 2.6 - Metadata Enrichment Framework
    AC: All (2.6.1-2.6.8)
    """

    def enrich_metadata(
        self,
        source_file: Path,
        entities: List[Entity],
        validation_report: ValidationReport,
        config: NormalizationConfig,
        readability_scores: Dict[str, float] | None = None,
    ) -> Metadata:
        """Enrich metadata with all processing information.

        Main entry point for metadata enrichment. Aggregates all metadata from
        processing pipeline and creates enriched Metadata object for audit trail.

        Args:
            source_file: Path to source document file
            entities: List of entities extracted from document
            validation_report: ValidationReport from Story 2.5
            config: NormalizationConfig with processing settings
            readability_scores: Optional readability metrics dict

        Returns:
            Enriched Metadata object with all fields populated

        Raises:
            ProcessingError: If file hashing fails (continue-on-error pattern)

        Examples:
            >>> enricher = MetadataEnricher()
            >>> metadata = enricher.enrich_metadata(
            ...     source_file=Path("audit.pdf"),
            ...     entities=[...],
            ...     validation_report=report,
            ...     config=config,
            ... )
            >>> assert metadata.file_hash  # SHA-256 hash
            >>> assert metadata.entity_tags  # Entity IDs
            >>> assert metadata.config_snapshot  # Full config

        Story: 2.6 - Metadata Enrichment Framework
        AC: All (2.6.1-2.6.8)
        """
        # AC-2.6.1: Calculate SHA-256 file hash
        file_hash = calculate_file_hash(source_file)

        # AC-2.6.3: Generate ISO 8601 timestamp
        processing_timestamp = datetime.now(timezone.utc)

        # AC-2.6.3: Get tool version from config
        tool_version = config.tool_version

        # AC-2.6.4: Aggregate entity tags and counts
        entity_tags, entity_counts = aggregate_entity_tags(entities)

        # AC-2.6.5: Aggregate quality scores and flags
        quality_scores, quality_flags = aggregate_quality_scores(
            validation_report, readability_scores
        )

        # AC-2.6.6: Serialize configuration snapshot
        config_snapshot = serialize_config_snapshot(config)

        # AC-2.6.5: Serialize ValidationReport to dict
        validation_report_dict = validation_report.model_dump(mode="json")

        # AC-2.6.2: Extract document type (already in validation or document)
        # For now, we'll leave document_type as None if not provided
        # This will be populated by the normalizer from document classification

        # Create enriched Metadata object (AC-2.6.7: JSON serializable)
        metadata = Metadata(
            source_file=source_file,
            file_hash=file_hash,
            processing_timestamp=processing_timestamp,
            tool_version=tool_version,
            config_version="1.0",  # Config version tracking
            document_type=None,  # Set by caller if available
            document_subtype=None,  # Set by caller if available
            entity_tags=entity_tags,
            entity_counts=entity_counts,
            quality_scores=quality_scores,
            quality_flags=quality_flags,
            config_snapshot=config_snapshot,
            validation_report=validation_report_dict,
            # OCR confidence and completeness ratio from validation report
            ocr_confidence=validation_report.confidence_scores,
            completeness_ratio=(
                quality_scores.get("completeness_ratio") if quality_scores else None
            ),
            section_context=None,
        )

        # AC-2.6.8: Full audit trail support
        return metadata
