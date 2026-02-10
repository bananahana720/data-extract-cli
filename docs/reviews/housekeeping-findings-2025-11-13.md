# Housekeeping Findings Report

**Generated**: 2025-11-13
**Scan Type**: Exhaustive with Housekeeping Focus
**Project**: Data Extraction Tool v0.1.0
**Analyst**: Tech Writer (BMAD Framework)

---

## Executive Summary

**Total Issues Found**: 8 categories
**Severity Breakdown**:
- 🔴 Critical (requires immediate action): 2
- 🟡 Medium (should address soon): 4
- 🟢 Low (nice-to-have): 2

**Impact**:
- **Context Bloat Reduction**: 165+ files archived (230→79 docs)
- **Code Redundancy**: Dual codebase identified (greenfield vs brownfield)
- **Build Artifacts**: 3,112 unnecessary files (293 __pycache__, 2,819 .pyc)
- **Test Outputs**: 14MB untracked test outputs

---

## 🔴 Critical Issues

### 1. Test Outputs Not Gitignored

**Location**: `tests/outputs/`
**Size**: 14MB
**File Count**: 20+ JSON/markdown output files
**Problem**: Test execution outputs are tracked in git

**Files**:
```
tests/outputs/COBIT-2019-Design-Guide_res_eng_1218_json.json (1.9MB)
tests/outputs/COBIT-2019-Framework-Governance-and-Management-Objectives_res_eng_1118_json.json (4.7MB)
tests/outputs/COBIT-2019-Framework-Introduction-and-Methodology_res_eng_1118_json.json (425KB)
... (17 more files)
```

**Recommendation**:
```bash
# Add to .gitignore
echo "tests/outputs/" >> .gitignore

# Remove from git (keep local files)
git rm --cached -r tests/outputs/

# Commit
git add .gitignore
git commit -m "chore: gitignore test output files"
```

**Rationale**: Test outputs are ephemeral and should not be version controlled. They bloat repository size and create merge conflicts.

---

### 2. Dual Codebase Redundancy (Greenfield + Brownfield)

**Status**: Expected during migration (Story 1.2-1.4)
**Risk**: Maintenance burden, confusion, potential divergence

**Redundant Modules**:

| Functionality | Brownfield | Greenfield | File Count | Redundancy |
|---------------|------------|------------|------------|------------|
| PDF Extraction | `src/extractors/pdf_extractor.py` | `src/data_extract/extract/pdf.py` | 2 files | 100% overlap |
| DOCX Extraction | `src/extractors/docx_extractor.py` | `src/data_extract/extract/docx.py` | 2 files | 100% overlap |
| Excel Extraction | `src/extractors/excel_extractor.py` | `src/data_extract/extract/excel.py` | 2 files | 100% overlap |
| PPTX Extraction | `src/extractors/pptx_extractor.py` | `src/data_extract/extract/pptx.py` | 2 files | 100% overlap |
| CSV Extraction | `src/extractors/csv_extractor.py` | `src/data_extract/extract/csv.py` | 2 files | 100% overlap |
| TXT Extraction | `src/extractors/txt_extractor.py` | `src/data_extract/extract/txt.py` | 2 files | 100% overlap |
| **Total** | **6 extractors** | **6 extractors + adapter** | **13 files** | **~12,000 LOC** |

**Additional Overlaps**:
- `src/core/` (3 files) vs `src/data_extract/core/` (4 files)
- `src/processors/` (4 files) vs `src/data_extract/normalize/` (8 files)
- `src/formatters/` (4 files) vs `src/data_extract/output/` (1 file)

**Recommendation**:
1. **Document migration plan** - Which modules migrate when?
2. **Deprecation timeline** - When will brownfield be removed?
3. **Testing strategy** - Ensure parity before migration
4. **Clear ownership** - Which codebase is source of truth for each feature?

**Epic 1-2 Status**: Keep both codebases, document in architecture
**Epic 3+**: Begin brownfield deprecation

