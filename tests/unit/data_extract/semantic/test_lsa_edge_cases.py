from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix

from data_extract.semantic.cache import CacheManager
from data_extract.semantic.lsa import LsaConfig, LsaReductionStage
from data_extract.semantic.models import SemanticResult


def test_lsa_handles_single_sample_without_failure() -> None:
    tfidf_matrix = csr_matrix(np.array([[0.4, 0.6]], dtype=float))
    semantic_input = SemanticResult(
        tfidf_matrix=tfidf_matrix,
        feature_names=np.array(["alpha", "beta"]),
        chunk_ids=["doc-1"],
        success=True,
    )

    stage = LsaReductionStage(config=LsaConfig(n_components=100))
    result = stage.process(semantic_input, None)

    assert result.success is True
    assert result.error is None
    assert result.data is not None
    assert "topics" in result.data


def test_lsa_cache_key_uses_full_sparse_content() -> None:
    """Matrices with same shape/nnz/sum must not collide."""
    matrix_a = csr_matrix(np.array([[1.0, 2.0, 0.0], [0.0, 0.0, 3.0]], dtype=float))
    matrix_b = csr_matrix(np.array([[1.0, 0.0, 2.0], [0.0, 3.0, 0.0]], dtype=float))
    feature_names = np.array(["alpha", "beta", "gamma"])

    with tempfile.TemporaryDirectory() as tmpdir:
        CacheManager._reset()
        cache_manager = CacheManager()
        cache_manager._initialized = False
        cache_manager.__init__(cache_dir=Path(tmpdir) / "lsa-cache")

        stage = LsaReductionStage(config=LsaConfig(n_components=100, use_cache=True))
        stage.cache_manager = cache_manager

        key_a = stage._generate_cache_key(matrix_a, feature_names)
        key_b = stage._generate_cache_key(matrix_b, feature_names)

    CacheManager._reset()
    assert key_a != key_b


def test_lsa_process_batch_combines_all_batches() -> None:
    """Batch processing should include every batch, not only the first one."""
    feature_names = np.array(["alpha", "beta", "gamma"])
    batch_1 = SemanticResult(
        tfidf_matrix=csr_matrix(np.array([[1.0, 0.0, 0.0], [0.9, 0.1, 0.0]], dtype=float)),
        feature_names=feature_names,
        chunk_ids=["a1", "a2"],
        success=True,
    )
    batch_2 = SemanticResult(
        tfidf_matrix=csr_matrix(np.array([[0.0, 1.0, 0.0], [0.0, 0.9, 0.1]], dtype=float)),
        feature_names=feature_names,
        chunk_ids=["b1", "b2"],
        success=True,
    )

    stage = LsaReductionStage(config=LsaConfig(n_components=100, use_cache=False))
    result = stage.process_batch([batch_1, batch_2], None)

    assert result.success is True
    assert result.chunk_ids == ["a1", "a2", "b1", "b2"]
    assert result.data is not None
    assert "lsa_vectors" in result.data
    assert result.data["lsa_vectors"].shape[0] == 4
