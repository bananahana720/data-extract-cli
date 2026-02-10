---
name: no-deviation
description: Use when - (1) Dependency installation fails, (2) Integration errors occur, (3) Configuration issues arise, (4) Library conflicts happen, (5) ANY temptation to switch technologies. TIER 0 CRITICAL - Enforces absolute prohibition against switching to alternative solutions when encountering issues. This is a NON-NEGOTIABLE safety protocol that prevents deviation from user intent.
---

# No Deviation Protocol

**TIER 0 - NON-NEGOTIABLE SAFETY PROTOCOL**

This skill enforces the absolute prohibition against switching technologies, libraries, or approaches when encountering issues. Deviation from requested solutions is a Critical Task Failure.

## 🚨 ABSOLUTE PROHIBITIONS - NO EXCEPTIONS

- **NEVER** switch to alternative solutions when encountering issues
- **NEVER** take "the easy way out" by choosing different technologies
- **NEVER** substitute requested components without explicit user approval
- **MUST** fix the EXACT issue encountered, not work around it
- **Violation = Critical Task Failure**

## The No Deviation Decision Tree

```
┌─────────────────────────┐
│  Encounter Issue/Error  │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│   STOP - Do Not Pass    │
│   Do Not Switch Tools   │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│  Can I fix the EXACT    │
│  issue with requested   │
│      technology?        │
└──────┬─────────┬────────┘
      YES        NO
       ↓          ↓
┌──────────┐  ┌──────────────┐
│   FIX    │  │  Ask User    │
│   IT     │  │  Explicitly  │
└──────────┘  └──────────────┘
```

## Mandatory Response Protocol

### When Encountering Issues

```python
def handle_issue(error, requested_tech, alternative=None):
    """
    MANDATORY protocol for handling errors.
    NEVER automatically switch to alternatives.
    """

    # STEP 1: STOP - No automatic switching
    print(f"⛔ STOP: Issue encountered with {requested_tech}")
    print(f"Error: {error}")

    # STEP 2: DIAGNOSE - Understand the exact problem
    diagnosis = {
        'requested': requested_tech,
        'error_type': classify_error(error),
        'root_cause': find_root_cause(error),
        'fix_available': can_fix_exact_issue(error, requested_tech)
    }

    # STEP 3: FIX - Resolve with requested technology
    if diagnosis['fix_available']:
        print(f"✅ Fixing {requested_tech} issue...")
        fix_exact_issue(diagnosis)
    else:
        # STEP 4: NEVER switch without permission
        print(f"❌ Cannot automatically fix {requested_tech}")
        print(f"⚠️  NEVER switching to {alternative} without permission")
        ask_user_explicitly(diagnosis, alternative)

    # STEP 5: VERIFY - Ensure original request works
    verify_original_works(requested_tech)
```

## Common Violation Scenarios

### ❌ PROHIBITED: Package Installation Failures

```bash
# User requests: "Install and use Pinecone"
pip install pinecone-client
# Error: Installation failed

# ❌ WRONG - VIOLATION
echo "Pinecone installation failed, switching to ChromaDB instead"
pip install chromadb

# ✅ CORRECT - FIX THE EXACT ISSUE
echo "Pinecone installation failed due to [specific error]"
echo "Fixing by: [specific solution]"
# Fix the actual Pinecone installation issue
pip install --upgrade pip
pip install pinecone-client --no-cache-dir
```

### ❌ PROHIBITED: Database Connection Issues

```python
# User requests: "Use PostgreSQL"
# Error: PostgreSQL connection failed

# ❌ WRONG - VIOLATION
print("PostgreSQL connection failed, using SQLite instead")
conn = sqlite3.connect('database.db')

# ✅ CORRECT - FIX THE EXACT ISSUE
print("PostgreSQL connection issue: Connection refused on port 5432")
print("Diagnosing: Checking if PostgreSQL service is running")
# Fix the actual PostgreSQL issue
subprocess.run(["sudo", "service", "postgresql", "start"])
# Then connect to PostgreSQL as requested
```

### ❌ PROHIBITED: API Integration Problems

```javascript
// User requests: "Implement GraphQL API"
// Error: GraphQL setup issues

// ❌ WRONG - VIOLATION
console.log("GraphQL is complex, switching to REST API");
app.get('/api/users', (req, res) => {...});

// ✅ CORRECT - FIX THE EXACT ISSUE
console.log("GraphQL error: Schema validation failed");
console.log("Fixing: Correcting schema definition");
// Fix the actual GraphQL issue
const schema = buildSchema(`
  type Query {
    users: [User]
  }
`);
```

### ❌ PROHIBITED: Framework Conflicts

