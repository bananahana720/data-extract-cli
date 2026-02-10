# Plain Text Output Format Reference

**Story**: 3.5 - Plain Text Output Format for LLM Upload
**Status**: Complete
**Version**: 1.0
**Last Updated**: 2025-11-15

## Overview

The TxtFormatter produces clean plain text output optimized for direct upload to LLM chat interfaces (ChatGPT, Claude) without manual cleanup. Output is deterministic, artifact-free, and supports optional metadata headers for context enrichment.

## Output Structure

### Basic Format (Metadata Disabled)

```
━━━ CHUNK 001 ━━━
This is the first chunk of clean text. Markdown formatting has been removed.
Paragraph spacing is preserved for readability.

━━━ CHUNK 002 ━━━
This is the second chunk demonstrating sequential numbering and delimiter rendering.
```

### With Metadata Headers (Enabled)

```
━━━ CHUNK 001 ━━━
Source: audit_report.pdf | Chunk: chunk_001
Entities: RISK-001, CTRL-042
Quality: 0.96
This is the first chunk with metadata headers providing traceability and context.

━━━ CHUNK 002 ━━━
Source: audit_report.pdf | Chunk: chunk_002
Quality: 0.92
This is the second chunk showing optional metadata (entities omitted when not present).
```

## Configuration Options

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_metadata` | `bool` | `False` | Enable compact metadata headers |
| `delimiter` | `str` | `"━━━ CHUNK {{n}} ━━━"` | Chunk separator pattern ({{n}} replaced with number) |

### Usage Examples

```python
# Default configuration (clean text only)
formatter = TxtFormatter()

# Enable metadata headers
formatter = TxtFormatter(include_metadata=True)

# Custom delimiter
formatter = TxtFormatter(delimiter="--- CHUNK {{n}} ---")

# Both options
formatter = TxtFormatter(
    include_metadata=True,
    delimiter="=== SECTION {{n}} ==="
)
```

## Metadata Header Fields

When `include_metadata=True`, headers include:

| Field | Format | Source | Optional |
|-------|--------|--------|----------|
| **Source** | `Source: filename.pdf` | `ChunkMetadata.source_file` | No |
| **Chunk ID** | `Chunk: chunk_001` | `ChunkMetadata.chunk_id` | No |
| **Entities** | `Entities: RISK-001, CTRL-042` | `ChunkMetadata.entity_tags` | Yes |
| **Quality** | `Quality: 0.96` | `ChunkMetadata.quality.overall` | Yes |

**Notes**:
- Headers are compact (1-3 lines maximum)
- Fields gracefully omitted when data not available
- Entity lists limited to first 5 entities (prevents header bloat)

## Text Cleaning Process

TxtFormatter automatically removes formatting artifacts:

### Markdown Artifacts Removed
- Headers: `# Title` → `Title`
- Bold: `**text**` → `text`
- Italic: `*text*` → `text`
- Lists: `- item` → `item`

### HTML Artifacts Removed
- Tags: `<p>text</p>` → `text`
- Entities: `&nbsp;` → ` ` (space)

### Whitespace Normalization
- Multiple spaces: `text  text` → `text text`
- Excessive newlines: `\n\n\n\n` → `\n\n` (paragraph break)
- Trailing whitespace: Removed
- File ending: Single trailing newline (deterministic)

### Preserved Elements
- **Paragraph breaks**: Double newlines (`\n\n`) preserved
- **Unicode characters**: Emoji, accented characters, symbols preserved
- **Intentional formatting**: Code blocks, tables converted to text

## Encoding & Compatibility

### UTF-8-sig Encoding
- **BOM Present**: First 3 bytes are `\xef\xbb\xbf` (UTF-8 byte order mark)
- **Windows Compatibility**: Notepad, Excel, legacy tools recognize encoding
- **Cross-platform**: Works on Windows, macOS, Linux

### Unicode Support
Preserves multilingual text and emoji:
- **Accented characters**: Café, résumé, naïve, Zürich
- **Symbols**: €100, ©2024, ™
- **Emoji**: 🚀✅⚠️📊🔒
- **Non-Latin scripts**: Chinese (中文), Arabic (العربية), Cyrillic (Русский)

### Path Compatibility
- **Windows**: `C:\Users\Documents\file.txt`
- **Unix/Linux**: `/home/user/documents/file.txt`
- **Unicode filenames**: `résumé_🚀.txt`

