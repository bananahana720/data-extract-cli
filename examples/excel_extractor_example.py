"""
Excel Extractor Usage Examples

This script demonstrates how to use ExcelExtractor to extract content
from Excel workbooks with various configurations.

Run from project root:
    python examples/excel_extractor_example.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from extractors.excel_extractor import ExcelExtractor


def example_basic_extraction():
    """Example 1: Basic Excel extraction."""
    print("=" * 70)
    print("Example 1: Basic Excel Extraction")
    print("=" * 70)

    # Create extractor
    extractor = ExcelExtractor()

    # Extract from a test file
    test_file = Path(__file__).parent.parent / "tests" / "fixtures" / "excel" / "multi_sheet.xlsx"

    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return

    result = extractor.extract(test_file)

    if result.success:
        print("\n[SUCCESS] Extraction successful!")
        print(f"  - Sheets: {len(result.tables)}")
        print(f"  - Content blocks: {len(result.content_blocks)}")

        # Show sheet names
        sheet_names = {b.position.sheet for b in result.content_blocks if b.position}
        print(f"  - Sheet names: {', '.join(sorted(sheet_names))}")

        # Show sample content
        print(
            f"\n  First table ({result.tables[0].num_rows} rows x {result.tables[0].num_columns} cols):"
        )
        if result.tables[0].cells:
            for i, row in enumerate(result.tables[0].cells[:3]):  # Show first 3 rows
                print(f"    Row {i+1}: {row}")
    else:
        print("\n[FAILED] Extraction failed:")
        for error in result.errors:
            print(f"    - {error}")


def example_with_formulas():
    """Example 2: Extracting workbooks with formulas."""
    print("\n" + "=" * 70)
    print("Example 2: Formula Extraction")
    print("=" * 70)

    # Create extractor with formula extraction enabled
    extractor = ExcelExtractor({"include_formulas": True})

    test_file = Path(__file__).parent.parent / "tests" / "fixtures" / "excel" / "with_formulas.xlsx"

    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return

    result = extractor.extract(test_file)

    if result.success:
        print("\n[SUCCESS] Extraction successful!")

        # Check for formulas in metadata
        for block in result.content_blocks:
            if block.metadata.get("has_formulas"):
                print(f"\n  Sheet '{block.position.sheet}' contains formulas:")
                formulas = block.metadata.get("formulas", {})
                for cell_ref, formula in formulas.items():
                    print(f"    {cell_ref}: {formula}")
    else:
        print("\n[FAILED] Extraction failed")


def example_with_configuration():
    """Example 3: Using configuration options."""
    print("\n" + "=" * 70)
    print("Example 3: Configuration Options")
    print("=" * 70)

    # Configure extractor with limits
    config = {
        "max_rows": 100,  # Limit to 100 rows per sheet
        "max_columns": 50,  # Limit to 50 columns
        "include_formulas": True,  # Extract formulas
        "skip_empty_cells": False,  # Don't skip empty cells
    }

    extractor = ExcelExtractor(config)

    test_file = (
        Path(__file__).parent.parent / "tests" / "fixtures" / "excel" / "simple_single_sheet.xlsx"
    )

    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return

    result = extractor.extract(test_file)

    if result.success:
        print("\n[SUCCESS] Extraction successful with configuration!")
        print(f"  - Max rows limit: {config['max_rows']}")
        print(f"  - Max columns limit: {config['max_columns']}")
        print(f"  - Actual rows extracted: {result.tables[0].num_rows}")
        print(f"  - Actual columns extracted: {result.tables[0].num_columns}")


def example_document_metadata():
    """Example 4: Accessing document metadata."""
    print("\n" + "=" * 70)
    print("Example 4: Document Metadata")
    print("=" * 70)

    extractor = ExcelExtractor()

    test_file = (
        Path(__file__).parent.parent / "tests" / "fixtures" / "excel" / "simple_single_sheet.xlsx"
    )

    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return

    result = extractor.extract(test_file)

    if result.success:
        metadata = result.document_metadata

        print("\n[SUCCESS] Document metadata extracted:")
        print(f"  - File: {metadata.source_file.name}")
        print(f"  - Format: {metadata.file_format}")
        print(f"  - Size: {metadata.file_size_bytes:,} bytes")
        print(f"  - Hash: {metadata.file_hash[:16]}...")
        print(f"  - Table count: {metadata.table_count}")

        if metadata.title:
            print(f"  - Title: {metadata.title}")
        if metadata.author:
            print(f"  - Author: {metadata.author}")
        if metadata.created_date:
            print(f"  - Created: {metadata.created_date}")


def example_error_handling():
    """Example 5: Error handling."""
    print("\n" + "=" * 70)
    print("Example 5: Error Handling")
    print("=" * 70)

    extractor = ExcelExtractor()

    # Try to extract from non-existent file
    nonexistent_file = Path("/tmp/does_not_exist.xlsx")

    result = extractor.extract(nonexistent_file)

    print("\nAttempting to extract from non-existent file:")
    print(f"  File: {nonexistent_file}")
    print(f"  Success: {result.success}")

    if not result.success:
        print(f"  Errors ({len(result.errors)}):")
        for error in result.errors:
            # Show first line of error message
            first_line = error.split("\n")[0]
            print(f"    - {first_line}")


def example_with_infrastructure():
    """Example 6: Using with ConfigManager (infrastructure integration)."""
    print("\n" + "=" * 70)
    print("Example 6: Infrastructure Integration")
    print("=" * 70)

    try:
        import tempfile
        from pathlib import Path

        from infrastructure import ConfigManager

        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
extractors:
  excel:
    max_rows: 1000
    include_formulas: true
    include_charts: true
"""
            )
            config_file = Path(f.name)

        try:
            # Create ConfigManager
            config = ConfigManager(config_file)

            # Create extractor with ConfigManager
            extractor = ExcelExtractor(config)

            print("\n[SUCCESS] ExcelExtractor created with ConfigManager!")
            print(f"  - max_rows: {extractor.max_rows}")
            print(f"  - include_formulas: {extractor.include_formulas}")
            print(f"  - include_charts: {extractor.include_charts}")
        finally:
            # Cleanup
            config_file.unlink()

    except ImportError:
        print("\n  Infrastructure components not available (optional)")
        print("  ExcelExtractor works with dict configuration as fallback")


def main():
    """Run all examples."""
    print("\n")
    print("*" * 70)
    print("* Excel Extractor Usage Examples")
    print("*" * 70)

    example_basic_extraction()
    example_with_formulas()
    example_with_configuration()
    example_document_metadata()
    example_error_handling()
    example_with_infrastructure()

    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  1. ExcelExtractor handles multi-sheet workbooks")
    print("  2. Formulas can be extracted with include_formulas=True")
    print("  3. Configuration limits extraction scope (max_rows, max_columns)")
    print("  4. Rich document metadata is available")
    print("  5. Graceful error handling with detailed messages")
    print("  6. Works with both dict config and ConfigManager")
    print("\n")


if __name__ == "__main__":
    main()
