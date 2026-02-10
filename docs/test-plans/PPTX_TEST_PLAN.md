# PowerPoint (PPTX) Extractor Test Plan

**Date**: 2025-10-29
**Implementation**: TDD (Test-Driven Development)
**Target Coverage**: >85%

---

## Requirements Coverage

### Requirement 1: Slide Content Extraction
**Description**: Extract text content from slides (titles, body text, shapes)
**Test Cases**:
- `test_extract_slide_title` - Extract slide title text
- `test_extract_slide_body` - Extract body text from text boxes
- `test_extract_multiple_shapes` - Extract text from multiple shapes on slide
- `test_empty_slide` - Handle slides with no text content
**Expected Behavior**: All text content extracted as ContentBlocks with type PARAGRAPH/HEADING
**Integration Points**: BaseExtractor interface, ContentBlock model

### Requirement 2: Speaker Notes Extraction
**Description**: Extract presenter notes from slides
**Test Cases**:
- `test_extract_speaker_notes` - Extract notes from slide
- `test_slide_without_notes` - Handle slides without notes
- `test_notes_with_formatting` - Preserve note text structure
**Expected Behavior**: Notes extracted as ContentBlocks with metadata indicating they are notes
**Integration Points**: ContentBlock metadata field

### Requirement 3: Slide Layout and Structure
**Description**: Preserve slide sequence and position information
**Test Cases**:
- `test_slide_sequence` - Verify slides extracted in correct order
- `test_slide_position_metadata` - Verify Position.slide field set correctly
- `test_sequence_index` - Verify sequence_index tracks content order
**Expected Behavior**: Position model used with slide number and sequence index
**Integration Points**: Position model, ContentBlock.position

### Requirement 4: Image/Chart Metadata Extraction
**Description**: Extract metadata about visual elements on slides
**Test Cases**:
- `test_image_metadata` - Extract image dimensions and position
- `test_chart_metadata` - Identify chart elements
- `test_shape_types` - Identify different shape types
**Expected Behavior**: ImageMetadata created for visual elements
**Integration Points**: ImageMetadata model

### Requirement 5: Presentation Metadata
**Description**: Extract presentation-level metadata (author, title, dates)
**Test Cases**:
- `test_presentation_metadata` - Extract core properties
- `test_slide_count` - Count total slides
- `test_file_hash` - Generate SHA256 hash
**Expected Behavior**: DocumentMetadata populated with presentation properties
**Integration Points**: DocumentMetadata model

### Requirement 6: Infrastructure Integration
**Description**: Use ConfigManager, LoggingFramework, ErrorHandler
**Test Cases**:
- `test_accepts_config_manager` - Constructor accepts ConfigManager
- `test_uses_config_values` - Respects configuration settings
- `test_backward_compatible_dict` - Still works with dict config
- `test_error_codes` - Uses ErrorHandler for structured errors
- `test_logging_operations` - Logs key extraction steps
**Expected Behavior**: Following patterns from DocxExtractor integration
**Integration Points**: Infrastructure modules

---

## Test Implementation Strategy

### Phase 1: Core Functionality (Red-Green-Refactor)
1. **RED**: Write test for basic slide text extraction
2. **GREEN**: Implement minimal PptxExtractor with python-pptx
3. **REFACTOR**: Clean up code, extract methods
4. **Repeat** for each core requirement

### Phase 2: Infrastructure Integration
1. **RED**: Write tests for ConfigManager integration
2. **GREEN**: Add infrastructure imports and initialization
3. **REFACTOR**: Follow DocxExtractor patterns

### Phase 3: Edge Cases and Validation
1. **RED**: Write tests for error conditions
2. **GREEN**: Add error handling with ErrorHandler
3. **REFACTOR**: Consolidate error handling patterns

---

## Configuration Schema

Add to `config_schema.yaml`:

```yaml
extractors:
  pptx:
    extract_notes: true         # Extract speaker notes
    extract_images: true        # Extract image metadata
    skip_empty_slides: false    # Skip slides with no content
```

---

## Error Code Mapping

| Error Code | Category | Use Case |
|------------|----------|----------|
| E001 | Validation | File not found |
| E002 | Validation | File not readable |
| E150 | Extraction | PPTX structure error |
| E151 | Extraction | Invalid slide structure |
| E152 | Extraction | Shape parsing error |
| E500 | Resource | Permission denied |

---

## Test Data Requirements

Create test PowerPoint files in `tests/fixtures/pptx/`:
- `simple_presentation.pptx` - 3 slides with titles and body text
- `with_notes.pptx` - Slides with speaker notes
- `empty.pptx` - Empty presentation
- `images_and_charts.pptx` - Visual elements

---

## Success Criteria

Implementation complete when:
1. All tests passing (>85% coverage)
2. Follows BaseExtractor interface exactly
3. Uses infrastructure components correctly
4. No regressions in existing extractors
5. Integration tests pass
6. Example script works
7. Handoff document complete

---

## Dependencies

**Required Library**: `python-pptx`
**Version**: Latest stable (pip install python-pptx)
**Compatibility**: Python 3.11+

---

## TDD Cycle Checklist

For each requirement:
- [ ] Write failing test
- [ ] Run test, verify failure
- [ ] Write minimal implementation
- [ ] Run test, verify pass
- [ ] Refactor code
- [ ] Run test, verify still passing
- [ ] Commit working code
- [ ] Move to next requirement
