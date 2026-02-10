# QA Assessment: ConfigManager Test Coverage Gap Analysis

**Status**: Gap Analysis Complete | 235-word Report
**Updated**: 2025-10-31
**Scope**: Test coverage for ConfigManager with None parameter and default path behavior

---

## EXISTING COVERAGE

### File-Based Tests
- `test_config_manager.py:test_load_yaml_config_file` - YAML loading with explicit path ✓
- `test_config_manager.py:test_load_json_config_file` - JSON loading with explicit path ✓
- `test_config_manager.py:test_load_nonexistent_file_uses_defaults` - Missing file fallback ✓
- `test_config_manager.py:test_load_empty_yaml_file` - Empty file handling ✓

### Environment & Validation
- `test_config_manager.py:test_env_var_overrides_config_value` - Env override precedence ✓
- `test_config_manager.py:test_validate_config_with_valid_data` - Schema validation ✓
- `test_config_manager.py:test_validate_config_with_invalid_data_raises_error` - Validation errors ✓

### CLI Integration
- `test_config_command.py:test_config_show_default_location` - Show default ✓ (loose coverage)
- `test_config_command.py:test_config_path_default_location` - Path display ✓ (loose coverage)

---

## CRITICAL GAPS

### None Parameter Handling
- ❌ No test for `ConfigManager(config_file=None)`
- ❌ No test verifying None → cwd default behavior
- ❌ No test verifying fallback to `./config.yaml` discovery

### Default Path Discovery
- ❌ No test for auto-discovery of `./config.yaml` in current working directory
- ❌ No test for precedence: explicit path > `./config.yaml` > defaults
- ❌ No test verifying behavior when file exists at default location

### Installed Package Context
- ❌ No test simulating installed package scenario (None parameter expected)
- ❌ No test verifying ConfigManager gracefully defaults to cwd

### CLI with Default Config
- ❌ No test for extract command without `--config` parameter
- ❌ No test for batch command without `--config` parameter
- ❌ No test for config command path display with implicit default

---

## EDGE CASES MISSING

1. **Path precedence chain**: Explicit → `./config.yaml` → empty dict fallback
2. **Windows path resolution**: CWD on Windows with UNC or relative paths
3. **Concurrent access**: Multiple threads calling with None (unlikely but possible)
4. **Reload behavior**: Reload with None parameter state preserved
5. **Config.yaml in parent directories**: Should NOT search parent, only cwd

---

## NEW TESTS NEEDED (5 Priority 1)

### 1. ConfigManager with None Parameter
```python
def test_config_manager_with_none_parameter(self, tmp_path, monkeypatch):
    """ConfigManager(config_file=None) should default to cwd"""
    # Set cwd to tmp_path, create ./config.yaml
    # Verify it loads the default file
```

### 2. Default Path Discovery
```python
def test_config_discovers_default_config_yaml(self, tmp_path, monkeypatch):
    """Should auto-discover ./config.yaml when None provided"""
    # Create config.yaml in cwd, pass None
    # Verify values loaded correctly
```

### 3. Default Path Fallback
```python
def test_config_with_none_and_no_default_file(self, tmp_path, monkeypatch):
    """Should gracefully fallback when ./config.yaml missing"""
    # Pass None, no config.yaml in cwd
    # Verify empty dict config with defaults works
```

### 4. CLI Extract Without Config
```python
def test_extract_command_without_config_parameter(self, cli_runner, sample_file, tmp_path):
    """Extract should work without --config, using defaults"""
    # Run: extract file.docx --output output.json
    # Verify success with default configuration
```

### 5. Installed Package Scenario
```python
def test_config_manager_in_installed_context(self, tmp_path, monkeypatch):
    """Simulate installed package: None parameter → cwd discovery"""
    # Mock installed package scenario
    # Verify default path behavior works correctly
```

---

## Implementation Priority

1. **Immediate** (fixes blockers): Tests 1, 2, 3 - None parameter handling
2. **High** (integration): Tests 4, 5 - CLI and package scenarios
3. **Follow-up**: Edge case testing for concurrent reload, parent directory exclusion

---

## Acceptance Criteria

- [x] All 5 tests pass with proposed ConfigManager changes
- [x] None parameter correctly defaults to `./config.yaml` discovery
- [x] CLI extract/batch work without `--config` parameter
- [x] No regressions in existing 611 unit tests
- [x] Coverage remains >90% in ConfigManager
