#!/usr/bin/env python3
"""
Create remaining skills in batch for efficiency.
"""

import subprocess
from pathlib import Path

SKILLS_DIR = Path.home() / ".claude" / "skills"
SKILL_CREATOR_PATH = (
    Path.home()
    / ".claude"
    / "plugins"
    / "marketplaces"
    / "anthropic-agent-skills"
    / "skill-creator"
)

# Define all remaining skills with their content
SKILLS = [
    {
        "name": "design-patterns",
        "description": "Enforces design consistency by studying and reusing existing patterns before creating new components. Use when: (1) Creating UI components, (2) Implementing new features, (3) Architecture decisions, (4) Writing new modules, (5) Need to maintain consistency. Prevents reinventing the wheel and ensures design coherence.",
        "content": '''---
name: design-patterns
description: Enforces design consistency by studying and reusing existing patterns before creating new components. Use when: (1) Creating UI components, (2) Implementing new features, (3) Architecture decisions, (4) Writing new modules, (5) Need to maintain consistency. Prevents reinventing the wheel and ensures design coherence.
---

# Design Patterns Protocol

This skill ensures design consistency by studying existing patterns before implementation, preventing redundant solutions and maintaining coherence.

## Core Principle

**Study existing patterns BEFORE creating anything new**

- MUST study 3-5 existing similar components/patterns
- MUST extract and document patterns found
- MUST reuse existing components (create new ONLY if no alternative)
- MUST maintain consistency with established patterns

## Pattern Discovery Workflow

### Step 1: Identify Similar Implementations

```python
def find_similar_patterns(task_type, feature_name):
    """Find existing patterns similar to what needs implementing."""

    patterns_found = {
        'ui_components': [],
        'api_patterns': [],
        'data_structures': [],
        'workflows': []
    }

    # Search strategies
    search_terms = generate_search_terms(task_type, feature_name)

    for term in search_terms:
        # Search UI components
        ui_matches = search_codebase(f"component.*{term}", "tsx", "jsx")
        patterns_found['ui_components'].extend(ui_matches)

        # Search API patterns
        api_matches = search_codebase(f"route.*{term}|endpoint.*{term}", "py", "js")
        patterns_found['api_patterns'].extend(api_matches)

    return patterns_found
```

### Step 2: Extract Patterns

```python
def extract_patterns(similar_implementations):
    """Extract reusable patterns from existing code."""

    patterns = {
        'colors': set(),
        'typography': set(),
        'spacing': set(),
        'components': set(),
        'layouts': set(),
        'api_structure': set(),
        'error_handling': set()
    }

    for impl in similar_implementations:
        # Extract visual patterns
        patterns['colors'].update(extract_colors(impl))
        patterns['typography'].update(extract_fonts(impl))
        patterns['spacing'].update(extract_spacing(impl))

        # Extract structural patterns
        patterns['components'].update(extract_components(impl))
        patterns['api_structure'].update(extract_api_patterns(impl))

    return consolidate_patterns(patterns)
```

### Step 3: Document Findings

```markdown
## Pattern Analysis Report

### Similar Implementations Found
1. UserProfileCard component - src/components/UserProfileCard.tsx
2. TeamMemberCard component - src/components/TeamMemberCard.tsx
3. ContactCard component - src/components/ContactCard.tsx

### Extracted Patterns
- **Colors**: Primary: #007bff, Secondary: #6c757d, Background: #f8f9fa
- **Typography**: Headers: Roboto 24px bold, Body: Open Sans 16px
- **Spacing**: Padding: 16px, Margin: 8px between elements
- **Components**: All use Card wrapper, Avatar component, ActionButtons
- **Layout**: Flexbox column, centered alignment, 320px max-width

### Recommendation
✅ REUSE: Extend existing Card component
❌ AVOID: Creating new card from scratch
```

## UI Pattern Compliance

```javascript
// Before implementing any UI
function enforceDesignConsistency(newComponent) {
    // Step 1: Find similar components
    const similar = findSimilarComponents(newComponent.type);

    if (similar.length === 0) {
        console.warn("No similar components found - document new pattern");
        return createNewPattern(newComponent);
    }

    // Step 2: Extract patterns
    const patterns = {
        colors: extractColors(similar),
        fonts: extractTypography(similar),
        spacing: extractSpacing(similar),
        components: extractReusableComponents(similar)
    };

    // Step 3: Apply patterns
    return applyPatterns(newComponent, patterns);
}
```

## API Pattern Compliance

```python
def enforce_api_patterns(new_endpoint):
    """Ensure API follows existing patterns."""

    # Find similar endpoints
    similar_endpoints = find_similar_api_endpoints(new_endpoint.resource)

    if not similar_endpoints:
        raise DesignError("No similar API patterns found - consult team")

    # Extract patterns
    patterns = {
        'url_structure': extract_url_pattern(similar_endpoints),
        'http_methods': extract_method_patterns(similar_endpoints),
        'response_format': extract_response_format(similar_endpoints),
        'error_handling': extract_error_patterns(similar_endpoints),
        'authentication': extract_auth_pattern(similar_endpoints)
    }

    # Apply patterns
    return apply_api_patterns(new_endpoint, patterns)
```

## Common Pattern Categories

### Visual Patterns
- Color schemes
- Typography scales
- Spacing systems
- Border styles
- Shadow effects
- Animation timings

### Component Patterns
- Form layouts
- Navigation structures
- Modal behaviors
- List presentations
- Card designs
- Button variants

### Code Patterns
- Error handling
- State management
- API communication
- Data validation
- Testing approaches
- Documentation style

## Pattern Reuse Decision Tree

```
Need to implement X
        ↓
Search for similar X
        ↓
Found similar?
    ├─Yes→ Can extend/modify?
    │       ├─Yes→ EXTEND existing
    │       └─No→ Why not? Document reason
    └─No→ Search broader patterns
            ↓
        Found patterns?
            ├─Yes→ APPLY patterns to new implementation
            └─No→ CREATE new pattern (document thoroughly)
```

## Integration with BMAD

When working with BMAD agents/workflows:
1. Check agent-manifest.csv for similar agents
2. Review workflow-manifest.csv for existing workflows
3. Study files-manifest.csv for file patterns
4. Maintain consistency with manifest structures

## Scripts

### Pattern Finder
See [scripts/find_patterns.py](scripts/find_patterns.py) - Discovers existing patterns

### Pattern Validator
See [scripts/validate_pattern_compliance.py](scripts/validate_pattern_compliance.py) - Ensures pattern compliance

## Critical Reminders

- **Research First**: Always search before creating
- **Document Patterns**: Record why patterns were chosen
- **Maintain Consistency**: Small deviations compound into chaos
- **Reuse > Create**: Extending is better than duplicating''',
    },
    {
        "name": "modern-tools",
        "description": "Enforces use of modern, performant tools (fd instead of find, rg instead of grep). Use when: (1) File searching operations, (2) Pattern matching in code, (3) Codebase exploration, (4) Performance-critical searches, (5) Any find/grep usage. Automatically substitutes legacy tools with modern equivalents.",
        "content": '''---
name: modern-tools
description: Enforces use of modern, performant tools (fd instead of find, rg instead of grep). Use when: (1) File searching operations, (2) Pattern matching in code, (3) Codebase exploration, (4) Performance-critical searches, (5) Any find/grep usage. Automatically substitutes legacy tools with modern equivalents.
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
find . -type f \\( -name "*.js" -o -name "*.jsx" \\) -mtime -7

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
rg -U "class.*\\n.*def __init__"

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
- **Educate**: Show performance comparisons to justify the switch''',
    },
    {
        "name": "infrastructure-orchestration",
        "description": "Ensures proper service management using orchestration scripts instead of individual commands. Use when: (1) Starting/stopping services, (2) Docker operations, (3) Deployment tasks, (4) Service dependencies exist, (5) Multiple services need coordination. Prevents service management errors and ensures proper startup/shutdown sequences.",
        "content": '''---
name: infrastructure-orchestration
description: Ensures proper service management using orchestration scripts instead of individual commands. Use when: (1) Starting/stopping services, (2) Docker operations, (3) Deployment tasks, (4) Service dependencies exist, (5) Multiple services need coordination. Prevents service management errors and ensures proper startup/shutdown sequences.
---

# Infrastructure Orchestration Protocol

This skill ensures services are managed through proper orchestration scripts, preventing dependency issues and maintaining correct startup/shutdown sequences.

## Core Principle

**NEVER start/stop individual services when orchestration exists**

- MUST search for orchestration scripts: start.sh, launch.sh, stop.sh, docker-compose.yml
- MUST use orchestration for ALL service operations
- MUST follow sequence: Stop ALL → Change → Start ALL → Verify
- MUST test complete lifecycle

## Orchestration Discovery

### Step 1: Find Orchestration Scripts

```bash
# Search for orchestration files
fd -t f "(start|launch|stop|restart|run|up|down)\\.(sh|bash|py)"
fd "docker-compose.*\\.ya?ml"
fd "Makefile"
fd "(package|composer|Gemfile|requirements)"

# Check common locations
ls scripts/ | rg "(start|stop|launch)"
ls bin/ | rg "(start|stop|launch)"
ls . | rg "docker-compose"

# Check for process managers
rg "supervisor|systemd|pm2|forever" --type yaml --type json
```

### Step 2: Understand Dependencies

```python
def analyze_service_dependencies():
    """Map out service dependency graph."""

    dependencies = {}

    # Parse docker-compose.yml
    if Path("docker-compose.yml").exists():
        with open("docker-compose.yml") as f:
            compose = yaml.load(f)
            for service, config in compose.get('services', {}).items():
                dependencies[service] = config.get('depends_on', [])

    # Parse start scripts
    start_scripts = find_files("start*.sh")
    for script in start_scripts:
        deps = extract_service_order(script)
        dependencies.update(deps)

    return create_dependency_graph(dependencies)
```

## Service Management Patterns

### Docker Compose Orchestration

```bash
# ❌ WRONG - Starting individual containers
docker run -d postgres
docker run -d redis
docker run -d app

# ✅ CORRECT - Using orchestration
docker-compose up -d

# Full lifecycle management
docker-compose down  # Stop all
# Make changes
docker-compose up -d  # Start all
docker-compose ps  # Verify
```

### Script-Based Orchestration

```bash
# ❌ WRONG - Manual service starts
systemctl start postgresql
systemctl start redis
systemctl start nginx
npm start

# ✅ CORRECT - Using orchestration script
./scripts/start-all.sh

# Typical orchestration script structure
#!/bin/bash
# start-all.sh
echo "Starting infrastructure..."

# Start in dependency order
systemctl start postgresql
wait_for_service postgresql 5432

systemctl start redis
wait_for_service redis 6379

systemctl start elasticsearch
wait_for_service elasticsearch 9200

# Start application
npm start &
wait_for_service app 3000

echo "All services started successfully"
```

### Kubernetes Orchestration

```bash
# ❌ WRONG - Individual deployments
kubectl apply -f postgres-deployment.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f app-deployment.yaml

# ✅ CORRECT - Using orchestration
kubectl apply -f k8s/  # Apply all manifests
# OR
helm install myapp ./chart

# Proper lifecycle
kubectl delete -f k8s/  # Stop all
# Make changes
kubectl apply -f k8s/  # Start all
kubectl get pods  # Verify
```

## Service Lifecycle Management

### Complete Shutdown Sequence

```python
def shutdown_services_safely():
    """Shutdown services in reverse dependency order."""

    # Get dependency graph
    deps = get_service_dependencies()
    shutdown_order = topological_sort_reverse(deps)

    for service in shutdown_order:
        print(f"Stopping {service}...")

        # Graceful shutdown
        send_sigterm(service)
        if not wait_for_shutdown(service, timeout=30):
            print(f"Force stopping {service}")
            send_sigkill(service)

        # Verify stopped
        assert not is_running(service), f"{service} still running!"

    print("All services stopped")
```

### Complete Startup Sequence

```python
def start_services_safely():
    """Start services in dependency order with health checks."""

    # Get dependency graph
    deps = get_service_dependencies()
    startup_order = topological_sort(deps)

    started = []

    for service in startup_order:
        print(f"Starting {service}...")

        try:
            start_service(service)
            wait_for_healthy(service)
            started.append(service)
            print(f"✅ {service} is healthy")

        except Exception as e:
            print(f"❌ Failed to start {service}: {e}")
            # Rollback
            for s in reversed(started):
                stop_service(s)
            raise

    print("All services started successfully")
```

## Health Check Patterns

```python
def wait_for_healthy(service, timeout=60):
    """Wait for service to become healthy."""

    health_checks = {
        'postgres': lambda: check_postgres_connection(),
        'redis': lambda: check_redis_ping(),
        'elasticsearch': lambda: check_elastic_cluster(),
        'app': lambda: check_http_endpoint('/health'),
        'rabbitmq': lambda: check_amqp_connection(),
        'mongodb': lambda: check_mongo_connection()
    }

    check = health_checks.get(service)
    if not check:
        # Generic TCP check
        return wait_for_port(get_service_port(service))

    start = time.time()
    while time.time() - start < timeout:
        try:
            if check():
                return True
        except:
            pass
        time.sleep(1)

    raise TimeoutError(f"{service} not healthy after {timeout}s")
```

## Configuration Management

### Environment-Specific Orchestration

```bash
# Development
./scripts/dev/start.sh

# Staging
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up

# Production
kubectl apply -k overlays/production/
```

### Secret Management

```python
def load_secrets_before_start():
    """Load secrets from vault before starting services."""

    # ❌ WRONG - Hardcoded secrets
    os.environ['DB_PASSWORD'] = 'hardcoded_password'

    # ✅ CORRECT - Load from secret manager
    secrets = load_from_vault([
        'db/password',
        'redis/password',
        'api/keys/external'
    ])

    for key, value in secrets.items():
        os.environ[key] = value

    # Now safe to start services
    run_orchestration_script()
```

## Common Orchestration Files

### docker-compose.yml
```yaml
version: '3.8'
services:
  db:
    image: postgres:14
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  app:
    build: .
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: ./start.sh
```

### Makefile
```makefile
.PHONY: start stop restart status

start:
\t@echo "Starting all services..."
\t@docker-compose up -d
\t@./scripts/wait-for-healthy.sh
\t@echo "All services ready"

stop:
\t@echo "Stopping all services..."
\t@docker-compose down
\t@echo "All services stopped"

restart: stop start

status:
\t@docker-compose ps
\t@./scripts/health-check.sh
```

## Integration with BMAD

When working with BMAD workflows:
- Check workflow-manifest.csv for orchestration workflows
- Use task-manifest.csv for service task sequences
- Maintain consistency with existing orchestration patterns

## Scripts

### Orchestration Finder
See [scripts/find_orchestration.py](scripts/find_orchestration.py) - Discovers orchestration scripts

### Dependency Analyzer
See [scripts/analyze_dependencies.py](scripts/analyze_dependencies.py) - Maps service dependencies

## Critical Reminders

- **Never Skip Orchestration**: Individual commands break dependencies
- **Test Full Lifecycle**: Always test stop → start → verify
- **Health Checks Required**: Don't assume services are ready immediately
- **Rollback on Failure**: If any service fails, stop all and investigate''',
    },
    {
        "name": "file-organization",
        "description": "Enforces proper file placement standards for project organization. Use when: (1) Creating new files, (2) Generating documentation, (3) Adding scripts or tools, (4) Creating artifacts or reports, (5) Any file creation task. Ensures consistent project structure and prevents file sprawl.",
        "content": '''---
name: file-organization
description: Enforces proper file placement standards for project organization. Use when: (1) Creating new files, (2) Generating documentation, (3) Adding scripts or tools, (4) Creating artifacts or reports, (5) Any file creation task. Ensures consistent project structure and prevents file sprawl.
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
        content += f"| [{file}]({file}) | {desc} | {modified:%Y-%m-%d} |\\n"

    index_path.write_text(content)
```

## File Naming Conventions

```python
def enforce_naming_convention(file_name, file_type):
    """Ensure file follows naming conventions."""

    conventions = {
        'python': r'^[a-z_]+\\.py$',  # snake_case.py
        'javascript': r'^[a-z][a-zA-Z]+\\.(js|jsx)$',  # camelCase.js
        'typescript': r'^[a-z][a-zA-Z]+\\.(ts|tsx)$',  # camelCase.ts
        'markdown': r'^[a-z-]+\\.md$',  # kebab-case.md
        'config': r'^\\.[a-z]+rc$|^[a-z]+\\.config\\.(js|json)$'
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
- **Update Indexes**: Maintain directory documentation''',
    },
    {
        "name": "change-tracking",
        "description": "Ensures proper change documentation through CHANGELOG updates and commit tracking. Use when: (1) Before making commits, (2) After implementing features, (3) Preparing releases, (4) Documenting bug fixes, (5) Any significant code changes. Maintains project history and facilitates collaboration.",
        "content": '''---
name: change-tracking
description: Ensures proper change documentation through CHANGELOG updates and commit tracking. Use when: (1) Before making commits, (2) After implementing features, (3) Preparing releases, (4) Documenting bug fixes, (5) Any significant code changes. Maintains project history and facilitates collaboration.
---

# Change Tracking Protocol

This skill ensures all changes are properly documented through CHANGELOG maintenance and structured commit tracking.

## Core Principle

**Every change must be documented**

- ALWAYS update CHANGELOG before commits
- Format: Date + categorized changes
- Use conventional commit format
- Track breaking changes explicitly

## CHANGELOG Management

### Standard CHANGELOG Format

```markdown
# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security vulnerability fixes

## [1.2.0] - 2024-01-15

### Added
- User authentication system
- Email notification service
- API rate limiting

### Fixed
- Memory leak in data processor
- SQL injection vulnerability in search
```

### Update CHANGELOG Workflow

```python
def update_changelog(changes):
    """Update CHANGELOG with new changes."""

    changelog_path = Path("CHANGELOG.md")

    # Read existing content
    if changelog_path.exists():
        content = changelog_path.read_text()
    else:
        content = create_initial_changelog()

    # Parse sections
    sections = parse_changelog_sections(content)

    # Add new changes to Unreleased
    for change in changes:
        category = determine_category(change)
        sections['Unreleased'][category].append(
            f"- {change['description']}"
        )

    # Write updated changelog
    new_content = format_changelog(sections)
    changelog_path.write_text(new_content)

    print(f"✅ Updated CHANGELOG with {len(changes)} changes")
```

## Change Categories

```python
def determine_category(change):
    """Determine which CHANGELOG category a change belongs to."""

    keywords = {
        'Added': ['new', 'add', 'create', 'implement', 'introduce'],
        'Changed': ['update', 'modify', 'refactor', 'improve', 'enhance'],
        'Deprecated': ['deprecate', 'obsolete', 'phase out'],
        'Removed': ['remove', 'delete', 'drop', 'eliminate'],
        'Fixed': ['fix', 'resolve', 'repair', 'correct', 'patch'],
        'Security': ['security', 'vulnerability', 'CVE', 'exploit']
    }

    change_lower = change['description'].lower()

    for category, words in keywords.items():
        if any(word in change_lower for word in words):
            return category

    # Default to Changed if unclear
    return 'Changed'
```

## Commit Message Standards

### Conventional Commits Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types and Examples

```python
COMMIT_TYPES = {
    'feat': 'New feature for the user',
    'fix': 'Bug fix for the user',
    'docs': 'Documentation only changes',
    'style': 'Formatting, missing semicolons, etc',
    'refactor': 'Code change that neither fixes a bug nor adds a feature',
    'perf': 'Code change that improves performance',
    'test': 'Adding missing tests',
    'chore': 'Maintain. Changes to build process, etc',
    'revert': 'Reverts a previous commit',
    'build': 'Changes to build system or dependencies',
    'ci': 'Changes to CI configuration files'
}

# Examples
examples = [
    "feat(auth): add OAuth2 login support",
    "fix(api): resolve memory leak in data processor",
    "docs(readme): update installation instructions",
    "refactor(utils): simplify date formatting logic",
    "perf(search): optimize database queries",
    "test(user): add integration tests for registration",
    "chore(deps): update dependencies to latest versions",
    "build(docker): optimize container size",
    "ci(github): add automated testing workflow"
]
```

## Automated Change Detection

```python
def detect_changes_for_changelog():
    """Automatically detect changes for CHANGELOG update."""

    changes = []

    # Get uncommitted changes
    result = subprocess.run(
        ["git", "diff", "--name-status"],
        capture_output=True,
        text=True
    )

    for line in result.stdout.splitlines():
        status, file_path = line.split(None, 1)

        change = {
            'file': file_path,
            'status': status,
            'description': generate_change_description(status, file_path)
        }

        changes.append(change)

    # Group by feature/module
    grouped = group_changes_by_feature(changes)

    return grouped

def generate_change_description(status, file_path):
    """Generate human-readable change description."""

    # Analyze file content for context
    if status == 'A':
        return f"Add {describe_file_purpose(file_path)}"
    elif status == 'M':
        return f"Update {describe_file_purpose(file_path)}"
    elif status == 'D':
        return f"Remove {describe_file_purpose(file_path)}"
    else:
        return f"Modify {file_path}"
```

## Version Management

```python
def prepare_release(version):
    """Prepare a new release with proper change tracking."""

    # Move Unreleased to new version
    changelog = read_changelog()
    unreleased = changelog.get('Unreleased', {})

    if not any(unreleased.values()):
        raise ValueError("No unreleased changes to release")

    # Create new version entry
    today = datetime.now().strftime("%Y-%m-%d")
    changelog[f"{version} - {today}"] = unreleased
    changelog['Unreleased'] = create_empty_sections()

    # Write updated changelog
    write_changelog(changelog)

    # Create git tag
    subprocess.run(["git", "tag", "-a", version, "-m", f"Release {version}"])

    # Generate release notes
    release_notes = generate_release_notes(unreleased)

    return release_notes
```

## Breaking Changes Tracking

```python
def track_breaking_changes(change):
    """Special handling for breaking changes."""

    indicators = [
        'BREAKING CHANGE:',
        'BREAKING:',
        '!:',  # In commit type
        'incompatible',
        'migration required'
    ]

    if any(ind in change['description'] for ind in indicators):
        # Add to special breaking changes section
        add_to_breaking_changes(change)

        # Suggest major version bump
        current_version = get_current_version()
        suggested = suggest_version_bump(current_version, 'major')

        print(f"⚠️  BREAKING CHANGE detected!")
        print(f"Consider version bump: {current_version} → {suggested}")
```

## Integration with Git Hooks

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check if CHANGELOG was updated
if ! git diff --cached --name-only | grep -q "CHANGELOG.md"; then
    echo "⚠️  Warning: CHANGELOG.md not updated"
    echo "Have you documented your changes?"
    read -p "Continue without updating CHANGELOG? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
```

### Commit Message Validation

```python
def validate_commit_message(message):
    """Validate commit message follows conventions."""

    pattern = r'^(feat|fix|docs|style|refactor|perf|test|chore|revert|build|ci)(\\(.+\\))?: .+'

    lines = message.strip().split('\\n')
    if not lines:
        return False, "Empty commit message"

    if not re.match(pattern, lines[0]):
        return False, f"Invalid format. Expected: type(scope): subject"

    # Check for breaking changes
    if 'BREAKING' in message:
        if 'BREAKING CHANGE:' not in message:
            return False, "Breaking changes must use 'BREAKING CHANGE:' format"

    return True, "Valid commit message"
```

## Change Summary Generation

```python
def generate_change_summary(start_date=None, end_date=None):
    """Generate a summary of changes for a time period."""

    if not start_date:
        start_date = datetime.now() - timedelta(days=7)
    if not end_date:
        end_date = datetime.now()

    # Get commits in date range
    commits = get_commits_in_range(start_date, end_date)

    summary = {
        'period': f"{start_date:%Y-%m-%d} to {end_date:%Y-%m-%d}",
        'total_commits': len(commits),
        'contributors': set(),
        'changes_by_type': {},
        'files_changed': set()
    }

    for commit in commits:
        # Parse commit type
        commit_type = extract_commit_type(commit['message'])
        summary['changes_by_type'][commit_type] = \\
            summary['changes_by_type'].get(commit_type, 0) + 1

        # Track contributors
        summary['contributors'].add(commit['author'])

        # Track files
        summary['files_changed'].update(commit['files'])

    return format_summary_report(summary)
```

## Scripts

### CHANGELOG Updater
See [scripts/update_changelog.py](scripts/update_changelog.py) - Automated CHANGELOG updates

### Change Analyzer
See [scripts/analyze_changes.py](scripts/analyze_changes.py) - Analyzes uncommitted changes

## References

- Keep a Changelog: [references/keep_a_changelog.md](references/keep_a_changelog.md)
- Semantic Versioning: [references/semver.md](references/semver.md)

## Critical Reminders

- **Update Before Commit**: CHANGELOG should reflect current state
- **Be Specific**: Vague entries like "bug fixes" are useless
- **Track Breaking Changes**: Users need migration guidance
- **Maintain History**: Never delete old entries''',
    },
]


