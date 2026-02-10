"""
PDF Extractor Usage Examples

This script demonstrates how to use the PdfExtractor to extract content
from PDF files with various configurations.

Examples:
1. Basic extraction with defaults
2. Using ConfigManager for configuration
3. Extracting with tables and images
4. Handling errors gracefully
5. Performance optimization
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from extractors import PdfExtractor
from infrastructure import ConfigManager


def example_1_basic_extraction():
    """Example 1: Basic PDF extraction with default settings."""
    print("\n" + "=" * 60)
    print("Example 1: Basic PDF Extraction")
    print("=" * 60)

    # Create extractor with defaults
    extractor = PdfExtractor()

    # Create a sample PDF for testing
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    pdf_path = Path("sample.pdf")
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.drawString(100, 750, "Hello from PDF!")
    c.drawString(100, 730, "This is a sample PDF document.")
    c.drawString(100, 710, "PdfExtractor can extract this text.")
    c.showPage()
    c.save()

    # Extract content
    result = extractor.extract(pdf_path)

    # Check results
    if result.success:
        print(f"\n[SUCCESS] Extracted {len(result.content_blocks)} blocks")
        print(f"Pages: {result.document_metadata.page_count}")
        print(f"File size: {result.document_metadata.file_size_bytes} bytes")

        print("\nExtracted Content:")
        for i, block in enumerate(result.content_blocks, 1):
            print(f"\nBlock {i} (Page {block.position.page}):")
            print(f"  {block.content[:100]}...")
    else:
        print("\n[ERROR] Extraction failed:")
        for error in result.errors:
            print(f"  - {error}")

    # Cleanup
    pdf_path.unlink()


def example_2_with_config():
    """Example 2: Using ConfigManager for configuration."""
    print("\n" + "=" * 60)
    print("Example 2: Extraction with ConfigManager")
    print("=" * 60)

    # Create config file
    config_path = Path("pdf_config.yaml")
    config_path.write_text(
        """
extractors:
  pdf:
    use_ocr: false          # Disable OCR for faster processing
    extract_images: true    # Extract image metadata
    extract_tables: true    # Extract table structures
    min_text_threshold: 5   # Minimum characters to consider as text
"""
    )

    # Load config
    config = ConfigManager(config_path)

    # Create extractor with config
    extractor = PdfExtractor(config)

    print("\nConfiguration loaded:")
    print(f"  OCR enabled: {extractor.use_ocr}")
    print(f"  Extract images: {extractor.extract_images}")
    print(f"  Extract tables: {extractor.extract_tables}")

    # Cleanup
    config_path.unlink()


def example_3_extract_tables():
    """Example 3: Extracting tables from PDF."""
    print("\n" + "=" * 60)
    print("Example 3: Table Extraction")
    print("=" * 60)

    # Create PDF with table
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

    pdf_path = Path("table_sample.pdf")

    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)

    # Create table data
    data = [
        ["Product", "Price", "Quantity"],
        ["Widget A", "$19.99", "100"],
        ["Widget B", "$29.99", "50"],
        ["Widget C", "$39.99", "25"],
    ]

    table = Table(data)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )

    doc.build([table])

    # Extract with table support
    extractor = PdfExtractor(config={"extract_tables": True})
    result = extractor.extract(pdf_path)

    if result.success:
        print(f"\n[SUCCESS] Found {len(result.tables)} table(s)")

        for i, table_meta in enumerate(result.tables, 1):
            print(f"\nTable {i}:")
            print(f"  Rows: {table_meta.num_rows}")
            print(f"  Columns: {table_meta.num_columns}")
            print(f"  Has header: {table_meta.has_header}")

            if table_meta.header_row:
                print(f"  Headers: {', '.join(table_meta.header_row)}")
    else:
        print("\n[ERROR] Extraction failed")

    # Cleanup
    pdf_path.unlink()


def example_4_error_handling():
    """Example 4: Graceful error handling."""
    print("\n" + "=" * 60)
    print("Example 4: Error Handling")
    print("=" * 60)

    extractor = PdfExtractor()

    # Try to extract from non-existent file
    result = extractor.extract(Path("nonexistent.pdf"))

    if not result.success:
        print("\n[EXPECTED] Extraction failed for missing file:")
        for error in result.errors:
            print(f"  - {error}")

    # Try to extract from corrupted PDF
    corrupted_path = Path("corrupted.pdf")
    corrupted_path.write_text("This is not a valid PDF")

    result = extractor.extract(corrupted_path)

    if not result.success:
        print("\n[EXPECTED] Extraction failed for corrupted file:")
        for error in result.errors:
            print(f"  - {error}")

    # Cleanup
    corrupted_path.unlink()


def example_5_metadata_extraction():
    """Example 5: Document metadata extraction."""
    print("\n" + "=" * 60)
    print("Example 5: Metadata Extraction")
    print("=" * 60)

    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    pdf_path = Path("metadata_sample.pdf")

    # Create PDF with metadata
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    # Set document properties (note: reportlab doesn't support all metadata fields)
    c.setTitle("Sample PDF Document")
    c.setAuthor("PdfExtractor Example")
    c.setSubject("Demonstrating metadata extraction")

    c.drawString(100, 750, "This PDF has metadata")
    c.showPage()
    c.save()

    # Extract
    extractor = PdfExtractor()
    result = extractor.extract(pdf_path)

    if result.success:
        metadata = result.document_metadata

        print("\n[SUCCESS] Document Metadata:")
        print(f"  Title: {metadata.title}")
        print(f"  Author: {metadata.author}")
        print(f"  Subject: {metadata.subject}")
        print(f"  Pages: {metadata.page_count}")
        print(f"  File size: {metadata.file_size_bytes} bytes")
        print(f"  File hash: {metadata.file_hash[:16]}...")
        print(f"  Created: {metadata.created_date}")
        print(f"  Modified: {metadata.modified_date}")

    # Cleanup
    pdf_path.unlink()


def example_6_multi_page():
    """Example 6: Multi-page document extraction."""
    print("\n" + "=" * 60)
    print("Example 6: Multi-Page Document")
    print("=" * 60)

    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    pdf_path = Path("multipage.pdf")

    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    # Create 3 pages
    for page_num in range(1, 4):
        c.drawString(100, 750, f"This is page {page_num}")
        c.drawString(100, 730, f"Content on page {page_num}")
        c.showPage()

    c.save()

    # Extract
    extractor = PdfExtractor()
    result = extractor.extract(pdf_path)

    if result.success:
        print(f"\n[SUCCESS] Extracted {result.document_metadata.page_count} pages")
        print(f"Total blocks: {len(result.content_blocks)}")

        # Group by page
        pages = {}
        for block in result.content_blocks:
            page_num = block.position.page
            if page_num not in pages:
                pages[page_num] = []
            pages[page_num].append(block)

        for page_num in sorted(pages.keys()):
            blocks = pages[page_num]
            print(f"\nPage {page_num}: {len(blocks)} block(s)")
            for block in blocks:
                preview = block.content[:50]
                print(f"  - {preview}...")

    # Cleanup
    pdf_path.unlink()


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("PDF Extractor Usage Examples")
    print("=" * 60)

    examples = [
        example_1_basic_extraction,
        example_2_with_config,
        example_3_extract_tables,
        example_4_error_handling,
        example_5_metadata_extraction,
        example_6_multi_page,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n[ERROR in {example.__name__}]: {str(e)}")

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
