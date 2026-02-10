# Test Fixtures

This directory contains test fixtures for the data extraction pipeline. Fixtures are organized by document type and size category to support unit, integration, and performance testing.

## Directory Structure

```
tests/fixtures/
├── pdfs/
│   ├── large/              # 50+ page PDFs for performance/stress testing
│   │   └── audit-report-large.pdf
│   ├── scanned/            # Image-based PDFs requiring OCR
│   │   └── audit-scan.pdf
│   └── *.pdf               # Standard PDF test files
├── xlsx/
│   ├── large/              # 10K+ row Excel files for performance testing
│   │   └── audit-data-10k-rows.xlsx
│   └── *.xlsx              # Standard Excel test files
├── docx/
│   └── *.docx              # Word document test files
├── pptx/
│   └── *.pptx              # PowerPoint test files
├── csv/
│   └── *.csv               # CSV test files
├── images/
│   └── *.png, *.jpg        # Image test files
├── archer/
│   └── *                   # Archer-specific audit domain files
└── real-world-files/
    └── *                   # Real-world framework documents (COBIT, NIST, OWASP)
```

## Fixture Inventory

### Large Document Fixtures (Performance Testing)

| Fixture | Type | Size | Rows/Pages | Purpose | Generated | Story |
|---------|------|------|------------|---------|-----------|-------|
| `pdfs/large/audit-report-large.pdf` | PDF | ~0.03 MB | 60+ pages | Large document memory validation (NFR-P2) | Script | 2.5.3 |
| `xlsx/large/audit-data-10k-rows.xlsx` | Excel | ~0.67 MB | 10,240 rows | Large spreadsheet processing timeout validation | Script | 2.5.3 |
| `pdfs/scanned/audit-scan.pdf` | PDF | ~0.25 MB | 5 pages | End-to-end OCR pipeline testing | Script | 2.5.3 |

**Total Large Fixtures Size**: 0.95 MB (well under 100MB repository health constraint)

### Standard Test Fixtures

| Fixture | Type | Size | Purpose |
|---------|------|------|---------|
| `pdfs/sample.pdf` | PDF | 629 bytes | Minimal PDF with basic text content for unit testing |
| `pdfs/COBIT-2019-*.pdf` | PDF | 0.79-11.36 MB | Real-world governance framework documents |
| `pdfs/NIST.SP.800-37r2.pdf` | PDF | 2.17 MB | Compliance standards testing |
| `pdfs/OWASP-*.pdf` | PDF | 1.58-2.94 MB | Security framework documents |
| `xlsx/sample.xlsx` | Excel | 4.8 KB | Simple Excel spreadsheet for tabular data extraction |
| `xlsx/multi_sheet.xlsx` | Excel | ~10 KB | Multi-sheet workbook testing |
| `xlsx/with_formulas.xlsx` | Excel | ~5 KB | Formula and calculation testing |
| `xlsx/NIST-Privacy-Framework-V1.0-Core.xlsx` | Excel | 0.11 MB | Real-world compliance data |
| `xlsx/sp800-53ar5-assessment-procedures.xlsx` | Excel | 0.45 MB | Complex audit procedure data |
| `docx/sample.docx` | Word | 36 KB | Word document with tables for extraction testing |
| `images/sample.png` | Image | 3.1 KB | Simple image with text for OCR testing |

**Total Repository Fixtures Size**: ~35.69 MB (65% margin under 100 MB constraint)

## Fixture Creation Process

### Large PDF Fixture (`audit-report-large.pdf`)

**Generated**: 2025-11-12 (Story 2.5.3)
**Script**: `scripts/generate_large_pdf_fixture.py`
**Library**: reportlab 3.5.0+

**Structure**:
- Cover page with title and confidentiality notice
- Table of contents (6 sections)
- Executive Summary (3 pages with key findings)
- Risk Assessment Findings (15 pages with 5 risk categories)
  - Risk tables with ID, Description, Impact, Likelihood, Rating columns
  - Analysis paragraphs for each category
- Control Framework Evaluation (12 pages with 4 control areas)
  - Control testing results tables
  - Effectiveness assessments
- Compliance Review Results (10 pages with 3 compliance domains)
  - Findings tables with status and actions
  - Domain-specific assessments
- Recommendations (5 pages with 15 recommendations)
- Appendix: Audit Policies (5 pages)

**Content Sanitization**:
- All content is synthetic/generic - no real company names
- No PII (personally identifiable information)
- No sensitive/proprietary data
- Realistic audit report structure preserved
- Headings, tables, and paragraphs follow industry standards

**Regeneration**:
```bash
python scripts/generate_large_pdf_fixture.py
```

Expected output: 60+ page PDF, ~0.03 MB size

### Large Excel Fixture (`audit-data-10k-rows.xlsx`)

