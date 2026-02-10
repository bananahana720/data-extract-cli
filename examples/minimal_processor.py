"""
Minimal example processor demonstrating the foundation interfaces.

This shows how to implement BaseProcessor using the core data models.
Use this as a template for real processors (context linking, metadata, etc.).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core import (
    BaseProcessor,
    ContentBlock,
    ExtractionResult,
    ProcessingResult,
    ProcessingStage,
)


class WordCountProcessor(BaseProcessor):
    """
    Simple processor that counts words in each content block.

    Demonstrates:
    - How to implement BaseProcessor interface
    - How to enrich ContentBlocks with metadata
    - How to create ProcessingResult
    - How to preserve immutability (create new blocks, don't modify)
    """

    def get_processor_name(self) -> str:
        """Return processor name."""
        return "Word Count Processor"

    def is_optional(self) -> bool:
        """This is a non-critical processor."""
        return True

    def process(self, extraction_result: ExtractionResult) -> ProcessingResult:
        """
        Process extracted content by adding word count metadata.

        Strategy:
        1. Iterate through content blocks
        2. Count words in each block
        3. Create new blocks with enriched metadata (immutable!)
        4. Return ProcessingResult
        """
        errors = []
        warnings = []
        enriched_blocks = []

        try:
            for block in extraction_result.content_blocks:
                # Count words
                word_count = len(block.content.split())

                # Create enriched metadata (add to existing metadata)
                enriched_metadata = {
                    **block.metadata,
                    "word_count": word_count,
                    "is_short": word_count < 10,
                    "is_long": word_count > 100,
                }

                # Create new block with enriched metadata (blocks are immutable)
                enriched_block = ContentBlock(
                    block_id=block.block_id,  # Keep same ID
                    block_type=block.block_type,
                    content=block.content,
                    raw_content=block.raw_content,
                    position=block.position,
                    parent_id=block.parent_id,
                    related_ids=block.related_ids,
                    metadata=enriched_metadata,  # New metadata
                    confidence=block.confidence,
                    style=block.style,
                )
                enriched_blocks.append(enriched_block)

            # Calculate overall statistics
            total_words = sum(block.metadata.get("word_count", 0) for block in enriched_blocks)

            stage_metadata = {
                "total_words": total_words,
                "average_words_per_block": (
                    total_words / len(enriched_blocks) if enriched_blocks else 0
                ),
                "blocks_processed": len(enriched_blocks),
            }

            return ProcessingResult(
                content_blocks=tuple(enriched_blocks),
                document_metadata=extraction_result.document_metadata,
                processing_stage=ProcessingStage.METADATA_AGGREGATION,
                stage_metadata=stage_metadata,
                success=True,
                warnings=tuple(warnings),
            )

        except Exception as e:
            errors.append(f"Processing failed: {str(e)}")
            return ProcessingResult(
                content_blocks=extraction_result.content_blocks,  # Return original
                document_metadata=extraction_result.document_metadata,
                processing_stage=ProcessingStage.METADATA_AGGREGATION,
                success=False,
                errors=tuple(errors),
            )


def main():
    """Example usage showing extractor → processor pipeline."""
    from minimal_extractor import TextFileExtractor

    # Create test file
    test_file = Path("test_document.txt")
    test_file.write_text(
        """Document Title

This is a short paragraph.

This is a much longer paragraph with many more words to demonstrate how the word count processor works. It should be marked as a long paragraph.

Short.

Another medium-length paragraph that falls somewhere in between the short and long examples."""
    )

    # Extract content
    extractor = TextFileExtractor()
    extraction_result = extractor.extract(test_file)

    if not extraction_result.success:
        print("Extraction failed!")
        return

    print(f"Extracted {len(extraction_result.content_blocks)} blocks\n")

    # Process content
    processor = WordCountProcessor()
    processing_result = processor.process(extraction_result)

    if not processing_result.success:
        print("Processing failed!")
        return

    print("[SUCCESS] Processing successful!")
    print("\nStage metadata:")
    for key, value in processing_result.stage_metadata.items():
        print(f"  {key}: {value}")

    print("\nEnriched content blocks:")
    for block in processing_result.content_blocks:
        word_count = block.metadata.get("word_count", 0)
        is_short = block.metadata.get("is_short", False)
        is_long = block.metadata.get("is_long", False)

        flags = []
        if is_short:
            flags.append("SHORT")
        if is_long:
            flags.append("LONG")
        flag_str = f" [{', '.join(flags)}]" if flags else ""

        print(f"  - [{block.block_type.value}] {word_count} words{flag_str}")
        print(f"    {block.content[:60]}...")

    # Cleanup
    test_file.unlink()


if __name__ == "__main__":
    main()
