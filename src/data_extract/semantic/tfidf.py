"""TF-IDF vectorization stage for semantic analysis."""

import logging
import time
from typing import List, Optional

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer

from ..core.models import Chunk, ProcessingContext
from ..core.pipeline import PipelineStage
from .cache import CacheManager
from .models import SemanticResult, TfidfConfig

logger = logging.getLogger(__name__)


class TfidfVectorizationStage(PipelineStage[List[Chunk], SemanticResult]):
    """TF-IDF vectorization pipeline stage with intelligent caching.

    Implements the PipelineStage protocol to convert text chunks into TF-IDF vectors,
    with quality filtering, configurable parameters, and aggressive caching for
    performance optimization.
    """

    def __init__(self, config: Optional[TfidfConfig] = None):
        """Initialize TF-IDF vectorization stage.

        Args:
            config: TF-IDF configuration (uses defaults if not provided)
        """
        self.config = config or TfidfConfig()
        self.cache_manager = CacheManager() if self.config.use_cache else None
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._last_cache_key: Optional[str] = None

    def process(
        self, input_data: List[Chunk], context: Optional[ProcessingContext] = None
    ) -> SemanticResult:
        """Process chunks to generate TF-IDF vectors.

        Args:
            input_data: List of text chunks to vectorize
            context: Processing context with configuration and logging

        Returns:
            SemanticResult containing TF-IDF matrix and metadata
        """
        start_time = time.time()

        # Validate input
        if not input_data:
            return SemanticResult(
                success=False,
                error="No chunks provided for vectorization",
                processing_time_ms=0.0,
            )

        # Filter chunks by quality score
        filtered_chunks = self._filter_chunks_by_quality(input_data)
        if not filtered_chunks:
            return SemanticResult(
                success=False,
                error=f"No chunks passed quality threshold ({self.config.quality_threshold})",
                processing_time_ms=(time.time() - start_time) * 1000,
            )

        # Extract text and IDs
        texts = [chunk.text for chunk in filtered_chunks]
        chunk_ids = [chunk.id for chunk in filtered_chunks]

        # Generate cache key if caching is enabled
        cache_key = None
        cache_hit = False
        cached_result = None

        if self.cache_manager:
            # Create deterministic content hash
            content = "\n".join(sorted(texts))  # Sort for determinism
            cache_key = self.cache_manager.generate_cache_key(content, self.config)

            # Try to retrieve from cache
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is not None:
                cache_hit = True
                logger.info(f"Cache hit for key {cache_key}")

        # Use cached result or compute new one
        if cached_result is not None:
            tfidf_matrix = cached_result["matrix"]
            vectorizer = cached_result["vectorizer"]
            vocabulary = cached_result["vocabulary"]
            feature_names = cached_result["feature_names"]
        else:
            # Create and fit vectorizer
            vectorizer = self._create_vectorizer()

            try:
                # Fit and transform texts
                tfidf_matrix = vectorizer.fit_transform(texts)

                # Extract vocabulary and feature names
                vocabulary = vectorizer.vocabulary_
                feature_names = np.array(vectorizer.get_feature_names_out())

                # Cache the result if caching is enabled
                if self.cache_manager and cache_key:
                    cache_data = {
                        "matrix": tfidf_matrix,
                        "vectorizer": vectorizer,
                        "vocabulary": vocabulary,
                        "feature_names": feature_names,
                    }
                    self.cache_manager.set(cache_key, cache_data)
                    logger.info(f"Cached result with key {cache_key}")

            except Exception as e:
                logger.error(f"Vectorization failed: {e}")
                return SemanticResult(
                    success=False,
                    error=f"Vectorization failed: {str(e)}",
                    processing_time_ms=(time.time() - start_time) * 1000,
                )

        # Store vectorizer for later use
        self._vectorizer = vectorizer
        self._last_cache_key = cache_key

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        # Log statistics
        logger.info(
            f"Vectorized {len(filtered_chunks)} chunks "
            f"({len(input_data) - len(filtered_chunks)} filtered out) "
            f"in {processing_time_ms:.1f}ms"
        )
        logger.info(
            f"Matrix shape: {tfidf_matrix.shape}, "
            f"Vocabulary size: {len(vocabulary)}, "
            f"Cache hit: {cache_hit}"
        )

        # Return semantic result
        return SemanticResult(
            tfidf_matrix=tfidf_matrix,
            vectorizer=vectorizer,
            vocabulary=vocabulary,
            feature_names=feature_names,
            chunk_ids=chunk_ids,
            cache_hit=cache_hit,
            processing_time_ms=processing_time_ms,
            success=True,
        )

    def _filter_chunks_by_quality(self, chunks: List[Chunk]) -> List[Chunk]:
        """Filter chunks based on quality score threshold.

        Args:
            chunks: List of chunks to filter

        Returns:
            List of chunks that pass the quality threshold
        """
        filtered = []
        for chunk in chunks:
            # Get quality score - it's a direct attribute in the Chunk model
            quality_score = chunk.quality_score if hasattr(chunk, "quality_score") else 1.0

            # Keep chunk if it passes threshold
            if quality_score >= self.config.quality_threshold:
                filtered.append(chunk)
            else:
                logger.debug(f"Filtered out chunk {chunk.id} with quality score {quality_score}")

        logger.info(
            f"Quality filtering: {len(filtered)}/{len(chunks)} chunks passed "
            f"(threshold={self.config.quality_threshold})"
        )
        return filtered

    def _create_vectorizer(self) -> TfidfVectorizer:
        """Create TF-IDF vectorizer with configuration.

        Returns:
            Configured TfidfVectorizer instance
        """
        # Get vectorizer parameters from config
        params = self.config.to_dict()

        # Add random state for determinism
        # Note: TfidfVectorizer doesn't have random_state, but we set it for consistency
        # The determinism comes from sorted input and fixed configuration

        # Create vectorizer
        vectorizer = TfidfVectorizer(**params)

        logger.debug(f"Created TfidfVectorizer with config: {params}")
        return vectorizer

    def transform(self, chunks: List[Chunk]) -> Optional[csr_matrix]:
        """Transform new chunks using fitted vectorizer.

        Args:
            chunks: List of chunks to transform

        Returns:
            TF-IDF matrix for the chunks, or None if not fitted
        """
        if self._vectorizer is None:
            logger.error("Vectorizer not fitted. Call process() first.")
            return None

        # Filter chunks by quality
        filtered_chunks = self._filter_chunks_by_quality(chunks)
        if not filtered_chunks:
            return None

        # Extract texts
        texts = [chunk.text for chunk in filtered_chunks]

        try:
            # Transform using fitted vectorizer
            tfidf_matrix = self._vectorizer.transform(texts)
            return tfidf_matrix
        except Exception as e:
            logger.error(f"Transform failed: {e}")
            return None

    def get_cache_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if self.cache_manager:
            return self.cache_manager.get_stats()
        return {"cache_enabled": False}

    def clear_cache(self) -> None:
        """Clear the cache."""
        if self.cache_manager:
            self.cache_manager.clear()
            logger.info("Cache cleared")

    def get_config(self) -> TfidfConfig:
        """Get current configuration.

        Returns:
            Current TF-IDF configuration
        """
        return self.config
