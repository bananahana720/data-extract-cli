# Scripts Refactoring Inventory - 2025-11-20

## Current Status

### ✅ Completed Refactorings

| Script | Original Lines | Refactored Lines | Date | Notes |
|--------|---------------|------------------|------|-------|
| scan_security.py | 1,064 | 127 + 16 modules | 2025-11-20 | Modular package structure |

### 🔴 Scripts Requiring Refactoring (>500 lines)

| Script | Lines | Priority | Complexity | Suggested Strategy |
|--------|-------|----------|------------|-------------------|
| **generate_fixtures.py** | 993 | **CRITICAL** | HIGH | Split by fixture type (PDF, HTML, CSV, JSON, etc.) |
| **manage_sprint_status.py** | 861 | **CRITICAL** | HIGH | Extract: status operations, reporting, validation, YAML handling |
| **generate_tests.py** | 793 | **HIGH** | MEDIUM | Separate test generation strategies by test type |
| **generate_docs.py** | 766 | **HIGH** | MEDIUM | Split by documentation type (API, user guide, technical) |
| **validate_performance.py** | 754 | **HIGH** | MEDIUM | Extract: metrics collection, benchmarks, reports, analysis |
| **setup_environment.py** | 748 | **MEDIUM** | LOW | Split setup phases (deps, config, validation) |
| **generate_story_template.py** | 736 | **MEDIUM** | LOW | Extract template types and generation logic |
| **init_claude_session.py** | 614 | **LOW** | LOW | Separate session management from initialization |
| **audit_dependencies.py** | 605 | **MEDIUM** | MEDIUM | Split audit checks by dependency type |
| **run_quality_gates.py** | 595 | **HIGH** | MEDIUM | Extract individual gate checks into modules |

### 📊 Refactoring Metrics

- **Total scripts > 500 lines**: 10 scripts
- **Total lines to refactor**: 7,669 lines
- **Average script size**: 767 lines
- **Target module size**: < 300 lines per module
- **Estimated modules needed**: ~40-50 modules

## Recommended Refactoring Sequence

### Phase 1: Critical Infrastructure (Week 1)
1. **generate_fixtures.py** (993 lines)
   - High impact on testing
   - Complex fixture generation logic
   - Multiple file format handlers

2. **manage_sprint_status.py** (861 lines)
   - Core project management tool
   - Complex YAML operations
   - Multiple status tracking functions

### Phase 2: Testing & Quality (Week 2)
3. **generate_tests.py** (793 lines)
   - Test generation strategies
   - Multiple test frameworks
   - Template-based generation

4. **run_quality_gates.py** (595 lines)
   - Quality enforcement
   - Multiple validation checks
   - Report generation

5. **validate_performance.py** (754 lines)
   - Performance metrics
   - Benchmark management
   - Analysis and reporting

### Phase 3: Documentation & Setup (Week 3)
6. **generate_docs.py** (766 lines)
   - Documentation generation
   - Multiple output formats
   - Template processing

7. **setup_environment.py** (748 lines)
   - Environment configuration
   - Dependency management
   - Validation checks

### Phase 4: Lower Priority (Week 4)
8. **generate_story_template.py** (736 lines)
   - Template management
   - Story generation
   - Format handling

9. **init_claude_session.py** (614 lines)
   - Session initialization
   - Configuration management
   - State handling

10. **audit_dependencies.py** (605 lines)
    - Dependency analysis
    - Security checks
    - Report generation

## Refactoring Patterns to Apply

### 1. Package Structure Pattern (from scan_security.py)
```
scripts/
├── script_name.py          # Thin orchestrator
└── package_name/           # Modular components
    ├── __init__.py
    ├── config.py           # Configuration
    ├── models.py           # Data models
    ├── orchestrator.py     # Main logic
    ├── operations/         # Core operations
    └── utils/              # Utilities
```

### 2. Separation Strategies
- **By Operation Type**: CRUD operations in separate modules
- **By Data Format**: One module per file format
- **By Feature**: Logical feature boundaries
- **By Responsibility**: Single responsibility per module

### 3. Common Extractions
- Configuration and constants → `config.py`
- Data models and classes → `models.py`
- File I/O operations → `utils/file_utils.py`
- CLI argument handling → `cli.py`
- Report generation → `reporters/`
- Validation logic → `validators/`

## Benefits Expected

### Immediate Benefits
- ✅ Pass quality gates (< 500 lines per file)
- ✅ Improved testability
- ✅ Easier maintenance
- ✅ Clear module boundaries

### Long-term Benefits
- ✅ Parallel development capability
- ✅ Reusable components
- ✅ Reduced cognitive load
- ✅ Plugin architecture potential

## Success Criteria

1. **No module exceeds 500 lines** (target: < 300)
2. **100% CLI compatibility maintained**
3. **All existing tests pass**
4. **Clear single responsibility per module**
5. **Consistent module structure across scripts**

## Risk Mitigation

1. **Test Coverage**: Run full test suite after each refactoring
2. **Backward Compatibility**: Keep original script as thin wrapper
3. **Documentation**: Update docs for new module structure
4. **Gradual Migration**: Refactor one script at a time
5. **Version Control**: Create feature branch for each refactoring
