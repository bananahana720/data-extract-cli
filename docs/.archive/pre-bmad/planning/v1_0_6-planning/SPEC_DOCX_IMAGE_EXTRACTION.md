# DOCX Image Extraction - Technical Specification

## Overview

**Feature**: DOCX Image Extraction
**Version**: v1.0.6
**Priority**: HIGH
**Risk**: LOW
**Confidence**: 95%

Extract inline images from DOCX files with complete metadata (format, dimensions, alt text) and binary data.

## Requirements

### Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-1 | Extract all inline images from `Document.inline_shapes` |
| FR-2 | Capture image format (PNG, JPEG, GIF, BMP, TIFF, EMF, WMF) |
| FR-3 | Calculate pixel dimensions from EMU values |
| FR-4 | Extract alt text when available |
| FR-5 | Store binary image data |
| FR-6 | Populate complete `ImageMetadata` for each image |
| FR-7 | Include images in `ExtractionResult.images` tuple |

### Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-1 | Performance: <100ms per image extraction |
| NFR-2 | Error handling: graceful degradation on corrupted images |
| NFR-3 | Memory: stream binary data, no full load |
| NFR-4 | Coverage: ≥85% test coverage |
| NFR-5 | Compatibility: no regressions (41+ tests pass) |

### Configuration Requirements

```python
config = {
    "extract_images": True  # Boolean toggle for image extraction
}
```

## Technical Approach

### API: python-docx inline_shapes

```python
from docx.enum.shape import WD_INLINE_SHAPE

# Access inline images
for inline_shape in doc.inline_shapes:
    if inline_shape.type == WD_INLINE_SHAPE.PICTURE:
        # Process image
        pass
```

### Extraction Algorithm

```alg-pseudo
for each inline_shape in document.inline_shapes:
  if inline_shape.type == PICTURE:
    1. Get relationship ID from inline_shape._inline.graphic.graphicData.pic.blipFill.blip.embed
    2. Access image_part from doc.part.related_parts[rID]
    3. Extract format from image_part.content_type
    4. Convert EMU dimensions to pixels
    5. Get alt text from inline_shape._inline.docPr.descr
    6. Read binary blob from image_part._blob
    7. Create ImageMetadata object
    8. Append to images list
```

### EMU to Pixel Conversion

```python
def _emu_to_pixels(emu_value: int) -> int:
    """
    Convert EMU (English Metric Units) to pixels.

    EMU per inch: 914400
    Pixels per inch: 96 (standard screen DPI)
    Formula: pixels = emu * 96 / 914400
    """
    return int(emu_value * 96 / 914400)
```

### Format Detection

```python
# Map MIME type to format string
MIME_TO_FORMAT = {
    'image/png': 'PNG',
    'image/jpeg': 'JPEG',
    'image/gif': 'GIF',
    'image/bmp': 'BMP',
    'image/tiff': 'TIFF',
    'image/x-emf': 'EMF',
    'image/x-wmf': 'WMF',
}

format_str = MIME_TO_FORMAT.get(image_part.content_type, 'UNKNOWN')
```

### Binary Data Access

```python
try:
    # Get relationship ID
    rId = inline_shape._inline.graphic.graphicData.pic.blipFill.blip.embed

    # Access image part
    image_part = doc.part.related_parts[rId]

    # Extract binary blob
    image_data = image_part._blob
except (KeyError, AttributeError) as e:
    # Handle missing relationship or corrupted structure
    pass
```

## Implementation Details

### File Location

`src/extractors/docx_extractor.py`

### New Method

```python
def _extract_images(self, doc: Document) -> list[ImageMetadata]:
    """
    Extract images from DOCX inline shapes.

    Args:
        doc: python-docx Document object

    Returns:
        List of ImageMetadata objects with format, dimensions, data

    Raises:
        ExtractionError: If critical image extraction fails
    """
    images = []

    for idx, inline_shape in enumerate(doc.inline_shapes):
        try:
            if inline_shape.type != WD_INLINE_SHAPE.PICTURE:
                continue

            # Extract relationship ID
            rId = inline_shape._inline.graphic.graphicData.pic.blipFill.blip.embed
            image_part = doc.part.related_parts[rId]

            # Format detection
            format_str = self._detect_image_format(image_part.content_type)

            # Dimension conversion
            width_px = self._emu_to_pixels(inline_shape.width)
            height_px = self._emu_to_pixels(inline_shape.height)

            # Alt text
            alt_text = getattr(inline_shape._inline.docPr, 'descr', None)

            # Binary data
            image_data = image_part._blob

            images.append(ImageMetadata(
                format=format_str,
                width=width_px,
                height=height_px,
                alt_text=alt_text,
                data=image_data,
                index=idx
            ))

        except (KeyError, AttributeError) as e:
            self.logger.warning(f"Image {idx} extraction failed: {e}")
            continue

    return images
```

