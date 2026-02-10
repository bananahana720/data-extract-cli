"""
Integration tests for large file processing.

Tests large document fixtures to validate:
- NFR-P2: <2GB memory usage for individual large files
- Timeout handling for large Excel files
- End-to-end OCR pipeline for scanned PDFs

Story: 2.5.3 - Large Document Fixtures & Testing Infrastructure
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="Brownfield migration: module depends on removed brownfield code"
)
