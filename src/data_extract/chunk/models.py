"""Chunk data models (re-exported from core for compatibility).

Story 3.1 uses Chunk model from core/models.py. This module provides
compatibility exports for tests and external code.

Story 3.2 implements ChunkMetadata for entity-aware chunking.
Story 3.3 adds QualityScore for quality scoring.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Re-export Chunk from core for compatibility
from ..core.models import Chunk, Metadata
from .entity_preserver import EntityReference
from .quality import QualityScore


@dataclass(frozen=True)
class ChunkMetadata:
    """Chunk-level metadata for entity-aware chunking and quality scoring (Stories 3.2-3.3).

    Extends document-level Metadata with chunk-specific fields for
    entity tracking, section context, relationship preservation, and quality metrics.
    Immutability enforced per ADR-001 to prevent pipeline state corruption.

    Story 3.2 fields: entity_tags, section_context, entity_relationships
    Story 3.3 fields: quality, source_hash, document_type, word_count, token_count,
                      created_at, processing_version

    Attributes:
        entity_tags: List of EntityReference objects for entities in chunk (AC-3.3-3)
        section_context: Section breadcrumb showing chunk location (AC-3.3-2)
        entity_relationships: Relationship triples within chunk (entity1_id, relation_type, entity2_id)
        source_metadata: Original document metadata for provenance tracking
        quality: Composite quality metrics (readability, OCR, completeness, coherence) (AC-3.3-4, AC-3.3-5)
        source_hash: SHA-256 hash of original source file for immutability verification (AC-3.3-1)
        document_type: Document classification from Epic 2 (report, matrix, export, image) (AC-3.3-1)
        word_count: Number of words in chunk (whitespace split) (AC-3.3-7)
        token_count: Estimated token count (len/4 heuristic) for LLM billing (AC-3.3-7)
        created_at: Processing timestamp for audit trail (AC-3.3-1)
        processing_version: Tool version for reproducibility (AC-3.3-1)

    Example:
        >>> chunk_meta = ChunkMetadata(
        ...     entity_tags=[
        ...         EntityReference(
        ...             entity_type="RISK",
        ...             entity_id="RISK-001",
        ...             start_pos=100,
        ...             end_pos=120,
        ...             is_partial=False,
        ...             context_snippet="...Data breach risk..."
        ...         )
        ...     ],
        ...     section_context="Risk Assessment > Identified Risks",
        ...     entity_relationships=[("RISK-001", "mitigated_by", "CTRL-042")],
        ...     source_metadata=document.metadata,
        ...     quality=QualityScore(
        ...         readability_flesch_kincaid=8.5,
        ...         readability_gunning_fog=10.2,
        ...         ocr_confidence=0.99,
        ...         completeness=0.95,
        ...         coherence=0.88,
        ...         overall=0.93,
        ...         flags=[]
        ...     ),
        ...     source_hash="a3b2c1...",
        ...     document_type="report",
        ...     word_count=150,
        ...     token_count=200,
        ...     created_at=datetime.now(),
        ...     processing_version="1.0.0"
        ... )
        >>> chunk_meta.to_dict()
        {'entity_tags': [...], 'section_context': '...', 'quality': {...}, ...}
    """

    # Chunk-specific fields (Story 3.2)
    entity_tags: List[EntityReference] = field(default_factory=list)
    section_context: str = ""
    entity_relationships: List[Tuple[str, str, str]] = field(default_factory=list)

    # Document provenance (Epic 2 Metadata)
    source_metadata: Optional[Metadata] = field(default=None)

    # Story 3.3 fields - Quality and metadata enrichment
    quality: Optional[QualityScore] = None
    source_hash: Optional[str] = None
    document_type: Optional[str] = None
    word_count: int = 0
    token_count: int = 0
    created_at: Optional[datetime] = None
    processing_version: str = "1.0.0"

    # Story 3.4 fields - JSON output provenance and reproducibility
    source_file: Optional[Path] = None
    config_snapshot: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary.

        AC-3.4-3: Fields never null - use empty string/array/dict for missing data.

        Returns:
            Dict with all ChunkMetadata fields JSON-serializable (Story 3.2 + 3.3 + 3.4 fields)
        """
        return {
            # Story 3.2 fields
            "entity_tags": [ref.to_dict() for ref in self.entity_tags],
            "section_context": self.section_context or "",
            "entity_relationships": [list(rel) for rel in self.entity_relationships],
            "source_metadata": (
                self.source_metadata.model_dump(mode="python") if self.source_metadata else {}
            ),
            # Story 3.3 fields
            "quality": self.quality.to_dict() if self.quality else {},
            "source_hash": self.source_hash or "",
            "document_type": self.document_type or "",
            "word_count": self.word_count,
            "token_count": self.token_count,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "processing_version": self.processing_version or "1.0.0",
            # Story 3.4 fields - JSON output provenance
            "source_file": str(self.source_file) if self.source_file else "",
            "config_snapshot": self.config_snapshot or {},
        }


__all__ = ["Chunk", "ChunkMetadata", "QualityScore"]
