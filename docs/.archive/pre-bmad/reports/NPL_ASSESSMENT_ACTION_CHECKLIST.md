# NPL Infrastructure Assessment - Action Checklist
**Immediate Implementation Guide**

**Date**: 2025-11-05
**Project**: data-extractor-tool
**Estimated Total Time**: 6-61 hours (depending on strategy)

---

## Phase 0: Strategic Decision (15 minutes)

**Choose your path**:

- [ ] **Option A: Maintain & Enhance** (61 hours)
  - Full NPL@1.0 compliance
  - Operational context loading
  - State persistence
  - **Best for**: Long-term NPL strategic adoption

- [ ] **Option B: Simplify & Consolidate** (8 hours)
  - Keep operational core (14 files, 180KB)
  - Archive non-functional components
  - Document manual workflows
  - **Best for**: Immediate practical value

- [ ] **Option C: Replace with Lightweight** (12 hours)
  - Remove .npl/ infrastructure
  - Create simple slash commands
  - No complex orchestration
  - **Best for**: Pragmatic efficiency

**Decision**: _________________ (Write your choice)

---

## Phase 1: Critical Fixes (Required for ALL options)

**Total Time**: 6.25 hours

### Task 1.1: Document Manual Loading Process (2 hours)

**File**: `.npl/README.md`

**Action**: Add section after line 270 ("Integration with Existing Docs"):

```markdown
---

## Manual Loading Guide

**IMPORTANT**: The `npl-load` command-line tool is not yet implemented. Use manual loading:

### Quick Start Context (Layer 1) - ~3,200 tokens
1. Read `PROJECT_STATE.md` for current status (800 tokens)
2. Read `.npl/components/development-quick.md` (2,400 tokens)
3. Optionally activate persona: Read `.npl/meta/personas/feature-developer.md`

### Standard Context (Layer 2) - ~8,000 tokens
1. Read `PROJECT_STATE.md`
2. Read `.npl/components/development-standard.md`
3. Read relevant workflow chain from `.npl/chains/`

### Full Context (Layer 3) - ~15,000 tokens
1. Read `PROJECT_STATE.md`
2. Read `.npl/components/development-full.md`
3. Read all architecture docs referenced

**Context Tracking**: Track manually which files you've read. No automatic --skip mechanism exists yet.
```

- [ ] Section added to README.md
- [ ] Examples updated to show Read tool usage
- [ ] Misleading command examples marked as "Planned Feature"

### Task 1.2: Create Missing State Files (15 minutes)

**File 1**: `.npl/.last_version.txt`

```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"

# Create state file
grep "^**Status**:" PROJECT_STATE.md | head -1 | awk '{print $2}' > .npl/.last_version.txt

# Verify
cat .npl/.last_version.txt
# Should output: v1.0.5
```

- [ ] File created
- [ ] Contains current version
- [ ] Check-staleness.sh can read it

**File 2**: `.npl/state/` directory (for future state tracking)

```bash
mkdir -p .npl/state
echo "{}" > .npl/state/.gitkeep
```

- [ ] Directory created
- [ ] Ready for state persistence implementation

### Task 1.3: Add NPL@1.0 Agent Declarations (4 hours)

**Files to Update** (20 files):

#### Components (7 files)
- [ ] `.npl/components/development-minimal.md`
- [ ] `.npl/components/development-quick.md`
- [ ] `.npl/components/development-standard.md`
- [ ] `.npl/components/development-full.md`
- [ ] `.npl/components/testing-quick.md`
- [ ] `.npl/components/deployment-check.md`
- [ ] `.npl/components/README.md`

**Pattern**:
```markdown
⌜component:development-quick|context-loader|NPL@1.0⌝
# Development Context: Quick Start

[existing content]

⌞component:development-quick⌟
```

#### Chains (5 files)
- [ ] `.npl/chains/feature-development.md`
- [ ] `.npl/chains/bug-fixing.md`
- [ ] `.npl/chains/testing.md`
- [ ] `.npl/chains/refactoring.md`
- [ ] `.npl/chains/deployment.md`

**Pattern**:
```markdown
⌜chain:feature-development|workflow|NPL@1.0⌝
# Feature Development Chain

[existing content]

⌞chain:feature-development⌟
```

#### Indexes (3 files)
- [ ] `.npl/indexes/quick-reference.md`
- [ ] `.npl/indexes/token-optimization-guide.md`
- [ ] `.npl/indexes/context-layers.yaml` (add YAML comment header)

**Pattern for Markdown**:
```markdown
⌜index:quick-reference|reference|NPL@1.0⌝
# NPL Infrastructure Quick Reference

[existing content]

⌞index:quick-reference⌟
```