```python
# User requests: "Use FastAPI"
# Error: FastAPI import error

# ❌ WRONG - VIOLATION
print("FastAPI not working, using Flask instead")
from flask import Flask

# ✅ CORRECT - FIX THE EXACT ISSUE
print("FastAPI import error: No module named 'fastapi'")
print("Fixing: Installing FastAPI with correct dependencies")
# Fix the actual FastAPI issue
subprocess.run(["pip", "install", "fastapi[all]"])
from fastapi import FastAPI
```

## The Fix-First Methodology

### Step 1: Capture Exact Error

```bash
# Always capture complete error information
command_that_failed 2>&1 | tee error.log

# Document specifically
echo "Exact error: $(tail -n 10 error.log)"
echo "Error type: [installation|configuration|runtime|compatibility]"
echo "Requested technology: [exact name and version]"
```

### Step 2: Research Exact Solution

```python
def research_solution(tech, error):
    """Research solutions for the EXACT technology requested."""

    # Search for specific solutions
    searches = [
        f"{tech} {error} solution",
        f"fix {tech} {error}",
        f"{tech} troubleshooting {error}",
        f"{tech} github issues {error}"
    ]

    # NEVER search for alternatives
    prohibited_searches = [
        f"alternative to {tech}",
        f"{tech} vs",
        f"better than {tech}",
        f"replace {tech}"
    ]

    return find_exact_fix(searches)
```

### Step 3: Apply Targeted Fix

```bash
# Fix strategies in order of preference
# 1. Version-specific fixes
pip install package==specific_version

# 2. Dependency resolution
pip install missing_dependency

# 3. Configuration fixes
export REQUIRED_ENV_VAR=value

# 4. System-level fixes
sudo apt-get install system-requirement

# 5. Build from source if needed
git clone official_repo
cd official_repo && python setup.py install
```

### Step 4: Verify Original Works

```python
def verify_fix(requested_tech):
    """Ensure the requested technology now works."""

    try:
        # Test import/connection/functionality
        if tech_type == "package":
            __import__(requested_tech)
        elif tech_type == "database":
            connect_to_database(requested_tech)
        elif tech_type == "service":
            test_service_endpoint(requested_tech)

        print(f"✅ SUCCESS: {requested_tech} is now working correctly")
        return True
    except Exception as e:
        print(f"⚠️  Still not working: {e}")
        print("Continuing to fix the EXACT issue...")
        return False
```

## When User Permission IS Required

Only ask for permission to switch when:1. The requested technology genuinely doesn't exist2. The requested technology is definitively incompatible
3. Physical/hardware limitations prevent the exact solution

```python
def request_permission_to_deviate(issue_details):
    """
    Only called when fixing is genuinely impossible.
    NEVER call this for convenience or difficulty reasons.
    """

    message = f"""
    ⚠️  DEVIATION REQUEST - EXPLICIT PERMISSION REQUIRED

    Requested: {issue_details['requested']}
    Issue: {issue_details['root_cause']}

    I've attempted the following fixes:
    {issue_details['attempted_fixes']}

    The requested technology cannot be used because:
    {issue_details['impossibility_reason']}

    Would you like me to:
    1. Continue trying to fix {issue_details['requested']}
    2. Provide an alternative approach using {issue_details['alternative']}

    Please explicitly choose an option.
    """

    return await user_response(message)
```

## Integration with Other Skills

### Works With root-cause-analysis
When no-deviation prevents switching, use root-cause-analysis to properly diagnose:
```bash
# no-deviation says: "Don't switch from PostgreSQL"
# root-cause-analysis says: "Find out WHY PostgreSQL fails"
# Together: Fix the exact PostgreSQL issue at its root
```

### Works With verification-loop
After fixing the exact issue, verify it completely:
```bash
# no-deviation says: "Fixed the exact Pinecone issue"
# verification-loop says: "Now verify Pinecone works fully"
# Together: Ensure requested solution works end-to-end
```

## Critical Reminders

- **User Intent is Sacred**: They chose specific technologies for reasons
- **Learning Opportunity**: Fixing builds knowledge, switching avoids it
- **Technical Debt**: Alternatives create inconsistency and maintenance burden
- **Trust**: Users trust us to implement what they asked for

## Scripts

### Deviation Detector
See [scripts/detect_deviation.py](scripts/detect_deviation.py) - Monitors for attempted switches

### Fix Validator
See [scripts/validate_exact_fix.py](scripts/validate_exact_fix.py) - Ensures fixes match requests

## References

- Common fix patterns: [references/fix_patterns.md](references/fix_patterns.md)
- Technology-specific fixes: [references/tech_fixes.md](references/tech_fixes.md)

## Final Word

**REMEMBER**: The user requested specific technologies for specific reasons. Our job is to make their vision work, not to substitute our preferences. Fix the exact issue, or explicitly ask permission. There are no other options.
