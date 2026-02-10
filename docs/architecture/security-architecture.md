# Security Architecture

## On-Premise Processing (Enterprise Requirement)
- **NO external API calls** (no OpenAI, Anthropic, etc.)
- **NO cloud dependencies** (no AWS, Azure, GCP services)
- **NO network transmission of data** (all processing local)
- **NO telemetry or usage tracking**

## Data Handling
- **Sensitive document processing**: Assume all inputs are confidential audit documents
- **Temporary file cleanup**: Delete temp files after processing (configurable retention)
- **File permissions**: Output files inherit source file permissions (or configurable)
- **No data in logs**: Log file paths and hashes, NOT content

## Input Validation
- **File type validation**: Check magic bytes, not just extensions
- **File size limits**: Configurable max file size (default: 100MB per file)
- **Path traversal prevention**: Validate all file paths (reject ../ patterns)
- **Safe extraction**: Prevent zip bombs, XML bombs in document parsing

## Dependency Security
- **Pinned versions**: All dependencies pinned in pyproject.toml for reproducibility
- **No transformer models**: Comply with enterprise IT restriction
- **Trusted sources**: All packages from official PyPI
- **Regular updates**: Security patches via Dependabot or manual review
