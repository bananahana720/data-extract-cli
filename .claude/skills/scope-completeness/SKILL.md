---
name: scope-completeness
description: Use when - (1) Processing multiple files or items, (2) Batch operations like refactoring or updates, (3) Search and replace across codebase, (4) Cleaning up or organizing projects, (5) Need to ensure nothing is missed. Ensures complete scope coverage for batch operations and systematic processing. Prevents incomplete processing and missing edge cases.
---

# Scope Completeness Protocol

This skill ensures comprehensive coverage in batch operations, preventing missed items and incomplete processing.

## Core Principle

**Process ALL items, not just obvious ones**

Before any batch operation:
- Use comprehensive glob patterns to find ALL matching items
- List all items explicitly: "Found N items: [list]"
- Check multiple locations (root, subdirectories, dot-directories)
- Verify completeness: "Processed N/N items"

## The Complete Scope Workflow

### Step 1: Define Scope

Clearly define what needs processing:

```python
# Define scope parameters
scope_definition = {
    'file_patterns': ['*.py', '*.js', '*.tsx'],
    'directories': ['src/', 'tests/', 'scripts/', '.github/'],
    'exclude_patterns': ['*.pyc', '__pycache__', 'node_modules'],
    'include_hidden': True,  # Don't forget dot directories!
}

print("Scope Definition:")
print(f"  Patterns: {scope_definition['file_patterns']}")
print(f"  Directories: {scope_definition['directories']}")
print(f"  Include hidden: {scope_definition['include_hidden']}")
```

### Step 2: Comprehensive Discovery

Find ALL items matching scope:

```bash
# Use multiple search strategies to ensure completeness

echo "=== Discovery Phase ==="

# Strategy 1: fd (file finder)
echo "Using fd..."
fd -t f -e py -e js -e tsx . > files_fd.txt

# Strategy 2: ripgrep files
echo "Using ripgrep..."
rg --files | grep -E '\.(py|js|tsx)$' > files_rg.txt

# Strategy 3: find command
echo "Using find..."
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.tsx" \) > files_find.txt

# Combine and deduplicate
cat files_fd.txt files_rg.txt files_find.txt | sort -u > all_files.txt

# Count and verify
TOTAL_FILES=$(wc -l < all_files.txt)
echo "Found $TOTAL_FILES files total"
```

### Step 3: Create Explicit Inventory

List ALL items before processing:

```python
def create_inventory(patterns, directories):
    """Create comprehensive inventory of items to process."""
    import glob
    from pathlib import Path

    inventory = {
        'files': [],
        'directories': [],
        'by_type': {},
        'by_location': {}
    }

    # Search in all specified directories
    for directory in directories:
        # Check if directory exists
        if not Path(directory).exists():
            print(f"⚠️  Directory not found: {directory}")
            continue

        for pattern in patterns:
            # Search in main directory
            found = glob.glob(f"{directory}/**/{pattern}", recursive=True)
            inventory['files'].extend(found)

            # Don't forget hidden directories!
            hidden_found = glob.glob(f"{directory}/**/.*/{pattern}", recursive=True)
            inventory['files'].extend(hidden_found)

    # Remove duplicates and sort
    inventory['files'] = sorted(set(inventory['files']))

    # Categorize by type
    for file in inventory['files']:
        ext = Path(file).suffix
        if ext not in inventory['by_type']:
            inventory['by_type'][ext] = []
        inventory['by_type'][ext].append(file)

    # Report
    print(f"\n📋 INVENTORY COMPLETE")
    print(f"Total files: {len(inventory['files'])}")
    print("\nBy type:")
    for ext, files in inventory['by_type'].items():
        print(f"  {ext}: {len(files)} files")

    print("\nFirst 10 files:")
    for file in inventory['files'][:10]:
        print(f"  - {file}")

    if len(inventory['files']) > 10:
        print(f"  ... and {len(inventory['files']) - 10} more")

    return inventory
```

### Step 4: Process with Progress Tracking

Process items with explicit progress reporting:

```python
def process_with_tracking(items, operation):
    """Process items with detailed progress tracking."""

    total = len(items)
    processed = 0
    failed = []
    skipped = []

    print(f"\n🔄 PROCESSING {total} items")
    print("=" * 50)

    for i, item in enumerate(items, 1):
        try:
            # Show progress every 10 items or for small batches
            if i % 10 == 0 or total < 50:
                print(f"Progress: {i}/{total} ({i*100//total}%)")

            # Apply operation
            result = operation(item)

            if result == 'skipped':
                skipped.append(item)
            else:
                processed += 1

        except Exception as e:
            print(f"❌ Failed: {item} - {e}")
            failed.append((item, str(e)))

    # Final report
    print("\n" + "=" * 50)
    print("📊 PROCESSING COMPLETE")
    print(f"  ✅ Processed: {processed}/{total}")
    print(f"  ⏭️  Skipped: {len(skipped)}")
    print(f"  ❌ Failed: {len(failed)}")

    if failed:
        print("\nFailed items:")
        for item, error in failed[:5]:
            print(f"  - {item}: {error}")
        if len(failed) > 5:
            print(f"  ... and {len(failed) - 5} more")

    return processed, skipped, failed
```