**Pattern for YAML** (add at top):
```yaml
# ⌜index:context-layers|configuration|NPL@1.0⌝
# Context Layers for Data Extractor Tool NPL Infrastructure
# [rest of YAML]
```

#### Documentation (5 files)
- [ ] `.npl/README.md`
- [ ] `.npl/INFRASTRUCTURE_DELIVERY.md`
- [ ] `.npl/MAINTENANCE_STRATEGY.md`
- [ ] `.npl/LIVING_REPOSITORY_SUMMARY.md`
- [ ] `.npl/REFRESH_LOG.md`

**Pattern**:
```markdown
⌜doc:readme|guide|NPL@1.0⌝
# NPL Infrastructure - Data Extractor Tool

[existing content]

⌞doc:readme⌟
```

**Validation** (after all updates):
```bash
# Count declarations
grep -r "⌜" .npl/ --include="*.md" | wc -l
# Should be ~32 (up from 12)

# Verify matching closing tags
grep -r "⌞" .npl/ --include="*.md" | wc -l
# Should match opening tags
```

- [ ] All files updated
- [ ] Declaration count verified
- [ ] Closing tags match

---

## Phase 2: Strategy-Specific Actions

### IF OPTION A: Maintain & Enhance (55 hours)

Continue to Phase 2A below.

### IF OPTION B: Simplify & Consolidate (2 hours)

**Task 2B.1**: Archive Non-Operational Components (1 hour)

```bash
cd .npl
mkdir -p archive/2025-11-05

# Archive low-value files
mv INFRASTRUCTURE_DELIVERY.md archive/2025-11-05/
mv LIVING_REPOSITORY_SUMMARY.md archive/2025-11-05/
mv QUICK_START.md archive/2025-11-05/
mv USAGE_GUIDE.md archive/2025-11-05/
mv EXECUTIVE_SUMMARY.md archive/2025-11-05/
mv IMPLEMENTATION_ROADMAP.md archive/2025-11-05/

# Archive non-functional components
mv components/README.md archive/2025-11-05/components-README.md

# Archive chains (no execution mechanism)
mv chains/ archive/2025-11-05/chains/

# Archive templates (empty)
rm -rf templates/
```

- [ ] Files archived
- [ ] Core 14 files remain
- [ ] README updated with archive note

**Task 2B.2**: Update README (1 hour)

Add archive notice:
```markdown
## 2025-11-05 Infrastructure Simplification

Non-operational components archived to `archive/2025-11-05/`:
- INFRASTRUCTURE_DELIVERY.md (104KB) - Overlapped README
- LIVING_REPOSITORY_SUMMARY.md - Overlapped MAINTENANCE_STRATEGY
- Components/Chains - No execution mechanism yet
- Templates - Empty directory

**Rationale**: Focus on operational core (hooks, personas, indexes). Archived components can be restored if/when operational infrastructure is implemented.
```

- [ ] Archive note added
- [ ] File size reduced: 498KB → ~180KB

**DONE - Option B Complete**

### IF OPTION C: Replace with Lightweight (12 hours)

**Task 2C.1**: Create Lightweight Slash Commands (8 hours)

See implementation guide in full assessment document, Section 7.1.

**Task 2C.2**: Archive .npl/ Directory (1 hour)

```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"
mv .npl .npl-archive-2025-11-05
```

- [ ] .npl/ archived
- [ ] New lightweight system in .claude/components/
- [ ] Slash commands operational

**DONE - Option C Complete**

---

## Phase 2A: Maintain & Enhance Implementation (55 hours)

**Only if Option A chosen**

### Task 2A.1: Create Operational Slash Command Loaders (6 hours)

**File**: `.claude/commands/load-quick.md`

```markdown
# Load Quick Development Context
**Purpose**: Load Layer 1 context for 80% of development tasks

## Context Components
This command loads the following files:

1. PROJECT_STATE.md - Current status and metrics
2. .npl/components/development-quick.md - Architecture fundamentals
3. docs/architecture/FOUNDATION.md (excerpt) - Core concepts

## Token Budget
Estimated: ~3,200 tokens

## Instructions for Claude
Please read the following files in order:
1. Read PROJECT_STATE.md
2. Read .npl/components/development-quick.md

This provides sufficient context for:
- Feature implementation
- Bug fixes
- Code reviews
- Test development

For more complex work, use /load-standard instead.
```

**Repeat for**:
- [ ] `/load-quick` (Layer 1)
- [ ] `/load-standard` (Layer 2)
- [ ] `/load-full` (Layer 3)
- [ ] `/load-testing` (Test-specific)
- [ ] `/load-deployment` (Deployment-specific)
- [ ] `/load-persona qa-engineer` (with persona activation)

**Validation**:
```bash
# In Claude Code
/load-quick
# Should output context loading instructions
```

- [ ] All slash commands created
- [ ] Tested in Claude Code
- [ ] Token estimates updated

