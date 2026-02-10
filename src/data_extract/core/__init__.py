"""Core data models and pipeline architecture.

Exports:
- EntityType: Enum for audit domain entity types
- Entity: Domain entity model with type, id, text, confidence, location
- Metadata: Provenance and quality tracking with entity tags
- Document: Processed document model
- Chunk: Semantic chunk for RAG
- ProcessingContext: Shared pipeline state
- PipelineStage: Pipeline stage protocol (when implemented)
"""

from .models import Chunk, Document, Entity, EntityType, Metadata, ProcessingContext

__all__ = [
    "EntityType",
    "Entity",
    "Metadata",
    "Document",
    "Chunk",
    "ProcessingContext",
]
