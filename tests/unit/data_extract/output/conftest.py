"""Fixtures for output module tests.

Provides shared test fixtures for all output formatter tests, including
sample chunks, metadata, and entities for testing various output formats.
"""

from datetime import datetime
from pathlib import Path
from typing import List

import pytest

from data_extract.core.models import (
    Chunk,
    ContentBlock,
    ContentType,
    Entity,
    EntityType,
    Metadata,
    Position,
)

# ============================================================================
# METADATA FIXTURES
# ============================================================================


@pytest.fixture
def sample_metadata() -> Metadata:
    """Sample metadata with all required fields for testing.

    Returns:
        Metadata with realistic values for testing output formatters
    """
    return Metadata(
        source_file=Path("/tmp/test_document.pdf"),
        file_hash="abc123def456",
        processing_timestamp=datetime(2024, 11, 30, 12, 0, 0),
        tool_version="1.0.0",
        config_version="1.0",
        document_type=None,
        document_subtype=None,
        quality_scores={"ocr_confidence": 0.95},
        ocr_confidence={1: 0.95, 2: 0.97},
        completeness_ratio=0.98,
        section_context=None,
    )


# ============================================================================
# CHUNK FIXTURES
# ============================================================================


@pytest.fixture
def sample_chunk(sample_metadata: Metadata) -> Chunk:
    """Single chunk with realistic text for testing.

    Returns:
        Chunk with ~100 words of realistic audit content
    """
    text = """Risk management frameworks provide systematic approaches to identifying, assessing,
    and mitigating organizational risks. These frameworks typically include governance structures,
    risk assessment methodologies, control implementation processes, and continuous monitoring
    mechanisms. Effective risk management requires alignment with organizational objectives,
    stakeholder engagement, and integration with strategic planning processes. Controls must be
    designed to address identified risks while maintaining operational efficiency and compliance
    with regulatory requirements. Regular assessment and updating of risk registers ensures that
    emerging threats are identified and managed appropriately."""

    return Chunk(
        id="test_document_001",
        text=text,
        document_id="test_document",
        position_index=0,
        token_count=120,
        word_count=95,
        quality_score=0.85,
        metadata=sample_metadata,
        section_context="Risk Management > Frameworks",
        readability_scores={
            "flesch_reading_ease": 45.2,
            "flesch_kincaid_grade": 12.5,
        },
    )


@pytest.fixture
def chunk_with_entities(sample_metadata: Metadata) -> Chunk:
    """Chunk with entity tags in metadata for testing entity handling.

    Returns:
        Chunk with entity_tags in metadata
    """
    text = """Control CTRL-042 mitigates Risk RISK-001 through automated monitoring
    and alerting mechanisms. This control requires quarterly testing and validation
    to ensure effectiveness."""

    # Create metadata with entity_tags
    metadata_dict = sample_metadata.model_dump()
    metadata_dict["entity_tags"] = ["RISK-001", "CTRL-042"]
    metadata_with_tags = Metadata(**metadata_dict)

    # Create sample entities
    entities = [
        Entity(
            type=EntityType.RISK,
            id="RISK-001",
            text="Risk RISK-001",
            confidence=0.95,
            location={"start": 18, "end": 28},
        ),
        Entity(
            type=EntityType.CONTROL,
            id="CTRL-042",
            text="Control CTRL-042",
            confidence=0.92,
            location={"start": 0, "end": 16},
        ),
    ]

    return Chunk(
        id="test_document_002",
        text=text,
        document_id="test_document",
        position_index=1,
        token_count=35,
        word_count=28,
        quality_score=0.90,
        metadata=metadata_with_tags,
        entities=entities,
        section_context="Controls > Monitoring",
    )


@pytest.fixture
def empty_chunk(sample_metadata: Metadata) -> Chunk:
    """Edge case chunk with minimal content for testing.

    Returns:
        Chunk with minimal valid content
    """
    return Chunk(
        id="test_document_003",
        text="N/A",
        document_id="test_document",
        position_index=2,
        token_count=1,
        word_count=1,
        quality_score=0.50,
        metadata=sample_metadata,
    )


