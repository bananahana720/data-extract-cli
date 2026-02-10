---
name: file-organization
description: Use when - (1) Creating new files, (2) Generating documentation, (3) Adding scripts or tools, (4) Creating artifacts or reports, (5) Any file creation task. Ensures consistent project structure and prevents file sprawl.
---

# File Organization Protocol

This skill enforces proper file placement standards to maintain clean, organized project structures and prevent file sprawl.

## Core Principle

**Every file has a designated home**

- Artifacts (summaries, reports) → `./docs/artifacts/`
- Utility scripts → `./scripts/`
- Documentation → `./docs/`
- Tests → `./tests/`
- Source code → `./src/`
- Configuration → `./` (root) or `./.config/`
- **NEVER** create artifacts in project root

## Standard Directory Structure

```
project/
├── src/                 # Source code
│   ├── components/      # UI components
│   ├── services/        # Business logic
│   ├── utils/          # Utilities
│   └── models/         # Data models
├── tests/              # Test files
│   ├── unit/          # Unit tests
│   ├── integration/   # Integration tests
│   └── e2e/          # End-to-end tests
├── docs/               # Documentation
│   ├── api/          # API documentation
│   ├── guides/       # User guides
│   ├── artifacts/    # Generated reports/summaries
│   └── architecture/ # Architecture docs
├── scripts/            # Utility scripts
│   ├── build/        # Build scripts
│   ├── deploy/       # Deployment scripts
│   └── dev/          # Development tools
├── config/             # Configuration files
├── public/             # Public assets
└── .github/            # GitHub specific files
```

## File Placement Rules

```python
def determine_file_location(file_name, file_type, content_type):
    """Determine correct location for a file."""

    rules = {
        # Documentation
        'markdown': {
            'api_doc': 'docs/api/',
            'guide': 'docs/guides/',
            'summary': 'docs/artifacts/',
            'readme': './',  # Root only for main README
            'architecture': 'docs/architecture/'
        },

        # Code files
        'python': {
            'test': 'tests/',
            'script': 'scripts/',
            'source': 'src/',
            'util': 'src/utils/'
        },

        # Configuration
        'config': {
            'docker': './',
            'ci': '.github/workflows/',
            'env': './',
            'app': 'config/'
        },

        # Generated files
        'generated': {
            'report': 'docs/artifacts/',
            'summary': 'docs/artifacts/',
            'build': 'dist/',
            'temp': 'tmp/'
        }
    }

    location = rules.get(file_type, {}).get(content_type)

    if not location:
        raise FileOrganizationError(
            f"No standard location for {file_type}/{content_type}"
        )

    return location
```

## File Creation Workflow

### Before Creating Any File

```python
def create_file_properly(file_name, content, file_type):
    """Create file in correct location."""

    # Step 1: Determine location
    location = determine_file_location(file_name, file_type)

    # Step 2: Ensure directory exists
    Path(location).mkdir(parents=True, exist_ok=True)

    # Step 3: Check for conflicts
    full_path = Path(location) / file_name
    if full_path.exists():
        if not confirm(f"File exists: {full_path}. Overwrite?"):
            return suggest_alternative_name(full_path)

    # Step 4: Create file
    full_path.write_text(content)

    # Step 5: Update index if needed
    update_directory_index(location)

    print(f"✅ Created: {full_path}")
    return full_path
```

## Common File Types and Locations

### Documentation Files

```python
# ❌ WRONG - Documentation in root
create_file("API_GUIDE.md", content, path="./")
create_file("summary.md", content, path="./")

# ✅ CORRECT - Documentation in proper directories
create_file("api-guide.md", content, path="docs/api/")
create_file("summary.md", content, path="docs/artifacts/")
```

### Script Files

```python
# ❌ WRONG - Scripts scattered
create_file("analyze.py", content, path="./")
create_file("helper.sh", content, path="src/")

# ✅ CORRECT - Scripts organized
create_file("analyze.py", content, path="scripts/")
create_file("helper.sh", content, path="scripts/dev/")
```

### Test Files