### Task 2A.2: Add Attention Markers (6 hours)

**Target Files**:

**File 1**: `.npl/components/development-quick.md` (lines 64-75)

**Before**:
```markdown
### Immutability Principles**:
```python
# ✓ CORRECT: Create new block with modifications
new_block = ContentBlock(...)
```

**After**:
```markdown
⌜🔒 CRITICAL PATTERN ⌟
### 🎯 Immutability Principles

**REQUIREMENT**: All data models are frozen dataclasses. You MUST create new instances, never modify existing.

```python
# ✓ CORRECT: Create new block with modifications
new_block = ContentBlock(
    block_id=old.block_id,
    metadata={**old.metadata, "new": "value"}
)

# ✗ WRONG: Mutate frozen dataclass
old.metadata["new"] = "value"  # FrozenInstanceError!
```
⌞🔒⌟
```

- [ ] `development-quick.md` enhanced
- [ ] `development-standard.md` enhanced
- [ ] `development-full.md` enhanced

**File 2**: `.npl/meta/personas/qa-engineer.md` (add npl-cot block)

After line 47, add:
```markdown
### 🎯 Test Design Thinking Process

<npl-cot>
When designing tests, I follow this reasoning chain:

1. **Identify Requirements**
   - What behavior needs verification?
   - What are the success criteria?

2. **Enumerate Scenarios**
   - Happy path (expected input/output)
   - Edge cases (boundaries, empty, null)
   - Error cases (invalid input, exceptions)
   - Integration points (dependencies)

3. **Design Test Structure**
   - Arrange: Set up test data and environment
   - Act: Execute the behavior
   - Assert: Verify expected outcomes
   - Cleanup: Restore state

4. **Validate Coverage**
   - All code paths exercised?
   - All error handlers tested?
   - Performance characteristics verified?
</npl-cot>
```

- [ ] All personas enhanced with thinking patterns

### Task 2A.3: Consolidate Documentation (3 hours)

**Action 1**: Merge INFRASTRUCTURE_DELIVERY.md → README.md

1. Identify unique sections in INFRASTRUCTURE_DELIVERY.md not in README
2. Append to README under new section: "## Complete Specification"
3. Delete INFRASTRUCTURE_DELIVERY.md
4. Update references

- [ ] Unique content identified
- [ ] Merged to README
- [ ] Original file deleted
- [ ] References updated

**Action 2**: Merge LIVING_REPOSITORY_SUMMARY.md → MAINTENANCE_STRATEGY.md

1. Extract unique insights
2. Merge into MAINTENANCE_STRATEGY under "## Summary"
3. Delete LIVING_REPOSITORY_SUMMARY.md

- [ ] Content merged
- [ ] Original deleted

**Action 3**: Reduce token-optimization-guide.md

1. Extract key points (top 20%)
2. Create 2-page summary
3. Archive full version
4. Replace with summary

- [ ] Summary created (4-5KB)
- [ ] Original archived

**Validation**:
```bash
du -sh .npl/
# Should be ~350KB (down from 498KB)
```

- [ ] 30% size reduction achieved

### Task 2A.4: Validate Token Counts (4 hours)

**Script**: `scripts/validate_npl_tokens.py`

```python
#!/usr/bin/env python3
import tiktoken
from pathlib import Path
import yaml

encoder = tiktoken.encoding_for_model("gpt-4")

def measure_tokens(file_path):
    content = file_path.read_text(encoding='utf-8')
    return len(encoder.encode(content))

def validate_component(component_path, claimed_tokens):
    actual = measure_tokens(component_path)
    diff = abs(actual - claimed_tokens)
    diff_pct = (diff / claimed_tokens * 100) if claimed_tokens > 0 else 0

    status = "✅" if diff_pct < 10 else "⚠️" if diff_pct < 20 else "❌"

    return {
        "file": component_path.name,
        "claimed": claimed_tokens,
        "actual": actual,
        "diff": diff,
        "diff_pct": f"{diff_pct:.1f}%",
        "status": status
    }

# Validate all components
components = [
    (".npl/components/development-minimal.md", 800),
    (".npl/components/development-quick.md", 3200),
    (".npl/components/development-standard.md", 8000),
    (".npl/components/development-full.md", 15000),
]

print("Token Count Validation Report")
print("=" * 60)
for path, claimed in components:
    result = validate_component(Path(path), claimed)
    print(f"{result['status']} {result['file']}: {result['actual']} tokens (claimed: {result['claimed']}, diff: {result['diff_pct']})")

