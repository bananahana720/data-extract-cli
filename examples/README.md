# Examples Directory

Working examples that demonstrate how to use the foundation.

## Purpose

These examples serve as:
1. **Templates** - Copy and modify for new modules
2. **Validation** - Prove the foundation works correctly
3. **Documentation** - Show the API in action
4. **Tests** - Quick smoke tests for foundation integrity

## Available Examples

### `minimal_extractor.py` ✓
**Demonstrates**: How to implement `BaseExtractor`

Extracts plain text files into `ContentBlock` objects.

**Key Patterns Shown**:
- Implementing required interface methods
- File validation
- Creating `ContentBlock` instances
- Building `ExtractionResult`
- Error handling (success/failure)
- Using `Position` for tracking

**Run**: `python examples/minimal_extractor.py`

**Expected Output**:
```
Extracting content from test_document.txt...

[SUCCESS] Extraction successful!
  Blocks: 5
  Words: 47
  Characters: 332

Content blocks:
  - [heading] Introduction...
  - [paragraph] This is a sample document...
```

### `minimal_processor.py` ✓
**Demonstrates**: How to implement `BaseProcessor`

Adds word count metadata to content blocks.

**Key Patterns Shown**:
- Implementing `BaseProcessor` interface
- Processing `ExtractionResult`
- Immutability pattern (create new blocks, don't modify)
- Building `ProcessingResult`
- Adding stage metadata
- Chaining extractor → processor

**Run**: `python examples/minimal_processor.py`

**Expected Output**:
```
Extracted 5 blocks

[SUCCESS] Processing successful!

Stage metadata:
  total_words: 47
  average_words_per_block: 9.4
  blocks_processed: 5

Enriched content blocks:
  - [heading] 2 words [SHORT]
  - [paragraph] 5 words [SHORT]
  - [paragraph] 26 words
```

### `simple_pipeline.py` ✓
**Demonstrates**: Complete end-to-end pipeline

Shows full data flow: Extract → Process → Format → Output

**Key Patterns Shown**:
- Implementing `BaseFormatter` interface
- Chaining all three stages together
- JSON output formatting
- Clear progress messages at each stage
- Complete pipeline execution pattern

**Run**: `python examples/simple_pipeline.py examples/sample_input.txt`

**Expected Output**:
```
======================================================================
SIMPLE PIPELINE DEMO - End-to-End Data Flow
======================================================================

[STAGE 1] EXTRACTION
  Input: examples\sample_input.txt
  Extractor: TextFileExtractor
  SUCCESS: Extracted 10 content blocks
  Document: 163 words, 1303 chars

[STAGE 2] PROCESSING
  Processor: WordCountProcessor
  SUCCESS: Enriched 10 blocks
  Statistics:
    - total_words: 163
    - average_words_per_block: 16.3

[STAGE 3] FORMATTING
  Formatter: JsonFormatter
  SUCCESS: Generated 4102 bytes of JSON

[STAGE 4] OUTPUT
  Output: examples\sample_input.json
  SUCCESS: Saved to examples\sample_input.json

======================================================================
PIPELINE COMPLETE
======================================================================
```

**Output**: Creates `sample_input.json` with structured JSON containing document metadata, statistics, and all content blocks.

## Using Examples as Templates

### To Create a New Extractor

1. Copy `minimal_extractor.py`
2. Rename class: `TextFileExtractor` → `MyExtractor`
3. Update `supports_format()` for your format
4. Update `extract()` with your extraction logic
5. Test with sample files

### To Create a New Processor

1. Copy `minimal_processor.py`
2. Rename class: `WordCountProcessor` → `MyProcessor`
3. Update `process()` with your enrichment logic
4. Set dependencies if needed: `get_dependencies()`
5. Test with extraction results

### To Create a New Formatter

1. Copy `JsonFormatter` from `simple_pipeline.py`
2. Rename class: `JsonFormatter` → `MyFormatter`
3. Update `get_format_type()` to return your format identifier
4. Update `format()` with your formatting logic
5. Test with processing results

## Guidelines

### Keep Examples Simple

Examples should be:
- **Minimal** - Only essential code
- **Clear** - Well-commented, easy to understand
- **Working** - Must run without errors
- **Self-contained** - No external dependencies (except foundation)

### Don't Use for Production

These are teaching tools, not production code:
- No configuration management
- No comprehensive error handling
- No logging
- No performance optimization

Real modules go in `src/extractors/`, `src/processors/`, etc.

## Testing Foundation Integrity

Run all examples to verify foundation is working:

```bash
python examples/minimal_extractor.py
python examples/minimal_processor.py
python examples/simple_pipeline.py examples/sample_input.txt
```

If all show `[SUCCESS]`, foundation is intact and the complete pipeline works end-to-end.

## Adding New Examples

When adding examples:
1. Create self-contained script
2. Include clear docstring explaining purpose
3. Show one pattern or concept clearly
4. Generate test data (don't require external files)
5. Clean up after running (delete test files)
6. Document in this README

## Quick Reference

**Foundation docs**: `../FOUNDATION.md`
**API reference**: `../QUICK_REFERENCE.md`
**Development guide**: `../GETTING_STARTED.md`