### Step 5: Verify Completeness

Ensure nothing was missed:

```bash
# Verification checklist
echo "=== COMPLETENESS VERIFICATION ==="

# 1. Check item count matches
EXPECTED=$(wc -l < all_files.txt)
PROCESSED=$(wc -l < processed_files.txt)

if [ "$EXPECTED" -eq "$PROCESSED" ]; then
    echo "✅ All $EXPECTED files processed"
else
    echo "❌ Mismatch: Expected $EXPECTED, Processed $PROCESSED"
    # Find what was missed
    comm -23 <(sort all_files.txt) <(sort processed_files.txt) > missed_files.txt
    echo "Missed files:"
    cat missed_files.txt
fi

# 2. Check common hiding spots
echo "Checking hidden directories..."
fd -H -t f -e py -e js -e tsx . | grep -E '/\.' > hidden_files.txt
if [ -s hidden_files.txt ]; then
    echo "⚠️  Found files in hidden directories:"
    head -5 hidden_files.txt
fi

# 3. Check commonly missed locations
COMMON_MISSED=(".github" ".vscode" "docs" "examples" "samples")
for dir in "${COMMON_MISSED[@]}"; do
    if [ -d "$dir" ]; then
        count=$(find "$dir" -type f \( -name "*.py" -o -name "*.js" \) | wc -l)
        echo "  $dir: $count relevant files"
    fi
done
```

## Common Scope Pitfalls

### Pitfall 1: Missing Hidden Directories
```bash
# ❌ BAD: Misses .github/, .vscode/, etc
find . -name "*.py"

# ✅ GOOD: Includes hidden directories
find . -name "*.py" -o -path "*/.*/*.py"
```

### Pitfall 2: Incomplete Glob Patterns
```bash
# ❌ BAD: Misses .jsx, .mjs, .cjs files
fd -e js

# ✅ GOOD: Comprehensive patterns
fd -e js -e jsx -e mjs -e cjs -e ts -e tsx
```

### Pitfall 3: Not Checking All Locations
```python
# ❌ BAD: Only checks src/
files = glob.glob("src/**/*.py")

# ✅ GOOD: Checks all relevant directories
locations = ["src/", "tests/", "scripts/", "tools/", ".github/"]
files = []
for loc in locations:
    files.extend(glob.glob(f"{loc}**/*.py", recursive=True))
```

## Batch Operation Strategies

### Strategy 1: Parallel Processing
```python
# Process in parallel for performance
from concurrent.futures import ThreadPoolExecutor

def batch_process_parallel(items, operation, max_workers=4):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(operation, items))
    return results
```

### Strategy 2: Chunked Processing
```python
# Process in chunks for large batches
def chunk_process(items, chunk_size=100):
    for i in range(0, len(items), chunk_size):
        chunk = items[i:i+chunk_size]
        print(f"Processing chunk {i//chunk_size + 1}: {len(chunk)} items")
        process_chunk(chunk)
```

### Strategy 3: Safe Mode Processing
```python
# Dry run first, then actual processing
def safe_batch_process(items, operation):
    # Dry run
    print("🔍 DRY RUN - No changes will be made")
    issues = []
    for item in items:
        if not validate_item(item):
            issues.append(item)

    if issues:
        print(f"⚠️  Found {len(issues)} potential issues")
        if not confirm("Continue anyway?"):
            return

    # Actual processing
    print("🚀 EXECUTING - Making changes")
    process_with_tracking(items, operation)
```

## Progress Reporting Format

Use this standard format for batch operations:

```
=================================
BATCH OPERATION: [Description]
=================================
Scope: [patterns/criteria]
Total items: N

Discovery Phase:
  ✓ Found N files in src/
  ✓ Found N files in tests/
  ✓ Found N files in .github/
  Total: N items

Processing:
  [████████████░░░░░░░] 75% (750/1000)
  Current: processing file_xyz.py
  Elapsed: 2m 30s
  Estimated: 50s remaining

Summary:
  ✅ Processed: 950/1000
  ⏭️  Skipped: 30 (unchanged)
  ❌ Failed: 20 (see errors.log)

Verification:
  ✓ All items in scope processed
  ✓ No files missed
  ✓ Results validated
=================================
```

## Scripts

### Scope Discovery Tool
See [scripts/discover_scope.py](scripts/discover_scope.py) for automated scope discovery

### Batch Processor
See [scripts/batch_processor.py](scripts/batch_processor.py) for parallel batch processing

## References

- Glob pattern guide: [references/glob_patterns.md](references/glob_patterns.md)
- Batch operation best practices: [references/batch_operations.md](references/batch_operations.md)
