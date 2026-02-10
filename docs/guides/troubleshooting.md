# Troubleshooting

Common issues and solutions for the Data Extraction Tool.

## Quick Diagnostics

Run these commands to diagnose issues:

```bash
# Check CLI installation
data-extract --version
data-extract --help

# Verify configuration
data-extract config show

# Validate dependencies
python -m spacy validate

# Check cache status
data-extract cache stats

# View active sessions
data-extract session list
```

## Installation Issues

### CLI Not Found

**Symptom:**
```bash
$ data-extract
bash: data-extract: command not found
```

**Solution:**

1. Verify installation:
```bash
# Using uv
uv pip list | grep data-extraction-tool

# Using pip
pip list | grep data-extraction-tool
```

2. Reinstall if missing:
```bash
# Using uv
uv pip install -e ".[dev]"

# Using pip
pip install -e ".[dev]"
```

3. Verify virtual environment is activated:
```bash
which python
# Should show .venv/bin/python or similar
```

4. Add to PATH if necessary:
```bash
export PATH="$PATH:$(pwd)/.venv/bin"
```

### spaCy Model Missing

**Symptom:**
```
OSError: [E050] Can't find model 'en_core_web_md'
```

**Solution:**

```bash
# Download model
python -m spacy download en_core_web_md

# Verify installation
python -m spacy validate

# Check installed models
python -m spacy info en_core_web_md
```

**Alternative (offline installation):**
```bash
# Download from GitHub releases
wget https://github.com/explosion/spacy-models/releases/download/en_core_web_md-3.7.1/en_core_web_md-3.7.1.tar.gz

# Install locally
pip install en_core_web_md-3.7.1.tar.gz
```

### Dependency Conflicts

**Symptom:**
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed
```

**Solution:**

1. Use uv (recommended):
```bash
uv pip install -e ".[dev]"
```

2. Or create fresh environment:
```bash
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

3. Check for conflicting packages:
```bash
pip check
```

### Import Errors

**Symptom:**
```python
ImportError: cannot import name 'X' from 'data_extract'
```

**Solution:**

1. Reinstall in development mode:
```bash
pip install -e ".[dev]"
```

2. Verify package structure:
```bash
ls -la src/data_extract/
```

3. Check Python version:
```bash
python --version
# Must be 3.11 or higher
```

## Extraction Issues

### PDF Extraction Fails

**Symptom:**
```
ERROR: Failed to extract PDF: ...
```

**Solutions:**

**For scanned PDFs:**
```bash
# Enable OCR fallback
data-extract process scan.pdf --ocr-fallback
```

**For encrypted PDFs:**
```bash
# Remove password protection first
pdftk encrypted.pdf input_pw PASSWORD output decrypted.pdf
data-extract process decrypted.pdf
```

**For corrupted PDFs:**
```bash
# Repair with Ghostscript
gs -o repaired.pdf -sDEVICE=pdfwrite -dPDFSETTINGS=/prepress corrupted.pdf
data-extract process repaired.pdf
```

**Check PDF validity:**
```bash
# Validate PDF structure
pdfinfo document.pdf
```

### Low OCR Confidence

**Symptom:**
```
WARNING: OCR confidence below threshold: 0.45
```

**Solutions:**

1. Lower confidence threshold:
```bash
data-extract process scan.pdf --confidence-threshold 0.3
```

2. Improve image quality:
```bash
# Increase DPI before scanning (300+ recommended)
# Use grayscale instead of color
# Ensure good lighting and contrast
```

3. Preprocess images:
```bash
# Use ImageMagick to enhance
convert input.pdf -density 300 -quality 100 enhanced.pdf
data-extract process enhanced.pdf --ocr-fallback
```

### Office Document Errors

**Symptom:**
```
ERROR: Failed to extract DOCX/XLSX: ...
```

**Solutions:**

**For DOCX:**
```bash
# Verify file is not corrupted
unzip -t document.docx

# Repair with LibreOffice
libreoffice --headless --convert-to docx broken.docx
```

**For XLSX:**
```bash
# Check for protected sheets
# Unprotect in Excel/LibreOffice first
```

**For PPTX:**
```bash
# Extract speaker notes if body is empty
# Use --extract-notes flag (if available)
```

### Empty Extraction Results

**Symptom:**
```
WARNING: No text extracted from document
```

**Solutions:**

1. Check document type:
```bash
file document.pdf
# Ensure it's actually a PDF, not renamed image
```

2. Verify content exists:
```bash
# Open in viewer and verify text is selectable
```

3. Enable verbose logging:
```bash
data-extract process document.pdf -vv
# Check logs for specific error
```