**Generated**: 2025-11-12 (Story 2.5.3)
**Script**: `scripts/generate_large_excel_fixture.py`
**Library**: openpyxl 3.0.10+

**Structure**:
- Header row with 14 columns (frozen for scrolling)
- 10,239 data rows (10,240 total including header)
- Realistic audit data structure

**Columns**:
1. Risk ID (format: R-00001 to R-10239)
2. Risk Description (15 variations)
3. Impact (Low/Medium/High/Critical)
4. Likelihood (Low/Medium/High)
5. Risk Rating (calculated from Impact × Likelihood)
6. Control ID (format: C-00001 to C-10239)
7. Control Description (15 variations)
8. Control Owner (10 departments)
9. Control Status (Effective/Partially Effective/Ineffective/Not Tested)
10. Test Date (randomized within FY 2024)
11. Test Result (Pass/Pass with Exceptions/Fail)
12. Findings (None/1 Minor/2 Minor/1 Major/Multiple Issues)
13. Action Required (None/Remediation Plan/Immediate Action/Monitoring)
14. Target Date (90-120 days from Test Date)

**Content Sanitization**:
- All data is synthetic/randomly generated
- No real company names or department names
- No PII
- Realistic audit data patterns preserved
- Risk ratings follow logical rules (High Impact + High Likelihood = Critical)

**Regeneration**:
```bash
python scripts/generate_large_excel_fixture.py
```

Expected output: 10,240 rows, ~0.67 MB size

### Scanned PDF Fixture (`audit-scan.pdf`)

**Generated**: 2025-11-12 (Story 2.5.3)
**Script**: `scripts/generate_scanned_pdf_fixture.py`
**Libraries**: PIL (Pillow) 10.0.0+, reportlab 3.5.0+

**Structure**:
- 5 image-based pages (150 DPI resolution)
- Page 1: Title page with "CONFIDENTIAL AUDIT REPORT" heading
- Page 2: Executive summary with bullet points
- Page 3: Risk assessment results table
- Pages 4-5: Additional detail pages

**OCR Testing Characteristics**:
- Clear, readable fonts (Arial, 24-48pt sizes)
- High contrast (black text on white background)
- Realistic document layouts (headings, paragraphs, tables)
- Page numbers in footer
- Tests OCR text extraction accuracy
- Tests OCR confidence scoring
- Tests table structure detection

**Content Sanitization**:
- All content is synthetic/generic
- No PII or sensitive information
- Realistic audit report structure

**Regeneration**:
```bash
python scripts/generate_scanned_pdf_fixture.py
```

Expected output: 5-page image-based PDF, ~0.25 MB size

**Note**: Temporary PNG images are created during generation and automatically cleaned up.

## Size Guidelines

### Standard Fixtures
- **<100KB each** (unit test fixtures)
- **Sanitized** - no sensitive data or PII
- **Representative** - reflect real-world audit document characteristics

### Large Fixtures
- **<50 MB each** (performance/integration test fixtures)
- **Total repository fixtures: <100 MB** (repository health constraint)
- **Sanitized** - all content must be synthetic or sanitized

### Real-World Files
- Used for integration tests and benchmarking
- Publicly available framework documents (COBIT, NIST, OWASP, COSO)
- Appropriate licensing for redistribution

## Usage in Tests

Test fixtures are accessible via pytest fixtures defined in:
- `tests/conftest.py` - Global fixtures
- `tests/unit/conftest.py` - Unit test fixtures
- `tests/integration/conftest.py` - Integration test fixtures
- `tests/performance/conftest.py` - Performance test fixtures

Example usage:
```python
def test_pdf_extraction(tmp_path):
    """Test PDF extraction with sample fixture."""
    fixture_path = Path("tests/fixtures/pdfs/sample.pdf")
    result = extract_pdf(fixture_path)
    assert result.success

@pytest.mark.integration
def test_large_pdf_memory_usage():
    """Test large PDF processing stays under 2GB memory (NFR-P2)."""
    fixture_path = Path("tests/fixtures/pdfs/large/audit-report-large.pdf")
    # ... memory monitoring logic ...
```

## Adding New Fixtures

### Guidelines for Contributors

When adding new test fixtures to this directory, follow these guidelines:

1. **Size Constraints**:
   - Standard fixtures: <100 KB each
   - Large fixtures: <50 MB each
   - Total repository fixtures: <100 MB
   - Check total size after adding:
     ```bash
     python -c "from pathlib import Path; total = sum(f.stat().st_size for f in Path('tests/fixtures').rglob('*') if f.is_file()); print(f'Total: {total / (1024*1024):.2f} MB'); exit(0 if total < 100*1024*1024 else 1)"
     ```

