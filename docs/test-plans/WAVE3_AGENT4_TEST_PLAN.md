# Test Plan for Wave 3 - Agent 4: Formatters

**Date**: 2025-10-29
**Agent**: TDD-Builder (Formatters)
**Status**: Planning Phase

---

## Overview

This document defines the comprehensive test strategy for implementing three output formatters using strict TDD methodology:
1. JsonFormatter - Hierarchical JSON output with metadata
2. MarkdownFormatter - Human-readable Markdown with preserved structure
3. ChunkedTextFormatter - Token-limited chunks maintaining context

---

## Requirements Coverage

### JsonFormatter Requirements

#### Requirement 1: Hierarchical JSON Structure
- **Test Case**: `test_json_hierarchical_structure`
- **Expected Behavior**: Output contains nested objects for content blocks with parent-child relationships
- **Integration Points**: ProcessingResult.content_blocks, Position data

#### Requirement 2: Include All Metadata
- **Test Case**: `test_json_includes_all_metadata`
- **Expected Behavior**: Document metadata, block metadata, style info all preserved
- **Integration Points**: DocumentMetadata, ContentBlock.metadata

#### Requirement 3: Pretty-Print Option
- **Test Case**: `test_json_pretty_print_option`
- **Expected Behavior**: Config controls indentation (compact vs readable)
- **Integration Points**: ConfigManager

#### Requirement 4: Valid JSON Schema
- **Test Case**: `test_json_schema_validity`
- **Expected Behavior**: Output is valid JSON, parseable by standard libraries
- **Integration Points**: json.loads validation

#### Requirement 5: Preserve Block Types
- **Test Case**: `test_json_preserves_content_types`
- **Expected Behavior**: All ContentType enum values correctly serialized
- **Integration Points**: ContentType enum

#### Requirement 6: Position Information
- **Test Case**: `test_json_includes_position_data`
- **Expected Behavior**: Page numbers, sequence indices preserved
- **Integration Points**: Position dataclass

#### Requirement 7: Error Handling
- **Test Case**: `test_json_handles_empty_input`
- **Expected Behavior**: Graceful handling of empty ProcessingResult
- **Integration Points**: ErrorHandler

#### Requirement 8: Unicode Support
- **Test Case**: `test_json_handles_unicode_content`
- **Expected Behavior**: Special characters, emojis preserved correctly
- **Integration Points**: UTF-8 encoding

---

### MarkdownFormatter Requirements

#### Requirement 1: Human-Readable Output
- **Test Case**: `test_markdown_readability`
- **Expected Behavior**: Clean markdown without excessive technical details
- **Integration Points**: ContentBlock.content

#### Requirement 2: Preserve Headings
- **Test Case**: `test_markdown_preserves_heading_hierarchy`
- **Expected Behavior**: ContentType.HEADING converted to markdown # syntax
- **Integration Points**: ContentType classification

#### Requirement 3: Preserve Structure
- **Test Case**: `test_markdown_preserves_document_structure`
- **Expected Behavior**: Parent-child relationships maintained via indentation/nesting
- **Integration Points**: ContentBlock.parent_id

#### Requirement 4: Frontmatter Metadata
- **Test Case**: `test_markdown_includes_yaml_frontmatter`
- **Expected Behavior**: Document metadata as YAML frontmatter block
- **Integration Points**: DocumentMetadata

#### Requirement 5: Lists and Quotes
- **Test Case**: `test_markdown_formats_lists_and_quotes`
- **Expected Behavior**: LIST_ITEM → bullet points, QUOTE → blockquote syntax
- **Integration Points**: ContentType enum

#### Requirement 6: Tables
- **Test Case**: `test_markdown_formats_tables`
- **Expected Behavior**: Table content rendered as markdown tables
- **Integration Points**: TableMetadata

#### Requirement 7: Code Blocks
- **Test Case**: `test_markdown_formats_code_blocks`
- **Expected Behavior**: ContentType.CODE wrapped in fenced code blocks
- **Integration Points**: ContentBlock.metadata for language