def create_skill(skill_info):
    """Create a single skill."""
    skill_name = skill_info["name"]
    skill_path = SKILLS_DIR / skill_name

    print(f"\nCreating {skill_name} skill...")

    # Initialize skill
    result = subprocess.run(
        [
            "python",
            str(SKILL_CREATOR_PATH / "scripts" / "init_skill.py"),
            skill_name,
            "--path",
            str(SKILLS_DIR),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Failed to initialize {skill_name}: {result.stderr}")
        return False

    # Write SKILL.md
    skill_md_path = skill_path / "SKILL.md"
    skill_md_path.write_text(skill_info["content"])

    # Clean up example files
    example_files = [
        skill_path / "scripts" / "example.py",
        skill_path / "references" / "api_reference.md",
        skill_path / "assets" / "example_asset.txt",
    ]

    trash_dir = SKILLS_DIR / "TRASH"
    trash_dir.mkdir(exist_ok=True)

    for example_file in example_files:
        if example_file.exists():
            new_name = f"{example_file.stem}_{skill_name}{example_file.suffix}"
            example_file.rename(trash_dir / new_name)

    print(f"✅ Created {skill_name} skill")
    return True


def main():
    """Create all remaining skills."""
    print("Creating Remaining Skills")
    print("=" * 40)

    success_count = 0
    for skill in SKILLS:
        if create_skill(skill):
            success_count += 1

    print(f"\n{'=' * 40}")
    print(f"✅ Successfully created {success_count}/{len(SKILLS)} skills")

    if success_count == len(SKILLS):
        print("\nAll skills created successfully!")
    else:
        print(f"\n⚠️  {len(SKILLS) - success_count} skills failed")


if __name__ == "__main__":
    main()
