# tmux-cli Documentation Updates - Windows/WSL Guidance

**Date**: 2025-11-13
**Context**: Story 2.5.3.1 - UAT Workflow Framework execution and tmux-cli testing
**Issue**: tmux-cli cannot be called directly from Windows due to tmux being Unix/Linux only

---

## Summary

Updated all AI instruction files that reference tmux-cli to include Windows/WSL guidance, ensuring future AI agents and developers understand the recommended approach for using tmux-cli on Windows systems.

## Root Cause

- tmux is a Unix/Linux-only tool (not available natively on Windows)
- tmux-cli uses Python's `subprocess.run()` which on Windows specifically looks for `.exe` executables
- While tmux is available in WSL (Ubuntu, version 3.4), tmux-cli running on Windows cannot find it
- Wrapper scripts (.bat, .cmd, Python) work when called directly but not via subprocess

## Solution

**Recommended approach**: Run workflows requiring tmux-cli from within WSL environment where tmux is natively available.

---

## Files Updated

### 1. CLAUDE.md (Project Instructions)

**Location**: Root directory - `CLAUDE.md`

**Section**: "Running UAT Workflows" → "tmux-cli Integration"

**Changes**:
- Added prominent Windows warning at top of tmux-cli section
- Provided WSL execution instructions with exact commands
- Separated "Windows Users" from "Linux/macOS or WSL" usage
- Added reference to detailed setup guide

**Impact**: AI agents will immediately see Windows limitations when working with UAT workflows

---

### 2. execute-tests Workflow Instructions

**Location**: `bmad/bmm/workflows/4-implementation/execute-tests/instructions.md`

**Section**: Step 5 - "Execute CLI tests (tmux-cli)"

**Changes**:
- Added Windows warning at start of CLI test execution step
- Provided three options:
  1. Run from WSL (recommended)
  2. Mark CLI tests as BLOCKED
  3. See detailed setup guide
- Included exact WSL navigation commands

**Impact**: Workflow execution will handle Windows gracefully with clear guidance

---

### 3. execute-tests Workflow README

**Location**: `bmad/bmm/workflows/4-implementation/execute-tests/README.md`

**Section**: "Test Execution Types" → "2. CLI Tests (tmux-cli)"

**Changes**:
- Added Windows-specific section after tmux-cli integration patterns
- Listed three options with code examples
- Provided WSL execution template with placeholders
- Added reference to both tmux-cli-instructions.md and tmux-cli-windows-setup.md

**Impact**: Developers reading workflow documentation will understand Windows requirements upfront

---

### 4. tmux-cli Instructions (General Reference)

**Location**: `docs/tmux-cli-instructions.md`

**Section**: "Prerequisites" (near top of document)

**Changes**:
- Expanded prerequisites section with Windows-specific guidance
- Added "⚠️ Windows Users" warning with two clear options
- Provided WSL navigation template
- Documented the limitation clearly
- Referenced detailed setup guide

**Impact**: First-time users of tmux-cli will immediately understand Windows requirements

---

### 5. Epic 2.5 Technical Specification

**Location**: `docs/tech-spec-epic-2.5.md`

**Section**: "Workflow 3: execute-tests" → "CLI Tests (tmux-cli)"

**Changes**:
- Added Windows warning after tmux-cli integration pattern example
- Provided WSL execution command sequence
- Added references to both instruction files

**Impact**: Technical specification now accurately reflects Windows considerations for UAT framework

---

## Supporting Documentation Created

### tmux-cli Windows Setup Guide

**Location**: `docs/uat/tmux-cli-windows-setup.md`

**Contents**:
- Summary of current status
- Technical details (root cause explanation)
- .tmux.conf configuration (WSL tmux → Windows PowerShell bridge)
- Three recommended solution options with pros/cons
- Quick setup instructions for Windows users
- Future enhancement suggestions
- References and next steps

**Purpose**: Comprehensive reference for Windows developers implementing CLI tests

---

## Test Results Updated

**Location**: `docs/uat/test-results/2.5-3.1-test-results.md`

**Section**: "Test Evidence" → "tmux-cli Integration Evidence"

**Changes**:
- Added "Windows Limitation Identified" section
- Documented technical root cause
- Listed attempted workarounds (.bat, .cmd, Python wrapper)
- Provided three recommendations for workflow enhancement
- Noted .tmux.conf configuration completed

**Impact**: Test execution results accurately reflect Windows findings

