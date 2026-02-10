"""
PowerPoint Extractor Usage Examples

Demonstrates how to use the PptxExtractor to extract content from PowerPoint presentations.

Examples cover:
- Basic extraction
- Configuration options
- Infrastructure integration
- Error handling
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core import ContentType
from extractors.pptx_extractor import PptxExtractor


def example_basic_extraction():
    """Example 1: Basic PowerPoint extraction."""
    print("\n=== Example 1: Basic Extraction ===")

    # Create extractor
    extractor = PptxExtractor()

    # Extract from a PowerPoint file
    pptx_file = Path("presentation.pptx")

    if pptx_file.exists():
        result = extractor.extract(pptx_file)

        if result.success:
            print(f"Extracted {len(result.content_blocks)} content blocks")
            print(f"From {result.document_metadata.page_count} slides")

            # Show first few blocks
            for block in result.content_blocks[:5]:
                print(f"\nSlide {block.position.slide}: {block.block_type.value}")
                print(f"  {block.content[:100]}...")
        else:
            print(f"Extraction failed: {result.errors}")
    else:
        print(f"File not found: {pptx_file}")


def example_with_configuration():
    """Example 2: Using configuration options."""
    print("\n=== Example 2: With Configuration ===")

    # Configure extractor
    config = {
        "extract_notes": True,  # Include speaker notes
        "extract_images": True,  # Extract image metadata
        "skip_empty_slides": False,  # Include empty slides
    }

    extractor = PptxExtractor(config)

    pptx_file = Path("presentation.pptx")
    if pptx_file.exists():
        result = extractor.extract(pptx_file)

        # Find speaker notes
        notes = [b for b in result.content_blocks if b.metadata.get("is_speaker_note", False)]

        print(f"Found {len(notes)} speaker notes")
        for note in notes:
            print(f"  Slide {note.position.slide}: {note.content[:50]}...")


def example_with_infrastructure():
    """Example 3: Using infrastructure components."""
    print("\n=== Example 3: With Infrastructure Integration ===")

    try:
        from infrastructure import ConfigManager

        # Create config file
        config_path = Path("config.yaml")
        if not config_path.exists():
            config_path.write_text(
                """
extractors:
  pptx:
    extract_notes: true
    extract_images: false
"""
            )

        # Use ConfigManager
        config = ConfigManager(config_path)
        extractor = PptxExtractor(config)

        print("Configuration loaded:")
        print(f"  extract_notes: {extractor.extract_notes}")
        print(f"  extract_images: {extractor.extract_images}")

    except ImportError:
        print("Infrastructure not available")


def example_slide_by_slide():
    """Example 4: Process slides individually."""
    print("\n=== Example 4: Slide-by-Slide Processing ===")

    extractor = PptxExtractor()
    pptx_file = Path("presentation.pptx")

    if pptx_file.exists():
        result = extractor.extract(pptx_file)

        if result.success:
            # Group blocks by slide
            slides = {}
            for block in result.content_blocks:
                slide_num = block.position.slide
                if slide_num not in slides:
                    slides[slide_num] = []
                slides[slide_num].append(block)

            # Process each slide
            for slide_num in sorted(slides.keys()):
                blocks = slides[slide_num]
                print(f"\nSlide {slide_num}:")
                print(f"  {len(blocks)} content blocks")

                # Find title
                titles = [b for b in blocks if b.block_type == ContentType.HEADING]
                if titles:
                    print(f"  Title: {titles[0].content}")


def example_metadata_extraction():
    """Example 5: Extract presentation metadata."""
    print("\n=== Example 5: Metadata Extraction ===")

    extractor = PptxExtractor()
    pptx_file = Path("presentation.pptx")

    if pptx_file.exists():
        result = extractor.extract(pptx_file)

        if result.success:
            meta = result.document_metadata

            print("Presentation Metadata:")
            print(f"  Title: {meta.title}")
            print(f"  Author: {meta.author}")
            print(f"  Created: {meta.created_date}")
            print(f"  Modified: {meta.modified_date}")
            print(f"  Slides: {meta.page_count}")
            print(f"  Words: {meta.word_count}")
            print(f"  File Size: {meta.file_size_bytes:,} bytes")
            print(f"  SHA256: {meta.file_hash[:16]}...")


def example_error_handling():
    """Example 6: Error handling."""
    print("\n=== Example 6: Error Handling ===")

    extractor = PptxExtractor()

    # Try to extract from non-existent file
    result = extractor.extract(Path("nonexistent.pptx"))

    if not result.success:
        print("Extraction failed (as expected):")
        for error in result.errors:
            print(f"  ERROR: {error}")

    # Try to extract from invalid file
    invalid_file = Path("invalid.txt")
    if not invalid_file.exists():
        invalid_file.write_text("Not a PowerPoint file")

    result = extractor.extract(invalid_file)

    if not result.success:
        print("\nInvalid file handling:")
        for error in result.errors:
            print(f"  ERROR: {error}")


def example_format_detection():
    """Example 7: Format detection."""
    print("\n=== Example 7: Format Detection ===")

    extractor = PptxExtractor()

    # Check supported formats
    print("Supported extensions:", extractor.get_supported_extensions())
    print("Format name:", extractor.get_format_name())

    # Test various file paths
    test_files = [
        "presentation.pptx",
        "document.docx",
        "data.xlsx",
        "report.pdf",
        "PRESENTATION.PPTX",
    ]

    for file_path in test_files:
        path = Path(file_path)
        supported = extractor.supports_format(path)
        print(f"  {file_path}: {'✓ Supported' if supported else '✗ Not supported'}")


def main():
    """Run all examples."""
    print("PowerPoint Extractor Examples")
    print("=" * 60)

    example_basic_extraction()
    example_with_configuration()
    example_with_infrastructure()
    example_slide_by_slide()
    example_metadata_extraction()
    example_error_handling()
    example_format_detection()

    print("\n" + "=" * 60)
    print("Examples complete!")


if __name__ == "__main__":
    main()
