# Project Maintenance Report - Data Extraction Tool

**Generated:** 2025-11-14
**Project:** Data Extraction Tool v0.1.0
**Analyst:** Claude Code (Project Analyst)
**Scope:** Comprehensive maintenance analysis covering documentation, file organization, and technical debt

---

## Executive Summary

### Current State

**Project Status:**
- **Epic Progress:** Epic 3 in progress (Stories 3.1-3.2 complete, 25% done)
- **Codebase:** Dual structure (greenfield modernization + brownfield legacy)
- **Documentation:** 280 markdown files (93 active + 187 archived/trashed)
- **Recent Activity:** 257 docs modified in last 7 days (active development)

**Key Metrics:**
- **CLAUDE.md:** 564 lines (comprehensive but needs Epic 3 status updates)
- **Master Index:** docs/index.md (425 lines, current as of 2025-11-13)
- **Archive:** 183 files in docs/.archive/pre-bmad/ (2.9 MB)
- **TRASH:** 186 files (2.9 MB, including pre-BMAD cleanup)
- **Test Files:** 81/81 tests passing in Epic 3

### Critical Findings

**Strengths:**
1. Well-organized documentation structure (stories, reviews, retrospectives, uat)
2. Recent housekeeping effort (165+ files archived on 2025-11-13)
3. Comprehensive master index (docs/index.md) with role-based navigation
4. Strong UAT framework integration (11 UAT docs, 22 XML context files)

**Issues Identified:**
1. **Critical:** CLAUDE.md references Epic 1/2 context but project is in Epic 3 (staleness)
2. **Critical:** Validation reports misplaced in docs/stories/ instead of docs/reviews/
3. **High:** Duplicate documentation index files (index.md vs DOCUMENTATION-INDEX-2025-11-13.md)
4. **High:** Review artifacts scattered across multiple directories
5. **Medium:** Performance baselines split (epic-3 vs story-2.5.1)
6. **Medium:** TRASH directory contains critical reference material, not just disposables

---

## File Organization Analysis

### What's Working Well

**1. Clear Directory Structure**
```
docs/
├── stories/           # 22 story files (well-organized by epic)
├── reviews/           # 14 review documents (consolidated Nov 13)
├── retrospectives/    # 3 epic retrospectives (complete)
├── uat/               # 11 UAT framework files
│   ├── test-cases/    # 5 test case specifications
│   ├── test-results/  # 5 execution results
│   ├── reviews/       # 5 QA approval reports
│   └── test-context/  # 3 XML context files (+ 19 .context.xml in stories/)
├── test-plans/        # 9 TDD test plans
└── architecture/      # 5 architectural deep-dives
```

**2. Comprehensive Master Index**
- docs/index.md (425 lines, generated 2025-11-13)
- Role-based navigation (Developer, QA, PM, DevOps, End User)
- Task-based quick reference ("I want to...")
- 93 active files documented with clear categories

**3. Strong Archive Strategy**
- docs/.archive/pre-bmad/ contains 183 historical files
- TRASH-FILES.md documents rationale for archived content
- Clear separation of BMAD-aligned vs pre-BMAD documentation

### What Needs Improvement

**1. Misplaced Validation Reports (HIGH PRIORITY)**

**Problem:** Story validation reports are stored in docs/stories/ instead of docs/reviews/

**Files Affected:**
```
docs/stories/validation-report-2.5-3.1-uat-workflow-framework-2025-11-13.md
docs/stories/validation-report-2.5-3.1-REVALIDATION-2025-11-13.md
```

**Impact:**
- Breaks organizational convention (reviews belong in docs/reviews/)
- Makes it harder to find all review artifacts
- Validation reports are NOT story content, they are quality checkpoints

**Recommendation:**
```bash
# Move validation reports to proper location
mv "docs/stories/validation-report-2.5-3.1-uat-workflow-framework-2025-11-13.md" \
   "docs/reviews/validation-report-2.5-3.1-uat-workflow-framework-2025-11-13.md"
mv "docs/stories/validation-report-2.5-3.1-REVALIDATION-2025-11-13.md" \
   "docs/reviews/validation-report-2.5-3.1-REVALIDATION-2025-11-13.md"

# Update any references in index.md or other docs
```

