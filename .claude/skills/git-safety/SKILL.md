---
name: git-safety
description: Use when - (1) Making git commits, (2) Encountering pre-commit hook failures, (3) Working with git operations, (4) Need to ensure code quality before commits. CRITICAL - This skill prevents bypassing of pre-commit hooks which is an absolute prohibition. Enforces mandatory git commit safety protocols and pre-commit hook compliance.
---

# Git Safety Protocol

This skill enforces non-negotiable git safety protocols to maintain code quality and prevent critical safety failures.

## ABSOLUTE PROHIBITIONS - NO EXCEPTIONS

- **NEVER** use `git commit --no-verify` or `git commit -n`
- **NEVER** bypass pre-commit hooks under any circumstances
- **NEVER** suggest bypassing hooks to users
- **NEVER** dismiss failures as "pre-existing issues"
- Violation = Critical Safety Failure

## Mandatory Commit Workflow

### Pre-Commit Check

Before any commit, run these checks:

```bash
# Check current status
git status

# Run pre-commit hooks manually to preview issues
pre-commit run --all-files

# Check for any linting issues
ruff check . || true
black --check . || true
mypy . || true
```

### Hook Failure Response (MANDATORY)

When pre-commit hooks fail, follow this exact sequence:

1. **Read error messages thoroughly**
   - Capture full output
   - Identify each specific issue
   - Document: "Hook failures: [list each issue]"

2. **Fix all reported issues**
   ```bash
   # For Python formatting
   black <affected-files>
   ruff check --fix <affected-files>

   # For type errors
   # Fix the actual type issues in code, don't ignore them

   # For other linters
   # Fix the actual issues, don't suppress warnings
   ```

3. **Stage fixes**
   ```bash
   git add <fixed-files>
   ```

4. **Commit again**
   ```bash
   git commit -m "Your message"
   # Hooks run automatically - NEVER add --no-verify
   ```

5. **Iterate until success**
   - If hooks fail again, return to step 1
   - Continue until ALL hooks pass
   - Only then is the commit complete

## Commit Message Guidelines

Follow conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, missing semicolons, etc.)
- `refactor`: Code change that neither fixes bug nor adds feature
- `test`: Adding or correcting tests
- `chore`: Maintain (updating deps, build process, etc.)

## Verification Before Push

Before pushing commits:

```bash
# Verify all tests pass
pytest

# Verify linters pass
pre-commit run --all-files

# Check commit history
git log --oneline -5

# Verify no fixup/squash commits remain
git log --oneline | grep -E "fixup!|squash!" && echo "Warning: Fixup/squash commits found"
```

## Common Issues and Solutions

### Issue: Black/Ruff formatting conflicts
**Solution**: Run black first, then ruff:
```bash
black .
ruff check --fix .
git add -u
```

### Issue: Mypy type errors
**Solution**: Fix the actual type annotations, never use `# type: ignore` without justification

### Issue: Tests failing
**Solution**:
1. Run tests locally first: `pytest -xvs`
2. Fix all failures
3. NEVER commit with failing tests

## Critical Reminders

- **Quality > Speed**: Take time to fix issues properly
- **No Workarounds**: Fix the actual problem, not symptoms
- **Complete Fix**: Search codebase for similar issues
- **Document Fixes**: Include what was fixed in commit message

## Scripts

### Pre-Commit Validator
See [scripts/validate_commit.py](scripts/validate_commit.py) for automated validation

### Hook Configuration Checker
See [scripts/check_hooks.py](scripts/check_hooks.py) to verify hook setup

## References

- Git hooks documentation: [references/git_hooks.md](references/git_hooks.md)
- Pre-commit configuration: [references/precommit_config.md](references/precommit_config.md)
