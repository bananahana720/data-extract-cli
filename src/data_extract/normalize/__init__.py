"""Text normalization pipeline stage.

This module contains text cleaning and normalization processors:
- Text cleaning and artifact removal (Story 2.1)
- Entity normalization for audit domain (Story 2.2)
- Schema standardization across document types (Story 2.3)
- OCR confidence scoring and validation (Story 2.4)
- Completeness validation and gap detection (Story 2.5)
- Metadata enrichment (Story 2.6)

Type Contract: Document (raw text) → Document (cleaned text, normalized entities)
"""

from .cleaning import CleaningResult, TextCleaner
from .config import NormalizationConfig, load_config, validate_entity_patterns
from .entities import EntityNormalizer
from .normalizer import Normalizer, NormalizerFactory

__all__ = [
    "NormalizationConfig",
    "load_config",
    "validate_entity_patterns",
    "TextCleaner",
    "CleaningResult",
    "EntityNormalizer",
    "Normalizer",
    "NormalizerFactory",
]
