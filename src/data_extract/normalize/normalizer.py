"""Normalizer orchestrator for text normalization pipeline.

This module implements the main Normalizer class that orchestrates
text cleaning and entity normalization using TextCleaner and EntityNormalizer.

Key classes:
- Normalizer: Main orchestrator implementing PipelineStage[Document, Document]
"""

from pathlib import Path
from typing import Optional

import structlog

from ..core.exceptions import CriticalError, ProcessingError
from ..core.models import Document, ProcessingContext
from .cleaning import TextCleaner
from .config import NormalizationConfig
from .entities import EntityNormalizer
from .metadata import MetadataEnricher
from .schema import SchemaStandardizer
from .validation import QualityValidator


class Normalizer:
    """Main normalization orchestrator (Story 2.1 + 2.2 + 2.3 + 2.4 + 2.5 + 2.6).

    Implements PipelineStage[Document, Document] protocol for integration
    with the modular pipeline architecture from Epic 1.

    Orchestrates:
    - Text cleaning via TextCleaner (Story 2.1)
    - Entity normalization via EntityNormalizer (Story 2.2)
    - Schema standardization via SchemaStandardizer (Story 2.3)
    - OCR quality validation via QualityValidator (Story 2.4)
    - Completeness validation via QualityValidator (Story 2.5)
    - Metadata enrichment via MetadataEnricher (Story 2.6)
    - Metadata enrichment with cleaning and entity metrics
    - Error handling (ProcessingError, CriticalError)
    - Structured logging via structlog

    Type Contract: Document (raw text) → Document (cleaned text + entities + standardized schema + validated OCR)

    Design:
    - Stateless: All state in ProcessingContext
    - Deterministic: Same input + config → same output
    - Auditable: All cleaning and entity decisions logged

    Example:
        >>> config = NormalizationConfig()
        >>> normalizer = Normalizer(config)
        >>> context = ProcessingContext(config={}, logger=logger)
        >>> processed_doc = normalizer.process(raw_doc, context)
    """

    def __init__(self, config: NormalizationConfig):
        """Initialize Normalizer with configuration.

        Args:
            config: Normalization configuration
        """
        self.config = config
        self.text_cleaner = TextCleaner(config)

        # Initialize EntityNormalizer if enabled (Story 2.2)
        self.entity_normalizer: Optional[EntityNormalizer] = None
        if config.enable_entity_normalization:
            try:
                self.entity_normalizer = EntityNormalizer(
                    patterns_file=config.entity_patterns_file,
                    dictionary_file=config.entity_dictionary_file,
                    context_window=config.entity_context_window,
                )
            except FileNotFoundError as e:
                # Entity normalization disabled if config files not found
                logger = structlog.get_logger()
                logger.warning("entity_normalization_disabled", reason=str(e))

        # Initialize SchemaStandardizer if enabled (Story 2.3)
        self.schema_standardizer: Optional[SchemaStandardizer] = None
        if config.enable_schema_standardization:
            self.schema_standardizer = SchemaStandardizer(
                schema_templates_file=config.schema_templates_file,
                enable_standardization=True,
            )

        # Initialize QualityValidator (Story 2.4 + 2.5)
        # Note: Always initialized but will skip validation if Tesseract unavailable
        self.quality_validator = QualityValidator(
            ocr_confidence_threshold=config.ocr_confidence_threshold,
            ocr_preprocessing_enabled=config.ocr_preprocessing_enabled,
            quarantine_low_confidence=config.quarantine_low_confidence,
        )

        # Initialize MetadataEnricher (Story 2.6)
        self.metadata_enricher = MetadataEnricher()

    def process(self, document: Document, context: ProcessingContext) -> Document:
        """Normalize document through all stages (PipelineStage protocol).

        Main pipeline method that cleans document text, enriches metadata,
        and logs cleaning metrics.

        Args:
            document: Document with raw text from extraction stage
            context: Processing context (config, logger, metrics)

        Returns:
            Document with cleaned text and enriched metadata

        Raises:
            ProcessingError: For recoverable errors (malformed text, etc.)
            CriticalError: For fatal errors (invalid config, missing dependencies)

        Pipeline Flow:
            1. Extract text from document
            2. Clean text using TextCleaner
            3. Aggregate CleaningResults
            4. Update document metadata
            5. Log metrics to context.logger
            6. Return normalized document

        Example:
            >>> doc = Document(
            ...     id="doc1",
            ...     text="Text ^^^^^ with noise",
            ...     metadata=metadata,
            ... )
            >>> cleaned = normalizer.process(doc, context)
            >>> assert "^^^^^" not in cleaned.text
        """
        try:
            # Get logger from context (or create fallback)
            logger = context.logger if context.logger else structlog.get_logger()

            # Extract text from document
            raw_text = document.text

            # Clean text using TextCleaner
            cleaned_text, cleaning_result = self.text_cleaner.clean_text(
                raw_text, doc_type=document.metadata.document_type
            )

            # Log cleaning metrics
            logger.info(
                "text_cleaning_complete",
                document_id=document.id,
                original_length=cleaning_result.original_length,
                cleaned_length=cleaning_result.cleaned_length,
                artifacts_removed=cleaning_result.artifacts_removed,
                whitespace_normalized=cleaning_result.whitespace_normalized,
            )

            # Update context metrics (accumulate)
            context.metrics["total_artifacts_removed"] = (
                context.metrics.get("total_artifacts_removed", 0)
                + cleaning_result.artifacts_removed
            )
            context.metrics["documents_normalized"] = (
                context.metrics.get("documents_normalized", 0) + 1
            )

            # Update document metadata with cleaning summary
            updated_metadata = document.metadata.model_copy(deep=True)
            updated_metadata.quality_scores["cleaning_artifacts_removed"] = float(
                cleaning_result.artifacts_removed
            )
            updated_metadata.quality_scores["cleaning_length_reduction"] = float(
                cleaning_result.original_length - cleaning_result.cleaned_length
            )

            # Add quality flags if significant changes were made
            if cleaning_result.artifacts_removed > 10:
                updated_metadata.quality_flags.append("high_ocr_artifact_count")

            # Create intermediate document with cleaned text
            intermediate_document = document.model_copy(
                update={
                    "text": cleaned_text,
                    "metadata": updated_metadata,
                }
            )

            # Step 2: Entity normalization (Story 2.2) if enabled
            if self.entity_normalizer:
                try:
                    normalized_document = self.entity_normalizer.process(
                        intermediate_document, context
                    )
                    logger.info(
                        "entity_normalization_complete",
                        document_id=document.id,
                        entities_found=len(normalized_document.entities),
                        entity_counts=normalized_document.metadata.entity_counts,
                    )
                except Exception as e:
                    # Log error but continue with cleaned text (graceful degradation)
                    logger.warning(
                        "entity_normalization_error",
                        document_id=document.id,
                        error=str(e),
                        fallback="continuing_without_entities",
                    )
                    normalized_document = intermediate_document
            else:
                # Entity normalization disabled or not configured
                normalized_document = intermediate_document

            # Step 3: Schema standardization (Story 2.3) if enabled
            if self.schema_standardizer:
                try:
                    standardized_document = self.schema_standardizer.process(
                        normalized_document, context
                    )
                    logger.info(
                        "schema_standardization_complete",
                        document_id=document.id,
                        document_type=standardized_document.metadata.document_type,
                        document_subtype=standardized_document.metadata.document_subtype,
                    )
                except Exception as e:
                    # Log error but continue without schema standardization (graceful degradation)
                    logger.warning(
                        "schema_standardization_error",
                        document_id=document.id,
                        error=str(e),
                        fallback="continuing_without_schema_standardization",
                    )
                    standardized_document = normalized_document
            else:
                # Schema standardization disabled or not configured
                standardized_document = normalized_document

            # Step 4: OCR quality validation (Story 2.4 + 2.5)
            try:
                validated_document = self.quality_validator.process(standardized_document, context)
                logger.info(
                    "quality_validation_complete",
                    document_id=document.id,
                    ocr_confidence_available=bool(validated_document.metadata.ocr_confidence),
                    completeness_ratio=validated_document.metadata.completeness_ratio,
                )
            except Exception as e:
                # Log error but continue without validation (graceful degradation)
                logger.warning(
                    "quality_validation_error",
                    document_id=document.id,
                    error=str(e),
                    fallback="continuing_without_validation",
                )
                validated_document = standardized_document

            # Step 8: Metadata enrichment (Story 2.6)
            try:
                # Get ValidationReport from quality validator's last validation
                # Note: In production, this would be stored or passed through
                # For now, we'll create a minimal ValidationReport from metadata
                from ..core.models import ValidationReport

                validation_report = ValidationReport(
                    quarantine_recommended=(len(validated_document.metadata.quality_flags) > 0),
                    confidence_scores=validated_document.metadata.ocr_confidence,
                    quality_flags=[],  # Already in metadata.quality_flags
                    extraction_gaps=[],
                    document_average_confidence=validated_document.metadata.quality_scores.get(
                        "ocr_confidence"
                    ),
                    scanned_pdf_detected=None,  # Not available at this stage
                    completeness_passed=(
                        validated_document.metadata.completeness_ratio is None
                        or validated_document.metadata.completeness_ratio
                        >= self.config.completeness_threshold
                    ),
                )

                # Enrich metadata with all processing information
                enriched_metadata = self.metadata_enricher.enrich_metadata(
                    source_file=validated_document.metadata.source_file,
                    entities=validated_document.entities,
                    validation_report=validation_report,
                    config=self.config,
                    readability_scores=None,  # Optional: can be added later
                )

                # Merge enriched metadata with existing metadata
                # Preserve quality_scores and quality_flags from earlier pipeline stages
                merged_quality_scores = validated_document.metadata.quality_scores.copy()
                merged_quality_scores.update(enriched_metadata.quality_scores)

                # Merge quality_flags (combine existing + new, deduplicate)
                merged_quality_flags = list(
                    set(validated_document.metadata.quality_flags + enriched_metadata.quality_flags)
                )

                # Preserve critical fields from original metadata if already set
                final_metadata = enriched_metadata.model_copy(
                    update={
                        "quality_scores": merged_quality_scores,
                        "quality_flags": merged_quality_flags,
                        "document_type": (
                            validated_document.metadata.document_type
                            or enriched_metadata.document_type
                        ),
                        "document_subtype": (
                            validated_document.metadata.document_subtype
                            or enriched_metadata.document_subtype
                        ),
                        # Preserve original file_hash and tool_version if already set
                        "file_hash": (
                            validated_document.metadata.file_hash
                            if validated_document.metadata.file_hash
                            else enriched_metadata.file_hash
                        ),
                        "tool_version": (
                            validated_document.metadata.tool_version
                            if validated_document.metadata.tool_version
                            else enriched_metadata.tool_version
                        ),
                    }
                )

                # Create final document with merged metadata
                final_document = validated_document.model_copy(update={"metadata": final_metadata})

                logger.info(
                    "metadata_enrichment_complete",
                    document_id=document.id,
                    file_hash=enriched_metadata.file_hash[:16] + "...",
                    entity_count=len(enriched_metadata.entity_tags),
                    config_snapshot_keys=len(enriched_metadata.config_snapshot),
                )

            except ProcessingError as e:
                # Log error but continue without enrichment (graceful degradation)
                logger.warning(
                    "metadata_enrichment_error",
                    document_id=document.id,
                    error=str(e),
                    fallback="continuing_without_enrichment",
                )
                final_document = validated_document

            return final_document

        except Exception as e:
            # Catch unexpected errors and wrap in ProcessingError
            error_msg = f"Text cleaning failed for document {document.id}: {e}"
            logger.error("text_cleaning_error", document_id=document.id, error=str(e))

            # Determine if error is recoverable
            if isinstance(e, (CriticalError, KeyboardInterrupt, SystemExit)):
                # Re-raise critical errors
                raise

            # Wrap as ProcessingError (recoverable - log, skip, continue batch)
            raise ProcessingError(error_msg) from e