4. Try alternative extractor:
```bash
# Check extraction section in output JSON
# Contact support if extractor selection is incorrect
```

## Performance Issues

### Slow Processing

**Symptom:**
Processing takes longer than expected.

**Solutions:**

1. Enable parallel processing:
```bash
data-extract process ./docs/ --max-workers 8 --batch-size 10
```

2. Use fast preset:
```bash
data-extract process ./docs/ --preset fast-batch
```

3. Disable semantic analysis:
```bash
data-extract process ./docs/ --disable-semantic
```

4. Reduce chunk size:
```bash
data-extract process ./docs/ --max-chunk-size 500
```

5. Check system resources:
```bash
# Monitor CPU/memory during processing
htop

# Check disk I/O
iostat -x 1
```

6. Enable caching:
```bash
# Cache is enabled by default, verify:
data-extract cache stats
```

### Memory Issues

**Symptom:**
```
MemoryError: Unable to allocate array
```

**Solutions:**

1. Reduce batch size:
```bash
data-extract process ./docs/ --batch-size 5
```

2. Process files sequentially:
```bash
data-extract process ./docs/ --max-workers 1
```

3. Disable semantic analysis:
```bash
data-extract process ./docs/ --disable-semantic
```

4. Process in smaller batches:
```bash
# Split directory and process separately
data-extract process ./docs/batch1/ --output-dir ./output
data-extract process ./docs/batch2/ --output-dir ./output
```

5. Increase system swap:
```bash
# Linux: Add swap space
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Disk Space Issues

**Symptom:**
```
OSError: [Errno 28] No space left on device
```

**Solutions:**

1. Clear cache:
```bash
data-extract cache clear
```

2. Clean old sessions:
```bash
data-extract session cleanup --days 7
```

3. Reduce output formats:
```bash
# Generate only needed formats
data-extract process ./docs/ --output-formats txt
```

4. Check disk usage:
```bash
df -h
du -sh output/
```

## Configuration Issues

### Invalid Configuration

**Symptom:**
```
ConfigurationError: Invalid setting: ...
```

**Solutions:**

1. Validate config file:
```bash
data-extract config validate
```

2. Check YAML syntax:
```bash
# Use online validator or
python -c "import yaml; yaml.safe_load(open('.data-extract.yaml'))"
```

3. Review configuration:
```bash
data-extract config show
```

4. Reset to defaults:
```bash
# Rename config file
mv .data-extract.yaml .data-extract.yaml.bak

# Run with defaults
data-extract process input.pdf
```

### Environment Variable Conflicts

**Symptom:**
Configuration doesn't match expected values.

**Solutions:**

1. Check active environment variables:
```bash
env | grep DATA_EXTRACT
```

2. Unset conflicting variables:
```bash
unset DATA_EXTRACT_LOG_LEVEL
unset DATA_EXTRACT_CACHE_DIR
```

3. Show merged configuration:
```bash
data-extract config show -vv
# Shows source of each setting
```

### Preset Not Found

**Symptom:**
```
ERROR: Unknown preset: custom-preset
```

**Solutions:**

1. List available presets:
```bash
data-extract process --help
# Shows available presets
```

2. Use built-in presets:
- `llm-upload`
- `high-quality`
- `fast-batch`
- `semantic-analysis`

3. Create custom config instead:
```yaml
# .data-extract.yaml
extraction:
  ocr_fallback: true
chunking:
  strategy: semantic
```

## Session Recovery

### Interrupted Processing

**Symptom:**
Batch processing stopped mid-execution.

**Solutions:**

1. List active sessions:
```bash
data-extract session list --active
```

2. Resume session:
```bash
data-extract session resume SESSION_ID
```

3. Or retry failed files:
```bash
data-extract retry ./docs/ --output-dir ./output
```

### Corrupted Session

**Symptom:**
```
ERROR: Cannot resume session: corrupted state
```

**Solutions:**

1. Clean corrupted session:
```bash
data-extract session cleanup --failed-only
```

2. Restart processing:
```bash
# Use incremental to skip completed files
data-extract process ./docs/ --output-dir ./output --incremental
```

### Session Files Accumulation

**Symptom:**
Large number of old session files.

**Solutions:**

1. Clean old sessions:
```bash
data-extract session cleanup --days 7
```

2. Configure automatic cleanup:
```yaml
# .data-extract.yaml
session:
  auto_cleanup: true
  cleanup_days: 7
