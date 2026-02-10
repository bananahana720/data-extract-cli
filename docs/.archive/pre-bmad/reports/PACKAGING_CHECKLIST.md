# Python Package Data Files - Quick Reference

## When to Update Package Configuration

Update these files whenever you:
- Add new data files (YAML, JSON, TXT, etc.)
- Add new directories with data files
- Change file extensions for data files

## Three Files to Keep in Sync

### 1. MANIFEST.in
Controls what goes into the source distribution (sdist).

```manifest
# Include data files
recursive-include src *.yaml
recursive-include src *.yml
recursive-include src *.json
recursive-include src *.txt
```

### 2. pyproject.toml
Primary packaging configuration for modern Python.

```toml
[tool.setuptools]
package-dir = {"" = "src"}
include-package-data = true

[tool.setuptools.package-data]
"*" = ["*.yaml", "*.yml", "*.json", "*.txt"]
infrastructure = ["*.yaml", "*.yml", "*.json"]
```

### 3. setup.py
Backward compatibility for older build systems.

```python
setup(
    include_package_data=True,
    package_data={
        '*': ['*.yaml', '*.yml', '*.json', '*.txt'],
        'infrastructure': ['*.yaml', '*.yml', '*.json'],
    },
)
```

## Quick Verification

### After Building
```bash
# Check wheel contents
python check_package_contents.py

# Or manually inspect
unzip -l dist/*.whl | grep -E '\.(yaml|json|txt)$'
```

### After Installing
```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# Install and test
pip install dist/*.whl
python -c "from pathlib import Path; import infrastructure; print(list(Path(infrastructure.__file__).parent.glob('*.yaml')))"

# Cleanup
deactivate
rm -rf test_env
```

## Common Patterns

### Add New File Type
```toml
# In pyproject.toml package-data
"*" = ["*.yaml", "*.yml", "*.json", "*.txt", "*.csv"]  # Added CSV
```

```manifest
# In MANIFEST.in
recursive-include src *.csv
```

```python
# In setup.py
package_data={'*': ['*.yaml', '*.yml', '*.json', '*.txt', '*.csv']}
```

### Add New Module with Data
```toml
# In pyproject.toml
[tool.setuptools.package-data]
"*" = ["*.yaml", "*.yml", "*.json", "*.txt"]
infrastructure = ["*.yaml", "*.yml", "*.json"]
new_module = ["*.yaml", "*.json"]  # Added new module
```

## Rebuild Process

```bash
# 1. Clean old builds
rm -rf dist/ build/ src/*.egg-info

# 2. Rebuild
python -m build

# 3. Verify
python check_package_contents.py

# 4. Test install
python -m venv test_env
test_env/Scripts/pip install dist/*.whl
test_env/Scripts/data-extract version
rm -rf test_env
```

## Troubleshooting

### Files Missing from Wheel
1. Check MANIFEST.in has `recursive-include src *.yaml`
2. Check pyproject.toml has package-data configuration
3. Check setup.py has package_data dictionary
4. Clean and rebuild: `rm -rf dist/ build/` then `python -m build`

### Warning: "no files found matching"
- Usually harmless if files truly don't exist
- Check if pattern matches actual files: `find src/ -name "*.yml"`

### import_resources vs __file__
Modern Python (3.9+) prefers importlib.resources:
```python
from importlib.resources import files
config_text = files('infrastructure').joinpath('error_codes.yaml').read_text()
```

Older approach (still works):
```python
from pathlib import Path
config_path = Path(__file__).parent / 'error_codes.yaml'
```

## Best Practices

1. ✅ Always include files in all three config files
2. ✅ Test installation in clean environment
3. ✅ Use wildcard patterns for consistency
4. ✅ Keep patterns in sync across files
5. ✅ Verify after every build

## References

- [Python Packaging Guide](https://packaging.python.org/en/latest/guides/using-manifest-in/)
- [setuptools Documentation](https://setuptools.pypa.io/en/latest/userguide/datafiles.html)
- [PEP 621 - pyproject.toml](https://peps.python.org/pep-0621/)
