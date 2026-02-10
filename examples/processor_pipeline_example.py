"""
Processor Pipeline Example - Chaining Content Processors

This example demonstrates:
- Using multiple processors in sequence
- How processors enrich content blocks
- How metadata flows through the pipeline
- Quality assessment workflow

Pipeline Flow:
    ExtractionResult
         ↓
    ContextLinker (builds hierarchy)
         ↓
    MetadataAggregator (computes statistics)
         ↓
    QualityValidator (scores quality)
         ↓
    Final ProcessingResult

Usage:
    python examples/processor_pipeline_example.py
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import (
    ContentBlock,
    ContentType,
    DocumentMetadata,
    ExtractionResult,
)
from src.processors import (
    ContextLinker,
    MetadataAggregator,
    QualityValidator,
)


def create_sample_document():
    """Create a sample document for processing."""
    blocks = [
        # Document title
        ContentBlock(
            block_type=ContentType.HEADING,
            content="Annual Report 2024",
            metadata={"level": 1},
        ),
        # Introduction section
        ContentBlock(
            block_type=ContentType.HEADING,
            content="Executive Summary",
            metadata={"level": 2},
        ),
        ContentBlock(
            block_type=ContentType.PARAGRAPH,
            content="This report summarizes the company's performance in 2024. "
            "We achieved strong growth across all key metrics.",
        ),
        # Financial section
        ContentBlock(
            block_type=ContentType.HEADING,
            content="Financial Results",
            metadata={"level": 2},
        ),
        ContentBlock(
            block_type=ContentType.PARAGRAPH,
            content="Revenue increased by 25% year-over-year to $5.2 billion.",
        ),
        ContentBlock(
            block_type=ContentType.TABLE,
            content="[Financial data table]",
            metadata={"rows": 5, "cols": 4},
        ),
        # Subsection
        ContentBlock(
            block_type=ContentType.HEADING,
            content="Regional Performance",
            metadata={"level": 3},
        ),
        ContentBlock(
            block_type=ContentType.PARAGRAPH,
            content="North America led growth with 30% increase in sales.",
        ),
        # Conclusion
        ContentBlock(
            block_type=ContentType.HEADING,
            content="Looking Forward",
            metadata={"level": 2},
        ),
        ContentBlock(
            block_type=ContentType.PARAGRAPH,
            content="We remain optimistic about future prospects and plan to expand into new markets.",
        ),
    ]

    return ExtractionResult(
        content_blocks=tuple(blocks),
        document_metadata=DocumentMetadata(
            source_file=Path("annual_report_2024.docx"),
            file_format="docx",
            title="Annual Report 2024",
            page_count=5,
        ),
        success=True,
    )


def print_separator(title: str):
    """Print a section separator."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def demonstrate_individual_processors():
    """Demonstrate each processor individually."""
    print_separator("INDIVIDUAL PROCESSOR DEMONSTRATION")

    document = create_sample_document()

    # 1. ContextLinker
    print("\n[1] ContextLinker - Building Document Hierarchy")
    print("-" * 80)

    context_linker = ContextLinker()
    context_result = context_linker.process(document)

    print(f"  Status: {'SUCCESS' if context_result.success else 'FAILED'}")
    print(f"  Stage: {context_result.processing_stage.value}")
    print("\n  Hierarchy Statistics:")
    print(f"    Blocks processed: {context_result.stage_metadata['blocks_processed']}")
    print(f"    Headings found: {context_result.stage_metadata['heading_count']}")
    print(f"    Max depth: {context_result.stage_metadata['max_depth']}")

    print("\n  Sample Block (with hierarchy metadata):")
    sample_block = context_result.content_blocks[4]  # Paragraph under "Financial Results"
    print(f"    Content: {sample_block.content[:60]}...")
    print(f"    Depth: {sample_block.metadata.get('depth')}")
    print(f"    Document path: {sample_block.metadata.get('document_path')}")

    # 2. MetadataAggregator
    print("\n[2] MetadataAggregator - Computing Statistics")
    print("-" * 80)

    metadata_agg = MetadataAggregator()
    metadata_result = metadata_agg.process(context_result)

    print(f"  Status: {'SUCCESS' if metadata_result.success else 'FAILED'}")
    print("\n  Content Statistics:")
    print(f"    Total words: {metadata_result.stage_metadata['total_words']}")
    print(f"    Total characters: {metadata_result.stage_metadata['total_characters']}")
    print(
        f"    Average words/block: {metadata_result.stage_metadata['average_words_per_block']:.1f}"
    )
    print(f"    Min words: {metadata_result.stage_metadata['min_words_per_block']}")
    print(f"    Max words: {metadata_result.stage_metadata['max_words_per_block']}")

    print("\n  Content Type Distribution:")
    for content_type, count in metadata_result.stage_metadata["content_type_distribution"].items():
        print(f"    {content_type}: {count}")

    print("\n  Summary:")
    summary = metadata_result.stage_metadata["summary"]
    print(f"    Headings: {summary['headings']}")

    # 3. QualityValidator
    print("\n[3] QualityValidator - Assessing Quality")
    print("-" * 80)

    quality_validator = QualityValidator()
    quality_result = quality_validator.process(metadata_result)

    print(f"  Status: {'SUCCESS' if quality_result.success else 'FAILED'}")
    print("\n  Quality Assessment:")
    print(f"    Overall Score: {quality_result.quality_score:.1f}/100")
    print(f"    Needs Review: {quality_result.needs_review}")

    print("\n  Dimension Scores:")
    print(f"    Completeness: {quality_result.stage_metadata['completeness_score']:.1f}/100")
    print(f"    Consistency: {quality_result.stage_metadata['consistency_score']:.1f}/100")
    print(f"    Readability: {quality_result.stage_metadata['readability_score']:.1f}/100")

    if quality_result.quality_issues:
        print("\n  Quality Issues:")
        for issue in quality_result.quality_issues:
            print(f"    - {issue}")
    else:
        print("\n  No quality issues detected!")