**Acceptance Criteria** (for migration completion):
- [ ] All brownfield tests pass on greenfield code
- [ ] Performance parity validated
- [ ] Brownfield code marked `@deprecated`
- [ ] Greenfield code is primary entry point
- [ ] Documentation updated

---

## 🟡 Medium Priority Issues

### 3. Documentation Redundancy (Cleaned Up! ✅)

**Action Taken**: Archived 165+ pre-BMAD files
**Before**: 230+ markdown files (verbose Claude Code reports)
**After**: 79 high-quality BMAD-aligned files
**Archive Location**: `TRASH/pre-bmad-docs/` + `docs/.archive/pre-bmad/`

**Remaining Structure**:
```
docs/
├── architecture/          (5 files - foundation, getting started, quick ref)
├── retrospectives/        (2 files - epic retros)
├── reviews/               (1 file - story reviews)
├── stories/               (20 files - epic/story specs)
├── test-plans/            (8 files)
├── uat/                   (5 files - test cases, results, reviews)
├── *.md                   (38 root files - BMM docs, guides, PRD, tech-specs)
```

**Status**: ✅ COMPLETE (Step 2)

---

### 4. Configuration File Proliferation

**Issue**: Multiple small YAML files for normalization config
**Location**: `config/normalize/`

**Files**:
```
config/normalize/cleaning_rules.yaml
config/normalize/entity_patterns.yaml
config/normalize/entity_dictionary.yaml
config/normalize/schema_templates.yaml
```

**Recommendation**:
**Option A** (Consolidate):
```yaml
# config/normalization.yaml
cleaning:
  rules: [...]
entities:
  patterns: [...]
  dictionary: [...]
schema:
  templates: [...]
```

**Option B** (Keep separate):
- Rationale: Each file serves distinct purpose, easier to maintain
- Better for large config sets
- **Recommended for now** (defer to Epic 5)

**Decision**: Keep as-is until Epic 5 (configuration cascade implementation)

---

### 5. Empty Directories After Cleanup

**Removed**: `docs/guides/`, `docs/infrastructure/` (empty after pre-BMAD cleanup)
**Status**: ✅ COMPLETE (Step 2)

**Remaining Empty**:
```bash
logs/  # Expected - log files are gitignored
```

**Recommendation**: Keep `logs/` directory with `.gitkeep` file for runtime log creation

---

### 6. Build Artifacts Present (But Gitignored)

**Artifacts Found**:
- 293 `__pycache__` directories
- 2,819 `.pyc`/`.pyo` compiled files
- 1 `*.egg-info` directory (`src/data_extraction_tool.egg-info/`)

**Status**: ✅ All gitignored properly
**Impact**: None on git, but clutters local filesystem

**Recommendation** (Optional Cleanup):
```bash
# Clean all Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete

# Or use git clean
git clean -fdX  # Remove all gitignored files
```

**Note**: Not urgent - these regenerate automatically. Clean before archiving/distributing.

---

## 🟢 Low Priority (Nice-to-Have)

### 7. Test Organization

**Current**:
```
tests/
├── fixtures/             (test data)
├── outputs/              (test execution outputs - should be temp)
├── performance/          (benchmarks)
├── unit/                 (unit tests)
├── integration/          (integration tests)
```

**Issue**: `tests/outputs/` mixes with test code

**Recommendation**:
```
tests/
├── fixtures/
├── performance/
├── unit/
├── integration/
└── .temp/                # Gitignored temp outputs
```

**Action**: Epic 5 - Test infrastructure refinement

---

### 8. Type Stubs Coverage

**Current**: Only `types-PyYAML` included
**Missing**: `types-python-docx`, `types-openpyxl`, `types-beautifulsoup4`

**Impact**: Low (libraries have inline types, mypy works fine)
**Benefit**: Better IDE autocomplete, more accurate mypy checks

**Recommendation**:
```toml
# pyproject.toml [project.optional-dependencies.dev]
"types-python-docx>=0.1.0",
"types-openpyxl>=3.0.0",
"types-beautifulsoup4>=4.12.0",
```

**Priority**: Low - defer to Epic 5

