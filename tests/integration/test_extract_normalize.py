"""Integration tests for Extract → Normalize pipeline.

Tests end-to-end flow from file extraction through adapter to normalizer.
Validates that adapted Documents pass Pydantic validation and are accepted
by the greenfield normalizer.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="Brownfield migration: module depends on removed brownfield code"
)
