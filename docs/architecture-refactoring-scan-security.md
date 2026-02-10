# Architecture - Security Scanner Refactoring

## Executive Summary

Refactoring scan_security.py (1,064 lines) into a modular, maintainable security scanning framework with clean separation of concerns, single responsibilities per module, and composition-based orchestration. The new architecture reduces all modules to <500 lines while preserving complete functionality.

## Decision Summary

| Category | Decision | Version | Affects Epics | Rationale |
| -------- | -------- | ------- | ------------- | --------- |
| Module Pattern | Decomposition by Responsibility | N/A | All | Each module handles one security scanning aspect |
| Package Structure | scripts/security/* hierarchy | N/A | All | Organized namespace for security components |
| Dependency Injection | Constructor injection | N/A | All | Testable, loosely coupled modules |
| Configuration | Centralized config module | N/A | All | Single source of truth for patterns/settings |
| Reporting | Strategy pattern for formats | N/A | All | Extensible report generation |
| Scanner Interface | Abstract base class | N/A | All | Consistent scanner implementation |
| CLI Preservation | Main orchestrator maintains interface | N/A | All | No breaking changes for users |
| Import Style | Relative imports within package | N/A | All | Clear internal vs external dependencies |

## Project Structure

```
scripts/
├── scan_security.py              # Main orchestrator (thin wrapper, <150 lines)
└── security/                      # Security scanning package
    ├── __init__.py               # Package initialization
    ├── config.py                 # Constants and configuration (~200 lines)
    ├── models.py                 # Data models (SecurityFinding, etc.) (~50 lines)
    ├── scanners/                 # Scanner implementations
    │   ├── __init__.py
    │   ├── base.py              # Abstract base scanner (~100 lines)
    │   ├── secrets.py           # Secrets detection (~300 lines)
    │   ├── dependencies.py      # Dependency vulnerability scanning (~250 lines)
    │   ├── permissions.py       # File permission validation (~150 lines)
    │   ├── sast.py             # SAST tool integration (~200 lines)
    │   └── history.py          # Git history scanning (~150 lines)
    ├── reporters/               # Report generation
    │   ├── __init__.py
    │   ├── base.py            # Abstract reporter (~50 lines)
    │   ├── markdown.py        # Markdown report generation (~150 lines)
    │   ├── json.py           # JSON report generation (~100 lines)
    │   └── console.py        # Console display (~150 lines)
    └── utils/                  # Shared utilities
        ├── __init__.py
        ├── file_utils.py      # File handling utilities (~100 lines)
        └── cache.py          # False positive caching (~100 lines)
```

## Module Breakdown

### Core Modules

#### 1. scan_security.py (Main Orchestrator)
- **Responsibility**: CLI interface and orchestration
- **Size**: ~150 lines
- **Functions**:
  - Parse command-line arguments
  - Initialize SecurityOrchestrator
  - Execute selected scans
  - Display results
  - Handle exit codes

#### 2. security/config.py
- **Responsibility**: Central configuration and constants
- **Size**: ~200 lines
- **Contains**:
  - SECRET_PATTERNS dictionary
  - SCAN_EXTENSIONS set
  - SENSITIVE_FILES dictionary
  - SEVERITY_LEVELS mapping
  - Directory paths (PROJECT_ROOT, REPORTS_DIR, etc.)

#### 3. security/models.py
- **Responsibility**: Data structures
- **Size**: ~50 lines
- **Contains**:
  - SecurityFinding dataclass
  - ScanStatistics dataclass

### Scanner Modules

#### 4. security/scanners/base.py
- **Responsibility**: Abstract scanner interface
- **Size**: ~100 lines
- **Provides**:
  - AbstractScanner base class
  - Common scanning methods
  - Finding collection interface

#### 5. security/scanners/secrets.py
- **Responsibility**: Secret and credential detection
- **Size**: ~300 lines
- **Methods**:
  - scan_with_patterns()
  - scan_with_gitleaks()
  - _should_scan_file()
  - _calculate_finding_hash()

#### 6. security/scanners/dependencies.py
- **Responsibility**: Vulnerable dependency detection
- **Size**: ~250 lines
- **Methods**:
  - scan_python_deps_safety()
  - scan_python_deps_pip_audit()
  - scan_npm_deps()
  - _map_cvss_to_severity()

#### 7. security/scanners/permissions.py
- **Responsibility**: File permission validation
- **Size**: ~150 lines
- **Methods**:
  - scan_sensitive_files()
  - validate_permission()
  - get_recommended_permissions()

#### 8. security/scanners/sast.py
- **Responsibility**: SAST tool integration
- **Size**: ~200 lines
- **Methods**:
  - scan_with_bandit()
  - scan_with_bandit_cli()
  - parse_sast_results()

#### 9. security/scanners/history.py
- **Responsibility**: Git history analysis
- **Size**: ~150 lines
- **Methods**:
  - scan_commits()
  - scan_commit_messages()
  - scan_diffs()

### Reporter Modules

#### 10. security/reporters/base.py
- **Responsibility**: Abstract reporter interface
- **Size**: ~50 lines
- **Provides**:
  - AbstractReporter base class
  - Report generation interface

#### 11. security/reporters/markdown.py
- **Responsibility**: Markdown report generation
- **Size**: ~150 lines
- **Methods**:
  - generate_report()
  - format_findings_section()
  - generate_recommendations()

#### 12. security/reporters/json.py
- **Responsibility**: JSON report generation
- **Size**: ~100 lines
- **Methods**:
  - generate_report()
  - serialize_findings()

#### 13. security/reporters/console.py
- **Responsibility**: Rich console output
- **Size**: ~150 lines
- **Methods**:
  - display_findings()
  - create_summary_panel()
  - create_findings_table()

### Utility Modules

#### 14. security/utils/file_utils.py
- **Responsibility**: File operations
- **Size**: ~100 lines
- **Functions**:
  - load_scanignore()
  - should_scan_file()
  - find_files_to_scan()

#### 15. security/utils/cache.py
- **Responsibility**: False positive management
- **Size**: ~100 lines
- **Functions**:
  - load_false_positives()
  - save_false_positives()
  - is_false_positive()

## Implementation Patterns

### Module Communication Pattern
```python
# Dependency injection for loose coupling
scanner = SecretsScanner(config=config, cache=cache_manager)
findings = scanner.scan(project_root)
reporter = MarkdownReporter(config=config)
report = reporter.generate(findings, stats)
```

### Scanner Implementation Pattern
```python
from security.scanners.base import AbstractScanner

class ConcreteScanner(AbstractScanner):
    def scan(self, project_root: Path) -> List[SecurityFinding]:
        """Implement scanning logic"""
        pass
```

### Error Handling Pattern
```python
try:
    result = scanner.scan()
except ScannerError as e:
    logger.error(f"Scanner failed: {e}")
    return []  # Graceful degradation
```

## Consistency Rules

### Import Convention
```python
# External imports
import json
from pathlib import Path

# Package imports
from security.models import SecurityFinding
from security.scanners.base import AbstractScanner

# Relative imports within module
from .utils import calculate_hash
```

### Naming Conventions
- Classes: PascalCase (SecurityScanner, MarkdownReporter)
- Functions/methods: snake_case (scan_secrets, generate_report)
- Constants: UPPER_SNAKE_CASE (SECRET_PATTERNS, SEVERITY_LEVELS)
- Private methods: Leading underscore (_internal_method)

### Module Size Limits
- No module exceeds 500 lines
- Prefer smaller, focused modules (100-300 lines)
- Split if approaching limit

## Migration Strategy

### Phase 1: Create Package Structure
```bash
mkdir -p scripts/security/scanners
mkdir -p scripts/security/reporters
mkdir -p scripts/security/utils
```

### Phase 2: Extract Modules
1. Extract models.py (SecurityFinding class)
2. Extract config.py (constants and patterns)
3. Extract base classes (AbstractScanner, AbstractReporter)
4. Extract scanner implementations
5. Extract reporter implementations
6. Extract utilities

### Phase 3: Update Main Script
1. Reduce scan_security.py to orchestration only
2. Import from new modules
3. Maintain CLI compatibility

### Phase 4: Validation
1. Run existing tests
2. Verify CLI interface unchanged
3. Compare output with original

## Testing Strategy

### Unit Testing
```python
# test_secrets_scanner.py
def test_pattern_detection():
    scanner = SecretsScanner(config=test_config)
    findings = scanner.scan_with_patterns(test_file)
    assert len(findings) == expected_count
```

### Integration Testing
```python
# test_orchestration.py
def test_full_security_scan():
    orchestrator = SecurityOrchestrator()
    findings = orchestrator.run_all_scans()
    assert findings  # Verify complete pipeline
```

## Benefits of Refactoring

1. **Maintainability**: Each module has single responsibility
2. **Testability**: Modules can be tested in isolation
3. **Extensibility**: Easy to add new scanners/reporters
4. **Readability**: Clear module boundaries and purposes
5. **Reusability**: Modules can be imported independently
6. **Performance**: Lazy loading of optional dependencies
7. **Quality Gates**: All modules under 500 lines (Ruff compliance)

## Architecture Decision Records (ADRs)

### ADR-001: Package-Based Decomposition
**Decision**: Use package structure (scripts/security/*) instead of flat modules
**Rationale**: Provides namespace isolation and logical grouping
**Consequences**: Requires __init__.py files but improves organization

### ADR-002: Abstract Base Classes
**Decision**: Use ABC for scanners and reporters
**Rationale**: Ensures consistent interface across implementations
**Consequences**: Slight overhead but enforces contracts

### ADR-003: Preserve CLI Interface
**Decision**: Keep scan_security.py as thin orchestrator
**Rationale**: No breaking changes for existing users/scripts
**Consequences**: Main script becomes a facade

### ADR-004: Composition Over Inheritance
**Decision**: Use composition for scanner orchestration
**Rationale**: More flexible than deep inheritance hierarchies
**Consequences**: Explicit dependency management required

---

_Generated by BMAD Decision Architecture Workflow v1.0_
_Date: 2025-11-20_
_For: Wave 4 Refactoring Sprint_
