# Configuration Management Analysis

## Summary
- Files scanned: 10 configuration files
- Key findings:
  - Comprehensive four-tier configuration cascade architecture planned (Epic 5)
  - Multiple YAML-based configuration files for extractors, normalizers, and infrastructure
  - Structured error code registry with 50+ error codes
  - Logging framework with environment-specific templates
  - Configuration schema defines 285+ settings across 12 sections

## Detailed Analysis

### Configuration Architecture

#### Four-Tier Precedence Cascade (Epic 5 Design)

The project implements a planned four-tier configuration cascade system:

1. **CLI Flags** (highest precedence) - Epic 5 implementation
2. **Environment Variables** (`DATA_EXTRACTOR_*` prefix) - Epic 5 implementation
3. **YAML Configuration Files** - Currently implemented
4. **Hardcoded Defaults** (lowest precedence) - Currently implemented

**Status**: Infrastructure prepared, full cascade implementation planned for Epic 5.

#### Configuration Files Scanned

**Infrastructure Configuration** (3 files):
- `src/infrastructure/config_schema.yaml` - Master configuration schema (285+ settings)
- `src/infrastructure/log_config.yaml` - Logging framework configuration
- `src/infrastructure/error_codes.yaml` - Error code registry (50+ error codes)

**Normalization Configuration** (4 files in `config/normalize/`):
- `cleaning_rules.yaml` - Text cleaning patterns (OCR artifacts, headers/footers, whitespace)
- `entity_patterns.yaml` - Entity recognition patterns for 6 audit domain types
- `entity_dictionary.yaml` - Entity normalization dictionary
- `schema_templates.yaml` - Document type schema templates

**Project Configuration**:
- `pyproject.toml` - Python project metadata, dependencies, tool configurations
- `docs/bmm-workflow-status.yaml` - BMAD workflow status tracking

### Configuration Schema Deep Dive

#### Master Configuration Schema (`config_schema.yaml`)

**12 Configuration Sections** (285+ total settings):

1. **General Settings** (6 settings)
   - `app_name`, `version`, `work_dir`, `max_workers`
   - Default: 4 workers for parallel processing

2. **Logging Configuration** (10 settings)
   - Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
   - Format: JSON (production) or text (development)
   - Rotation: 10MB max size, 5 backup files
   - Handlers: file + optional console

3. **Extractors Configuration** (40+ settings)
   - **DOCX**: paragraph length limits, style extraction, empty paragraph handling
   - **PDF**: OCR settings (DPI: 300, language: eng), page range, image extraction
   - **PPTX**: speaker notes, slide numbers, image extraction
   - **XLSX**: sheet selection, header detection, row/column limits

4. **Processors Configuration** (15+ settings)
   - **Context Linker**: enabled, max_depth: 10 levels
   - **Metadata Aggregator**: word count, character count, language detection
   - **Quality Validator**: min_quality_score: 0.70, fail_on_low_quality: false

5. **Formatters Configuration** (15+ settings)
   - **JSON**: indent: 2, include_nulls: false, sort_keys: false
   - **Markdown**: TOC enabled, TOC depth: 3, code language: text
   - **Chunked**: max_tokens: 4000, overlap: 200, strategy: paragraph

6. **Pipeline Settings** (7 settings)
   - fail_fast: false, retry_on_failure: true, max_retries: 3
   - show_progress: true, track_metrics: true

7. **Performance Settings** (5 settings)
   - Caching: enabled, directory: ./.cache, expiration: 3600s
   - memory_limit_mb: 500, extraction_timeout: 300s

8. **Security Settings** (7 settings)
   - validate_file_signatures: true
   - max_file_size_mb: 100
   - allowed_extensions: [.docx, .pdf, .pptx, .xlsx]
   - scan_malware: false, sanitize_content: true

**Environment Variable Override Pattern**:
```
DATA_EXTRACTOR_<SECTION>_<KEY>

Examples:
DATA_EXTRACTOR_LOGGING_LEVEL=DEBUG
DATA_EXTRACTOR_EXTRACTORS_DOCX_MAX_PARAGRAPH_LENGTH=500
DATA_EXTRACTOR_PERFORMANCE_MEMORY_LIMIT_MB=1000
```

