# TxtFormatter Sample Outputs

This directory contains sample TXT outputs demonstrating the plain text formatter capabilities.

## Files

| File | Description | Features |
|------|-------------|----------|
| `sample-basic.txt` | Basic clean text output | Default delimiter, no metadata, clean text |
| `sample-with-metadata.txt` | Output with metadata headers | Source file, entities, quality scores |
| `sample-custom-delimiter.txt` | Custom delimiter pattern | Custom `=== SECTION {{n}} ===` delimiter |

## How These Were Generated

```python
from data_extract.output.formatters import TxtFormatter
from pathlib import Path

# sample-basic.txt
formatter = TxtFormatter()
result = formatter.format_chunks(chunks, Path("sample-basic.txt"))

# sample-with-metadata.txt
formatter = TxtFormatter(include_metadata=True)
result = formatter.format_chunks(chunks, Path("sample-with-metadata.txt"))

# sample-custom-delimiter.txt
formatter = TxtFormatter(delimiter="=== SECTION {{n}} ===")
result = formatter.format_chunks(chunks, Path("sample-custom-delimiter.txt"))
```

## Validation

All samples have been validated for:
- ✅ UTF-8-sig encoding with BOM
- ✅ No markdown artifacts (`**bold**`, `# headers`)
- ✅ No HTML tags (`<p>`, `<div>`)
- ✅ No JSON/ANSI artifacts
- ✅ Clean copy/paste to ChatGPT (no cleanup needed)
- ✅ Clean copy/paste to Claude (no cleanup needed)

## Usage

Open any sample file and copy/paste directly into ChatGPT or Claude to see the LLM upload workflow in action.
