---
name: modern-tools
description: Use when - (1) File searching operations, (2) Pattern matching in code, (3) Codebase exploration, (4) Performance-critical searches, (5) Any find/grep usage. Enforces use of modern, performant tools (fd instead of find, rg instead of grep). Automatically substitutes legacy tools with modern equivalents.
---

# Modern Tools Protocol

This skill enforces the use of modern, performant command-line tools over legacy alternatives, significantly improving performance and usability.

## Tool Substitution Rules

### MUST Use Modern Alternatives

| Legacy Tool | Modern Tool | Performance Gain | Usage |
|-------------|-------------|------------------|-------|
| `find` | `fd` | 5-10x faster | File/directory search |
| `grep` | `rg` (ripgrep) | 10-100x faster | Content search |
| `ls` | `exa` or `lsd` | 2x faster, better output | Directory listing |
| `cat` | `bat` | Same speed, syntax highlighting | File viewing |
| `sed` | `sd` | 2x faster, intuitive syntax | String substitution |
| `diff` | `delta` | Better visualization | File comparison |
| `du` | `dust` | 3x faster, better visualization | Disk usage |

## File Search Operations

### ❌ NEVER Use find
```bash
# ❌ WRONG - Using find
find . -name "*.py" -type f

# ✅ CORRECT - Using fd
fd -e py -t f

# ❌ WRONG - Complex find
find . -type f \( -name "*.js" -o -name "*.jsx" \) -mtime -7

# ✅ CORRECT - Simple fd
fd -e js -e jsx -t f --changed-within 7d
```

### fd Common Patterns

```bash
# Find all Python files
fd -e py

# Find files by pattern
fd pattern

# Find only directories
fd -t d

# Find hidden files
fd -H

# Exclude directories
fd -E node_modules -E .git

# Find and execute
fd -e py -x python {}

# Case insensitive search
fd -i readme

# Find files modified in last hour
fd --changed-within 1h
```

## Content Search Operations

### ❌ NEVER Use grep
```bash
# ❌ WRONG - Using grep
grep -r "TODO" . --include="*.py"

# ✅ CORRECT - Using ripgrep
rg "TODO" -t py

# ❌ WRONG - Complex grep
grep -r "function.*export" --include="*.js" --include="*.jsx" -n

# ✅ CORRECT - Simple ripgrep
rg "function.*export" -t js -t jsx -n
```

### Ripgrep Common Patterns

```bash
# Search in specific file types
rg "pattern" -t py

# Search with context
rg "error" -C 3  # 3 lines before and after

# Search only filenames
rg --files | rg "test"

# Multiline search
rg -U "class.*\n.*def __init__"

# Search and replace preview
rg "old" --replace "new"

# Ignore case
rg -i "pattern"

# Show only files with matches
rg -l "pattern"

# Exclude patterns
rg "pattern" -g "!*.test.js"

# Search in hidden files
rg --hidden "pattern"
```

## Performance Comparisons

```python
def benchmark_search_tools():
    """Compare performance of legacy vs modern tools."""

    import time
    import subprocess

    # Test: Find all Python files
    start = time.time()
    subprocess.run(["find", ".", "-name", "*.py"], capture_output=True)
    find_time = time.time() - start

    start = time.time()
    subprocess.run(["fd", "-e", "py"], capture_output=True)
    fd_time = time.time() - start

    print(f"find: {find_time:.2f}s")
    print(f"fd: {fd_time:.2f}s")
    print(f"fd is {find_time/fd_time:.1f}x faster")

    # Test: Search for pattern
    start = time.time()
    subprocess.run(["grep", "-r", "TODO", "."], capture_output=True)
    grep_time = time.time() - start

    start = time.time()
    subprocess.run(["rg", "TODO"], capture_output=True)
    rg_time = time.time() - start

    print(f"grep: {grep_time:.2f}s")
    print(f"rg: {rg_time:.2f}s")
    print(f"ripgrep is {grep_time/rg_time:.1f}x faster")
```

## Automatic Tool Substitution

```python
def substitute_legacy_command(command):
    """Automatically replace legacy tools with modern ones."""

    substitutions = {
        'find': convert_find_to_fd,
        'grep': convert_grep_to_rg,
        'ls': convert_ls_to_exa,
        'cat': convert_cat_to_bat,
        'sed': convert_sed_to_sd,
        'diff': convert_diff_to_delta
    }

    parts = command.split()
    if parts[0] in substitutions:
        modern_command = substitutions[parts[0]](command)
        print(f"📝 Converted: {command}")
        print(f"✨ To modern: {modern_command}")
        return modern_command

    return command

def convert_find_to_fd(find_cmd):
    """Convert find command to fd equivalent."""
    # Parse find arguments and convert to fd syntax
    # Example: find . -name "*.py" → fd -e py
    pass

def convert_grep_to_rg(grep_cmd):
    """Convert grep command to ripgrep equivalent."""
    # Parse grep arguments and convert to rg syntax
    # Example: grep -r "pattern" → rg "pattern"
    pass
```

## Installation Commands

```bash
# Install modern tools
# macOS
brew install fd ripgrep bat exa dust sd git-delta

# Ubuntu/Debian
sudo apt install fd-find ripgrep bat exa dust
# Note: fd might be installed as 'fdfind' on Ubuntu

# Arch Linux
pacman -S fd ripgrep bat exa dust sd git-delta

# From source (Rust required)
cargo install fd-find ripgrep bat exa du-dust sd git-delta
```

## Integration with Other Skills

### With scope-completeness
```bash
# scope-completeness needs to find ALL files
# Use fd for comprehensive, fast discovery
fd -t f -H . > all_files.txt  # Hidden files included

# NOT: find . -type f > all_files.txt
```

### With root-cause-analysis
```bash
# root-cause needs to search for patterns
# Use ripgrep for fast pattern matching
rg "error_pattern" --json | analyze_occurrences

# NOT: grep -r "error_pattern" | analyze_occurrences
```

## Configuration Files

### .fdignore (fd)
```
node_modules
.git
*.pyc
__pycache__
build
dist
```

### .rgignore (ripgrep)
```
node_modules/
*.min.js
*.map
build/
dist/
```

## Scripts

### Command Converter
See [scripts/convert_to_modern.py](scripts/convert_to_modern.py) - Converts legacy commands

### Performance Benchmarker
See [scripts/benchmark_tools.py](scripts/benchmark_tools.py) - Compares tool performance

## Critical Reminders

- **Performance Matters**: 10x faster adds up across thousands of operations
- **Better UX**: Modern tools have intuitive syntax and colored output
- **Consistency**: Always use modern tools, no exceptions
- **Educate**: Show performance comparisons to justify the switch