#### Requirement 8: Image References
- **Test Case**: `test_markdown_includes_image_references`
- **Expected Behavior**: Images referenced with markdown image syntax
- **Integration Points**: ImageMetadata

---

### ChunkedTextFormatter Requirements

#### Requirement 1: Respect Token Limits
- **Test Case**: `test_chunked_respects_token_limit`
- **Expected Behavior**: No chunk exceeds configured token limit
- **Integration Points**: ConfigManager for token limit setting

#### Requirement 2: Configurable Token Limit
- **Test Case**: `test_chunked_configurable_token_limit`
- **Expected Behavior**: Token limit set via config, defaults to 8000
- **Integration Points**: ConfigManager

#### Requirement 3: Maintain Context Across Chunks
- **Test Case**: `test_chunked_maintains_context`
- **Expected Behavior**: Chunk headers repeat context (current heading, section)
- **Integration Points**: ContentBlock.parent_id for context

#### Requirement 4: Add Chunk Metadata
- **Test Case**: `test_chunked_includes_metadata`
- **Expected Behavior**: Chunk number, total chunks, source info
- **Integration Points**: FormattedOutput.content structure

#### Requirement 5: Smart Splitting
- **Test Case**: `test_chunked_splits_on_boundaries`
- **Expected Behavior**: Split at heading/paragraph boundaries, not mid-sentence
- **Integration Points**: ContentType.HEADING as split points

#### Requirement 6: Token Counting Algorithm
- **Test Case**: `test_chunked_token_counting_accuracy`
- **Expected Behavior**: Reasonable approximation (word count * 1.3)
- **Integration Points**: Custom token estimation

#### Requirement 7: Handle Oversized Blocks
- **Test Case**: `test_chunked_handles_oversized_blocks`
- **Expected Behavior**: Single block > limit goes in own chunk with warning
- **Integration Points**: FormattedOutput.warnings

#### Requirement 8: Multi-Chunk Output
- **Test Case**: `test_chunked_generates_multiple_files`
- **Expected Behavior**: Multiple chunks = multiple files in additional_files
- **Integration Points**: FormattedOutput.additional_files

---

## Implementation Strategy

### Phase 1: JsonFormatter (Est: 3 Red-Green-Refactor cycles)

**Cycle 1: Basic Structure**
1. RED: Write tests for hierarchical structure + metadata inclusion
2. GREEN: Minimal implementation - flat JSON with content blocks
3. REFACTOR: Extract JSON building logic, add proper nesting

**Cycle 2: Configuration & Options**
1. RED: Write tests for pretty-print, schema validation
2. GREEN: Add config support, json.dumps with indent
3. REFACTOR: Clean up config handling pattern

**Cycle 3: Edge Cases & Validation**
1. RED: Write tests for empty input, unicode, error cases
2. GREEN: Add validation and error handling
3. REFACTOR: Polish, ensure infrastructure integration

**Coverage Target**: >85%
**Key Classes**: JsonFormatter (src/formatters/json_formatter.py)

---

### Phase 2: MarkdownFormatter (Est: 4 Red-Green-Refactor cycles)

**Cycle 1: Basic Conversion**
1. RED: Write tests for heading hierarchy, paragraph conversion
2. GREEN: Minimal implementation - flat markdown output
3. REFACTOR: Extract conversion methods per content type

**Cycle 2: Frontmatter & Structure**
1. RED: Write tests for YAML frontmatter, structure preservation
2. GREEN: Add frontmatter generation, basic nesting
3. REFACTOR: Clean up structure building logic

**Cycle 3: Rich Content (Lists, Tables, Code)**
1. RED: Write tests for lists, quotes, tables, code blocks
2. GREEN: Add format converters for each type
3. REFACTOR: Extract formatters into helper methods

**Cycle 4: Images & Polish**
1. RED: Write tests for image references, edge cases
2. GREEN: Add image handling, error cases
3. REFACTOR: Polish output formatting

**Coverage Target**: >85%
**Key Classes**: MarkdownFormatter (src/formatters/markdown_formatter.py)

---

