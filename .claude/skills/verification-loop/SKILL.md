---
name: verification-loop
description: Use when - (1) After making any code changes, (2) Implementing features or fixes, (3) Before declaring tasks complete, (4) Running test suites, (5) Need to ensure all tests and linters pass. Enforces mandatory verification loops for all changes to ensure quality and prevent incomplete work. CRITICAL - Never declare complete without ALL verifications passing.
---

# Verification Loop Protocol

This skill enforces mandatory verification iterations to ensure all changes are properly tested and validated before declaring completion.

## Core Principle

**ONLY declare complete when ALL tests pass**

Mandatory iteration pattern:
1. Make change
2. Run tests/verification IMMEDIATELY
3. Analyze failures
4. IF failures exist: fix and GOTO step 1
5. ONLY declare complete when ALL tests pass

## Completion Criteria Checklist

ALL must be true before declaring complete:
- ✅ All tests passing
- ✅ All linters passing
- ✅ Verified in running environment
- ✅ No errors in logs

## The Verification Workflow

### Step 1: Make Changes

Implement your changes:
```bash
# Track what files were modified
git status
git diff

# Document changes
echo "Changes made:"
echo "- Modified: [files]"
echo "- Purpose: [what was changed and why]"
```

### Step 2: Run Verification Suite

**IMMEDIATELY** after changes, run ALL verifications:

```bash
# Run test suite
echo "=== Running Tests ==="
pytest -xvs || TESTS_FAILED=true

# Run linters
echo "=== Running Linters ==="
pre-commit run --all-files || LINTERS_FAILED=true

# Check type hints
echo "=== Type Checking ==="
mypy . || TYPES_FAILED=true

# Check for security issues
echo "=== Security Check ==="
bandit -r . || SECURITY_FAILED=true

# Summary
if [ "$TESTS_FAILED" = true ] || [ "$LINTERS_FAILED" = true ] || [ "$TYPES_FAILED" = true ] || [ "$SECURITY_FAILED" = true ]; then
    echo "❌ VERIFICATION FAILED - Must fix issues"
    exit 1
else
    echo "✅ All verifications passed"
fi
```

### Step 3: Analyze Failures

If ANY failures occur:

```python
def analyze_failures(output):
    """Parse and categorize failures."""

    failures = {
        'test_failures': [],
        'lint_errors': [],
        'type_errors': [],
        'security_issues': []
    }

    # Parse output and categorize
    # Document each failure type

    print(f"Total failures: {sum(len(v) for v in failures.values())}")
    print("Categories:")
    for category, issues in failures.items():
        if issues:
            print(f"  {category}: {len(issues)} issues")
            for issue in issues[:3]:  # Show first 3
                print(f"    - {issue}")

    return failures
```

### Step 4: Fix and Iterate

**MANDATORY**: Fix ALL issues before proceeding:

```bash
# For each failure category
while [ "$FAILURES_EXIST" = true ]; do
    echo "Fixing issues..."

    # Fix test failures
    if [ "$TESTS_FAILED" = true ]; then
        echo "Fixing test failures..."
        # Fix the actual issues
        # Re-run tests
        pytest -xvs && TESTS_FAILED=false
    fi

    # Fix linter issues
    if [ "$LINTERS_FAILED" = true ]; then
        echo "Fixing linter issues..."
        black .
        ruff check --fix .
        # Re-run linters
        pre-commit run --all-files && LINTERS_FAILED=false
    fi

    # Check if all fixed
    if [ "$TESTS_FAILED" = false ] && [ "$LINTERS_FAILED" = false ]; then
        FAILURES_EXIST=false
    fi
done
```

### Step 5: Final Verification

Before declaring complete:

```bash
# Full verification suite
echo "=== FINAL VERIFICATION ==="

# 1. All tests must pass
pytest || exit 1

# 2. All linters must pass
pre-commit run --all-files || exit 1

# 3. No type errors
mypy . || exit 1

# 4. Application runs
python -m app --version || exit 1

# 5. No errors in logs
tail -n 100 app.log | grep -i error && echo "Errors found in logs!" && exit 1

echo "✅ ALL VERIFICATIONS PASSED - Task Complete"
```

## ABSOLUTE PROHIBITIONS

**NEVER do these:**
- NEVER dismiss test failures as "pre-existing issues unrelated to changes"
- NEVER dismiss linting errors as "pre-existing issues unrelated to changes"
- NEVER ignore ANY failing test or linting issue, regardless of origin
- MUST fix ALL failures before declaring complete, even if they existed before

**Rationale:** Code quality is a collective responsibility. All failures block completion.

## Verification Stages

### Stage 1: Unit Tests
```bash
pytest tests/unit/ -xvs
```

### Stage 2: Integration Tests
```bash
pytest tests/integration/ -xvs
```

### Stage 3: End-to-End Tests
```bash
pytest tests/e2e/ -xvs
```

### Stage 4: Performance Tests
```bash
pytest tests/performance/ --benchmark-only
```

### Stage 5: Security Tests
```bash
bandit -r src/
safety check
```

## Common Failure Patterns

### Pattern 1: Cascading Test Failures
**Symptom:** One change breaks multiple tests
**Solution:** Fix root cause first, then re-run all tests

### Pattern 2: Flaky Tests
**Symptom:** Tests pass/fail inconsistently
**Solution:** Run 3 times, if fails 2/3, investigate timing/state issues

### Pattern 3: Environment-Specific Failures
**Symptom:** Works locally but fails in CI
**Solution:** Match CI environment exactly, check dependencies

## Progress Tracking

Track iteration progress:

```markdown
## Verification Progress

### Iteration 1
- [ ] Tests: 45/50 passing
- [ ] Linters: 3 errors
- [ ] Types: Clean
- Status: INCOMPLETE - fixing test failures

### Iteration 2
- [ ] Tests: 48/50 passing
- [ ] Linters: 3 errors
- [ ] Types: Clean
- Status: INCOMPLETE - 2 tests still failing

### Iteration 3
- [x] Tests: 50/50 passing
- [ ] Linters: 3 errors
- [x] Types: Clean
- Status: INCOMPLETE - fixing linter issues

### Iteration 4
- [x] Tests: 50/50 passing
- [x] Linters: Clean
- [x] Types: Clean
- Status: COMPLETE ✅
```

## Verification Report Template

```markdown
## Verification Report

### Changes Made
- [List of changes]

### Verification Results
- Tests: X/Y passing
- Linters: Pass/Fail
- Type Check: Pass/Fail
- Security: Pass/Fail

### Iterations Required: N

### Issues Fixed
1. [Issue 1 description and fix]
2. [Issue 2 description and fix]

### Final Status: ✅ COMPLETE / ❌ INCOMPLETE
```

## Scripts

### Automated Verification Runner
See [scripts/run_verification.sh](scripts/run_verification.sh) for complete verification automation

### Iteration Tracker
See [scripts/track_iterations.py](scripts/track_iterations.py) to log verification attempts

## References

- Testing best practices: [references/testing_guide.md](references/testing_guide.md)
- Linter configuration: [references/linter_config.md](references/linter_config.md)
