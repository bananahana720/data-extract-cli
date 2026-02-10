"""
DocxExtractor Usage Examples

Demonstrates how to use the DocxExtractor for various use cases.
This serves as both documentation and a reference implementation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from extractors import DocxExtractor


def basic_extraction_example():
    """Most basic usage: extract content from a DOCX file."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Extraction")
    print("=" * 70)

    # Create extractor with defaults
    extractor = DocxExtractor()

    # Path to your DOCX file
    file_path = Path("path/to/your/document.docx")

    # Check if format is supported
    if not extractor.supports_format(file_path):
        print(f"Error: Format not supported for {file_path}")
        return

    # Extract content
    result = extractor.extract(file_path)

    # Check success
    if result.success:
        print(f"Success! Extracted {len(result.content_blocks)} blocks")

        # Access document metadata
        print(f"\nDocument: {result.document_metadata.title}")
        print(f"Author: {result.document_metadata.author}")
        print(f"Words: {result.document_metadata.word_count}")

        # Access content blocks
        for block in result.content_blocks:
            print(f"\n[{block.block_type.value}] {block.content[:80]}...")
    else:
        print("Extraction failed:")
        for error in result.errors:
            print(f"  - {error}")


def configured_extraction_example():
    """Extraction with custom configuration."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Configured Extraction")
    print("=" * 70)

    # Create extractor with custom config
    config = {
        "max_paragraph_length": 1000,  # Truncate long paragraphs
        "skip_empty": True,  # Skip empty paragraphs
        "extract_styles": True,  # Include style metadata
    }

    extractor = DocxExtractor(config=config)

    file_path = Path("path/to/your/document.docx")
    result = extractor.extract(file_path)

    if result.success:
        print(f"Extracted with config: {len(result.content_blocks)} blocks")

        # Check for warnings (e.g., truncated paragraphs)
        if result.warnings:
            print(f"\nWarnings ({len(result.warnings)}):")
            for warning in result.warnings:
                print(f"  - {warning}")


def metadata_focused_example():
    """Extract only document metadata, not content."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Metadata Extraction")
    print("=" * 70)

    extractor = DocxExtractor()
    file_path = Path("path/to/your/document.docx")

    result = extractor.extract(file_path)

    if result.success:
        meta = result.document_metadata

        print("File Information:")
        print(f"  Path: {meta.source_file}")
        print(f"  Format: {meta.file_format}")
        print(f"  Size: {meta.file_size_bytes:,} bytes")
        print(f"  Hash: {meta.file_hash}")

        print("\nDocument Properties:")
        print(f"  Title: {meta.title or '(none)'}")
        print(f"  Author: {meta.author or '(none)'}")
        print(f"  Subject: {meta.subject or '(none)'}")
        print(f"  Keywords: {', '.join(meta.keywords) if meta.keywords else '(none)'}")

        print("\nDates:")
        print(f"  Created: {meta.created_date}")
        print(f"  Modified: {meta.modified_date}")
        print(f"  Extracted: {meta.extracted_at}")

        print("\nStatistics:")
        print(f"  Word count: {meta.word_count}")
        print(f"  Character count: {meta.character_count}")


