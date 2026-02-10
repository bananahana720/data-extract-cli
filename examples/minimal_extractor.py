"""
Minimal example extractor demonstrating the foundation interfaces.

This shows how to implement BaseExtractor using the core data models.
Use this as a template for real format extractors (DOCX, PDF, etc.).
"""

import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core import (
    BaseExtractor,
    ContentBlock,
    ContentType,
    DocumentMetadata,
    ExtractionResult,
    Position,
)


class TextFileExtractor(BaseExtractor):
    """
    Simple extractor for plain text files.

    Demonstrates:
    - How to implement BaseExtractor interface
    - How to create ContentBlock objects
    - How to populate ExtractionResult
    - Error handling patterns
    """

    def supports_format(self, file_path: Path) -> bool:
        """Check if file is a text file."""
        return file_path.suffix.lower() in [".txt", ".md", ".log"]

    def get_supported_extensions(self) -> list[str]:
        """Supported file extensions."""
        return [".txt", ".md", ".log"]

    def extract(self, file_path: Path) -> ExtractionResult:
        """
        Extract content from text file.

        Strategy:
        1. Validate file
        2. Read content
        3. Split into paragraphs
        4. Create ContentBlock for each paragraph
        5. Generate metadata
        6. Return ExtractionResult
        """
        errors = []
        warnings = []
        content_blocks = []

        # Step 1: Validate
        is_valid, validation_errors = self.validate_file(file_path)
        if not is_valid:
            return ExtractionResult(
                success=False,
                errors=tuple(validation_errors),
                document_metadata=DocumentMetadata(
                    source_file=file_path,
                    file_format="text",
                ),
            )

        try:
            # Step 2: Read content
            text = file_path.read_text(encoding="utf-8")

            # Step 3: Split into paragraphs
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

            if not paragraphs:
                warnings.append("No content found in file")

            # Step 4: Create ContentBlocks
            for idx, paragraph in enumerate(paragraphs):
                # Detect if this is a heading (simple heuristic: short, no punctuation)
                is_heading = len(paragraph) < 80 and not paragraph.endswith(".")

                block = ContentBlock(
                    block_id=uuid4(),
                    block_type=ContentType.HEADING if is_heading else ContentType.PARAGRAPH,
                    content=paragraph,
                    raw_content=paragraph,
                    position=Position(sequence_index=idx),
                    confidence=1.0,  # High confidence for plain text
                    metadata={
                        "char_count": len(paragraph),
                        "word_count": len(paragraph.split()),
                    },
                )
                content_blocks.append(block)

            # Step 5: Generate metadata
            metadata = DocumentMetadata(
                source_file=file_path,
                file_format="text",
                file_size_bytes=file_path.stat().st_size,
                word_count=len(text.split()),
                character_count=len(text),
            )

            # Step 6: Return result
            return ExtractionResult(
                content_blocks=tuple(content_blocks),
                document_metadata=metadata,
                success=True,
                warnings=tuple(warnings),
            )

        except UnicodeDecodeError:
            errors.append("File is not valid UTF-8 text")
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")

        # Return failed result
        return ExtractionResult(
            success=False,
            errors=tuple(errors),
            document_metadata=DocumentMetadata(
                source_file=file_path,
                file_format="text",
            ),
        )


def main():
    """Example usage of the TextFileExtractor."""
    # Create a test file
    test_file = Path("test_document.txt")
    test_file.write_text(
        """Introduction

This is a sample document to demonstrate the extraction system.
It has multiple paragraphs that will be extracted as separate content blocks.

Key Features

The extractor identifies headings and paragraphs.
Each block has metadata including position and confidence.

This shows how the foundation models work together."""
    )

    # Create extractor
    extractor = TextFileExtractor()

    # Check if supported
    if not extractor.supports_format(test_file):
        print(f"Format not supported: {test_file.suffix}")
        return

    # Extract content
    print(f"Extracting content from {test_file}...")
    result = extractor.extract(test_file)

    # Display results
    if result.success:
        print("\n[SUCCESS] Extraction successful!")
        print(f"  Blocks: {len(result.content_blocks)}")
        print(f"  Words: {result.document_metadata.word_count}")
        print(f"  Characters: {result.document_metadata.character_count}")

        print("\nContent blocks:")
        for block in result.content_blocks:
            print(f"  - [{block.block_type.value}] {block.content[:60]}...")
    else:
        print("\n[FAILED] Extraction failed:")
        for error in result.errors:
            print(f"  - {error}")

    # Cleanup
    test_file.unlink()


if __name__ == "__main__":
    main()
