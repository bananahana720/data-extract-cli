"""Preset configuration data models.

This module defines the data models for preset configurations, including
validation rules and serialization/deserialization support.
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import yaml


class ValidationLevel(str, Enum):
    """Validation strictness levels for preset configurations."""

    MINIMAL = "minimal"
    STANDARD = "standard"
    STRICT = "strict"


@dataclass
class PresetConfig:
    """Configuration preset for data extraction pipeline.

    Attributes:
        name: Unique identifier for the preset
        description: Human-readable description
        chunk_size: Target size for text chunks (128-2048 tokens)
        quality_threshold: Minimum quality score (0.0-1.0)
        output_format: Output format (json, txt, csv)
        dedup_threshold: Similarity threshold for deduplication (0.0-1.0)
        include_metadata: Whether to include metadata in output
        validation_level: Strictness of validation
        created: Timestamp of preset creation
    """

    name: str
    description: str = ""
    chunk_size: int = 500
    quality_threshold: float = 0.7
    output_format: str = "json"
    dedup_threshold: float = 0.95
    include_metadata: bool = True
    validation_level: ValidationLevel = ValidationLevel.STANDARD
    created: datetime | None = None

    def __post_init__(self) -> None:
        """Validate preset configuration after initialization.

        Raises:
            ValueError: If any validation constraint is violated
        """
        # Validate name
        if not self.name or not self.name.strip():
            raise ValueError("Preset name is required")

        # Validate chunk_size range
        if not 128 <= self.chunk_size <= 2048:
            raise ValueError(f"chunk_size must be between 128 and 2048, got {self.chunk_size}")

        # Validate quality_threshold range
        if not 0.0 <= self.quality_threshold <= 1.0:
            raise ValueError(
                f"quality_threshold must be between 0.0 and 1.0, got {self.quality_threshold}"
            )

        # Validate dedup_threshold range
        if not 0.0 <= self.dedup_threshold <= 1.0:
            raise ValueError(
                f"dedup_threshold must be between 0.0 and 1.0, got {self.dedup_threshold}"
            )

        # Validate output_format
        valid_formats = {"json", "txt", "csv"}
        if self.output_format not in valid_formats:
            raise ValueError(
                f"output_format must be one of {valid_formats}, got {self.output_format}"
            )

        # Ensure validation_level is an enum
        if isinstance(self.validation_level, str):
            self.validation_level = ValidationLevel(self.validation_level)

    def to_dict(self) -> dict[str, Any]:
        """Convert preset to dictionary.

        Returns:
            Dictionary representation of the preset
        """
        result = asdict(self)
        # Convert enum to string value
        if isinstance(result["validation_level"], ValidationLevel):
            result["validation_level"] = result["validation_level"].value
        # Convert datetime to ISO format string
        if result["created"]:
            result["created"] = result["created"].isoformat()
        return result

    def to_yaml(self) -> str:
        """Serialize preset to YAML string.

        Returns:
            YAML string representation
        """
        data = self.to_dict()
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "PresetConfig":
        """Deserialize preset from YAML string.

        Args:
            yaml_str: YAML string containing preset configuration

        Returns:
            PresetConfig instance

        Raises:
            ValueError: If YAML is invalid or missing required fields
        """
        try:
            data = yaml.safe_load(yaml_str)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("YAML must contain a mapping")

        # Convert string validation_level to enum
        if "validation_level" in data and isinstance(data["validation_level"], str):
            data["validation_level"] = ValidationLevel(data["validation_level"])

        # Convert ISO string back to datetime
        if "created" in data and isinstance(data["created"], str):
            data["created"] = datetime.fromisoformat(data["created"])

        return cls(**data)

    def model_dump(self) -> dict[str, Any]:
        """Pydantic-compatible serialization method.

        This method exists for compatibility with Pydantic-style APIs,
        but delegates to to_dict().

        Returns:
            Dictionary representation of the preset
        """
        return self.to_dict()
