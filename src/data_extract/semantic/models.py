"""Semantic analysis models and data structures."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
from scipy.sparse import csr_matrix


@dataclass
class SemanticResult:
    """Result of semantic analysis containing TF-IDF vectors and metadata.

    Contains semantic-specific data like TF-IDF matrices, vocabulary,
    feature names, and chunk identifiers.
    """

    tfidf_matrix: Optional[csr_matrix] = None
    vectorizer: Optional[Any] = None
    vocabulary: Optional[Dict[str, int]] = None
    feature_names: Optional[np.ndarray] = None
    chunk_ids: Optional[List[str]] = None
    cache_hit: bool = False
    processing_time_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        """Initialize data and metadata after dataclass initialization."""
        if self.data is None:
            self.data = {
                "tfidf_matrix": self.tfidf_matrix,
                "vectorizer": self.vectorizer,
                "vocabulary": self.vocabulary,
                "feature_names": self.feature_names,
                "chunk_ids": self.chunk_ids,
            }

        if self.metadata is None:
            self.metadata = {
                "cache_hit": self.cache_hit,
                "processing_time_ms": self.processing_time_ms,
                "matrix_shape": self.tfidf_matrix.shape if self.tfidf_matrix is not None else None,
                "vocabulary_size": len(self.vocabulary) if self.vocabulary else 0,
                "num_chunks": len(self.chunk_ids) if self.chunk_ids else 0,
            }

    def get_chunk_vector(self, chunk_id: str) -> Optional[csr_matrix]:
        """Get TF-IDF vector for a specific chunk.

        Args:
            chunk_id: Identifier of the chunk

        Returns:
            Sparse vector for the chunk, or None if not found
        """
        if not self.chunk_ids or chunk_id not in self.chunk_ids:
            return None
        if self.tfidf_matrix is None:
            return None
        idx = self.chunk_ids.index(chunk_id)
        return self.tfidf_matrix[idx]

    def get_vocabulary_size(self) -> int:
        """Get the size of the vocabulary."""
        return len(self.vocabulary) if self.vocabulary else 0

    def get_num_chunks(self) -> int:
        """Get the number of chunks processed."""
        return len(self.chunk_ids) if self.chunk_ids else 0


@dataclass
class TfidfConfig:
    """Configuration for TF-IDF vectorization.

    Attributes:
        max_features: Maximum number of features (vocabulary size)
        min_df: Minimum document frequency for a term
        max_df: Maximum document frequency for a term
        ngram_range: Range of n-grams to extract
        sublinear_tf: Whether to use sublinear TF scaling
        use_cache: Whether to use caching
        quality_threshold: Minimum quality score for chunks
        random_state: Random state for reproducibility
    """

    max_features: int = 5000
    min_df: int = 2
    max_df: float = 0.95
    ngram_range: tuple = (1, 2)
    sublinear_tf: bool = True
    use_cache: bool = True
    quality_threshold: float = 0.5
    random_state: int = 42

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for vectorizer initialization."""
        return {
            "max_features": self.max_features,
            "min_df": self.min_df,
            "max_df": self.max_df,
            "ngram_range": self.ngram_range,
            "sublinear_tf": self.sublinear_tf,
            "use_idf": True,
            "norm": "l2",
            "smooth_idf": True,
            "token_pattern": r"\b\w+\b",
            "lowercase": True,
            "strip_accents": "unicode",
        }

    def get_cache_key_components(self) -> tuple:
        """Get components for cache key generation.

        Returns:
            Tuple of config values that affect output
        """
        return (
            self.max_features,
            self.min_df,
            self.max_df,
            self.ngram_range,
            self.sublinear_tf,
            self.quality_threshold,
            self.random_state,
        )
