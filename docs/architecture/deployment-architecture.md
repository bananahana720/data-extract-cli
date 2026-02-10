# Deployment Architecture

## Local Development
```
Developer Workstation
├── Python 3.12 virtual environment
├── Source code (git repository)
├── Test fixtures (sample audit documents)
└── Local output directory
```

## Enterprise Deployment (Future)
```
Enterprise Workstation (F100 Environment)
├── Python 3.12 (IT-approved)
├── Tesseract OCR (system-installed)
├── Tool installed via pip (internal PyPI mirror or wheel file)
├── Configuration in user home directory (~/.data-extract/)
├── Shared output location (network drive)
└── Logs (local or network share)
```

## Packaging & Distribution
- **Development**: `pip install -e ".[dev]"` from source
- **User install**: `pip install data-extraction-tool` (future: internal PyPI)
- **Wheel distribution**: Build wheel for air-gapped systems (`pip wheel .`)
- **Dependencies bundled**: Optional vendoring for restricted networks
