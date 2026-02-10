"""Normalization configuration models and loaders.

This module defines configuration for text normalization pipeline:
- NormalizationConfig: Main configuration model with text cleaning and entity settings
- load_config(): Configuration cascade loader (CLI > env > YAML > defaults)

Configuration cascade precedence (highest to lowest):
1. CLI flags (passed as kwargs)
2. Environment variables (DATA_EXTRACT_NORMALIZE_* prefix)
3. YAML configuration file
4. Hardcoded defaults
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


class NormalizationConfig(BaseModel):
    """Configuration for text normalization pipeline.

    Defines settings for text cleaning, artifact removal, whitespace
    normalization, header/footer detection, and entity normalization.

    Attributes:
        remove_ocr_artifacts: Enable OCR artifact removal (AC-2.1.1)
        remove_headers_footers: Enable header/footer removal (AC-2.1.3)
        normalize_whitespace: Enable whitespace normalization (AC-2.1.2)
        header_repetition_threshold: Min pages for header/footer detection (AC-2.1.4)
        whitespace_max_consecutive_newlines: Max consecutive newlines (AC-2.1.2)
        ocr_artifact_patterns_file: Path to OCR artifact patterns YAML
        header_footer_patterns_file: Path to header/footer patterns YAML
        enable_entity_normalization: Enable entity recognition and normalization (AC-2.2.1)
        entity_patterns_file: Path to entity patterns YAML (AC-2.2.7)
        entity_dictionary_file: Path to entity dictionary YAML (AC-2.2.3)
        entity_context_window: Context window size for entity disambiguation (AC-2.2.1)
        ocr_confidence_threshold: Minimum OCR confidence threshold (AC-2.4.2)
        ocr_preprocessing_enabled: Enable image preprocessing before OCR (AC-2.4.3)
        quarantine_low_confidence: Enable quarantine for low confidence (AC-2.4.5)
    """

    model_config = ConfigDict(frozen=False)

    # Text Cleaning Flags (Story 2.1)
    remove_ocr_artifacts: bool = Field(
        default=True, description="Enable OCR artifact removal (AC-2.1.1)"
    )
    remove_headers_footers: bool = Field(
        default=True, description="Enable header/footer removal (AC-2.1.3)"
    )
    normalize_whitespace: bool = Field(
        default=True, description="Enable whitespace normalization (AC-2.1.2)"
    )

    # Thresholds
    header_repetition_threshold: int = Field(
        default=3,
        ge=1,
        description="Min pages for header/footer detection (AC-2.1.4)",
    )
    whitespace_max_consecutive_newlines: int = Field(
        default=2, ge=1, description="Max consecutive newlines (AC-2.1.2)"
    )

    # Configuration file paths (Story 2.1)
    ocr_artifact_patterns_file: Optional[Path] = Field(
        default=None, description="Path to OCR artifact patterns YAML (optional)"
    )
    header_footer_patterns_file: Optional[Path] = Field(
        default=None, description="Path to header/footer patterns YAML (optional)"
    )

    # Entity Normalization Flags (Story 2.2)
    enable_entity_normalization: bool = Field(
        default=True, description="Enable entity recognition and normalization (AC-2.2.1)"
    )

    # Entity Configuration file paths (Story 2.2)
    entity_patterns_file: Optional[Path] = Field(
        default=None, description="Path to entity patterns YAML (AC-2.2.7)"
    )
    entity_dictionary_file: Optional[Path] = Field(
        default=None, description="Path to entity dictionary YAML (AC-2.2.3)"
    )

    # Entity Processing Settings (Story 2.2)
    entity_context_window: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Context window size for entity disambiguation (AC-2.2.1)",
    )

    # Schema Standardization Flags (Story 2.3)
    enable_schema_standardization: bool = Field(
        default=True, description="Enable schema standardization across document types (AC-2.3.2)"
    )

    # Schema Configuration file paths (Story 2.3)
    schema_templates_file: Optional[Path] = Field(
        default=None, description="Path to schema templates YAML (AC-2.3.3)"
    )

    # OCR Validation Flags (Story 2.4)
    ocr_confidence_threshold: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Minimum OCR confidence threshold for quality validation (AC-2.4.2)",
    )
    ocr_preprocessing_enabled: bool = Field(
        default=True, description="Enable image preprocessing before OCR (AC-2.4.3)"
    )
    quarantine_low_confidence: bool = Field(
        default=True, description="Enable quarantine for low confidence extractions (AC-2.4.5)"
    )

    # Completeness Validation Flags (Story 2.5)
    completeness_threshold: float = Field(
        default=0.90,
        ge=0.0,
        le=1.0,
        description="Minimum completeness ratio threshold for quality validation (AC-2.5.3)",
    )

    # Metadata Enrichment Flags (Story 2.6)
    tool_version: str = Field(
        default="2.0.0",
        description="Version of the data extraction tool (for reproducibility, AC-2.6.3)",
    )

    @field_validator(
        "ocr_artifact_patterns_file",
        "header_footer_patterns_file",
        "entity_patterns_file",
        "entity_dictionary_file",
        "schema_templates_file",
    )
    @classmethod
    def validate_file_paths(cls, v: Optional[Path]) -> Optional[Path]:
        """Validate that configuration file paths exist if specified.

        Args:
            v: Path to validate

        Returns:
            Validated path or None

        Raises:
            ValueError: If path is specified but does not exist
        """
        if v is not None and not v.exists():
            raise ValueError(f"Configuration file not found: {v}")
        return v


def validate_entity_patterns(patterns_file: Path) -> List[str]:
    """Validate entity patterns YAML file and return validation errors.

    Checks that:
    - All 6 entity types have patterns defined
    - All regex patterns compile successfully
    - Required fields (pattern, description, priority) are present
    - Priority values are positive integers

    Args:
        patterns_file: Path to entity_patterns.yaml file

    Returns:
        List of validation error messages (empty if valid)

    Example:
        >>> errors = validate_entity_patterns(Path("config/normalize/entity_patterns.yaml"))
        >>> if errors:
        ...     print("Validation errors:", errors)
    """
    errors: List[str] = []

    try:
        with open(patterns_file, "r", encoding="utf-8") as f:
            patterns_config = yaml.safe_load(f) or {}
    except Exception as e:
        return [f"Failed to load patterns file: {e}"]

    # Required entity types (AC-2.2.1)
    required_types = ["processes", "risks", "controls", "regulations", "policies", "issues"]

    # Check all entity types are defined
    for entity_type in required_types:
        if entity_type not in patterns_config:
            errors.append(f"Missing entity type: {entity_type}")
            continue

        patterns = patterns_config[entity_type]
        if not isinstance(patterns, list) or len(patterns) == 0:
            errors.append(f"Entity type '{entity_type}' has no patterns defined")
            continue

        # Validate each pattern
        for i, pattern_def in enumerate(patterns):
            if not isinstance(pattern_def, dict):
                errors.append(f"{entity_type}[{i}]: Pattern must be a dictionary")
                continue

            # Check required fields
            if "pattern" not in pattern_def:
                errors.append(f"{entity_type}[{i}]: Missing 'pattern' field")
            if "description" not in pattern_def:
                errors.append(f"{entity_type}[{i}]: Missing 'description' field")
            if "priority" not in pattern_def:
                errors.append(f"{entity_type}[{i}]: Missing 'priority' field")

            # Validate regex pattern compilation (AC-2.2.7)
            if "pattern" in pattern_def:
                try:
                    re.compile(pattern_def["pattern"])
                except re.error as e:
                    errors.append(f"{entity_type}[{i}]: Invalid regex pattern: {e}")

            # Validate priority is positive integer
            if "priority" in pattern_def:
                priority = pattern_def["priority"]
                if not isinstance(priority, int) or priority < 1:
                    errors.append(f"{entity_type}[{i}]: Priority must be positive integer")

    return errors


def load_config(
    yaml_path: Optional[Path] = None,
    env_vars: Optional[Dict[str, Any]] = None,
    cli_flags: Optional[Dict[str, Any]] = None,
) -> NormalizationConfig:
    """Load normalization configuration with cascade precedence.

    Configuration cascade (highest to lowest precedence):
    1. CLI flags (cli_flags parameter)
    2. Environment variables (DATA_EXTRACT_NORMALIZE_* prefix)
    3. YAML configuration file (yaml_path parameter)
    4. Hardcoded defaults (NormalizationConfig defaults)

    Args:
        yaml_path: Path to YAML configuration file (optional)
        env_vars: Environment variables dict (defaults to os.environ)
        cli_flags: CLI flags dict (highest precedence)

    Returns:
        NormalizationConfig: Merged configuration with cascade precedence

    Raises:
        ValueError: If YAML file is invalid or file paths don't exist

    Examples:
        >>> # Load with defaults only
        >>> config = load_config()

        >>> # Load with YAML file
        >>> config = load_config(yaml_path=Path("config/normalize/cleaning_rules.yaml"))

        >>> # Load with CLI overrides
        >>> config = load_config(
        ...     yaml_path=Path("config/normalize/cleaning_rules.yaml"),
        ...     cli_flags={"remove_ocr_artifacts": False}
        ... )
    """
    # Start with empty config dict
    merged_config: Dict[str, Any] = {}

    # Layer 4: Hardcoded defaults (handled by Pydantic defaults)

    # Layer 3: YAML configuration file
    if yaml_path is not None and yaml_path.exists():
        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_config = yaml.safe_load(f) or {}
            merged_config.update(yaml_config)

    # Layer 2: Environment variables (DATA_EXTRACT_NORMALIZE_* prefix)
    if env_vars is None:
        env_vars = dict(os.environ)

    env_prefix = "DATA_EXTRACT_NORMALIZE_"
    for key, value in env_vars.items():
        if key.startswith(env_prefix):
            # Convert DATA_EXTRACT_NORMALIZE_REMOVE_OCR_ARTIFACTS -> remove_ocr_artifacts
            config_key = key[len(env_prefix) :].lower()

            # Parse boolean env vars
            if value.lower() in ("true", "1", "yes"):
                merged_config[config_key] = True
            elif value.lower() in ("false", "0", "no"):
                merged_config[config_key] = False
            else:
                # Try to parse as int, else keep as string
                try:
                    merged_config[config_key] = int(value)
                except ValueError:
                    merged_config[config_key] = value

    # Layer 1: CLI flags (highest precedence)
    if cli_flags is not None:
        merged_config.update(cli_flags)

    # Convert Path strings to Path objects
    for path_field in [
        "ocr_artifact_patterns_file",
        "header_footer_patterns_file",
        "entity_patterns_file",
        "entity_dictionary_file",
    ]:
        if path_field in merged_config and isinstance(merged_config[path_field], str):
            merged_config[path_field] = Path(merged_config[path_field])

    # Create and validate NormalizationConfig
    return NormalizationConfig(**merged_config)
