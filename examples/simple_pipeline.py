"""
Simple Pipeline Demo - End-to-End Data Flow

Demonstrates: Extract → Process → Format → Output

This script shows the complete data flow through the system:
1. TextExtractor - Parse text file into ContentBlocks
2. WordCountProcessor - Enrich with word count metadata
3. JsonFormatter - Convert to JSON output
4. Save to file

Usage:
    python examples/simple_pipeline.py examples/sample_input.txt
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import our working examples
from minimal_extractor import TextFileExtractor
from minimal_processor import WordCountProcessor

from core import (
    BaseFormatter,
    FormattedOutput,
    ProcessingResult,
)


class JsonFormatter(BaseFormatter):
    """
    Simple JSON formatter for demo.

    Converts ProcessingResult to structured JSON output.
    """

    def get_format_type(self) -> str:
        """Return format type identifier."""
        return "json"

    def format(self, processing_result: ProcessingResult) -> FormattedOutput:
        """
        Format processing result as JSON.

        Structure:
        {
            "document": {...metadata...},
            "statistics": {...processing stats...},
            "content": [
                {
                    "type": "heading",
                    "content": "...",
                    "metadata": {...}
                },
                ...
            ]
        }
        """
        try:
            # Build document section
            doc = processing_result.document_metadata
            document_info = {
                "source": str(doc.source_file),
                "format": doc.file_format,
                "size_bytes": doc.file_size_bytes,
                "word_count": doc.word_count,
                "character_count": doc.character_count,
            }

            # Build statistics section from processing stage
            statistics = {
                "processing_stage": processing_result.processing_stage.value,
                "quality_score": processing_result.quality_score,
                "total_blocks": len(processing_result.content_blocks),
                **processing_result.stage_metadata,
            }

            # Build content section
            content_list = []
            for block in processing_result.content_blocks:
                block_data = {
                    "type": block.block_type.value,
                    "content": block.content,
                    "metadata": block.metadata,
                }

                # Add position if available
                if block.position:
                    block_data["position"] = {
                        "sequence": block.position.sequence_index,
                    }

                content_list.append(block_data)

            # Assemble final structure
            output_data = {
                "document": document_info,
                "statistics": statistics,
                "content": content_list,
            }

            # Convert to JSON string
            json_content = json.dumps(output_data, indent=2)

            return FormattedOutput(
                content=json_content,
                format_type="json",
                source_document=doc.source_file,
                success=True,
            )

        except Exception as e:
            return FormattedOutput(
                content="{}",
                format_type="json",
                source_document=processing_result.document_metadata.source_file,
                success=False,
                errors=(f"Formatting failed: {str(e)}",),
            )


def run_pipeline(input_file: Path, output_file: Path) -> bool:
    """
    Run the complete pipeline: Extract → Process → Format → Save

    Args:
        input_file: Path to input text file
        output_file: Path to save JSON output

    Returns:
        True if pipeline succeeded, False otherwise
    """
    print("=" * 70)
    print("SIMPLE PIPELINE DEMO - End-to-End Data Flow")
    print("=" * 70)
    print()

    # Stage 1: EXTRACTION
    print("[STAGE 1] EXTRACTION")
    print(f"  Input: {input_file}")
    print("  Extractor: TextFileExtractor")

    extractor = TextFileExtractor()

    if not extractor.supports_format(input_file):
        print(f"  ERROR: Format not supported - {input_file.suffix}")
        return False

    extraction_result = extractor.extract(input_file)

    if not extraction_result.success:
        print("  ERROR: Extraction failed")
        for error in extraction_result.errors:
            print(f"    - {error}")
        return False

    print(f"  SUCCESS: Extracted {len(extraction_result.content_blocks)} content blocks")
    print(
        f"  Document: {extraction_result.document_metadata.word_count} words, "
        f"{extraction_result.document_metadata.character_count} chars"
    )
    print()

    # Stage 2: PROCESSING
    print("[STAGE 2] PROCESSING")
    print("  Processor: WordCountProcessor")

    processor = WordCountProcessor()
    processing_result = processor.process(extraction_result)

    if not processing_result.success:
        print("  ERROR: Processing failed")
        for error in processing_result.errors:
            print(f"    - {error}")
        return False

    print(f"  SUCCESS: Enriched {len(processing_result.content_blocks)} blocks")
    print("  Statistics:")
    for key, value in processing_result.stage_metadata.items():
        print(f"    - {key}: {value}")
    print()

    # Stage 3: FORMATTING
    print("[STAGE 3] FORMATTING")
    print("  Formatter: JsonFormatter")

    formatter = JsonFormatter()
    formatted_output = formatter.format(processing_result)

    if not formatted_output.success:
        print("  ERROR: Formatting failed")
        for error in formatted_output.errors:
            print(f"    - {error}")
        return False

    print(f"  SUCCESS: Generated {len(formatted_output.content)} bytes of JSON")
    print()

    # Stage 4: OUTPUT
    print("[STAGE 4] OUTPUT")
    print(f"  Output: {output_file}")

    try:
        output_file.write_text(formatted_output.content, encoding="utf-8")
        print(f"  SUCCESS: Saved to {output_file}")
    except Exception as e:
        print(f"  ERROR: Failed to save - {str(e)}")
        return False

    print()

    # Final summary
    print("=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print()
    print("Data Flow Summary:")
    print(f"  Input:  {input_file.name}")
    print(f"  Blocks: {len(extraction_result.content_blocks)}")
    print(f"  Words:  {extraction_result.document_metadata.word_count}")
    print(f"  Output: {output_file.name}")
    print()
    print("Sample Content Blocks:")
    for i, block in enumerate(processing_result.content_blocks[:3], 1):
        word_count = block.metadata.get("word_count", 0)
        content_preview = block.content[:60] + "..." if len(block.content) > 60 else block.content
        print(f"  {i}. [{block.block_type.value}] {word_count} words")
        print(f"     {content_preview}")

    if len(processing_result.content_blocks) > 3:
        print(f"  ... and {len(processing_result.content_blocks) - 3} more blocks")

    print()
    return True


def main():
    """Main entry point."""
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python simple_pipeline.py <input_file> [output_file]")
        print()
        print("Example:")
        print("  python examples/simple_pipeline.py examples/sample_input.txt")
        sys.exit(1)

    input_file = Path(sys.argv[1])

    # Determine output file
    if len(sys.argv) >= 3:
        output_file = Path(sys.argv[2])
    else:
        # Default: same name as input but .json extension
        output_file = input_file.with_suffix(".json")

    # Validate input
    if not input_file.exists():
        print(f"ERROR: Input file not found - {input_file}")
        sys.exit(1)

    # Run pipeline
    success = run_pipeline(input_file, output_file)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
