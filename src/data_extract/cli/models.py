"""Pydantic CLI models for data-extract command.

Story 5-1: Refactored Command Structure with Click-to-Typer Migration.

This module provides Pydantic models for:
- CommandResult: Standardized command result for pipeline composition (AC-5.1-9)
- Configuration models: Pydantic validation for complex config/input models (AC-5.1-4)
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class OutputFormat(str, Enum):
    """Output format choices for CLI commands."""

    json = "json"
    csv = "csv"
    html = "html"
    txt = "txt"


class CommandResult(BaseModel):
    """Standardized command result for pipeline composition.

    This model provides a consistent interface for command outputs,
    supporting:
    - Success/failure state tracking
    - Error accumulation
    - Data passing between pipeline stages
    - Command and argument tracking for debugging
    - Metadata for timing and execution context

    Attributes:
        success: Whether the command succeeded.
        exit_code: Process exit code (0 for success, non-negative).
        output: Human-readable output message.
        errors: List of error messages (empty on success).
        data: Optional structured data for pipeline chaining.
        command: Name of the executed command.
        args: Command arguments (list or dict).
        metadata: Execution metadata (timing, pipeline context, etc.).
        timestamp: Execution timestamp (auto-generated if not provided).
    """

    model_config = ConfigDict(frozen=False, validate_assignment=True)

    success: bool
    exit_code: int = Field(ge=0, description="Exit code (must be non-negative)")
    output: str = ""
    errors: list[str] = Field(default_factory=list)
    data: Optional[dict[str, Any]] = None
    command: Optional[str] = None
    args: Optional[Union[list[str], dict[str, Any]]] = None
    metadata: Optional[dict[str, Any]] = None
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

    @field_validator("exit_code")
    @classmethod
    def validate_exit_code(cls, v: int) -> int:
        """Validate exit_code is non-negative."""
        if v < 0:
            raise ValueError("exit_code must be non-negative")
        return v

    def is_success(self) -> bool:
        """Check if command succeeded.

        Returns:
            True if the command was successful (success=True).
        """
        return self.success

    def error_summary(self) -> str:
        """Get summary of errors as a single string.

        Returns:
            Semicolon-separated error messages, or "No errors" if none.
        """
        if not self.errors:
            return "No errors"
        return "; ".join(self.errors)

    @classmethod
    def create_success(
        cls,
        output: str = "",
        data: Optional[dict[str, Any]] = None,
        command: Optional[str] = None,
        args: Optional[Union[list[str], dict[str, Any]]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> "CommandResult":
        """Factory method to create a successful command result.

        Args:
            output: Human-readable success message.
            data: Optional structured output data.
            command: Name of the executed command.
            args: Command arguments.
            metadata: Execution metadata.

        Returns:
            CommandResult with success=True and exit_code=0.
        """
        return cls(
            success=True,
            exit_code=0,
            output=output,
            data=data,
            command=command,
            args=args,
            metadata=metadata,
        )

    @classmethod
    def create_error(
        cls,
        errors: list[str],
        exit_code: int = 1,
        output: str = "",
        command: Optional[str] = None,
        args: Optional[Union[list[str], dict[str, Any]]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> "CommandResult":
        """Factory method to create an error command result.

        Args:
            errors: List of error messages.
            exit_code: Exit code (default 1 for general error).
            output: Human-readable error message.
            command: Name of the executed command.
            args: Command arguments.
            metadata: Execution metadata.

        Returns:
            CommandResult with success=False.
        """
        return cls(
            success=False,
            exit_code=exit_code,
            output=output,
            errors=errors,
            command=command,
            args=args,
            metadata=metadata,
        )


class TfidfConfig(BaseModel):
    """TF-IDF vectorization configuration.

    Attributes:
        max_features: Maximum vocabulary size (default 5000, range 100-50000).
        ngram_range: N-gram range as (min, max) tuple (default (1, 2)).
        min_df: Minimum document frequency (default 2, >= 1).
        max_df: Maximum document frequency ratio (default 0.95, range 0.0-1.0).
    """

    model_config = ConfigDict(validate_assignment=True)

    max_features: int = Field(default=5000, ge=100, le=50000, description="Maximum vocabulary size")
    ngram_range: tuple[int, int] = Field(default=(1, 2), description="N-gram range (min, max)")
    min_df: int = Field(default=2, ge=1, description="Minimum document frequency")
    max_df: float = Field(
        default=0.95, ge=0.0, le=1.0, description="Maximum document frequency ratio"
    )

    @field_validator("max_features", mode="before")
    @classmethod
    def coerce_max_features(cls, v: Any) -> int:
        """Coerce string to int for max_features."""
        if isinstance(v, str):
            return int(v)
        if isinstance(v, int):
            return v
        raise TypeError(f"max_features must be int or str, got {type(v)}")

    @field_validator("min_df", mode="before")
    @classmethod
    def coerce_min_df(cls, v: Any) -> int:
        """Coerce string to int for min_df."""
        if isinstance(v, str):
            return int(v)
        if isinstance(v, int):
            return v
        raise TypeError(f"min_df must be int or str, got {type(v)}")

    @field_validator("max_df", mode="before")
    @classmethod
    def coerce_max_df(cls, v: Any) -> float:
        """Coerce string/int to float for max_df."""
        if isinstance(v, str):
            return float(v)
        if isinstance(v, int):
            return float(v)
        if isinstance(v, float):
            return v
        raise TypeError(f"max_df must be float, int, or str, got {type(v)}")

    @field_validator("ngram_range", mode="before")
    @classmethod
    def coerce_ngram_range(cls, v: Any) -> tuple[int, int]:
        """Coerce list to tuple for ngram_range."""
        if isinstance(v, list) and len(v) == 2:
            return (int(v[0]), int(v[1]))
        if isinstance(v, tuple) and len(v) == 2:
            return v
        raise ValueError("ngram_range must be a tuple or list of 2 integers")

    @model_validator(mode="after")
    def validate_ngram_order(self) -> "TfidfConfig":
        """Validate ngram_range min <= max."""
        if self.ngram_range[0] > self.ngram_range[1]:
            raise ValueError(
                f"ngram_range min ({self.ngram_range[0]}) must be <= max ({self.ngram_range[1]})"
            )
        return self

    @model_validator(mode="after")
    def validate_df_ordering(self) -> "TfidfConfig":
        """Validate min_df < max_df when min_df is a float.

        When min_df is an int, no cross-validation needed with max_df.
        When min_df is a float (0.0-1.0 range), ensure min_df < max_df.
        """
        # Note: min_df is currently typed as int in the Field definition,
        # but scikit-learn accepts both int and float (0.0-1.0) values.
        # This validator checks the logical constraint for the float case.
        min_df_val = float(self.min_df)

        # If min_df appears to be a proportion (0.0-1.0), validate ordering
        if 0.0 <= min_df_val <= 1.0:
            if min_df_val >= self.max_df:
                raise ValueError(
                    f"min_df ({min_df_val}) must be < max_df ({self.max_df}) "
                    f"when min_df is in range [0.0, 1.0]"
                )

        return self


class SimilarityConfig(BaseModel):
    """Similarity analysis configuration.

    Attributes:
        duplicate_threshold: Threshold for duplicate detection (default 0.95, range 0.0-1.0).
        related_threshold: Threshold for related documents (default 0.7, range 0.0-1.0).
    """

    model_config = ConfigDict(validate_assignment=True)

    duplicate_threshold: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Threshold for duplicate detection",
    )
    related_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Threshold for related documents"
    )

    @field_validator("duplicate_threshold", "related_threshold", mode="before")
    @classmethod
    def coerce_threshold(cls, v: Any) -> float:
        """Coerce string/int to float for thresholds."""
        if isinstance(v, str):
            return float(v)
        if isinstance(v, int):
            return float(v)
        if isinstance(v, float):
            return v
        raise TypeError(f"threshold must be float, int, or str, got {type(v)}")

    @model_validator(mode="after")
    def validate_threshold_ordering(self) -> "SimilarityConfig":
        """Validate duplicate_threshold >= related_threshold.

        Duplicates should be stricter (higher threshold) than related documents.
        """
        if self.duplicate_threshold < self.related_threshold:
            raise ValueError(
                f"duplicate_threshold ({self.duplicate_threshold}) must be >= "
                f"related_threshold ({self.related_threshold}). "
                f"Duplicates should be stricter than related documents."
            )
        return self


class LsaConfig(BaseModel):
    """LSA (Latent Semantic Analysis) configuration.

    Attributes:
        n_components: Number of LSA components/topics (default 100, range 1-500).
        n_clusters: Number of clusters for clustering (None for auto).
    """

    model_config = ConfigDict(validate_assignment=True)

    n_components: int = Field(default=100, ge=1, le=500, description="Number of LSA components")
    n_clusters: Optional[int] = Field(
        default=None, ge=1, description="Number of clusters (None for auto)"
    )

    @field_validator("n_components", mode="before")
    @classmethod
    def coerce_n_components(cls, v: Any) -> int:
        """Coerce string to int for n_components."""
        if isinstance(v, str):
            return int(v)
        if isinstance(v, int):
            return v
        raise TypeError(f"n_components must be int or str, got {type(v)}")

    @field_validator("n_clusters", mode="before")
    @classmethod
    def coerce_n_clusters(cls, v: Any) -> Optional[int]:
        """Coerce string to int or None for n_clusters."""
        if v is None or v == "auto":
            return None
        if isinstance(v, str):
            return int(v)
        if isinstance(v, int):
            return v
        raise TypeError(f"n_clusters must be int, str, or None, got {type(v)}")


class CacheConfig(BaseModel):
    """Cache configuration for semantic analysis.

    Attributes:
        enabled: Whether caching is enabled (default True).
        max_size_mb: Maximum cache size in megabytes (default 500, must be > 0).
    """

    model_config = ConfigDict(validate_assignment=True)

    enabled: bool = Field(default=True, description="Whether caching is enabled")
    max_size_mb: int = Field(default=500, gt=0, description="Maximum cache size in MB")

    @field_validator("enabled", mode="before")
    @classmethod
    def coerce_enabled(cls, v: Any) -> bool:
        """Coerce string to bool for enabled."""
        if isinstance(v, str):
            lower = v.lower()
            if lower in ("true", "1", "yes", "on"):
                return True
            if lower in ("false", "0", "no", "off"):
                return False
            raise ValueError(f"Cannot coerce '{v}' to boolean")
        if isinstance(v, bool):
            return v
        raise TypeError(f"enabled must be bool or str, got {type(v)}")

    @field_validator("max_size_mb", mode="before")
    @classmethod
    def coerce_max_size_mb(cls, v: Any) -> int:
        """Coerce string to int for max_size_mb."""
        if isinstance(v, str):
            return int(v)
        if isinstance(v, int):
            return v
        raise TypeError(f"max_size_mb must be int or str, got {type(v)}")


class QualityConfig(BaseModel):
    """Quality metrics configuration.

    Attributes:
        min_score: Minimum quality score threshold (default 0.3, range 0.0-1.0).
        skip_readability: Skip readability metrics for faster processing.
    """

    model_config = ConfigDict(validate_assignment=True)

    min_score: float = Field(default=0.3, ge=0.0, le=1.0, description="Minimum quality score")
    skip_readability: bool = Field(
        default=False, description="Skip readability metrics for faster processing"
    )

    @field_validator("min_score", mode="before")
    @classmethod
    def coerce_min_score(cls, v: Any) -> float:
        """Coerce string/int to float for min_score."""
        if isinstance(v, str):
            return float(v)
        if isinstance(v, int):
            return float(v)
        if isinstance(v, float):
            return v
        raise TypeError(f"min_score must be float, int, or str, got {type(v)}")

    @field_validator("skip_readability", mode="before")
    @classmethod
    def coerce_skip_readability(cls, v: Any) -> bool:
        """Coerce string to bool for skip_readability."""
        if isinstance(v, str):
            lower = v.lower()
            if lower in ("true", "1", "yes", "on"):
                return True
            if lower in ("false", "0", "no", "off"):
                return False
            raise ValueError(f"Cannot coerce '{v}' to boolean")
        if isinstance(v, bool):
            return v
        raise TypeError(f"skip_readability must be bool or str, got {type(v)}")


class SemanticConfig(BaseModel):
    """Full semantic analysis configuration.

    This model aggregates all semantic analysis sub-configurations.

    Attributes:
        tfidf: TF-IDF vectorization configuration.
        similarity: Similarity analysis configuration.
        lsa: LSA configuration.
        cache: Cache configuration.
        quality: Quality metrics configuration.
    """

    model_config = ConfigDict(validate_assignment=True)

    tfidf: TfidfConfig = Field(default_factory=TfidfConfig)
    similarity: SimilarityConfig = Field(default_factory=SimilarityConfig)
    lsa: LsaConfig = Field(default_factory=LsaConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    quality: QualityConfig = Field(default_factory=QualityConfig)

    @field_validator("tfidf", mode="before")
    @classmethod
    def coerce_tfidf(cls, v: Any) -> TfidfConfig:
        """Coerce dict to TfidfConfig."""
        if isinstance(v, dict):
            return TfidfConfig(**v)
        return v

    @field_validator("similarity", mode="before")
    @classmethod
    def coerce_similarity(cls, v: Any) -> SimilarityConfig:
        """Coerce dict to SimilarityConfig."""
        if isinstance(v, dict):
            return SimilarityConfig(**v)
        return v

    @field_validator("lsa", mode="before")
    @classmethod
    def coerce_lsa(cls, v: Any) -> LsaConfig:
        """Coerce dict to LsaConfig."""
        if isinstance(v, dict):
            return LsaConfig(**v)
        return v

    @field_validator("cache", mode="before")
    @classmethod
    def coerce_cache(cls, v: Any) -> CacheConfig:
        """Coerce dict to CacheConfig."""
        if isinstance(v, dict):
            return CacheConfig(**v)
        return v

    @field_validator("quality", mode="before")
    @classmethod
    def coerce_quality(cls, v: Any) -> QualityConfig:
        """Coerce dict to QualityConfig."""
        if isinstance(v, dict):
            return QualityConfig(**v)
        return v


class ChunkConfig(BaseModel):
    """Chunking configuration.

    Attributes:
        max_tokens: Maximum tokens per chunk (default 512, range 64-4096).
        overlap: Overlapping tokens between chunks (default 128, range 0-1024).
        size: Alias for max_tokens (for backward compatibility).
    """

    model_config = ConfigDict(validate_assignment=True)

    max_tokens: int = Field(default=512, ge=64, le=4096, description="Maximum tokens per chunk")
    overlap: int = Field(default=128, ge=0, le=1024, description="Overlapping tokens")
    size: Optional[int] = Field(default=None, description="Alias for max_tokens (deprecated)")

    @field_validator("max_tokens", "overlap", mode="before")
    @classmethod
    def coerce_int_fields(cls, v: Any) -> int:
        """Coerce string to int for integer fields."""
        if isinstance(v, str):
            return int(v)
        return v

    @field_validator("size", mode="before")
    @classmethod
    def coerce_size(cls, v: Any) -> Optional[int]:
        """Coerce string to int for size."""
        if v is None:
            return None
        if isinstance(v, str):
            return int(v)
        return v

    @model_validator(mode="after")
    def sync_size_with_max_tokens(self) -> "ChunkConfig":
        """Sync size with max_tokens for backward compatibility."""
        if self.size is not None and self.max_tokens == 512:
            object.__setattr__(self, "max_tokens", self.size)
        return self


class ExportConfig(BaseModel):
    """Export configuration.

    Attributes:
        format: Output format (json, csv, txt, html, graph).
        output_path: Output file or directory path.
        include_matrix: Include full similarity matrix.
        include_graph: Include similarity graph.
        pretty_print: Pretty print JSON output.
    """

    model_config = ConfigDict(validate_assignment=True)

    format: str = Field(default="json", description="Output format")
    output_path: Optional[Path] = Field(default=None, description="Output file or directory path")
    include_matrix: bool = Field(default=False, description="Include full similarity matrix")
    include_graph: bool = Field(default=True, description="Include similarity graph")
    pretty_print: bool = Field(default=True, description="Pretty print JSON output")

    @field_validator("format", mode="before")
    @classmethod
    def validate_export_format(cls, v: Any) -> str:
        """Validate format is one of the allowed values."""
        valid_formats = {"json", "csv", "txt", "html", "graph"}
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower in valid_formats:
                return v_lower
            raise ValueError(f"Invalid format: {v}. Must be one of: {valid_formats}")
        return str(v)

    @field_validator("output_path", mode="before")
    @classmethod
    def coerce_export_output_path(cls, v: Any) -> Optional[Path]:
        """Coerce string to Path for output_path."""
        if v is None:
            return None
        if isinstance(v, str):
            return Path(v)
        return v


class OutputConfig(BaseModel):
    """Output configuration for CLI commands.

    Attributes:
        format: Output format (json, csv, html, txt).
        output_path: Output file or directory path.
        include_matrix: Include full similarity matrix in output.
        include_graph: Include similarity graph in output.
        pretty_print: Pretty print JSON output.
    """

    model_config = ConfigDict(frozen=True)

    format: Union[OutputFormat, str] = Field(default=OutputFormat.json, description="Output format")
    output_path: Optional[Path] = Field(default=None, description="Output file or directory")
    include_matrix: bool = Field(default=False, description="Include full similarity matrix")
    include_graph: bool = Field(default=True, description="Include similarity graph")
    pretty_print: bool = Field(default=True, description="Pretty print JSON output")

    @field_validator("format", mode="before")
    @classmethod
    def validate_format(cls, v: Union[OutputFormat, str]) -> OutputFormat:
        """Validate and coerce format to OutputFormat enum."""
        if isinstance(v, OutputFormat):
            return v
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower in OutputFormat.__members__:
                return OutputFormat(v_lower)
            raise ValueError(
                f"Invalid format: {v}. Must be one of: {list(OutputFormat.__members__.keys())}"
            )
        raise ValueError(f"format must be string or OutputFormat, got {type(v)}")


class ProcessConfig(BaseModel):
    """Process command configuration.

    Attributes:
        input_path: Path to input file or directory.
        output_path: Path to output file or directory.
        recursive: Process directories recursively.
        output_format: Output format.
        chunk_size: Maximum chunk size in tokens.
        overlap: Chunk overlap size.
    """

    model_config = ConfigDict(frozen=True)

    input_path: Path = Field(description="Path to input file or directory")
    output_path: Optional[Path] = Field(
        default=None, description="Path to output file or directory"
    )
    recursive: bool = Field(default=True, description="Process directories recursively")
    output_format: OutputFormat = Field(default=OutputFormat.json, description="Output format")
    chunk_size: int = Field(default=512, ge=1, description="Maximum chunk size")
    overlap: int = Field(default=50, ge=0, description="Chunk overlap size")

    @field_validator("input_path", mode="before")
    @classmethod
    def validate_input_path(cls, v: Union[Path, str]) -> Path:
        """Coerce input_path to Path object."""
        if isinstance(v, str):
            return Path(v)
        if isinstance(v, Path):
            return v
        raise TypeError(f"input_path must be Path or str, got {type(v)}")

    @field_validator("output_path", mode="before")
    @classmethod
    def validate_output_path(cls, v: Optional[Union[Path, str]]) -> Optional[Path]:
        """Coerce output_path to Path object if provided."""
        if v is None:
            return None
        if isinstance(v, str):
            return Path(v)
        if isinstance(v, Path):
            return v
        raise TypeError(f"output_path must be Path, str, or None, got {type(v)}")


class BatchConfig(BaseModel):
    """Batch processing configuration.

    Attributes:
        batch_size: Number of files to process in each batch.
        max_workers: Maximum number of parallel workers.
        continue_on_error: Continue processing on individual file errors.
        checkpoint_interval: Save checkpoint every N files.
    """

    model_config = ConfigDict(frozen=True)

    batch_size: int = Field(default=10, ge=1, description="Files per batch")
    max_workers: int = Field(default=4, ge=1, description="Parallel workers")
    continue_on_error: bool = Field(default=True, description="Continue on file errors")
    checkpoint_interval: int = Field(default=100, ge=1, description="Checkpoint interval")


class ConfigModel(BaseModel):
    """Root configuration model combining all configuration sections.

    This is the top-level configuration model that encompasses all CLI options.
    Supports the 6-layer configuration cascade for Story 5-2.

    Attributes:
        output_dir: Output directory for processed files.
        format: Default output format.
        semantic: Semantic analysis configuration.
        chunk: Chunking configuration.
        quality: Quality metrics configuration.
        cache: Cache configuration.
    """

    model_config = ConfigDict(validate_assignment=True)

    # Output configuration
    output_dir: Optional[str] = Field(
        default=None, description="Output directory for processed files"
    )
    format: str = Field(default="json", description="Default output format")

    # Nested configurations
    semantic: SemanticConfig = Field(default_factory=SemanticConfig)
    chunk: ChunkConfig = Field(default_factory=ChunkConfig)
    quality: QualityConfig = Field(default_factory=QualityConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)

    @field_validator("semantic", mode="before")
    @classmethod
    def coerce_semantic(cls, v: Any) -> SemanticConfig:
        """Coerce dict to SemanticConfig."""
        if isinstance(v, dict):
            return SemanticConfig(**v)
        return v

    @field_validator("chunk", mode="before")
    @classmethod
    def coerce_chunk(cls, v: Any) -> ChunkConfig:
        """Coerce dict to ChunkConfig."""
        if isinstance(v, dict):
            return ChunkConfig(**v)
        return v

    @field_validator("quality", mode="before")
    @classmethod
    def coerce_config_quality(cls, v: Any) -> QualityConfig:
        """Coerce dict to QualityConfig."""
        if isinstance(v, dict):
            return QualityConfig(**v)
        return v

    @field_validator("cache", mode="before")
    @classmethod
    def coerce_config_cache(cls, v: Any) -> CacheConfig:
        """Coerce dict to CacheConfig."""
        if isinstance(v, dict):
            return CacheConfig(**v)
        return v


class CliConfig(BaseModel):
    """Root CLI configuration model aggregating all configuration sections.

    This is the top-level configuration model that encompasses all CLI options
    and serves as the primary configuration interface for Story 5-1.

    Attributes:
        semantic: Semantic analysis configuration (TF-IDF, LSA, similarity).
        cache: Cache configuration for performance optimization.
        output: Output formatting configuration.
    """

    model_config = ConfigDict(validate_assignment=True)

    semantic: SemanticConfig = Field(default_factory=SemanticConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

    @field_validator("semantic", mode="before")
    @classmethod
    def coerce_cli_semantic(cls, v: Any) -> SemanticConfig:
        """Coerce dict to SemanticConfig."""
        if isinstance(v, dict):
            return SemanticConfig(**v)
        return v

    @field_validator("cache", mode="before")
    @classmethod
    def coerce_cli_cache(cls, v: Any) -> CacheConfig:
        """Coerce dict to CacheConfig."""
        if isinstance(v, dict):
            return CacheConfig(**v)
        return v

    @field_validator("output", mode="before")
    @classmethod
    def coerce_cli_output(cls, v: Any) -> OutputConfig:
        """Coerce dict to OutputConfig."""
        if isinstance(v, dict):
            return OutputConfig(**v)
        return v
