"""
Performance benchmarks for document extractors.

This module benchmarks all extractors (DOCX, PDF, PPTX, XLSX, TXT) across
different file sizes to establish performance baselines and detect regressions.

Performance Targets (from requirements):
    - Text extraction: <2s per MB
    - OCR extraction: <15s per page
    - Memory: <500MB per file
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="Brownfield migration: module depends on removed brownfield code"
)