class NormalizerFactory:
    """Factory for creating Normalizer instances with different configurations.

    Provides convenience methods for common normalization scenarios.

    Example:
        >>> # Default normalizer
        >>> normalizer = NormalizerFactory.create_default()
        >>>
        >>> # Custom normalizer
        >>> config = NormalizationConfig(remove_ocr_artifacts=False)
        >>> normalizer = NormalizerFactory.create(config)
    """

    @staticmethod
    def create_default() -> Normalizer:
        """Create normalizer with default configuration.

        Returns:
            Normalizer with default NormalizationConfig

        Example:
            >>> normalizer = NormalizerFactory.create_default()
            >>> assert normalizer.config.remove_ocr_artifacts is True
        """
        config = NormalizationConfig()
        return Normalizer(config)

    @staticmethod
    def create(config: NormalizationConfig) -> Normalizer:
        """Create normalizer with custom configuration.

        Args:
            config: Custom normalization configuration

        Returns:
            Normalizer with provided configuration

        Example:
            >>> config = NormalizationConfig(remove_headers_footers=False)
            >>> normalizer = NormalizerFactory.create(config)
            >>> assert normalizer.config.remove_headers_footers is False
        """
        return Normalizer(config)

    @staticmethod
    def create_from_yaml(yaml_path: str) -> Normalizer:
        """Create normalizer from YAML configuration file.

        Args:
            yaml_path: Path to YAML configuration file

        Returns:
            Normalizer with configuration loaded from YAML

        Example:
            >>> normalizer = NormalizerFactory.create_from_yaml(
            ...     "config/normalize/cleaning_rules.yaml"
            ... )
        """

        from .config import load_config

        config = load_config(yaml_path=Path(yaml_path))
        return Normalizer(config)
