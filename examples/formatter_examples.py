"""
Formatter Usage Examples

Demonstrates how to use all three output formatters:
- JsonFormatter: Hierarchical JSON output
- MarkdownFormatter: Human-readable Markdown
- ChunkedTextFormatter: Token-limited text chunks

Run this file to see example output from each formatter.
"""

# Add parent directory to path for imports
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.models import (
    ContentBlock,
    ContentType,
    DocumentMetadata,
    Position,
    ProcessingResult,
    ProcessingStage,
)
from src.formatters import (
    ChunkedTextFormatter,
    JsonFormatter,
    MarkdownFormatter,
)


def create_sample_processing_result() -> ProcessingResult:
    """
    Create a sample ProcessingResult for demonstration.

    Returns:
        ProcessingResult with various content types
    """
    # Create some sample content blocks
    heading_id = uuid4()
    subheading_id = uuid4()

    blocks = [
        ContentBlock(
            block_id=heading_id,
            block_type=ContentType.HEADING,
            content="Sample Document: Formatter Demonstration",
            position=Position(page=1, sequence_index=0),
            metadata={"level": 1},
        ),
        ContentBlock(
            block_id=uuid4(),
            block_type=ContentType.PARAGRAPH,
            content="This is a sample document demonstrating the three output formatters. "
            "Each formatter produces a different representation of the same content.",
            position=Position(page=1, sequence_index=1),
            parent_id=heading_id,
        ),
        ContentBlock(
            block_id=subheading_id,
            block_type=ContentType.HEADING,
            content="Features of the Formatters",
            position=Position(page=1, sequence_index=2),
            parent_id=heading_id,
            metadata={"level": 2},
        ),
        ContentBlock(
            block_id=uuid4(),
            block_type=ContentType.LIST_ITEM,
            content="JsonFormatter: Produces structured JSON with full metadata",
            position=Position(page=1, sequence_index=3),
            parent_id=subheading_id,
            metadata={"list_type": "bullet"},
        ),
        ContentBlock(
            block_id=uuid4(),
            block_type=ContentType.LIST_ITEM,
            content="MarkdownFormatter: Creates clean, readable Markdown",
            position=Position(page=1, sequence_index=4),
            parent_id=subheading_id,
            metadata={"list_type": "bullet"},
        ),
        ContentBlock(
            block_id=uuid4(),
            block_type=ContentType.LIST_ITEM,
            content="ChunkedTextFormatter: Splits content into token-limited chunks",
            position=Position(page=1, sequence_index=5),
            parent_id=subheading_id,
            metadata={"list_type": "bullet"},
        ),
        ContentBlock(
            block_id=uuid4(),
            block_type=ContentType.QUOTE,
            content="These formatters make it easy to integrate document extraction "
            "with downstream AI processing pipelines.",
            position=Position(page=2, sequence_index=6),
        ),
        ContentBlock(
            block_id=uuid4(),
            block_type=ContentType.CODE,
            content="# Example usage\nfrom src.formatters import JsonFormatter\n\n"
            "formatter = JsonFormatter()\nresult = formatter.format(processing_result)",
            position=Position(page=2, sequence_index=7),
            metadata={"language": "python"},
        ),
    ]

    metadata = DocumentMetadata(
        source_file=Path("sample_document.docx"),
        file_format="docx",
        file_size_bytes=25600,
        title="Formatter Demonstration",
        author="Data Extraction Tool",
        created_date=datetime(2025, 10, 29),
        page_count=2,
        word_count=85,
    )

    return ProcessingResult(
        content_blocks=tuple(blocks),
        document_metadata=metadata,
        processing_stage=ProcessingStage.FORMATTING,
        quality_score=98.5,
        success=True,
    )


def demonstrate_json_formatter():
    """Demonstrate JsonFormatter usage."""
    print("=" * 80)
    print("JSON FORMATTER DEMONSTRATION")
    print("=" * 80)

    result = create_sample_processing_result()

    # Example 1: Flat JSON structure
    print("\n1. Flat JSON Structure (default):")
    print("-" * 40)
    formatter = JsonFormatter(config={"pretty_print": True, "hierarchical": False})
    output = formatter.format(result)
    print(output.content[:500] + "...\n")  # Show first 500 chars

    # Example 2: Hierarchical JSON structure
    print("\n2. Hierarchical JSON Structure:")
    print("-" * 40)
    formatter = JsonFormatter(config={"pretty_print": True, "hierarchical": True})
    output = formatter.format(result)
    print(output.content[:500] + "...\n")

    # Example 3: Compact JSON
    print("\n3. Compact JSON (no pretty-print):")
    print("-" * 40)
    formatter = JsonFormatter(config={"pretty_print": False})
    output = formatter.format(result)
    print(output.content[:200] + "...\n")

    print(f"Status: {output.success}")
    print(f"Format: {output.format_type}")
    print()