---

## Source Code Structure Summary

### Greenfield (Modern - 27 files)

**Location**: `src/data_extract/`
**Epic**: 1-2 (active development)
**Type Checking**: Strict mypy
**Coverage**: >80% target

```
src/data_extract/
├── __init__.py
├── cli.py                  # Entry point (Typer migration planned)
├── chunk/                  # Epic 3 - Semantic chunking
│   └── __init__.py         (1 file)
├── config/                 # Epic 5 - Config cascade
│   └── __init__.py         (1 file)
├── core/                   # Foundation
│   ├── __init__.py
│   ├── exceptions.py       # Custom exceptions
│   ├── models.py           # Pydantic models (ExtractionResult, ProcessingResult)
│   └── pipeline.py         # Pipeline orchestration (4 files)
├── extract/                # Extractors (Epic 2 complete)
│   ├── __init__.py
│   ├── adapter.py          # Extractor adapter pattern
│   ├── csv.py
│   ├── docx.py
│   ├── excel.py
│   ├── pdf.py
│   ├── pptx.py
│   └── txt.py              (8 files)
├── normalize/              # Normalization (Epic 2 complete)
│   ├── __init__.py
│   ├── cleaning.py         # Text cleaning
│   ├── config.py           # Normalization config
│   ├── entities.py         # Entity extraction
│   ├── metadata.py         # Metadata enrichment
│   ├── normalizer.py       # Main normalizer
│   ├── schema.py           # Schema standardization
│   └── validation.py       # Validation rules (8 files)
├── output/                 # Epic 3 - Output formatters
│   └── __init__.py         (1 file - planned expansion)
├── semantic/               # Epic 4 - Semantic analysis
│   └── __init__.py         (1 file - placeholder)
└── utils/                  # Utilities
    ├── __init__.py
    └── nlp.py              # NLP helpers (spaCy integration) (2 files)
```

**Total**: 27 files, ~8,000 LOC (estimated)

---

### Brownfield (Legacy - 31 files)

**Location**: `src/{cli,core,extractors,formatters,infrastructure,pipeline,processors}/`
**Status**: Maintenance mode (Stories 1.2-1.4)
**Type Checking**: Excluded during migration
**Coverage**: >60% baseline (1,000+ tests)

```
src/
├── cli/                    # CLI commands (Click-based)
│   └── (5 files)
├── core/                   # Core models/interfaces
│   └── (3 files)
├── extractors/             # Document extractors
│   ├── __init__.py
│   ├── csv_extractor.py    # 🔄 Duplicates data_extract/extract/csv.py
│   ├── docx_extractor.py   # 🔄 Duplicates data_extract/extract/docx.py
│   ├── excel_extractor.py  # 🔄 Duplicates data_extract/extract/excel.py
│   ├── pdf_extractor.py    # 🔄 Duplicates data_extract/extract/pdf.py
│   ├── pptx_extractor.py   # 🔄 Duplicates data_extract/extract/pptx.py
│   └── txt_extractor.py    # 🔄 Duplicates data_extract/extract/txt.py (7 files)
├── formatters/             # Output formatters
│   ├── __init__.py
│   ├── chunked_text_formatter.py
│   ├── json_formatter.py
│   └── markdown_formatter.py (4 files)
├── infrastructure/         # Config, logging, errors
│   └── (5 files + 3 YAML configs)
├── pipeline/               # Pipeline orchestration
│   └── (3 files)
└── processors/             # Processing stages
    ├── __init__.py
    ├── context_linker.py   # Builds document hierarchy
    ├── metadata_aggregator.py  # Computes statistics
    └── quality_validator.py    # Quality scoring (4 files)
```

**Total**: 31 files, ~10,000 LOC (estimated)

**Migration Path** (from CLAUDE.md):
- Epic 1: Assess brownfield (Stories 1.2-1.4) ✅
- Epic 2: Build greenfield extract + normalize ✅
- Epic 3: Build greenfield chunk + output 🔄
- Epic 4: Build greenfield semantic 📋
- Epic 5: Deprecate brownfield 📋

