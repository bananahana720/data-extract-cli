# spaCy Troubleshooting Guide

This guide helps resolve common issues with spaCy 3.7.2+ and the `en_core_web_md` language model used in this project.

## Table of Contents

- [Model Not Found Error](#model-not-found-error)
- [Version Compatibility Issues](#version-compatibility-issues)
- [Performance Issues](#performance-issues)
- [Installation Failures](#installation-failures)
- [Import Errors](#import-errors)
- [Network/Proxy Issues](#networkproxy-issues)

---

## Model Not Found Error

### Symptom
```
OSError: [E050] Can't find model 'en_core_web_md'
```

### Solution
Download the language model:
```bash
python -m spacy download en_core_web_md
```

### Verification
```bash
# Check installed models
python -m spacy validate

# Test model loading
python -c "import spacy; nlp = spacy.load('en_core_web_md'); print('Model loaded successfully')"
```

### Alternative: Manual Installation
If the download command fails, manually download and install:

```bash
# Download model manually from GitHub releases
# Visit: https://github.com/explosion/spacy-models/releases/en_core_web_md-3.8.0

# Install from downloaded .whl file
pip install en_core_web_md-3.8.0-py3-none-any.whl
```

---

## Version Compatibility Issues

### Symptom
```
ValueError: [E941] Can't find model 'en_core_web_md'. It looks like you're trying to load a model from spaCy 3.x with an older version of spaCy.
```

### Solution
Ensure spaCy version is 3.7.2 or higher:

```bash
# Check current version
python -c "import spacy; print(spacy.__version__)"

# Upgrade spaCy if needed
pip install --upgrade "spacy>=3.7.2,<4.0"

# Re-download model for current spaCy version
python -m spacy download en_core_web_md
```

### Python Version Check
spaCy 3.7.2+ requires Python 3.7+. This project requires Python 3.12+:

```bash
python --version
# Should show Python 3.12.x or 3.13.x
```

---

## Performance Issues

### Symptom
Slow model loading or sentence segmentation.

### Baseline Performance
- **Model load time**: ~1-2 seconds (first load only)
- **Segmentation speed**: 4000+ words/second
- **Memory footprint**: ~100MB loaded model

### Solutions

#### 1. Pre-load Model Once
The utility function uses lazy loading with module-level caching. Model loads once on first call.

```python
from src.data_extract.utils.nlp import get_sentence_boundaries

# First call loads model (1-2 seconds)
boundaries1 = get_sentence_boundaries("First text.")

# Subsequent calls reuse cached model (instant)
boundaries2 = get_sentence_boundaries("Second text.")
```

#### 2. Use Provided nlp Parameter
For batch processing, load model once and pass it:

```python
import spacy
from src.data_extract.utils.nlp import get_sentence_boundaries

# Load model once
nlp = spacy.load("en_core_web_md")

# Process multiple documents with same model
for document in documents:
    boundaries = get_sentence_boundaries(document.text, nlp=nlp)
```

#### 3. Check System Resources
- Ensure adequate RAM (model requires ~100MB)
- Check CPU usage (text processing is CPU-intensive)
- Close other applications if system is resource-constrained

---

## Installation Failures

### Symptom 1: pip Network Timeout
```
ERROR: Could not find a version that satisfies the requirement spacy>=3.7.2
```

### Solution
Check network connectivity and try with increased timeout:

```bash
pip install --timeout=60 "spacy>=3.7.2,<4.0"
```

### Symptom 2: SSL Certificate Errors
```
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

### Solution
For corporate networks with SSL inspection:

```bash
# Temporary workaround (not recommended for production)
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org spacy

# Better: Install corporate SSL certificates
# Contact IT for certificate installation instructions
```

### Symptom 3: Permission Denied
```
PermissionError: [Errno 13] Permission denied
```

### Solution
Use user-level installation:

```bash
pip install --user "spacy>=3.7.2,<4.0"
python -m spacy download en_core_web_md --user
```

---

## Import Errors

### Symptom
```python
ImportError: cannot import name 'Language' from 'spacy.language'
```

### Solution
Reinstall spaCy with dependencies:

```bash
pip uninstall spacy
pip install --no-cache-dir "spacy>=3.7.2,<4.0"
python -m spacy download en_core_web_md
```

### Verify Installation
```bash
python -c "from spacy.language import Language; print('Import successful')"
```

---

## Network/Proxy Issues

### Symptom
Model download fails behind corporate proxy.

### Solution 1: Configure pip Proxy
```bash
# Set proxy environment variables
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Windows
set HTTP_PROXY=http://proxy.company.com:8080
set HTTPS_PROXY=http://proxy.company.com:8080

# Download model
python -m spacy download en_core_web_md
```

### Solution 2: Manual Download
If automated download fails, manually download and install:

1. Visit: https://github.com/explosion/spacy-models/releases
2. Download: `en_core_web_md-3.8.0-py3-none-any.whl` (~33MB)
3. Install locally:
   ```bash
   pip install path/to/en_core_web_md-3.8.0-py3-none-any.whl
   ```

---

## Advanced Debugging

### Enable Verbose Logging
```python
import structlog
import logging

# Configure structlog for debugging
logging.basicConfig(level=logging.DEBUG)

from src.data_extract.utils.nlp import get_sentence_boundaries

# Model load and processing will log detailed info
boundaries = get_sentence_boundaries("Test text.")
```

### Check Model Metadata
```python
import spacy

nlp = spacy.load("en_core_web_md")
print(f"Model name: {nlp.meta['name']}")
print(f"Version: {nlp.meta['version']}")
print(f"Language: {nlp.meta['lang']}")
print(f"Pipeline: {nlp.pipe_names}")
print(f"Vocab size: {len(nlp.vocab)}")
```

Expected output:
```
Model name: en_core_web_md
Version: 3.8.0
Language: en
Pipeline: ['tok2vec', 'tagger', 'parser', 'attribute_ruler', 'lemmatizer', 'ner']
Vocab size: 764
```

---

## Common Questions

### Q: Why en_core_web_md instead of en_core_web_sm?
**A:** `en_core_web_md` provides better accuracy for sentence segmentation (95%+ on our gold standard corpus). The small model has lower accuracy on complex cases (abbreviations, dialogue).

### Q: Can I use a different spaCy model?
**A:** Yes, but you'll need to:
1. Update `pyproject.toml` dependencies
2. Modify `src/data_extract/utils/nlp.py` to load your model
3. Re-run accuracy tests to ensure ≥95% accuracy
4. Update documentation

### Q: Does the model work offline?
**A:** Yes! After initial download, the model is cached locally and works offline. Model location:
- **Windows**: `C:\Users\<username>\AppData\Local\Programs\Python\Python3XX\Lib\site-packages\en_core_web_md\`
- **macOS**: `/usr/local/lib/python3.XX/site-packages/en_core_web_md/`
- **Linux**: `/usr/local/lib/python3.XX/dist-packages/en_core_web_md/`

### Q: How do I update the model?
**A:** Download the latest version:
```bash
python -m spacy download en_core_web_md --upgrade
```

---

## Performance Benchmarks

Based on Story 2.5.2 validation tests:

| Metric | Requirement | Actual (Windows) |
|--------|-------------|------------------|
| Model load time | <5 seconds | ~1.2 seconds |
| Segmentation (1000 words) | <250ms | ~220ms |
| Throughput | >4000 words/sec | ~4850 words/sec |
| Accuracy (gold standard) | ≥95% | 100% |

**Note**: Performance varies by hardware. These benchmarks are from development system (Windows 11, 16GB RAM, Intel i7).

---

## Getting Help

If issues persist after trying these solutions:

1. **Check spaCy Documentation**: https://spacy.io/usage
2. **spaCy GitHub Issues**: https://github.com/explosion/spaCy/issues
3. **Project Documentation**: See `CLAUDE.md` for architecture details
4. **Contact**: Create an issue in this repository with:
   - Python version (`python --version`)
   - spaCy version (`python -c "import spacy; print(spacy.__version__)"`)
   - Error message (full traceback)
   - Operating system
