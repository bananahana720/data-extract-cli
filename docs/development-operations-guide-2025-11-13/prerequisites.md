# Prerequisites

## Python Version

**Mandatory Requirement:** Python 3.12 or higher

```bash
# Verify your Python version
python --version
# Expected output: Python 3.12.x or 3.13.x
```

**Downloads:**
- **Windows**: https://www.python.org/downloads/
- **macOS**: `brew install python@3.12` or https://www.python.org/downloads/
- **Linux**: `sudo apt install python3.12` (Ubuntu/Debian) or equivalent for your distribution

## System Dependencies

### Optional: OCR Support (pytesseract)

For processing scanned PDFs without native text, install Tesseract:

**Windows:**
1. Download installer: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to default location: `C:\Program Files\Tesseract-OCR`
3. Set environment variable (optional if installed to default):
   ```bash
   set TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
   ```

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install tesseract-ocr
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install tesseract
```

### Git

Required for version control:

**Windows/macOS:** Download from https://git-scm.com/
**Linux:** `sudo apt install git` (Ubuntu/Debian) or equivalent

## Platform Notes

- **Windows**: Primary target platform - all features tested on Windows 11
- **macOS**: Fully supported - minor differences in path handling
- **Linux**: Fully supported - tested on Ubuntu 22.04+

---