---

## Configuration Files Created

### .tmux.conf (Windows PowerShell Bridge)

**Locations**:
- Windows: `C:\Users\Andrew\.tmux.conf`
- WSL: `~/.tmux.conf` (copied from Windows)

**Configuration**:
```tmux
# Bridge WSL tmux with Windows PowerShell
set -g default-command "cd $(pwsh.exe -c 'Write-Host -NoNewLine $env:userprofile' | xargs -0 wslpath); exec pwsh.exe --nologo"
set-window-option -g automatic-rename off
bind c new-window -n "PowerShell"

# Additional settings for CLI testing
set -g history-limit 50000
set -g display-time 4000
set -g mouse on
```

**Purpose**: Enables WSL tmux to control Windows PowerShell sessions for hybrid testing scenarios

**Credit**: Based on Stack Overflow solution (CC BY-SA 4.0)

---

## Wrapper Scripts Created (For Reference)

Although not functional with tmux-cli due to subprocess limitations, these wrappers are available for direct tmux usage:

1. **tmux.bat** - `C:\Users\Andrew\.local\bin\tmux.bat`
2. **tmux.cmd** - `C:\Users\Andrew\.local\bin\tmux.cmd`
3. **tmux** (Python) - `C:\Users\Andrew\.local\bin\tmux`

All wrappers forward commands to WSL tmux: `wsl tmux %*`

These work when called directly (e.g., `tmux.cmd -V` returns "tmux 3.4") but cannot be invoked by tmux-cli.

---

## Recommended Workflow on Windows

For any UAT workflow requiring CLI tests (execute-tests with test_execution_mode=automated or hybrid):

```bash
# 1. Enter WSL environment
wsl

# 2. Navigate to project (Windows filesystem is at /mnt/c/)
cd /mnt/c/Users/Andrew/projects/data-extraction-tool-1

# 3. Verify tmux available
tmux -V
# Expected: tmux 3.4

# 4. Run workflow normally
workflow execute-tests test_execution_mode=hybrid

# 5. tmux-cli commands work natively in WSL
tmux-cli launch "zsh"
tmux-cli send "data-extract process test.pdf" --pane=2
tmux-cli capture --pane=2
```

---

## Files Affected Summary

| File | Type | Change Type |
|------|------|-------------|
| CLAUDE.md | AI Instructions | Updated - Windows guidance |
| bmad/bmm/workflows/4-implementation/execute-tests/instructions.md | Workflow | Updated - Windows warning |
| bmad/bmm/workflows/4-implementation/execute-tests/README.md | Documentation | Updated - Windows options |
| docs/tmux-cli-instructions.md | Reference | Updated - Prerequisites |
| docs/tech-spec-epic-2.5.md | Specification | Updated - CLI tests section |
| docs/uat/tmux-cli-windows-setup.md | Documentation | Created - Setup guide |
| docs/uat/test-results/2.5-3.1-test-results.md | Test Results | Updated - Evidence section |
| C:\Users\Andrew\.tmux.conf | Configuration | Created - PowerShell bridge |
| ~/.tmux.conf (WSL) | Configuration | Created - PowerShell bridge |

**Total files updated**: 7
**Total files created**: 3

---

## Verification

All updates verified:
- ✅ Windows warnings added to all AI instruction files mentioning tmux-cli
- ✅ WSL execution path documented consistently across all files
- ✅ References to detailed setup guide included
- ✅ .tmux.conf configuration created and tested
- ✅ Test results updated with findings

---

## Next Steps

1. **For Story 2.5.3.1**: Test results are complete, proceed to review-uat-results workflow
2. **For Future Stories**: Use WSL execution for any CLI testing scenarios
3. **For Enhancement**: Consider adding OS detection to execute-tests workflow
4. **For CI/CD**: Document WSL requirement for automated UAT pipelines on Windows

---

## References

- Original Stack Overflow solution: https://superuser.com/a (CC BY-SA 4.0)
- tmux-cli documentation: `docs/tmux-cli-instructions.md`
- Python subprocess documentation: https://docs.python.org/3/library/subprocess.html
- WSL documentation: https://docs.microsoft.com/en-us/windows/wsl/

---

**Status**: Complete - All AI instruction files updated with Windows/WSL guidance
**Story Impact**: No blocking issues for Story 2.5.3.1 UAT completion
**Recommendation**: Document this pattern for future UAT workflows with CLI testing requirements