def demonstrate_pipeline():
    """Demonstrate chained processor pipeline."""
    print_separator("PROCESSOR PIPELINE DEMONSTRATION")

    document = create_sample_document()

    print("\n  Creating processor pipeline:")
    print("    [1] ContextLinker")
    print("    [2] MetadataAggregator")
    print("    [3] QualityValidator")

    # Create processors
    processors = [
        ContextLinker(),
        MetadataAggregator(),
        QualityValidator(),
    ]

    print("\n  Processing document through pipeline...")

    # Process through pipeline
    current_result = document

    for i, processor in enumerate(processors, 1):
        print(f"\n  [{i}] Running {processor.get_processor_name()}...")

        # Convert ExtractionResult to format expected by processors
        if i == 1:
            processing_result = processor.process(current_result)
        else:
            # Subsequent processors receive ProcessingResult but need ExtractionResult interface
            # In practice, we'd convert ProcessingResult back to ExtractionResult
            # For this demo, we'll create a new ExtractionResult with enriched blocks
            extraction_for_next = ExtractionResult(
                content_blocks=current_result.content_blocks,
                document_metadata=current_result.document_metadata,
                success=True,
            )
            processing_result = processor.process(extraction_for_next)

        current_result = processing_result

        print(f"      Status: {'SUCCESS' if processing_result.success else 'FAILED'}")
        print(f"      Blocks: {len(processing_result.content_blocks)}")

    print("\n  Pipeline complete!")

    # Show final enriched block
    print("\n  Sample Enriched Block:")
    final_block = current_result.content_blocks[4]  # Paragraph
    print(f"    Type: {final_block.block_type.value}")
    print(f"    Content: {final_block.content[:50]}...")
    print(f"    Metadata keys: {list(final_block.metadata.keys())}")

    # Show final statistics
    print("\n  Final Statistics:")
    print(f"    Quality Score: {current_result.quality_score:.1f}/100")
    print(f"    Needs Review: {current_result.needs_review}")
    print(f"    Processing Stage: {current_result.processing_stage.value}")


def demonstrate_error_handling():
    """Demonstrate error handling with problematic content."""
    print_separator("ERROR HANDLING DEMONSTRATION")

    # Create document with quality issues
    problematic_blocks = [
        ContentBlock(
            block_type=ContentType.PARAGRAPH,
            content="",  # Empty block
        ),
        ContentBlock(
            block_type=ContentType.PARAGRAPH,
            content="###!!!***&&&",  # Corrupted text
        ),
        ContentBlock(
            block_type=ContentType.PARAGRAPH,
            content="Normal text here.",
            confidence=0.25,  # Low confidence
        ),
    ]

    problematic_doc = ExtractionResult(
        content_blocks=tuple(problematic_blocks),
        document_metadata=DocumentMetadata(
            source_file=Path("problematic.docx"),
            file_format="docx",
        ),
        success=True,
    )

    print("\n  Processing document with quality issues...")

    # Run through pipeline
    result = ContextLinker().process(problematic_doc)
    result = MetadataAggregator().process(
        ExtractionResult(
            content_blocks=result.content_blocks,
            document_metadata=result.document_metadata,
            success=True,
        )
    )
    result = QualityValidator().process(
        ExtractionResult(
            content_blocks=result.content_blocks,
            document_metadata=result.document_metadata,
            success=True,
        )
    )

    print("\n  Quality Assessment:")
    print(f"    Score: {result.quality_score:.1f}/100")
    print(f"    Needs Review: {result.needs_review}")

    print("\n  Detected Issues:")
    for issue in result.quality_issues:
        print(f"    - {issue}")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 80)
    print("  PROCESSOR PIPELINE EXAMPLE")
    print("  Demonstrating ContextLinker, MetadataAggregator, and QualityValidator")
    print("=" * 80)

    try:
        # Demonstrate individual processors
        demonstrate_individual_processors()

        # Demonstrate full pipeline
        demonstrate_pipeline()

        # Demonstrate error handling
        demonstrate_error_handling()

        print_separator("DEMONSTRATION COMPLETE")
        print("\n  All processors executed successfully!")
        print("  See output above for detailed results.\n")

    except Exception as e:
        print(f"\n  ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