# Update YAML files with actual counts
```

- [ ] Script created
- [ ] All components measured
- [ ] YAML files updated with actual counts
- [ ] Report generated

### Task 2A.5: Implement State Persistence (8 hours)

**File**: `.npl/state/session_state.json`

**Schema**:
```json
{
  "session_id": "uuid",
  "started_at": "2025-11-05T10:30:00Z",
  "loaded_components": [
    {
      "name": "development-quick",
      "path": ".npl/components/development-quick.md",
      "loaded_at": "2025-11-05T10:32:15Z",
      "tokens": 3247
    }
  ],
  "active_persona": {
    "name": "qa-engineer",
    "loaded_at": "2025-11-05T10:35:00Z"
  },
  "active_workflow": {
    "name": "feature-development",
    "current_phase": 2,
    "phases_completed": [1]
  },
  "total_tokens_loaded": 3247
}
```

**Implementation**: Create state management module in `.npl/hooks/state_manager.sh`

- [ ] State schema defined
- [ ] State read/write functions
- [ ] Integration with slash commands
- [ ] Tested

### Task 2A.6: Implement Workflow State Machine (12 hours)

**File**: `.npl/state/workflow_<name>.yaml`

**Implementation**: See full assessment Section 7.3

- [ ] Workflow states tracked
- [ ] Phase transitions managed
- [ ] Quality gates enforced
- [ ] Resume capability

### Task 2A.7: Build npl-load CLI Tool (16 hours)

**Only if high usage validates the investment**

**Implementation**: See full assessment Section 7.1

- [ ] CLI tool implemented
- [ ] Context loading operational
- [ ] --skip tracking works
- [ ] Relevance scoring integrated

**DONE - Option A Complete**

---

## Phase 3: Validation & Documentation

**Time**: 2 hours

### Task 3.1: Validate Implementation

**Checklist**:
- [ ] Critical issues fixed (P0)
- [ ] NPL@1.0 declarations present
- [ ] Token counts measured
- [ ] Documentation updated
- [ ] State files exist
- [ ] Hooks operational

**Test Cases**:
```bash
# Test 1: Hook runs successfully
bash .npl/hooks/check-staleness.sh
# Should output staleness status

# Test 2: State file exists
cat .npl/.last_version.txt
# Should output current version

# Test 3: NPL declarations present
grep -c "⌜" .npl/README.md
# Should be > 0

# Test 4: Slash commands work
# In Claude Code:
/load-quick
# Should load context
```

- [ ] All tests pass

### Task 3.2: Update Assessment Documents

**File**: `docs/reports/NPL_INFRASTRUCTURE_ASSESSMENT.md`

Add section at end:
```markdown
---

## Implementation Log

### 2025-11-XX: Phase 1 Complete
- ✅ Manual loading documented
- ✅ State files created
- ✅ NPL declarations added
- **Status**: P0 issues resolved

### 2025-11-XX: Phase 2 Complete
- ✅ [List completed tasks]
- **Status**: [Option A/B/C] implementation complete

**Measured Improvements**:
- Token savings: [actual percentage]
- Load time: [actual time]
- Developer satisfaction: [feedback]
```

- [ ] Implementation log added
- [ ] Metrics recorded

### Task 3.3: Document Lessons Learned

**File**: `.npl/LESSONS_LEARNED.md`

```markdown
# NPL Infrastructure Implementation - Lessons Learned

## What Went Well
- [List successes]

## What Could Improve
- [List challenges]

## Recommendations for Future NPL Projects
1. [Key lesson]
2. [Key lesson]
...

## Metrics Achieved
- Token reduction: X%
- Implementation time: Y hours
- Operational status: Z% functional
```

- [ ] Lessons documented
- [ ] Shared with team

---

## Success Criteria

Mark when achieved:

**Phase 1 (P0 - Critical)**:
- [ ] No broken command references in documentation
- [ ] State files exist and are maintained
- [ ] NPL@1.0 syntax compliance ≥90%

**Phase 2 (P1 - High Value)**:
- [ ] Context loading works (manual or automated)
- [ ] Token counts validated and accurate
- [ ] Documentation consolidated (≤350KB)

**Phase 3 (P2 - Optimization)**:
- [ ] State persistence operational
- [ ] Workflow tracking functional
- [ ] Measured token savings ≥30%

**Overall Success** (pick one):
- [ ] **Option A**: Fully functional NPL infrastructure, 30-40% token savings
- [ ] **Option B**: Lightweight operational core, 10-15% token savings
- [ ] **Option C**: Simple pragmatic system, 15-20% token savings

---

## Progress Tracking

**Phase 1 Progress**: _____ / 3 tasks complete
**Phase 2 Progress**: _____ / ___ tasks complete (varies by option)
**Phase 3 Progress**: _____ / 3 tasks complete

**Overall Progress**: _____ %

**Estimated Completion Date**: _____________

---

**Last Updated**: 2025-11-05
**Maintained By**: [Your name]
**Status**: Ready for implementation