```python
# ❌ WRONG - Tests mixed with source
create_file("test_user.py", content, path="src/models/")

# ✅ CORRECT - Tests in test directory
create_file("test_user.py", content, path="tests/unit/models/")
```

## Directory Index Management

```python
def update_directory_index(directory):
    """Maintain index.md for directory contents."""

    index_path = Path(directory) / "index.md"

    files = sorted([
        f.name for f in Path(directory).iterdir()
        if f.is_file() and f.name != "index.md"
    ])

    content = f"""# {Path(directory).name} Directory

## Files in this directory

| File | Description | Last Modified |
|------|-------------|---------------|
"""

    for file in files:
        file_path = Path(directory) / file
        modified = datetime.fromtimestamp(file_path.stat().st_mtime)
        desc = extract_description(file_path)
        content += f"| [{file}]({file}) | {desc} | {modified:%Y-%m-%d} |\n"

    index_path.write_text(content)
```

## File Naming Conventions

```python
def enforce_naming_convention(file_name, file_type):
    """Ensure file follows naming conventions."""

    conventions = {
        'python': r'^[a-z_]+\.py$',  # snake_case.py
        'javascript': r'^[a-z][a-zA-Z]+\.(js|jsx)$',  # camelCase.js
        'typescript': r'^[a-z][a-zA-Z]+\.(ts|tsx)$',  # camelCase.ts
        'markdown': r'^[a-z-]+\.md$',  # kebab-case.md
        'config': r'^\.[a-z]+rc$|^[a-z]+\.config\.(js|json)$'
    }

    pattern = conventions.get(file_type)
    if pattern and not re.match(pattern, file_name):
        suggestion = suggest_proper_name(file_name, file_type)
        raise NamingError(f"Invalid name: {file_name}. Suggested: {suggestion}")

    return True
```

## Cleanup and Organization

### Find Misplaced Files

```bash
# Find markdown files not in docs/
fd -e md -E docs

# Find Python scripts not in scripts/ or src/
fd -e py -E scripts -E src -E tests

# Find test files not in tests/
rg -l "def test_|class Test" --type py | rg -v "^tests/"
```

### Organize Existing Files

```python
def reorganize_project():
    """Move misplaced files to correct locations."""

    moves = []

    # Find misplaced documentation
    for md_file in Path(".").glob("*.md"):
        if md_file.name != "README.md":
            moves.append((md_file, Path("docs") / md_file.name))

    # Find misplaced scripts
    for script in Path(".").glob("*.sh"):
        moves.append((script, Path("scripts") / script.name))

    # Confirm moves
    print("Proposed file moves:")
    for src, dst in moves:
        print(f"  {src} → {dst}")

    if confirm("Proceed with reorganization?"):
        for src, dst in moves:
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
            print(f"Moved: {src} → {dst}")
```

## Integration with BMAD

When working with BMAD:
- Follow files-manifest.csv structure
- Maintain consistency with existing organization
- Place BMAD-specific files in designated directories:
  - Agents → `bmad/agents/`
  - Workflows → `bmad/workflows/`
  - Tasks → `bmad/tasks/`

## Common Anti-Patterns

### ❌ Root Directory Pollution
```bash
# Bad: Everything in root
./
├── analyze.py
├── summary.md
├── test_user.py
├── deploy.sh
└── API_DOCS.md
```

### ✅ Organized Structure
```bash
# Good: Everything in its place
./
├── docs/
│   ├── api/API_DOCS.md
│   └── artifacts/summary.md
├── scripts/
│   ├── analyze.py
│   └── deploy.sh
└── tests/
    └── test_user.py
```

## Scripts

### File Organizer
See [scripts/organize_files.py](scripts/organize_files.py) - Reorganizes misplaced files

### Structure Validator
See [scripts/validate_structure.py](scripts/validate_structure.py) - Validates project structure

## Critical Reminders

- **No Root Pollution**: Keep root directory clean
- **Consistent Structure**: Follow established patterns
- **Create Directories**: Ensure target directories exist
- **Update Indexes**: Maintain directory documentation