### Error Code Registry (`error_codes.yaml`)

**50+ Structured Error Codes** across 9 categories:

| Category | Code Range | Count | Examples |
|----------|------------|-------|----------|
| Validation Errors | E001-E099 | 6 | E001: File not found, E005: Unsupported format |
| Extraction Errors | E100-E199 | 21 | E100: Document corrupted, E102: Password-protected |
| DOCX-Specific | E110-E129 | 2 | E110: Invalid XML structure |
| PDF-Specific | E130-E149 | 2 | E130: Unsupported encryption, E131: Scanned PDF |
| Processing Errors | E200-E299 | 4 | E200: Context linking failed, E202: Quality validation |
| Formatting Errors | E300-E399 | 3 | E300: Formatting failed, E302: JSON serialization |
| Configuration Errors | E400-E499 | 4 | E400: Config file not found, E403: Value out of range |
| Resource Errors | E500-E599 | 4 | E500: Out of memory, E502: Operation timeout |
| External Service | E600-E699 | 2 | E600: OCR service unavailable |
| Pipeline Errors | E700-E799 | 3 | E700: Pipeline init failed, E702: No suitable extractor |
| Unknown Errors | E900-E999 | 2 | E900: Unhandled exception, E901: Assertion failed |

**Error Structure** (per code):
- `category`: Error category classification
- `message`: User-friendly message
- `technical_message`: Technical details with placeholders
- `recoverable`: Boolean flag (can processing continue?)
- `suggested_action`: Actionable resolution guidance

### Logging Configuration (`log_config.yaml`)

**Logging Framework Features**:

1. **Environment-Specific Configurations**:
   - Development: DEBUG level, text format, console + file (1MB, 3 backups)
   - Production: INFO level, JSON format, file only (100MB, 10 backups)
   - Debug: DEBUG level, JSON format, verbose logging (5MB, 2 backups)

2. **JSON Format Fields** (production):
   - timestamp (ISO 8601), level, message, module, function, line
   - correlation_id (request tracking), duration_seconds (performance)
   - Custom fields via `extra={...}`

3. **Rotation Settings**:
   - max_bytes: File size threshold for rotation
   - backup_count: Number of rotated files to retain
   - Thread-safe rotating file handler

### Normalization Configuration

#### Text Cleaning Rules (`cleaning_rules.yaml`)

**OCR Artifact Patterns** (9 patterns):
- Repeated special characters: `^^^`, `■■■`, `~~~`
- Long underscores/dashes/equals (10+ consecutive)
- Control characters (non-printable ASCII)
- Random symbol sequences (5+ chars)
- Isolated symbols surrounded by whitespace

**Header/Footer Patterns** (11 patterns):
- Page numbers: "Page 1", "Page 1 of 10", standalone numbers
- Confidentiality markers: "Confidential", "Internal Use Only"
- Draft markers: "DRAFT", "Preliminary"
- Date stamps: MM/DD/YYYY, YYYY-MM-DD formats
- Document IDs and version headers

**Whitespace Normalization**:
- max_consecutive_newlines: 2 (preserve paragraph breaks)
- normalize_tabs: true, tab_size: 4
- trim_lines: true, normalize_multiple_spaces: true

