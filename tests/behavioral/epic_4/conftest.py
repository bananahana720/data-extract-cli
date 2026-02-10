"""Shared fixtures and configuration for Epic 4 behavioral tests.

This module provides common fixtures and utilities for all behavioral tests
in the Epic 4 test suite.
"""

import pytest


def pytest_configure(config):
    """Configure pytest with custom markers for behavioral tests."""
    config.addinivalue_line("markers", "behavioral: mark test as a behavioral validation test")
    config.addinivalue_line("markers", "semantic: mark test as related to semantic analysis")
    config.addinivalue_line("markers", "epic4: mark test as part of Epic 4 test suite")
    config.addinivalue_line("markers", "performance: mark test as a performance benchmark")
    config.addinivalue_line(
        "markers", "determinism: mark test as validating deterministic behavior"
    )


@pytest.fixture(scope="session")
def test_report_path(tmp_path_factory):
    """Create a temporary directory for test reports.

    Returns:
        Path to test report directory.
    """
    return tmp_path_factory.mktemp("behavioral_reports")


@pytest.fixture
def behavioral_test_config():
    """Configuration for behavioral tests.

    Returns:
        Dictionary of test configuration parameters.
    """
    return {
        "duplicate_detection": {
            "precision_threshold": 0.85,
            "recall_threshold": 0.80,
            "f1_threshold": 0.825,
            "similarity_threshold": 0.7,
        },
        "cluster_coherence": {
            "silhouette_threshold": 0.65,
            "domain_accuracy_threshold": 0.80,
            "n_components": 100,
            "n_clusters": 10,
        },
        "rag_improvement": {
            "precision_improvement_threshold": 0.25,
            "recall_improvement_threshold": 0.20,
            "mrr_improvement_threshold": 0.15,
            "retrieval_k": 5,
        },
        "performance": {
            "max_processing_time_seconds": 60,
            "max_memory_mb": 500,
            "documents_count": 10000,
            "batch_size": 1000,
        },
        "determinism": {"n_runs": 3, "seed": 42, "decimal_precision": 10},
    }


@pytest.fixture(autouse=True)
def reset_random_state():
    """Reset random state before each test for reproducibility."""
    import random

    import numpy as np

    np.random.seed(42)
    random.seed(42)
    yield
    # Cleanup after test if needed