**2. Review Artifacts Scattered (MEDIUM PRIORITY)**

**Problem:** Story 3.2 review artifacts are in docs/reviews/ but could be better organized:

```
docs/reviews/REVIEW-STORY-3.2-BUCKET-B.md
docs/reviews/STORY-3.2-BUCKET-C-REMEDIATION-REPORT.md
docs/reviews/STORY-3.2-FINAL-CODE-REVIEW.md
docs/reviews/STORY-3.2-FINAL-VALIDATION-REPORT.md
```

**Recommendation:**
Consider creating story-specific review subdirectories for complex stories with multiple review rounds:
```
docs/reviews/3.2-entity-aware-chunking/
├── bucket-b-review.md
├── bucket-c-remediation.md
├── final-code-review.md
└── final-validation.md
```

This would improve discoverability and reduce root-level clutter in docs/reviews/.

**3. Duplicate Documentation Index (MEDIUM PRIORITY)**

**Files:**
- docs/index.md (425 lines, 2025-11-13)
- docs/DOCUMENTATION-INDEX-2025-11-13.md (533 lines, 2025-11-13)

**Problem:**
- Two competing master indexes created on the same day
- DOCUMENTATION-INDEX-2025-11-13.md appears to be a housekeeping report, not a master index
- Potential confusion about which is canonical

**Recommendation:**
1. Keep docs/index.md as the canonical master index
2. Rename DOCUMENTATION-INDEX-2025-11-13.md to reflect its true purpose:
   ```bash
   mv "docs/DOCUMENTATION-INDEX-2025-11-13.md" \
      "docs/reviews/housekeeping-documentation-index-2025-11-13.md"
   ```
3. Update references if needed

**4. Audit Reports Location Inconsistency (LOW PRIORITY)**

**Current Location:** docs/reviews/audit-report-*.md (4 files)

**Files:**
```
audit-report-create-test-cases-2025-11-13.md
audit-report-build-test-context-2025-11-13.md
audit-report-execute-tests-2025-11-13.md
audit-report-review-uat-results-2025-11-13.md
```

**Observation:**
- These are workflow audit reports (BMAD workflow quality audits)
- Currently in docs/reviews/ (makes sense)
- docs/index.md line 160 references these in root docs/ (incorrect path)

**Recommendation:**
- Keep in docs/reviews/ (current location is correct)
- Update docs/index.md references to use correct path: `docs/reviews/audit-report-*.md`

**5. Performance Baselines Split (MEDIUM PRIORITY)**

**Files:**
- docs/performance-baselines-epic-3.md (Epic 3 consolidated)
- docs/performance-baselines-story-2.5.1.md (Story 2.5.1 specific)
- docs/performance-bottlenecks-story-2.5.1.md (Story 2.5.1 analysis)

**Issue:**
- Not actually a problem, but could benefit from consolidation strategy
- Epic 3 baselines should reference/supersede Story 2.5.1 baselines

**Recommendation:**
Add cross-references:
```markdown
# In performance-baselines-epic-3.md
## Previous Baselines
See [Story 2.5.1 Baselines](./performance-baselines-story-2.5.1.md) for Epic 2 extraction/normalization performance targets.

# In performance-baselines-story-2.5.1.md
## Note
This baseline is for Epic 2 (Extract/Normalize). For Epic 3 chunking baselines, see [Epic 3 Baselines](./performance-baselines-epic-3.md).
```

---

## Documentation Debt Assessment

### Outdated Documentation

**1. CLAUDE.md Epic Status References (CRITICAL)**

**Location:** C:\Users\Andrew\projects\data-extraction-tool-1\CLAUDE.md (564 lines)

**Issues:**
- Line 9: "Status: Brownfield modernization (Epic 1 - Foundation in progress)" - OUTDATED
  - **Reality:** Epic 3 in progress (Stories 3.1-3.2 complete)
- Line 118: "### Current: Epic 1 - Foundation" section lists Epic 1 as current
  - **Reality:** Epic 1, 2, 2.5 complete; Epic 3 25% done