**Formatting Preservation** (8 patterns):
- Markdown lists: `- `, `* `, `+ `, `1. `, `a. `
- Code blocks: indented (4+ spaces), fenced (```)
- Emphasis markers: `**bold**`, `*italic*`, `_italic_`

**Header/Footer Detection Settings**:
- min_pages_for_detection: 3
- header_region_percent: 10% (top), footer_region_percent: 10% (bottom)
- similarity_threshold: 0.8 (80% similarity required)
- max_header_length: 500 chars, max_footer_length: 500 chars

**Determinism Settings**:
- disable_randomness: true
- precompile_patterns: true
- timestamp_in_metadata_only: true

#### Entity Recognition Patterns (`entity_patterns.yaml`)

**6 Audit Domain Entity Types**:

1. **Process** - Business/operational processes (4 pattern groups)
   - ID formats: `PROC-\d{1,5}`, `P-\d{1,5}`, `Process-\d{1,5}`
   - Aliases: workflow, procedure
   - Archer-specific: `ARCH-PROC-\d{1,6}`

2. **Risk** - Risk identification and assessment (5 pattern groups)
   - ID formats: `RISK-\d{1,5}`, `R-\d{1,5}`
   - Risk types: inherent, residual, operational, strategic, compliance, financial
   - Severity levels: high, medium, low, critical
   - Archer-specific: `ARCH-RISK-\d{1,6}`, compressed format `R-\d{4,6}`

3. **Control** - Control measures and procedures (4 pattern groups)
   - ID formats: `CTRL-\d{1,5}`, `C-\d{1,5}`, `Control-\d{1,5}`
   - Control types: preventive, detective, corrective
   - Categories: access, security, internal, compensating
   - Archer-specific: `ARCH-CTRL-\d{1,6}`, compressed `C-\d{4,6}`

4. **Regulation** - Regulatory requirements (9 pattern groups)
   - Specific regulations: SOX, GDPR, HIPAA, PCI-DSS, NIST CSF, ISO 27001/27002/31000, COBIT, COSO
   - ID formats: `REG-<name>` (e.g., `REG-SOX`, `REG-GDPR`)
   - Archer-specific: `ARCH-REG-\d{1,6}`

5. **Policy** - Organizational policies (4 pattern groups)
   - ID formats: `POL-\d{1,5}`, `P-\d{1,5}`, `Policy-\d{1,5}`
   - Policy types: security, data, access, privacy, IT
   - Common policies: acceptable use, password, retention
   - Archer-specific: `ARCH-POL-\d{1,6}`

6. **Issue** - Audit findings and observations (5 pattern groups)
   - ID formats: `ISS-\d{1,5}`, `I-\d{1,5}`, `Issue-\d{1,5}`
   - Synonyms: finding, audit finding
   - Severity: high, medium, low, critical
   - Types: control deficiency, material weakness, significant deficiency
   - Archer-specific: `ARCH-ISS-\d{1,6}`, compressed `I-\d{4,6}`

**Pattern Structure**:
- `pattern`: Regex (Python syntax)
- `description`: Human-readable description
- `priority`: Matching order (1 = highest)
- `context_required`: Boolean (requires surrounding context?)
- `context_keywords`: Keywords within ±5 words for disambiguation
- `id_formats`: Supported ID format patterns

**Context Analysis Settings**:
- window_size: 5 words (before/after entity mention)
- min_confidence: 0.7
- require_context_for_ambiguous: true

**ID Normalization Rules**:
- canonical_separator: "-"
- strip_characters: ["#", ":", "_", " "]
- capitalize_type: true ("risk" → "Risk")
- preserve_leading_zeros: false

**Disambiguation Rules**:
- Exclusion keywords: "at risk", "in control", "process of", "issue with"
- Entity indicators: "ID", "identifier", "number", "ref", "reference", "documented", "assigned"

**Total Pattern Count**: 40+ patterns across 6 entity types

### pyproject.toml Configuration

**Tool Configurations Embedded**:

1. **pytest** (`[tool.pytest.ini_options]`):
   - testpaths: ["tests"]
   - python_files: ["test_*.py"]
   - addopts: "-v --cov=src --cov-report=term-missing"
   - markers: performance, slow

2. **black** (`[tool.black]`):
   - line-length: 100
   - target-version: ['py312']

3. **ruff** (`[tool.ruff]`):
   - line-length: 100
   - target-version: "py312"
   - select: ["E", "F", "I", "N", "W"]
   - ignore: ["E501"] (line too long, handled by black)

4. **mypy** (`[tool.mypy]`):
   - python_version: "3.12"
   - warn_return_any: true, warn_unused_configs: true
   - disallow_untyped_defs: true
   - **Brownfield exclusions**: `src/(cli|extractors|processors|formatters|core|pipeline|infrastructure)/`

**Dependencies** (36 packages):
- Core: pydantic>=2.0, PyYAML>=6.0, python-dotenv>=1.0, structlog>=24.0
- Epic 2: beautifulsoup4>=4.12, lxml>=5.0, spacy>=3.7.2
- Brownfield: python-docx, pypdf>=3.0, python-pptx, openpyxl, click, rich, pdfplumber, Pillow
- Dev (16 packages): pytest>=8.0, pytest-cov>=5.0, black>=24.0, ruff>=0.6, mypy>=1.11, pre-commit>=3.0

**Package Data Inclusion**:
- `*.yaml`, `*.yml`, `*.json`, `*.txt` files included in all packages
- Specific package data for infrastructure, cli, formatters, extractors, processors

## Recommendations

### Configuration Management Improvements

1. **Consolidate Configuration Files**
   - Consider merging `config_schema.yaml` and actual default values into a single source of truth
   - Create environment-specific override files (dev.yaml, prod.yaml) instead of embedded templates

2. **Configuration Validation**
   - Implement Pydantic models for configuration validation (leverage existing Pydantic v2 usage)
   - Add configuration schema versioning for migration support
   - Validate configuration on startup with clear error messages

3. **Environment Variable Support**
   - Implement `DATA_EXTRACTOR_*` environment variable parsing (Epic 5)
   - Document all supported environment variables in a central reference
   - Add `.env.example` file with all available settings

4. **Configuration Documentation**
   - Generate configuration reference from `config_schema.yaml` automatically
   - Add inline examples for complex settings (regex patterns, quality thresholds)
   - Document configuration cascade precedence with visual diagram

5. **Error Code Registry**
   - Add error code lookup utility function
   - Implement error code testing (ensure all codes are reachable)
   - Add error code versioning for API stability

6. **Logging Configuration**
   - Consider structured logging configuration using code-based setup (not just YAML)
   - Add log sampling/throttling for high-volume operations
   - Implement log aggregation hooks for production environments

7. **Entity Pattern Management**
   - Add pattern testing framework (validate regex patterns with examples)
   - Implement pattern performance profiling (identify slow regex patterns)
   - Consider pattern compilation caching strategy

### Security Considerations

1. **Secrets Management**
   - Do not store secrets in YAML configuration files
   - Use environment variables or secret management service for sensitive data
   - Add pre-commit hook to prevent committing `.env` files

2. **Configuration Injection**
   - Validate all configuration inputs to prevent injection attacks
   - Sanitize user-provided regex patterns before compilation
   - Implement configuration schema whitelist (reject unknown keys)

### Performance Optimizations

1. **Configuration Loading**
   - Cache compiled regex patterns from entity_patterns.yaml
   - Lazy-load configuration sections only when needed
   - Profile configuration loading time (target <100ms)

2. **Pattern Matching**
   - Precompile all regex patterns on initialization
   - Use pattern priority ordering to short-circuit expensive matches
   - Consider regex optimization for hot paths (entity recognition)

### Epic 5 Readiness

**Configuration Cascade Implementation Checklist**:
- [ ] Implement CLI flag parsing (Typer-based)
- [ ] Implement environment variable parsing (`DATA_EXTRACTOR_*`)
- [ ] Implement YAML file discovery (~/.data-extract/config.yaml, project-local)
- [ ] Implement precedence resolution (merge configurations)
- [ ] Add configuration override logging (show final resolved config)
- [ ] Add `data-extract config show` command to display active configuration
- [ ] Add `data-extract config validate` command to check configuration validity
- [ ] Document configuration cascade with examples in user guide

**Configuration Files Status**:
- ✅ YAML configuration files prepared
- ✅ Error code registry comprehensive
- ✅ Logging framework configured
- ✅ Entity patterns defined
- ⏳ Environment variable parsing (Epic 5)
- ⏳ CLI flag integration (Epic 5)
- ⏳ Configuration validation framework (Epic 5)
