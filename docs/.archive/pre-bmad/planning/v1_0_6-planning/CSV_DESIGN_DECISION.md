# CSV Design Decision - ContentBlock Architecture

**Document ID**: CSV-DESIGN-001
**Version**: 1.0
**Created**: 2025-11-06
**Status**: FINAL RECOMMENDATION
**Target**: v1.0.6

---

## Executive Summary

**Recommendation**: **Option B - Single TABLE ContentBlock per CSV file** with full TableMetadata

**Rationale**: Aligns with Excel extractor pattern, maximizes compatibility with existing formatters, provides optimal balance between simplicity and functionality, and supports all downstream processing requirements.

**Key Decision Points**:
- CSV files are inherently single-table structures (unlike multi-sheet Excel)
- TableMetadata provides rich structure preservation without complexity
- Formatters (JSON, Markdown) already handle TABLE blocks and TableMetadata
- Single ContentBlock per file simplifies pipeline processing
- Header detection heuristic based on data type analysis (95%+ accuracy expected)

---

## CSV Characteristics Analysis

### Core Properties
CSV (Comma-Separated Values) is a flat, tabular data format with these characteristics:

**Structure**:
- Flat 2D grid: rows and columns
- No native pagination (unlike PDF)
- No native sheets (unlike Excel)
- Single logical table per file
- Optional header row (first row)

**Data**:
- Text-based encoding (UTF-8, Latin-1, CP1252, etc.)
- String representation of all values (no native types)
- Delimiter variations: comma (`,`), tab (`	`), semicolon (`;`), pipe (`|`)
- Quoting for embedded delimiters: `"value, with, commas"`
- Escape sequences: `""` for literal quotes

**Challenges**:
1. **Delimiter ambiguity**: Must detect from content
2. **Encoding detection**: No metadata, trial-and-error needed
3. **Header detection**: No standard marker, heuristic required
4. **Type inference**: Everything is text initially
5. **Malformed data**: Inconsistent column counts, encoding errors
6. **Large files**: Can exceed memory limits (streaming needed)

### CSV vs Excel Comparison

| Aspect | CSV | Excel (XLSX) | Implication |
|--------|-----|--------------|-------------|
| **Structure** | Single flat table | Multi-sheet workbook | CSV simpler |
| **Metadata** | None | Rich (formulas, styles, charts) | CSV has minimal metadata |
| **Headers** | Implicit (by convention) | Explicit (first row assumption) | CSV needs detection |
| **Data Types** | Text only | Typed (number, date, formula) | CSV requires inference |
| **Delimiters** | Varies (`,` `;` `	` `|`) | N/A (binary format) | CSV needs detection |
| **Encoding** | Varies (UTF-8, Latin-1, etc.) | UTF-8 (ZIP-based) | CSV needs detection |
| **File Size** | Can be very large (GB) | Typically smaller (compressed) | CSV may need streaming |
| **Pagination** | None | Sheets | CSV is single-unit |

**Key Insight**: Excel has **multiple tables** (sheets), CSV has **one table**. This suggests CSV should map to a **single TABLE ContentBlock**, not multiple blocks.