**Impact:**
- Misleads new developers about project status
- AI assistants using CLAUDE.md will have incorrect context
- Undermines trust in documentation accuracy

**Recommended Updates:**

```markdown
# Line 9 - Update status
**Status**: Epic 3 - Chunk & Output (in progress, Stories 3.1-3.2 complete)

# Line 118-123 - Replace Epic 1 section with current epic
### Current: Epic 3 - Chunk & Output
- ✅ Story 3.1: Semantic boundary-aware chunking engine (complete)
- ✅ Story 3.2: Entity-aware chunking (complete)
- 📋 Stories 3.3-3.7: Metadata, output formats, configuration (backlog)

### Completed
- **Epic 1 - Foundation** (4 stories complete)
- **Epic 2 - Extract & Normalize** (6 stories complete)
- **Epic 2.5 - Refinement & Quality** (8 stories complete)
```

**2. Missing Epic 3 Context in CLAUDE.md (HIGH)**

**Issue:**
- CLAUDE.md has extensive Epic 2 "Lessons Learned" section (lines 180-241)
- No equivalent "Epic 3: Chunking Engine" section with:
  - ChunkingEngine usage patterns
  - Entity-aware chunking integration
  - Performance baselines reference
  - UAT workflow guidance

**Current Epic 3 Content:**
- Line 239-330: "Epic 3: Chunking Engine" section EXISTS
- Includes EntityPreserver integration, usage patterns, configuration reference
- **Status:** Actually well-documented, no action needed

**Correction:** Upon re-review, Epic 3 documentation in CLAUDE.md is comprehensive. No action required.

### Duplicate Documentation

**1. Source Tree Analysis Variants**

**Files:**
- docs/reviews/source-tree-analysis-2025-11-13.md
- docs/reviews/source-tree-analysis-annotated-2025-11-13.md

**Assessment:**
- Both generated same day (2025-11-13)
- "annotated" version is likely enhanced version
- Not necessarily duplicates if annotated adds value

**Recommendation:**
- Keep annotated version as primary
- Add note to non-annotated version: "See annotated version for enhanced context"

**2. Test Context XML Files (INFORMATIONAL)**

**Count:** 22 XML files total
- 19 .context.xml files in docs/stories/ (story-specific context)
- 3 in docs/uat/test-context/ (UAT-specific context)

**Assessment:**
- This is expected/appropriate separation
- Story context used for development
- UAT context used for acceptance testing
- Not duplication, just different purposes

### Missing Documentation

**1. Epic 3 Retrospective (EXPECTED)**

**Status:** Not yet due
- Epic 3 is 25% complete (2/8 stories done)
- Retrospectives typically done after epic completion
- docs/retrospectives/epic-3-retro-{date}.md will be created later

**2. Brownfield Migration Plan (MEDIUM PRIORITY)**

**Identified in:** docs/reviews/housekeeping-findings-2025-11-13.md

**Issue:**
- Dual codebase exists (greenfield + brownfield)
- ~13 files with 100% functional overlap
- No documented migration timeline

**Recommendation:**
Create docs/brownfield-migration-plan.md with:
- Which modules migrate in which epic
- Deprecation timeline
- Testing strategy for parity validation
- Ownership/source-of-truth designation

**3. Performance Optimization Roadmap (LOW PRIORITY)**

**Context:**
- NFR-P3 adjusted from 2.0s to 3.0s actual (Epic 3 chunking)
- NFR-P2 trade-off documented (4.15GB vs 2GB batch memory)
- performance-bottlenecks-story-2.5.1.md exists but Epic 3-specific optimization plan missing

**Recommendation:**
Add section to performance-baselines-epic-3.md:
```markdown
## Future Optimization Opportunities
1. Reduce chunking latency from 3.0s to <2.0s (original target)
   - Profile sentence segmentation overhead
   - Consider spaCy model optimization
2. Reduce batch memory from 4.15GB to <2GB
   - Investigate generator-based streaming
   - Evaluate memory pooling strategies
```

---

## Immediate Action Items

### Priority 1: Critical (Within 24 hours)