def content_type_filtering_example():
    """Filter content blocks by type."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Content Type Filtering")
    print("=" * 70)

    extractor = DocxExtractor()
    file_path = Path("path/to/your/document.docx")

    result = extractor.extract(file_path)

    if result.success:
        from core import ContentType

        # Get only headings
        headings = [
            block for block in result.content_blocks if block.block_type == ContentType.HEADING
        ]

        print(f"Headings ({len(headings)}):")
        for heading in headings:
            print(f"  - {heading.content}")

        # Get only paragraphs
        paragraphs = [
            block for block in result.content_blocks if block.block_type == ContentType.PARAGRAPH
        ]

        print(f"\nParagraphs ({len(paragraphs)}):")
        for para in paragraphs[:3]:  # Show first 3
            print(f"  - {para.content[:60]}...")


def error_handling_example():
    """Demonstrate error handling patterns."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Error Handling")
    print("=" * 70)

    extractor = DocxExtractor()

    # Test various error conditions
    test_cases = [
        Path("nonexistent.docx"),  # File not found
        Path("test_docx_extractor.py"),  # Wrong format
        Path("corrupted.docx"),  # Corrupted file
    ]

    for file_path in test_cases:
        print(f"\nTesting: {file_path}")

        # Check format first
        if not extractor.supports_format(file_path):
            print(f"  Format not supported: {file_path.suffix}")
            continue

        # Try extraction
        result = extractor.extract(file_path)

        if result.success:
            print(f"  Success: {len(result.content_blocks)} blocks")
        else:
            print("  Failed:")
            for error in result.errors:
                print(f"    - {error}")


def batch_extraction_example():
    """Extract from multiple files."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Batch Extraction")
    print("=" * 70)

    extractor = DocxExtractor()

    # Get all DOCX files in directory
    directory = Path("path/to/your/documents")
    docx_files = list(directory.glob("*.docx"))

    print(f"Found {len(docx_files)} DOCX files")

    # Extract from each
    results = []
    for file_path in docx_files:
        print(f"\nExtracting: {file_path.name}")
        result = extractor.extract(file_path)

        if result.success:
            print(f"  ✓ {len(result.content_blocks)} blocks")
            results.append(result)
        else:
            print(f"  ✗ Failed: {result.errors[0]}")

    print(f"\nSuccessfully extracted {len(results)} of {len(docx_files)} files")


def advanced_metadata_example():
    """Access detailed block metadata."""
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Advanced Metadata Access")
    print("=" * 70)

    extractor = DocxExtractor(config={"extract_styles": True})
    file_path = Path("path/to/your/document.docx")

    result = extractor.extract(file_path)

    if result.success:
        print("Block Details:\n")

        for idx, block in enumerate(result.content_blocks[:5]):  # First 5 blocks
            print(f"Block {idx + 1}:")
            print(f"  ID: {block.block_id}")
            print(f"  Type: {block.block_type.value}")
            print(f"  Position: {block.position}")
            print(f"  Confidence: {block.confidence}")

            # Access metadata
            if block.metadata:
                print("  Metadata:")
                for key, value in block.metadata.items():
                    print(f"    {key}: {value}")

            # Content preview
            preview = block.content[:60]
            if len(block.content) > 60:
                preview += "..."
            print(f"  Content: {preview}\n")


def validation_example():
    """Validate file before extraction."""
    print("\n" + "=" * 70)
    print("EXAMPLE 8: Pre-Extraction Validation")
    print("=" * 70)

    extractor = DocxExtractor()
    file_path = Path("path/to/your/document.docx")

    # Validate file before extraction
    is_valid, errors = extractor.validate_file(file_path)

    if is_valid:
        print(f"✓ File is valid: {file_path}")
        print(f"  Format: {extractor.get_format_name()}")
        print(f"  Extensions: {extractor.get_supported_extensions()}")

        # Proceed with extraction
        result = extractor.extract(file_path)
        print(f"  Extracted: {len(result.content_blocks)} blocks")
    else:
        print("✗ File validation failed:")
        for error in errors:
            print(f"  - {error}")


def main():
    """Run all examples (with dummy file paths)."""
    print("\nDocxExtractor Usage Examples")
    print("=" * 70)
    print("\nNOTE: These examples use placeholder paths.")
    print("Replace 'path/to/your/document.docx' with actual file paths.\n")

    # Uncomment to run specific examples:

    # basic_extraction_example()
    # configured_extraction_example()
    # metadata_focused_example()
    # content_type_filtering_example()
    # error_handling_example()
    # batch_extraction_example()
    # advanced_metadata_example()
    # validation_example()

    print("\nTo run examples, uncomment the desired example in main()")
    print("and provide valid file paths.")


if __name__ == "__main__":
    main()
