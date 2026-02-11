from __future__ import annotations

import numpy as np
from scipy.sparse import csr_matrix

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