**1. Update CLAUDE.md Epic Status**
- **File:** CLAUDE.md line 9
- **Change:** "Epic 1 - Foundation in progress" → "Epic 3 - Chunk & Output (in progress, Stories 3.1-3.2 complete)"
- **Effort:** 5 minutes
- **Impact:** Prevents AI/developer confusion about project status

**2. Move Validation Reports to docs/reviews/**
- **Files:**
  - docs/stories/validation-report-2.5-3.1-uat-workflow-framework-2025-11-13.md
  - docs/stories/validation-report-2.5-3.1-REVALIDATION-2025-11-13.md
- **Target:** docs/reviews/
- **Effort:** 10 minutes
- **Impact:** Restores organizational consistency

### Priority 2: High (Within 1 week)

**3. Rename/Relocate DOCUMENTATION-INDEX-2025-11-13.md**
- **File:** docs/DOCUMENTATION-INDEX-2025-11-13.md
- **Target:** docs/reviews/housekeeping-documentation-index-2025-11-13.md
- **Rationale:** Eliminate confusion with canonical index.md
- **Effort:** 5 minutes

**4. Fix Audit Report References in docs/index.md**
- **File:** docs/index.md lines 158-162
- **Issue:** References audit reports in root docs/ but they're in docs/reviews/
- **Fix:** Update paths to docs/reviews/audit-report-*.md
- **Effort:** 5 minutes

**5. Update CLAUDE.md "Current Epic" Section**
- **File:** CLAUDE.md lines 118-123
- **Change:** Replace Epic 1 current status with Epic 3 current status
- **Move Epic 1-2.5 to "Completed" subsection**
- **Effort:** 15 minutes

### Priority 3: Medium (Within 2 weeks)

**6. Create Brownfield Migration Plan**
- **New File:** docs/brownfield-migration-plan.md
- **Content:** Timeline, testing strategy, deprecation plan
- **Reference:** docs/reviews/housekeeping-findings-2025-11-13.md (lines 60-97)
- **Effort:** 2-3 hours

**7. Add Cross-References to Performance Baselines**
- **Files:**
  - docs/performance-baselines-epic-3.md
  - docs/performance-baselines-story-2.5.1.md
- **Content:** Mutual cross-references explaining scope differences
- **Effort:** 15 minutes

**8. Consolidate Story 3.2 Review Artifacts**
- **Current:** 4 files in docs/reviews/ with BUCKET-B, BUCKET-C, FINAL prefixes
- **Target:** Optionally create docs/reviews/3.2-entity-aware-chunking/ subdirectory
- **Decision Required:** Check if pattern repeats for future complex stories
- **Effort:** 30 minutes

### Priority 4: Low (Within 1 month)

**9. Audit TRASH Directory Contents**
- **Location:** TRASH/ (186 files, 2.9 MB)
- **Action:** Review for accidentally trashed critical files
- **Current Files:**
  - 3-2-test-context-template.xml (template placeholder)
  - story-review-append.txt (temporary review file)
  - test_*.py files (5 Python test files - verify these should be deleted)
- **Effort:** 1 hour

**10. Add Source Tree Analysis Cross-Reference**
- **Files:**
  - docs/reviews/source-tree-analysis-2025-11-13.md
  - docs/reviews/source-tree-analysis-annotated-2025-11-13.md
- **Action:** Add note to non-annotated version pointing to annotated
- **Effort:** 5 minutes

---

## Long-term Recommendations

### 1. Documentation Maintenance Cadence

**Establish Regular Reviews:**
- **Epic Transition:** Update CLAUDE.md status when epic changes
- **Weekly:** Update sprint-status.yaml (currently happening)
- **Monthly:** Audit TRASH/ and docs/.archive/ for accidental inclusions
- **Per Story:** Run validation reports and move to docs/reviews/

**Proposed Workflow:**
```
Story Complete → Validation Report Generated → Move to docs/reviews/ → Update index.md
Epic Complete → Retrospective → Update CLAUDE.md → Archive old working docs
```

### 2. Documentation Organization Principles

**Enforce Separation of Concerns:**
1. **docs/stories/** - Story specifications ONLY (no validation reports)
2. **docs/reviews/** - All review artifacts (validations, code reviews, audits)
3. **docs/retrospectives/** - Epic retrospectives ONLY
4. **docs/uat/** - UAT framework artifacts ONLY (test cases, results, reviews)

**Benefits:**
- Predictable locations reduce search time
- Easier to onboard new team members
- Automated tooling can rely on consistent paths

### 3. Archive Strategy

**Current State:**
- docs/.archive/pre-bmad/ (183 files, well-organized)
- TRASH/ (186 files, mixed quality)

**Recommendation:**
1. **Archive Strategy:**
   - Keep docs/.archive/ for historical reference documentation
   - Use TRASH/ only for truly disposable files (temp outputs, experiments)
   - Review TRASH/ contents before deleting permanently

2. **TRASH Cleanup:**
   - Verify test_*.py files in TRASH/ are truly obsolete
   - Move any reference-quality files to docs/.archive/
   - Delete confirmed disposables

3. **Size Monitoring:**
   - Track archive growth (currently 2.9 MB each)
   - Consider compression if archive exceeds 10 MB
   - Document what's archived in TRASH-FILES.md (currently good)

### 4. Documentation Generation Automation

**Current Tools:**
- BMAD workflows (document-project, create-story, UAT workflows)
- Manual index.md updates

**Future Enhancements:**
1. **Auto-generate index.md** from directory scans + metadata
2. **Validate cross-references** (detect broken links)
3. **Enforce naming conventions** (validation-report-* in docs/reviews/)
4. **Track documentation staleness** (flag docs unchanged >30 days in active epic)

**Implementation Priority:** Low (current manual process works well)

### 5. Brownfield Transition Strategy

**Goal:** Safely deprecate brownfield code by Epic 5

**Phased Approach:**
1. **Epic 3 (current):** Both codebases coexist, greenfield preferred
2. **Epic 4:** Mark brownfield modules `@deprecated`, redirect to greenfield
3. **Epic 5:** Remove brownfield code, archive in docs/.archive/brownfield/

**Success Criteria:**
- All brownfield tests pass on greenfield implementations
- Performance parity validated (no regressions)
- Documentation updated to reflect single codebase
- Migration lessons captured in retrospective

### 6. Performance Baseline Consolidation

**Current State:**
- Story-specific baselines (2.5.1, 3.1, 3.2)
- Epic-level baselines (epic-3)

**Recommendation:**
Create master performance tracking:
```
docs/performance-tracking.md
├── Epic 1 Baselines (infrastructure)
├── Epic 2 Baselines (extraction/normalization)
├── Epic 2.5 Baselines (optimization)
├── Epic 3 Baselines (chunking) ← Link to existing epic-3.md
└── Trends & Regression Analysis
```

**Benefits:**
- Single source of truth for all performance targets
- Easier to track degradation across epics
- Supports NFR compliance validation

---

## Metrics & Health Indicators

### Documentation Coverage

| Category | File Count | Lines | Completeness |
|----------|-----------|-------|--------------|
| Stories | 22 | 25,000+ | ✅ Excellent (all active stories documented) |
| Reviews | 14 | 8,000+ | ✅ Good (some organization needed) |
| Retrospectives | 3 | 2,000+ | ✅ Complete (all completed epics) |
| UAT | 11 | 8,000+ | ✅ Excellent (comprehensive framework) |
| Architecture | 6 | 8,000+ | ✅ Excellent (detailed ADRs) |
| User Guides | 4 | 3,000+ | ✅ Good (end-user focused) |
| Test Plans | 9 | 4,000+ | ✅ Good (TDD-aligned) |
| **Total Active** | **93** | **70,000+** | ✅ Comprehensive |

### Documentation Staleness

| Epic | Last Update | Status | Staleness |
|------|-------------|--------|-----------|
| Epic 1 | 2025-11-10 | Complete | 🟢 Fresh |
| Epic 2 | 2025-01-11 | Complete | 🟢 Fresh |
| Epic 2.5 | 2025-11-13 | Complete | 🟢 Fresh |
| Epic 3 | 2025-11-14 | In Progress | 🟢 Current |
| CLAUDE.md | 2025-11-13? | Needs Update | 🟡 Stale (Epic 1/2 refs) |
| index.md | 2025-11-13 | Current | 🟢 Fresh |

### Archive Health

| Location | File Count | Size | Last Updated | Status |
|----------|-----------|------|--------------|--------|
| docs/.archive/pre-bmad/ | 183 | 2.9 MB | 2025-11-13 | ✅ Well-organized |
| TRASH/ | 186 | 2.9 MB | 2025-11-14 | ⚠️ Needs review |
| TRASH-FILES.md | - | - | 2025-11-13 | ✅ Up-to-date |

### File Organization Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Files in correct directory | 100% | ~95% | 🟡 Good (2 validation reports misplaced) |
| Broken references | 0 | 4 | 🟡 Low (audit report paths in index.md) |
| Duplicate indexes | 1 | 2 | 🟡 Low (DOCUMENTATION-INDEX-2025-11-13.md) |
| Orphaned files | 0 | 0 | ✅ Excellent |

### Repository Size Trends

| Component | Size | Trend | Health |
|-----------|------|-------|--------|
| Active docs/ | ~4-5 MB | Stable | ✅ Healthy |
| Archive | 2.9 MB | Growing | ✅ Expected |
| TRASH | 2.9 MB | Stable | ✅ Acceptable |
| Total Docs | ~10 MB | Controlled | ✅ Healthy |

**Note:** 280 total markdown files is appropriate for a project of this complexity. Archive strategy prevents bloat.

---

## Conclusion

### Overall Assessment: GOOD with Minor Issues

**Strengths:**
1. ✅ **Excellent organization** - Clear directory structure, role-based navigation
2. ✅ **Comprehensive coverage** - 93 active files, 70,000+ lines of quality documentation
3. ✅ **Recent housekeeping** - 165+ files archived Nov 13, reducing context bloat 65%
4. ✅ **Strong UAT framework** - 11 docs, well-integrated into workflow
5. ✅ **Consistent updates** - 257 docs modified in last 7 days (active development)

**Weaknesses:**
1. 🟡 **CLAUDE.md staleness** - References Epic 1/2 as current (should be Epic 3)
2. 🟡 **Misplaced validation reports** - 2 files in docs/stories/ instead of docs/reviews/
3. 🟡 **Duplicate indexes** - index.md vs DOCUMENTATION-INDEX-2025-11-13.md
4. 🟡 **Review artifact scatter** - Story 3.2 reviews could be better organized

### Risk Assessment

**Low Risk Areas:**
- Documentation completeness (93 files covering all active work)
- Archive strategy (well-documented, preserved in TRASH-FILES.md)
- UAT framework (operational, 11 docs)

**Medium Risk Areas:**
- CLAUDE.md staleness (AI assistants may use outdated context)
- File organization inconsistencies (minor impact on findability)
- TRASH directory contents (may contain accidentally trashed files)

**High Risk Areas:**
- None identified

### Recommended Focus

**Next 7 Days:**
1. ✅ Update CLAUDE.md epic status (5 min, critical)
2. ✅ Move validation reports to docs/reviews/ (10 min, critical)
3. ✅ Fix audit report paths in index.md (5 min, high)
4. ✅ Rename DOCUMENTATION-INDEX-2025-11-13.md (5 min, high)

**Total Effort:** ~25 minutes to resolve all critical/high priority issues

**Next 30 Days:**
1. Create brownfield migration plan (2-3 hours)
2. Add performance baseline cross-references (15 min)
3. Audit TRASH directory (1 hour)
4. Consider Story 3.2 review consolidation (30 min)

**Total Effort:** ~4-5 hours for all medium/low priority items

### Success Criteria

**Documentation Health:**
- ✅ All files in correct directories (validation reports moved)
- ✅ CLAUDE.md reflects current epic (Epic 3)
- ✅ Single canonical index (index.md)
- ✅ No broken references in master index
- ✅ TRASH directory audited for accidental inclusions

**Ongoing Maintenance:**
- Update CLAUDE.md at epic transitions
- Generate validation reports directly to docs/reviews/
- Monthly TRASH/ audits
- Quarterly archive size review

---

## Appendix: File Inventory

### Active Documentation (93 files)

**Root Documentation:**
- CLAUDE.md (564 lines) - Primary developer guide
- README.md - Project overview
- TRASH-FILES.md (74 lines) - Archive documentation

**docs/ Root (23 files):**
- index.md (425 lines) - Master documentation index
- DOCUMENTATION-INDEX-2025-11-13.md (533 lines) - Housekeeping report [RENAME PENDING]
- architecture.md (4,847 lines) - Complete technical architecture
- PRD.md (1,300 lines) - Product requirements
- epics.md (2,645 lines) - Epic breakdown
- brownfield-assessment.md (1,686 lines) - Legacy code analysis
- ci-cd-pipeline.md (4,000+ lines) - CI/CD documentation
- tech-spec-epic-1.md, tech-spec-epic-2.md, tech-spec-epic-2.5.md, tech-spec-epic-3.md
- traceability-*.md (4 files) - Requirements traceability
- performance-baselines-epic-3.md, performance-baselines-story-2.5.1.md
- performance-bottlenecks-story-2.5.1.md
- 7 analysis documents (config, test, CLI, shared-utilities, CI/CD, source-tree)
- 5 user guides (QUICKSTART, USER_GUIDE, CONFIG_GUIDE, LOGGING_GUIDE, ERROR_HANDLING_GUIDE)
- 4 integration guides

**docs/stories/ (22 files):**
- 18 story specifications (.md)
- 2 validation reports (.md) [MOVE TO docs/reviews/ PENDING]
- 1 completion summary (.md)
- 19 story context files (.context.xml)
- 1 testing standards file (.xml)

**docs/reviews/ (14 files):**
- 4 audit reports (UAT workflow audits)
- 4 Story 3.2 review artifacts
- 3 analysis documents (research, housekeeping, source-tree)
- 2 code reviews
- 1 shared utilities analysis

**docs/retrospectives/ (3 files):**
- epic-1-retro-20251110.md
- epic-2-retro-20250111.md
- epic-2.5-retro-2025-11-13.md

**docs/uat/ (11 files):**
- test-cases/ (5 files: 2.5-3.1, 3.1, 3.2)
- test-results/ (5 files: 2.5-3.1, 3.1, 3-2)
- reviews/ (5 files: 2.5-3.1, 3.1, 3.2)
- test-context/ (3 .xml files)
- 2 tmux-cli documentation files

**docs/test-plans/ (9 files):**
- PPTX_TEST_PLAN.md, EXCEL_EXTRACTOR_TEST_PLAN.md
- TDD_TEST_PLAN_CLI.md, TDD_TEST_PLAN_INTEGRATION.md, TDD_TEST_PLAN_DOCX_COVERAGE.md
- TEST_SKIP_POLICY.md, SKIP_CLEANUP_QUICK_REF.md
- atdd-checklist-3.1.md, atdd-checklist-3.2.md

**docs/architecture/ (5 files):**
- FOUNDATION.md, GETTING_STARTED.md, QUICK_REFERENCE.md
- INFRASTRUCTURE_NEEDS.md, TESTING_INFRASTRUCTURE.md

### Archived Documentation (183 files)

**docs/.archive/pre-bmad/**
- assessment/ - ADR assessment reports
- deployment/ - v1.0.4 deployment validation
- planning/ - v1.0.6 planning documents
- reports/ - 105+ Claude Code session reports
- wave-handoffs/ - Legacy wave handoff documents
- Root files: backlog.md, test-triage reports, epic-2-transition-brief.md

### TRASH Directory (186 files)

**TRASH/pre-bmad-docs/**
- Same structure as docs/.archive/pre-bmad/
- Additional files: brownfield-test-failures-tracking.md, CLI test triage, P0 fixes

**TRASH/ root:**
- 3-2-test-context-template.xml (template placeholder)
- story-review-append.txt (temporary review content)
- test_*.py (5 Python test files - VERIFY BEFORE DELETION)

---

**Report End**

**Next Actions:** See "Immediate Action Items" section for prioritized task list.
**Questions:** Contact project analyst or review docs/index.md for additional context.
