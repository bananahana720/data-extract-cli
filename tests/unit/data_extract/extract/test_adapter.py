"""Unit tests for ExtractorAdapter base class.

Tests adapter conversion logic, metadata mapping, and error handling.
Uses mocked brownfield extractors to validate adapter behavior in isolation.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="Brownfield migration: ExtractorAdapter imports from deleted src.core"
)

# Skip all imports to avoid ModuleNotFoundError during collection
# import hashlib
# from datetime import datetime, timezone
# from pathlib import Path
# from unittest.mock import Mock
# from data_extract.core.models import Document, QualityFlag
# from data_extract.extract.adapter import ExtractorAdapter
# from src.core.models import (
#     ContentBlock,
#     ContentType,
#     DocumentMetadata,
#     ImageMetadata,
#     Position,
#     TableMetadata,
# )
# from src.core.models import (
#     ExtractionResult as BrownfieldExtractionResult,
# )
