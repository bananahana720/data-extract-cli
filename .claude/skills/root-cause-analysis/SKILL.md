---
name: root-cause-analysis
description: Use when - (1) Debugging errors or bugs, (2) Fixing test failures, (3) Resolving system issues, (4) Investigating unexpected behavior, (5) Need to find and fix ALL instances of a problem. Systematic root cause analysis using 5 Whys methodology for debugging and fixing issues properly. Prevents symptom-fixing and ensures complete resolution.
---

# Root Cause Analysis Protocol

This skill enforces systematic root cause analysis to ensure issues are properly fixed at their source, not just masked at the symptom level.

## Core Principle

**NEVER fix symptoms without understanding root cause**

Before implementing ANY fix:
- Apply "5 Whys" methodology - trace to root cause
- Search entire codebase for similar patterns
- Fix ALL affected locations, not just discovery point
- Document: "Root cause: [X], affects: [Y], fixing: [Z]"

## The 5 Whys Workflow

### Step 1: Identify the Problem

Document the immediate symptom:
```bash
# Capture the exact error
echo "SYMPTOM: [exact error message or behavior]"

# Save full error context
<command-that-failed> 2>&1 | tee error_log.txt

# Document environment state
echo "Environment: $(date), $(pwd), $(git rev-parse HEAD)"
```

### Step 2: Apply 5 Whys

Trace back through causality:

```
Problem: Test test_user_auth failing
Why 1: Authentication token is None
Why 2: Token generation function returns None on error
Why 3: Database connection fails silently
Why 4: Connection pool exhausted
Why 5: Connection leak in user service - connections not closed

ROOT CAUSE: Missing connection.close() in finally blocks
```

### Step 3: Search for Pattern

Find ALL instances of the root cause:

```bash
# Use ripgrep for comprehensive search
rg -l "pattern-that-causes-issue" --type py

# Check for similar code structures
rg -A 3 -B 3 "similar-pattern" --type py

# Find all files with the problematic import/usage
rg "from module import problematic_function"

# Use AST grep for structural patterns (if available)
ast-grep --pattern '$FUNC($$$) { $$$ }' --lang python
```

### Step 4: Create Fix Inventory

List ALL locations needing fixes:

```python
# Document all affected files
affected_files = [
    "src/services/user_service.py:45-67",  # Missing finally block
    "src/services/auth_service.py:123-145", # Same pattern
    "src/utils/database.py:89-95",         # Connection not closed
    "tests/fixtures/db_fixtures.py:34-40"  # Test cleanup issue
]

print(f"Found {len(affected_files)} locations to fix")
for file in affected_files:
    print(f"  - {file}")
```

### Step 5: Implement Comprehensive Fix

Fix ALL instances, not just the triggering one:

```bash
# Fix each location systematically
for file in "${affected_files[@]}"; do
    echo "Fixing: $file"
    # Apply fix
    # Verify fix
    # Document change
done
```

### Step 6: Verify Complete Resolution

Ensure the problem is truly fixed:

```bash
# Run original failing test
pytest tests/test_user_auth.py -xvs

# Run all related tests
pytest tests/ -k "auth or user or connection" -xvs

# Check for regressions
pytest tests/ --lf  # Run last failed
pytest tests/  # Run all tests

# Verify no similar issues remain
rg "problematic-pattern" && echo "WARNING: Pattern still exists!"
```

## Common Anti-Patterns to Avoid

### ❌ Symptom Masking
```python
# BAD: Hiding the error
try:
    result = risky_operation()
except Exception:
    result = None  # Masks the real issue
```

### ❌ Local Fix Only
```python
# BAD: Fixing only where error appeared
# Fixed in user_service.py but same bug exists in auth_service.py
```

### ❌ Incomplete Analysis
```python
# BAD: Stopping at first "why"
# "Test fails because assertion wrong" - NO, go deeper!
```

## Root Cause Categories

### Category 1: Logic Errors
- Missing error handling
- Incorrect conditions
- Off-by-one errors
- Race conditions

### Category 2: Resource Management
- Memory leaks
- Connection leaks
- File handle leaks
- Deadlocks

### Category 3: Data Issues
- Type mismatches
- Encoding problems
- Null/undefined handling
- Boundary conditions

### Category 4: Integration Issues
- API contract violations
- Version incompatibilities
- Configuration mismatches
- Environment differences

## Documentation Template

Always document findings using this template:

```markdown
## Root Cause Analysis: [Issue Description]

### Symptom
[What was observed]

### 5 Whys Analysis
1. Why: [First cause]
2. Why: [Second cause]
3. Why: [Third cause]
4. Why: [Fourth cause]
5. Why: [Root cause]

### Root Cause
[Final root cause description]

### Affected Locations
- File1: Line X-Y - [Description]
- File2: Line X-Y - [Description]
- Total: N locations

### Fix Applied
[Description of systematic fix]

### Verification
- [ ] Original issue resolved
- [ ] All similar patterns fixed
- [ ] Tests passing
- [ ] No regressions
```

## Scripts

### Root Cause Finder
See [scripts/find_root_cause.py](scripts/find_root_cause.py) for automated pattern detection

### Fix Validator
See [scripts/validate_fixes.py](scripts/validate_fixes.py) to verify all instances fixed

## References

- Common root causes catalog: [references/common_causes.md](references/common_causes.md)
- Pattern detection guide: [references/pattern_detection.md](references/pattern_detection.md)