## Performance Characteristics

### Latency Benchmarks

| Document Size | Chunks | Target | Actual | Status |
|---------------|--------|--------|--------|--------|
| Small | 10 | <1s | ~0.01s | ✅ 100x faster |
| Large | 100 | <3s | ~0.03s | ✅ 100x faster |
| Very Large | 1000 | <30s | ~0.3s | ✅ 100x faster |

### Memory Usage
- **Peak memory**: ~5MB (constant across batch sizes)
- **Streaming**: Iterator-based processing (no full materialization)
- **Scalability**: Linear scaling with document size

## LLM Upload Workflow

### Recommended Workflow

1. **Generate TXT output**
   ```python
   formatter = TxtFormatter(include_metadata=True)
   result = formatter.format_chunks(chunks, Path("context.txt"))
   ```

2. **Open output file**
   ```bash
   # Windows
   notepad context.txt

   # macOS
   open context.txt

   # Linux
   gedit context.txt
   ```

3. **Select all text** (Ctrl+A / Cmd+A)

4. **Copy** (Ctrl+C / Cmd+C)

5. **Paste into LLM chat**
   - ChatGPT: Paste directly into message box
   - Claude: Paste directly into message box
   - No cleanup required

### ChatGPT Upload Tips
- Maximum context: ~128k tokens (GPT-4 Turbo)
- Chunk count estimate: 500-1000 chunks typical
- Metadata headers help ChatGPT understand structure

### Claude Upload Tips
- Maximum context: ~200k tokens (Claude 3.5 Sonnet)
- Chunk count estimate: 800-1500 chunks typical
- Delimiters help Claude parse document boundaries

## Validation & Quality Checks

### Automated Validation (CI/CD)
```bash
# All 41 automated tests
pytest tests/unit/test_output/test_txt_formatter.py -v
pytest tests/integration/test_output/test_txt_pipeline.py -v
pytest tests/integration/test_output/test_txt_compatibility.py -v
pytest tests/performance/test_txt_performance.py -v
```

### Manual Validation Checklist
- [ ] No markdown artifacts (`**bold**`, `# headers`)
- [ ] No HTML tags (`<p>`, `<div>`)
- [ ] No JSON braces (`{`, `}`, `[`, `]` in wrong places)
- [ ] No ANSI color codes (`\x1b[`)
- [ ] Delimiters render correctly (`━━━ CHUNK 001 ━━━`)
- [ ] Sequential numbering (001, 002, 003...)
- [ ] Metadata headers present when enabled
- [ ] UTF-8 BOM present (check first 3 bytes)
- [ ] Copy/paste to ChatGPT works without cleanup
- [ ] Copy/paste to Claude works without cleanup

## Troubleshooting

### Issue: Metadata headers missing
**Solution**: Ensure `include_metadata=True` when creating TxtFormatter

### Issue: Custom delimiter not rendering
**Solution**: Use `{{n}}` placeholder in delimiter pattern (e.g., `"--- CHUNK {{n}} ---"`)

### Issue: Unicode characters corrupted
**Solution**: Verify UTF-8-sig encoding used, not UTF-8 (BOM required for some tools)

### Issue: Artifacts still present
**Solution**: Check shared utils (`clean_text()`) is being called, review test suite for edge cases

## Implementation Details

### Files
- **Formatter**: `src/data_extract/output/formatters/txt_formatter.py`
- **Shared Utils**: `src/data_extract/output/utils.py`
- **Tests**: `tests/unit/test_output/test_txt_formatter.py`

### Dependencies
- **spaCy**: Sentence boundary detection (inherited from chunking engine)
- **pathlib**: Cross-platform path handling
- **re**: Text cleaning regex patterns

### Design Patterns
- **Pre-compiled regex**: Module-level pattern compilation for performance
- **Shared utilities**: Reusable text cleaning across formatters
- **Deterministic output**: Same input → byte-identical files
- **Fail-fast validation**: Errors propagate immediately

## See Also
- **JSON Output Format**: `docs/json-schema-reference.md`
- **Chunking Engine**: `CLAUDE.md` (Epic 3: Chunking Engine section)
- **Architecture**: `docs/architecture.md` (Output Pipeline section)
- **Tech Spec**: `docs/tech-spec-epic-3.md` (Story 3.5 specification)
