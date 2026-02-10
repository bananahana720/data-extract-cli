{
  "content_blocks": [
    {
      "block_id": "7bc0deb7-da04-4f11-8a52-dfbc60ead2a1",
      "block_type": "heading",
      "content": "Sample Test Document",
      "raw_content": "Sample Test Document",
      "position": {
        "sequence_index": 0
      },
      "metadata": {
        "char_count": 20,
        "word_count": 3,
        "depth": 0,
        "document_path": [],
        "quality_checked": true
      },
      "confidence": 1.0
    },
    {
      "block_id": "00100166-717c-4654-8546-c916fa933360",
      "block_type": "paragraph",
      "content": "Introduction\nThis is a sample document for testing the text extraction functionality.\nIt contains multiple paragraphs, headings, and different types of content.",
      "raw_content": "Introduction\nThis is a sample document for testing the text extraction functionality.\nIt contains multiple paragraphs, headings, and different types of content.",
      "position": {
        "sequence_index": 1
      },
      "parent_id": "7bc0deb7-da04-4f11-8a52-dfbc60ead2a1",
      "metadata": {
        "char_count": 160,
        "word_count": 22,
        "depth": 1,
        "document_path": [
          "Sample Test Document"
        ],
        "quality_checked": true
      },
      "confidence": 1.0
    },
    {
      "block_id": "d9cc86e1-885d-4154-9f31-cb057eb7804a",
      "block_type": "paragraph",
      "content": "Background\nThe document extraction tool processes various file formats including\nDOCX, PDF, PPTX, and XLSX files. This simple text file serves as a\nbasic fixture for testing core extraction logic.",
      "raw_content": "Background\nThe document extraction tool processes various file formats including\nDOCX, PDF, PPTX, and XLSX files. This simple text file serves as a\nbasic fixture for testing core extraction logic.",
      "position": {
        "sequence_index": 2
      },
      "parent_id": "7bc0deb7-da04-4f11-8a52-dfbc60ead2a1",
      "metadata": {
        "char_count": 196,
        "word_count": 30,
        "depth": 1,
        "document_path": [
          "Sample Test Document"
        ],
        "quality_checked": true
      },
      "confidence": 1.0
    },
    {
      "block_id": "5e5ef199-a14f-4d55-9b45-225a1ecac09e",
      "block_type": "paragraph",
      "content": "Testing Approach\nWhen testing extractors, we follow these patterns:\n1. Test successful extraction with valid files\n2. Test error handling with invalid files\n3. Test format-specific features\n4. Test edge cases like empty or very large files",
      "raw_content": "Testing Approach\nWhen testing extractors, we follow these patterns:\n1. Test successful extraction with valid files\n2. Test error handling with invalid files\n3. Test format-specific features\n4. Test edge cases like empty or very large files",
      "position": {
        "sequence_index": 3
      },
      "parent_id": "7bc0deb7-da04-4f11-8a52-dfbc60ead2a1",
      "metadata": {
        "char_count": 239,
        "word_count": 37,
        "depth": 1,
        "document_path": [
          "Sample Test Document"
        ],
        "quality_checked": true
      },
      "confidence": 1.0
    },
    {
      "block_id": "8551edf6-4fd5-4066-95bc-5378c488ef3a",
      "block_type": "paragraph",
      "content": "Expected Results\nThis file should be extracted as:\n- A heading block for each section title\n- Paragraph blocks for each text section\n- Proper sequence ordering maintained",
      "raw_content": "Expected Results\nThis file should be extracted as:\n- A heading block for each section title\n- Paragraph blocks for each text section\n- Proper sequence ordering maintained",
      "position": {
        "sequence_index": 4
      },
      "parent_id": "7bc0deb7-da04-4f11-8a52-dfbc60ead2a1",
      "metadata": {
        "char_count": 170,
        "word_count": 28,
        "depth": 1,
        "document_path": [
          "Sample Test Document"
        ],
        "quality_checked": true
      },
      "confidence": 1.0
    },
    {
      "block_id": "11d094e9-f73f-4fac-830e-361a23940a05",
      "block_type": "paragraph",
      "content": "Conclusion\nThis fixture file provides a baseline for testing text extraction\ncapabilities of the system.",
      "raw_content": "Conclusion\nThis fixture file provides a baseline for testing text extraction\ncapabilities of the system.",
      "position": {
        "sequence_index": 5
      },
      "parent_id": "7bc0deb7-da04-4f11-8a52-dfbc60ead2a1",
      "metadata": {
        "char_count": 104,
        "word_count": 15,
        "depth": 1,
        "document_path": [
          "Sample Test Document"
        ],
        "quality_checked": true
      },
      "confidence": 1.0
    }
  ],
  "document_metadata": {
    "source_file": "C:\\Users\\Andrew\\Documents\\AI ideas for fun and work\\Prompt Research\\Data Extraction\\data-extractor-tool\\tests\\fixtures\\sample.txt",
    "file_format": "text",
    "file_size_bytes": 900,
    "word_count": 135,
    "character_count": 900,
    "extracted_at": "2025-11-03T00:33:37.553572+00:00"
  },
  "processing_stage": "quality_validation",
  "quality_score": 100.0,
  "processing_success": true
}