@pytest.fixture
def sample_chunks(sample_metadata: Metadata) -> List[Chunk]:
    """List of varied chunks for batch testing.

    Returns:
        List of 5 chunks with varying content lengths and types
    """
    chunks = []

    # Chunk 1: Long content (~150 words)
    chunks.append(
        Chunk(
            id="batch_001",
            text="""Enterprise risk management encompasses the methods and processes used by
            organizations to manage risks and seize opportunities related to the achievement of
            their objectives. ERM provides a framework for risk management, which typically involves
            identifying particular events or circumstances relevant to the organization's objectives,
            assessing them in terms of likelihood and magnitude of impact, determining a response
            strategy, and monitoring progress. By identifying and proactively addressing risks and
            opportunities, enterprises can protect and create value for their stakeholders, including
            owners, employees, customers, regulators, and society overall. The framework emphasizes
            that risk management is not merely about avoiding risks, but about understanding them to
            make informed decisions that balance risk and reward.""",
            document_id="batch_test",
            position_index=0,
            token_count=150,
            word_count=125,
            quality_score=0.88,
            metadata=sample_metadata,
            section_context="ERM > Overview",
        )
    )

    # Chunk 2: Medium content (~80 words)
    chunks.append(
        Chunk(
            id="batch_002",
            text="""Internal controls are processes designed by an organization's board of directors,
            management, and other personnel to provide reasonable assurance regarding achievement of
            objectives relating to operations, reporting, and compliance. Controls can be preventive,
            detective, or corrective in nature. Effective internal control frameworks typically follow
            the COSO framework principles, which include control environment, risk assessment, control
            activities, information and communication, and monitoring activities.""",
            document_id="batch_test",
            position_index=1,
            token_count=90,
            word_count=75,
            quality_score=0.82,
            metadata=sample_metadata,
            section_context="Controls > Internal Controls",
        )
    )

    # Chunk 3: Short content (~40 words)
    chunks.append(
        Chunk(
            id="batch_003",
            text="""Regulatory compliance requires organizations to adhere to laws, regulations,
            guidelines, and specifications relevant to their business. Non-compliance can result in
            legal penalties, financial losses, and reputational damage.""",
            document_id="batch_test",
            position_index=2,
            token_count=45,
            word_count=38,
            quality_score=0.78,
            metadata=sample_metadata,
            section_context="Compliance > Regulatory",
        )
    )

    # Chunk 4: Very short content (~20 words)
    chunks.append(
        Chunk(
            id="batch_004",
            text="""Audit findings must be documented with sufficient detail to support conclusions
            and recommendations.""",
            document_id="batch_test",
            position_index=3,
            token_count=22,
            word_count=18,
            quality_score=0.75,
            metadata=sample_metadata,
            section_context="Audit > Documentation",
        )
    )

    # Chunk 5: Edge case - minimal content
    chunks.append(
        Chunk(
            id="batch_005",
            text="See appendix for details.",
            document_id="batch_test",
            position_index=4,
            token_count=5,
            word_count=5,
            quality_score=0.60,
            metadata=sample_metadata,
            section_context="References",
        )
    )

    return chunks


# ============================================================================
# CONTENT BLOCK FIXTURES (for future use)
# ============================================================================


@pytest.fixture
def sample_content_block() -> ContentBlock:
    """Sample content block for testing structural output.

    Returns:
        ContentBlock with realistic paragraph content
    """
    return ContentBlock(
        block_type=ContentType.PARAGRAPH,
        content="This is a sample paragraph for testing content block formatting.",
        position=Position(page=1, sequence_index=0),
        metadata={"style": "normal"},
    )


@pytest.fixture
def sample_table_block() -> ContentBlock:
    """Sample table content block for testing table formatting.

    Returns:
        ContentBlock representing a table
    """
    return ContentBlock(
        block_type=ContentType.TABLE,
        content="Risk ID | Description | Severity\nRISK-001 | Data breach | High",
        position=Position(page=1, sequence_index=1),
        metadata={"rows": 2, "columns": 3},
    )