2. **Content Sanitization** (CRITICAL):
   - Never commit files with PII (names, emails, SSNs, etc.)
   - Never commit proprietary/confidential company data
   - Use synthetic data generators or sanitization scripts
   - For real-world documents: obtain permission and sanitize first
   - Document sanitization process in commit message

3. **Organization**:
   - Place fixtures in type-specific subdirectories (`pdfs/`, `xlsx/`, etc.)
   - Use `large/` subdirectory for performance testing fixtures (>50 pages, >10K rows)
   - Use descriptive filenames: `{purpose}-{variant}.{ext}` (e.g., `audit-report-large.pdf`)

4. **Documentation**:
   - Add entry to "Fixture Inventory" table above
   - Document purpose and key characteristics
   - If generated by script, document script path and regeneration command
   - If sourced externally, document source and licensing

5. **Naming Conventions**:
   - Use lowercase with hyphens: `my-fixture-name.pdf`
   - Include size hint for large files: `audit-data-100k-rows.xlsx`
   - Include variant/purpose: `scanned-with-tables.pdf`, `multi-sheet-complex.xlsx`

6. **Testing Integration**:
   - Reference fixture in test docstring
   - Use `@pytest.mark.integration` for large fixture tests
   - Use `@pytest.mark.performance` for performance validation tests
   - Document expected processing characteristics (time, memory)

### Example: Adding a New Large DOCX Fixture

```bash
# 1. Create generation script
cat > scripts/generate_large_docx_fixture.py << 'EOF'
"""Generate large DOCX fixture for testing."""
from pathlib import Path
from docx import Document

def generate_large_docx(output_path: Path, num_pages: int = 100):
    doc = Document()
    # ... generation logic ...
    doc.save(output_path)

if __name__ == "__main__":
    output_dir = Path(__file__).parent.parent / "tests" / "fixtures" / "docx" / "large"
    output_dir.mkdir(parents=True, exist_ok=True)
    generate_large_docx(output_dir / "report-large.docx", num_pages=100)
EOF

# 2. Generate fixture
python scripts/generate_large_docx_fixture.py

# 3. Verify size
ls -lh tests/fixtures/docx/large/report-large.docx

# 4. Update this README with inventory entry

# 5. Commit with descriptive message
git add tests/fixtures/docx/large/report-large.docx scripts/generate_large_docx_fixture.py tests/fixtures/README.md
git commit -m "Add large DOCX fixture for Story X.Y.Z

- 100+ page synthetic document (~5 MB)
- Generated with python-docx
- All content sanitized (no PII)
- Purpose: Large document processing validation"
```

## Fixture Maintenance

### Regenerating All Large Fixtures

To regenerate all large fixtures (useful after library updates):

```bash
python scripts/generate_large_pdf_fixture.py
python scripts/generate_large_excel_fixture.py
python scripts/generate_scanned_pdf_fixture.py
```

### Validating Fixture Integrity

Run the fixture validation test to ensure all fixtures are accessible and parseable:

```bash
pytest tests/integration/test_fixtures.py -v
```

### Checking Repository Size

Monitor total fixture size to stay under 100 MB constraint:

```bash
# Total size of all fixtures
python -c "from pathlib import Path; total = sum(f.stat().st_size for f in Path('tests/fixtures').rglob('*') if f.is_file()); print(f'Total: {total / (1024*1024):.2f} MB'); exit(0 if total < 100*1024*1024 else 1)"

# Largest fixtures
python -c "from pathlib import Path; fixtures = sorted([(f, f.stat().st_size) for f in Path('tests/fixtures').rglob('*') if f.is_file()], key=lambda x: x[1], reverse=True); print('\n'.join([f'{f.name}: {size / (1024*1024):.2f} MB' for f, size in fixtures[:10]]))"
```

## Related Documentation

- **Testing Strategy**: `docs/TESTING-README.md` - Overall testing framework and standards
- **CLAUDE.md**: Testing organization, markers, and coverage requirements
- **Architecture**: `docs/architecture.md` - ADR-005 (Streaming Pipeline), ADR-006 (Continue-On-Error)
- **Performance Baselines**: `docs/performance-baselines-story-2.5.1.md` - NFR validation benchmarks

## Story History

- **Story 1.3** (2025-11-10): Initial fixture infrastructure created
  - Basic sample fixtures for unit testing
  - Real-world framework documents added
- **Story 2.5.3** (2025-11-12): Large fixture infrastructure added
  - `audit-report-large.pdf` (60+ pages, 0.03 MB)
  - `audit-data-10k-rows.xlsx` (10,240 rows, 0.67 MB)
  - `audit-scan.pdf` (5 pages, 0.25 MB)
  - Generation scripts with full documentation
  - Total fixture size: 35.69 MB (65% margin under 100 MB constraint)

## Maintenance

Created: 2025-11-10
Last Updated: 2025-11-12 (Story 2.5.3)
Maintained by: Dev team