### Integration Points

| Location | Line | Action |
|----------|------|--------|
| Imports | ~15 | Add `from docx.enum.shape import WD_INLINE_SHAPE` |
| Class constants | ~35 | Add `MIME_TO_FORMAT` mapping dict |
| Helper methods | ~180 | Add `_emu_to_pixels()` method |
| Helper methods | ~190 | Add `_detect_image_format()` method |
| Helper methods | ~200 | Add `_extract_images()` method |
| `extract()` method | ~140 | Call `images = self._extract_images(doc)` |
| `extract()` method | ~155 | Add `images=tuple(images)` to ExtractionResult |

### Configuration Integration

```python
# In extract() method
if self.config.get('extract_images', True):
    images = self._extract_images(doc)
else:
    images = []
```

### Error Handling Strategy

| Error Type | Handling |
|------------|----------|
| Missing relationship ID | Log warning, skip image, continue |
| KeyError on related_parts | Log warning, skip image, continue |
| Corrupted blob | Log warning, create empty ImageMetadata, continue |
| Unknown MIME type | Use 'UNKNOWN' format, log info, continue |
| Missing dimensions | Use 0 for width/height, log warning, continue |
| AttributeError on docPr | Set alt_text=None, continue |

**Strategy**: Degrade gracefully. Never fail entire extraction due to single image issue.

## Data Structures

### ImageMetadata Fields

```python
@dataclass
class ImageMetadata:
    format: str           # "PNG", "JPEG", "UNKNOWN", etc.
    width: int            # Pixels (converted from EMU)
    height: int           # Pixels (converted from EMU)
    alt_text: str | None  # From inline_shape._inline.docPr.descr
    data: bytes           # Binary blob from image_part._blob
    index: int            # Position in inline_shapes collection
```

### ExtractionResult Extension

```python
# Current (v1.0.5)
ExtractionResult(
    text=extracted_text,
    metadata=metadata_dict,
    tables=tuple(tables)
)

# New (v1.0.6)
ExtractionResult(
    text=extracted_text,
    metadata=metadata_dict,
    tables=tuple(tables),
    images=tuple(images)  # NEW: tuple[ImageMetadata, ...]
)
```

## Edge Cases

### Missing Relationship IDs

```python
# Symptom: inline_shape has no embedded image relationship
# Cause: Shape is placeholder or drawing object, not actual image
# Handling: Skip via type check (WD_INLINE_SHAPE.PICTURE)

if inline_shape.type != WD_INLINE_SHAPE.PICTURE:
    continue  # Not an image
```

### Corrupted Image Blobs

```python
# Symptom: image_part._blob is None or malformed
# Cause: Document corruption or encoding issue
# Handling: Log warning, create metadata with empty bytes

try:
    image_data = image_part._blob
    if not image_data:
        raise ValueError("Empty blob")
except Exception as e:
    self.logger.warning(f"Corrupted blob at index {idx}: {e}")
    image_data = b''  # Empty bytes
```

### Unknown Formats

```python
# Symptom: content_type not in MIME_TO_FORMAT mapping
# Cause: Rare format (SVG, WebP) or custom type
# Handling: Use "UNKNOWN", log for investigation

format_str = MIME_TO_FORMAT.get(
    image_part.content_type,
    'UNKNOWN'
)
if format_str == 'UNKNOWN':
    self.logger.info(f"Unknown MIME: {image_part.content_type}")
```

### Missing Dimensions

```python
# Symptom: inline_shape.width or .height raises AttributeError
# Cause: Malformed shape XML structure
# Handling: Default to 0, log warning

try:
    width_px = self._emu_to_pixels(inline_shape.width)
    height_px = self._emu_to_pixels(inline_shape.height)
except AttributeError:
    self.logger.warning(f"Missing dimensions at index {idx}")
    width_px = height_px = 0
```

### Documents Without Images

```python
# Symptom: doc.inline_shapes is empty collection
# Cause: Document has no inline images (valid scenario)
# Handling: Return empty list (not an error)

if not doc.inline_shapes:
    return []  # Valid: no images in document
```

## Testing Requirements

### Unit Tests (7 minimum)

| Test | File | Purpose |
|------|------|---------|
| `test_extract_single_image` | `test_extractors/test_docx_extractor.py` | Verify single image extraction |
| `test_extract_multiple_images` | `test_extractors/test_docx_extractor.py` | Verify batch extraction |
| `test_emu_to_pixels_conversion` | `test_extractors/test_docx_extractor.py` | Validate dimension math |
| `test_image_format_detection` | `test_extractors/test_docx_extractor.py` | Verify MIME mapping |
| `test_missing_alt_text` | `test_extractors/test_docx_extractor.py` | Handle None alt text |
| `test_corrupted_image_handling` | `test_extractors/test_docx_extractor.py` | Graceful degradation |
| `test_no_images_document` | `test_extractors/test_docx_extractor.py` | Empty collection handling |