### Phase 3: ChunkedTextFormatter (Est: 4 Red-Green-Refactor cycles)

**Cycle 1: Token Counting**
1. RED: Write tests for token counting algorithm
2. GREEN: Implement simple word-based estimation
3. REFACTOR: Optimize counting, make configurable

**Cycle 2: Chunk Splitting**
1. RED: Write tests for smart splitting at boundaries
2. GREEN: Implement basic split on headings
3. REFACTOR: Add paragraph-level splitting, optimize

**Cycle 3: Context Maintenance**
1. RED: Write tests for context headers in chunks
2. GREEN: Add context tracking and chunk headers
3. REFACTOR: Optimize context generation

**Cycle 4: Metadata & Edge Cases**
1. RED: Write tests for chunk metadata, oversized blocks
2. GREEN: Add metadata, handle edge cases
3. REFACTOR: Polish multi-file output

**Coverage Target**: >85%
**Key Classes**: ChunkedTextFormatter (src/formatters/chunked_text_formatter.py)

---

## Test Quality Metrics

### Coverage Targets
- **Line Coverage**: >85% for each formatter
- **Branch Coverage**: >80% for conditional logic
- **Edge Case Coverage**: 100% for error conditions

### Test Characteristics
- **Isolation**: Each test independent, no shared state
- **Speed**: Unit tests <100ms each
- **Clarity**: Test names describe behavior
- **Assertions**: Comprehensive validation of outputs

---

## Testing Tools Integration

### Python unittest/pytest
- Core testing framework
- Fixtures for sample ProcessingResult objects
- Parametrized tests for variations

### Infrastructure Integration
- ConfigManager for configuration testing
- LoggingFramework for structured logging validation
- ErrorHandler for error code testing
- ProgressTracker (minimal - formatters are fast)

---

## Sample Test Data

### Minimal ProcessingResult
```python
ProcessingResult(
    content_blocks=(
        ContentBlock(
            block_type=ContentType.HEADING,
            content="Test Heading"
        ),
        ContentBlock(
            block_type=ContentType.PARAGRAPH,
            content="Test paragraph."
        )
    ),
    document_metadata=DocumentMetadata(
        source_file=Path("test.docx"),
        file_format="docx"
    ),
    success=True
)
```

### Rich ProcessingResult
- Multiple content types (headings, paragraphs, lists, code, tables)
- Parent-child relationships
- Position information
- Metadata and style info
- Images and tables

### Edge Case Inputs
- Empty ProcessingResult (no blocks)
- Single block
- Deeply nested structure (10+ levels)
- Unicode content (emojis, Chinese characters, RTL languages)
- Very long content (>100k characters)

---

## Success Criteria

### Per Formatter
1. All requirement tests pass
2. Coverage >85%
3. Follows BaseFormatter interface
4. Uses infrastructure correctly
5. Comprehensive error handling
6. Clear documentation

### Overall
1. All 3 formatters complete
2. Examples demonstrate usage
3. No regressions in existing tests
4. Integration with infrastructure validated
5. Handoff document complete

---

## Risk Mitigation

### Technical Risks
- **Risk**: Complex JSON nesting logic
  - **Mitigation**: Start simple (flat), incrementally add nesting

- **Risk**: Markdown edge cases (escaping, nested structures)
  - **Mitigation**: Use proven markdown library patterns

- **Risk**: Token counting accuracy
  - **Mitigation**: Simple heuristic (word count * 1.3), document limitations

- **Risk**: Chunking splits mid-content
  - **Mitigation**: Split only on content block boundaries

### Process Risks
- **Risk**: Test suite runs slow
  - **Mitigation**: Keep unit tests focused, use fixtures

- **Risk**: Coverage gaps
  - **Mitigation**: Review coverage reports after each cycle

---

## Next Steps

1. Set up test directory structure
2. Create test fixtures (sample ProcessingResult objects)
3. Begin JsonFormatter TDD cycles
4. Continue with MarkdownFormatter
5. Complete with ChunkedTextFormatter
6. Create examples
7. Write handoff document

---

**Status**: Planning Complete | Ready to Begin Implementation