---

## Housekeeping Action Plan

### Immediate (Do Now)

1. **Add `tests/outputs/` to .gitignore** 🔴
   ```bash
   echo "tests/outputs/" >> .gitignore
   git rm --cached -r tests/outputs/
   git add .gitignore
   git commit -m "chore: gitignore test output files"
   ```

2. **Commit documentation cleanup** 🔴
   ```bash
   git add .
   git commit -m "docs: archive 165+ pre-BMAD files, housekeeping cleanup"
   ```

3. **Add `.gitkeep` to logs directory** 🟡
   ```bash
   touch logs/.gitkeep
   git add logs/.gitkeep
   git commit -m "chore: preserve logs directory with .gitkeep"
   ```

### Short-Term (This Sprint)

4. **Document dual codebase migration plan** 🟡
   - Create `docs/migration-strategy.md`
   - Define brownfield deprecation timeline
   - Establish testing parity requirements

5. **Review and update .gitignore** 🟡
   - Audit all gitignored paths
   - Add comments explaining each section
   - Verify no important files excluded

### Medium-Term (Epic 3-5)

6. **Consolidate test outputs** 🟢
   - Move `tests/outputs/` → `tests/.temp/`
   - Update test fixtures to use `.temp/`
   - Gitignore `.temp/` directory

7. **Consider config consolidation** 🟢
   - Evaluate `config/normalize/*.yaml` consolidation
   - Defer to Epic 5 (configuration cascade)

8. **Add type stubs for better IDE experience** 🟢
   - `types-python-docx`, `types-openpyxl`, `types-beautifulsoup4`
   - Low priority, nice-to-have

### Long-Term (Post-Epic 5)

9. **Complete brownfield deprecation**
   - Mark brownfield code `@deprecated`
   - Remove brownfield modules
   - Update all imports to greenfield

10. **Final cleanup**
    - Run `git clean -fdX` to remove all build artifacts
    - Archive old documentation
    - Update all documentation links

---

## Metrics

### Before Housekeeping
- **Documentation**: 230+ markdown files (verbose, low-quality)
- **Context Bloat**: High (100+ session reports)
- **Redundancy**: Dual codebase (expected)
- **Untracked Outputs**: 14MB test files
- **Build Artifacts**: 3,112 cached files

### After Housekeeping (Current)
- **Documentation**: 79 high-quality BMAD-aligned files (-65% reduction)
- **Context Bloat**: Minimal (only current work)
- **Redundancy**: Documented and tracked
- **Untracked Outputs**: Identified (fix pending)
- **Build Artifacts**: Gitignored (cleanup optional)

### Target (Post-Actions)
- **Documentation**: 79 files + migration strategy
- **Context Bloat**: Zero (all archived)
- **Redundancy**: Planned migration path
- **Untracked Outputs**: Zero (gitignored)
- **Build Artifacts**: Cleaned (pre-distribution)

---

## Conclusion

**Overall Health**: 🟢 Good (with actionable improvements)

**Strengths**:
- ✅ Clean documentation structure (post-cleanup)
- ✅ Well-configured .gitignore (minor gap)
- ✅ Proper dual codebase strategy (Epic-based migration)
- ✅ Modern tooling (Black, Ruff, mypy, pre-commit)
- ✅ Comprehensive testing infrastructure

**Improvements**:
- 🔴 Gitignore `tests/outputs/` (critical)
- 🟡 Document migration strategy
- 🟢 Optional cleanups (defer to Epic 5)

**Risk Assessment**:
- **Low**: All critical issues have clear fixes
- **Dual codebase risk**: Mitigated by Epic-based migration plan
- **Documentation bloat**: ✅ Resolved

---

**Next Steps**:
1. Fix `.gitignore` for `tests/outputs/`
2. Commit housekeeping changes
3. Continue exhaustive scan (Steps 5-12)
4. Generate comprehensive master index

**Scan Status**: Step 4 Complete
**Next**: Step 5 - Source Tree Analysis with Housekeeping Notes