def demonstrate_markdown_formatter():
    """Demonstrate MarkdownFormatter usage."""
    print("=" * 80)
    print("MARKDOWN FORMATTER DEMONSTRATION")
    print("=" * 80)

    result = create_sample_processing_result()

    # Example 1: Default markdown
    print("\n1. Default Markdown Output:")
    print("-" * 40)
    formatter = MarkdownFormatter()
    output = formatter.format(result)
    print(output.content)
    print()

    # Example 2: Markdown with heading offset
    print("\n2. Markdown with Heading Offset (all headings +1 level):")
    print("-" * 40)
    formatter = MarkdownFormatter(config={"heading_offset": 1})
    output = formatter.format(result)
    print(output.content[:400] + "...\n")

    # Example 3: Markdown without frontmatter
    print("\n3. Markdown without Frontmatter:")
    print("-" * 40)
    formatter = MarkdownFormatter(config={"include_frontmatter": False})
    output = formatter.format(result)
    print(output.content[:300] + "...\n")

    print(f"Status: {output.success}")
    print(f"Format: {output.format_type}")
    print()


def demonstrate_chunked_formatter():
    """Demonstrate ChunkedTextFormatter usage."""
    print("=" * 80)
    print("CHUNKED TEXT FORMATTER DEMONSTRATION")
    print("=" * 80)

    result = create_sample_processing_result()

    # Example 1: Default token limit (should fit in one chunk)
    print("\n1. Default Token Limit (8000 tokens):")
    print("-" * 40)
    formatter = ChunkedTextFormatter()
    output = formatter.format(result)
    print(output.content)
    print(f"\nNumber of chunks: {1 + len(output.additional_files)}")
    print()

    # Example 2: Small token limit (force multiple chunks)
    print("\n2. Small Token Limit (50 tokens - forces multiple chunks):")
    print("-" * 40)
    formatter = ChunkedTextFormatter(config={"token_limit": 50})
    output = formatter.format(result)
    print("First chunk:")
    print(output.content[:400] + "...")
    print(f"\nNumber of chunks: {1 + len(output.additional_files)}")
    if output.additional_files:
        print("Additional chunk files:")
        for filepath in output.additional_files:
            print(f"  - {filepath}")
    print()

    # Example 3: Without context headers
    print("\n3. Without Context Headers:")
    print("-" * 40)
    formatter = ChunkedTextFormatter(
        config={
            "token_limit": 50,
            "include_context_headers": False,
        }
    )
    output = formatter.format(result)
    print(output.content[:300] + "...\n")

    print(f"Status: {output.success}")
    print(f"Format: {output.format_type}")
    if output.warnings:
        print("Warnings:")
        for warning in output.warnings:
            print(f"  - {warning}")
    print()


def demonstrate_formatter_comparison():
    """Compare all three formatters side-by-side."""
    print("=" * 80)
    print("FORMATTER COMPARISON")
    print("=" * 80)

    result = create_sample_processing_result()

    formatters = [
        ("JSON", JsonFormatter(config={"pretty_print": True})),
        ("Markdown", MarkdownFormatter()),
        ("Chunked Text", ChunkedTextFormatter(config={"token_limit": 1000})),
    ]

    for name, formatter in formatters:
        output = formatter.format(result)
        print(f"\n{name} Formatter:")
        print("-" * 40)
        print(f"Format Type: {output.format_type}")
        print(f"Content Length: {len(output.content)} characters")
        print(f"Success: {output.success}")
        print(f"Additional Files: {len(output.additional_files)}")
        if output.warnings:
            print(f"Warnings: {len(output.warnings)}")


def main():
    """Run all demonstrations."""
    print("\n")
    print("*" * 80)
    print("*" + " " * 78 + "*")
    print("*" + "  FORMATTER USAGE EXAMPLES".center(78) + "*")
    print("*" + " " * 78 + "*")
    print("*" * 80)
    print("\n")

    try:
        demonstrate_json_formatter()
        demonstrate_markdown_formatter()
        demonstrate_chunked_formatter()
        demonstrate_formatter_comparison()

        print("\n")
        print("=" * 80)
        print("All demonstrations completed successfully!")
        print("=" * 80)
        print("\n")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