```

## Validation Issues

### Validation Warnings

**Symptom:**
```
WARNING: Document completeness below threshold: 0.85
```

**Solutions:**

1. Review validation report:
```bash
data-extract validate output.json --verbose
```

2. Check extraction confidence:
```bash
# Look at "confidence" field in JSON output
cat output.json | jq '.extraction.confidence'
```

3. Re-extract with different settings:
```bash
data-extract process input.pdf --ocr-fallback --confidence-threshold 0.5
```

### Failed Validation

**Symptom:**
```
ERROR: Validation failed: missing required fields
```

**Solutions:**

1. Check file integrity:
```bash
# Verify JSON is valid
python -m json.tool output.json > /dev/null
```

2. Re-generate output:
```bash
# Clear cache and re-process
data-extract cache clear input.pdf
data-extract process input.pdf --output-dir ./output
```

3. Use non-strict validation:
```bash
# Allow warnings
data-extract validate output.json --no-strict
```

## Semantic Analysis Issues

### Semantic Analysis Fails

**Symptom:**
```
ERROR: Semantic analysis failed: ...
```

**Solutions:**

1. Verify dependencies:
```bash
python -c "import sklearn; print(sklearn.__version__)"
python -c "import textstat; print(textstat.__version__)"
```

2. Check corpus size:
```bash
# Semantic analysis requires minimum 2 chunks
# Check chunk count in JSON output
```

3. Adjust similarity threshold:
```bash
data-extract process input.pdf --similarity-threshold 0.9
```

4. Disable semantic analysis:
```bash
data-extract process input.pdf --disable-semantic
```

### Low Quality Scores

**Symptom:**
Quality metrics (readability, coherence) are unexpectedly low.

**Solutions:**

1. Review source document:
```bash
# Check if source is actually low quality (OCR artifacts, formatting issues)
```

2. Enable text cleaning:
```bash
# Already enabled by default, but verify in config
data-extract config show normalization
```

3. Use high-quality preset:
```bash
data-extract process input.pdf --preset high-quality
```

## Logging and Debugging

### Enable Verbose Logging

```bash
# Single verbose flag
data-extract process input.pdf -v

# Double verbose (debug level)
data-extract process input.pdf -vv

# Triple verbose (trace level)
data-extract process input.pdf -vvv
```

### Log to File

```bash
# Redirect stderr to file
data-extract process input.pdf 2> debug.log

# Or use environment variable
export DATA_EXTRACT_LOG_FILE=debug.log
data-extract process input.pdf
```

### Debug Configuration

```bash
# Show all configuration sources
data-extract config show -vv

# Show environment variables
env | grep DATA_EXTRACT

# Validate configuration
data-extract config validate --verbose
```

### Profile Performance

```bash
# Time processing
time data-extract process input.pdf

# Profile with Python
python -m cProfile -o profile.stats $(which data-extract) process input.pdf

# Analyze profile
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
```

## Getting Help

### Built-in Help

```bash
# General help
data-extract --help

# Command-specific help
data-extract process --help

# Extended help with examples
data-extract process --learn
```

### System Information

```bash
# Python version
python --version

# Package version
data-extract --version

# Environment info
python -m pip list
```

### Report Issues

When reporting issues, include:

1. Command executed
2. Error message (full traceback)
3. Python version
4. Package version
5. Operating system
6. Sample file (if possible)

**Example report:**
```
Command:
  data-extract process document.pdf

Error:
  [Full error message and traceback]

Environment:
  Python: 3.11.5
  data-extract: 1.0.0
  OS: Ubuntu 22.04
  spaCy model: en_core_web_md-3.7.1

Sample:
  [Attach or describe problematic file]
```

## Common Patterns

### Retry Failed Batch

```bash
# Initial batch
data-extract process ./docs/ --output-dir ./output

# Retry failures
data-extract retry ./docs/ --output-dir ./output --max-retries 5

# Validate results
data-extract validate ./output/
```

### Incremental Updates

```bash
# Initial processing
data-extract process ./docs/ --output-dir ./output

# Add new files to ./docs/

# Process only new/changed files
data-extract process ./docs/ --output-dir ./output --incremental
```

### Clean Slate

```bash
# Clear all cached data
data-extract cache clear

# Clean old sessions
data-extract session cleanup --days 0

# Remove output directory
rm -rf output/

# Reprocess from scratch
data-extract process ./docs/ --output-dir ./output
```

### Performance Tuning

```bash
# Start with fast preset
data-extract process ./docs/ --preset fast-batch

# If quality is insufficient, try balanced
data-extract process ./docs/ --preset llm-upload

# If quality is still insufficient, use high quality
data-extract process ./docs/ --preset high-quality

# For maximum quality, enable semantic analysis
data-extract process ./docs/ --enable-semantic --preset high-quality
```