### Test Fixtures

```python
# tests/fixtures/docx_images/
test_single_image.docx      # 1 PNG image, 800x600, with alt text
test_multiple_images.docx   # 3 images (PNG, JPEG, GIF)
test_no_images.docx         # Valid DOCX, no images
test_corrupted_image.docx   # 1 image with bad relationship
test_unknown_format.docx    # SVG or WebP image
```

### Integration Tests (3 minimum)

| Test | Purpose |
|------|---------|
| `test_docx_image_to_json_formatter` | Verify images in JSON output |
| `test_docx_image_to_markdown_formatter` | Verify image references in markdown |
| `test_docx_image_config_toggle` | Verify `extract_images=False` skips |

### Coverage Target

**Minimum**: 85%
**Files**:
- `src/extractors/docx_extractor.py`: ≥90% (new methods fully covered)
- `tests/test_extractors/test_docx_extractor.py`: 100% (all tests execute)

**Validation**:
```bash
pytest --cov=src/extractors/docx_extractor --cov-report=term-missing
```

## Success Criteria

### Functional Success

- [ ] All images from `inline_shapes` extracted
- [ ] ImageMetadata complete for each image
- [ ] Format detected correctly (PNG, JPEG, etc.)
- [ ] Width/height converted from EMU to pixels
- [ ] Alt text extracted when present
- [ ] Binary data stored in ImageMetadata.data
- [ ] Images included in ExtractionResult.images tuple

### Configuration Success

- [ ] `extract_images=True` extracts images
- [ ] `extract_images=False` skips extraction (empty tuple)
- [ ] Config toggle tested in integration tests

### Error Handling Success

- [ ] Missing relationship ID: warning logged, skip image
- [ ] Corrupted blob: warning logged, empty bytes stored
- [ ] Unknown format: "UNKNOWN" used, info logged
- [ ] Missing dimensions: defaults to 0, warning logged
- [ ] Documents without images: returns empty list (no error)

### Testing Success

- [ ] 7+ unit tests pass
- [ ] 3+ integration tests pass
- [ ] Coverage ≥85% on docx_extractor.py
- [ ] All 41+ existing tests pass (no regressions)

### Performance Success

- [ ] Single image extraction: <100ms
- [ ] 10 images extraction: <1 second
- [ ] Memory: no spikes (streaming binary data)

## Dependencies

### Existing

| Dependency | Version | Status |
|------------|---------|--------|
| python-docx | ≥0.8.11 | ✓ Installed |
| ImageMetadata | v1.0.0 | ✓ Exists in `models/` |
| ExtractionResult | v1.0.0 | ✓ Exists in `models/` |
| Pipeline image support | v1.0.3 | ✓ PPTX images working |

### New

None. All required dependencies already in place.

## Acceptance Criteria

### Implementation Checklist

- [ ] `_emu_to_pixels()` method added
- [ ] `_detect_image_format()` method added
- [ ] `_extract_images()` method added
- [ ] `WD_INLINE_SHAPE` import added
- [ ] `MIME_TO_FORMAT` constant defined
- [ ] `extract()` method calls `_extract_images()`
- [ ] `ExtractionResult` includes `images` parameter
- [ ] Configuration `extract_images` toggle implemented

### Testing Checklist

- [ ] 7 unit tests written
- [ ] 5 test fixtures created
- [ ] 3 integration tests written
- [ ] Coverage report shows ≥85%
- [ ] All tests pass: `pytest tests/test_extractors/test_docx_extractor.py -v`

### Validation Commands

```bash
# Run unit tests
pytest tests/test_extractors/test_docx_extractor.py -v

# Run integration tests
pytest tests/integration/test_extractor_processor_integration.py -k docx_image -v

# Check coverage
pytest --cov=src/extractors/docx_extractor --cov-report=html

# Verify no regressions
pytest tests/ -v

# Test extraction
python -m data_extractor_tool extract tests/fixtures/docx_images/test_multiple_images.docx \
    --format json \
    --output output.json \
    --config extract_images=true
```

### Acceptance Test

```python
# Manual validation script
from docx import Document
from src.extractors.docx_extractor import DOCXExtractor

extractor = DOCXExtractor({'extract_images': True})
result = extractor.extract('tests/fixtures/docx_images/test_multiple_images.docx')

assert len(result.images) == 3
assert result.images[0].format in ['PNG', 'JPEG', 'GIF']
assert result.images[0].width > 0
assert result.images[0].height > 0
assert len(result.images[0].data) > 0
print("✓ All acceptance criteria met")
```

---

**Status**: Ready for implementation
**Estimated Effort**: 4-6 hours
**Risk Assessment**: LOW (90% pattern match with proven PPTX implementation)
