# Configuration Guide

**Last Updated**: 2025-10-29 (Wave 2 - Agent 1: ConfigManager)

Comprehensive guide to configuration management for the data extraction tool.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration Files](#configuration-files)
- [Environment Variables](#environment-variables)
- [Priority and Overrides](#priority-and-overrides)
- [Validation](#validation)
- [API Reference](#api-reference)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Basic Usage

```python
from infrastructure import ConfigManager

# Load configuration from file
config = ConfigManager("config.yaml")

# Access configuration values
log_level = config.get("logging.level")
max_workers = config.get("general.max_workers", default=4)

# Get entire section
extractor_config = config.get_section("extractors.docx")

# Check if key exists
if config.has("extractors.pdf.use_ocr"):
    use_ocr = config.get("extractors.pdf.use_ocr")
```

### With Defaults

```python
# Provide default configuration
defaults = {
    "logging": {
        "level": "INFO",
        "format": "%(message)s"
    },
    "general": {
        "max_workers": 4
    }
}

config = ConfigManager("config.yaml", defaults=defaults)

# Missing keys fall back to defaults
log_level = config.get("logging.level")  # Returns "INFO" if not in file
```

### With Environment Variables

```python
# Environment variables override file configuration
# Set: DATA_EXTRACTOR_LOGGING_LEVEL=DEBUG

config = ConfigManager("config.yaml", env_prefix="DATA_EXTRACTOR")

# Returns "DEBUG" from environment variable
log_level = config.get("logging.level")
```

### With Validation

```python
from pydantic import BaseModel, Field

class AppConfig(BaseModel):
    logging: dict
    extractors: dict

# Validates configuration against schema
config = ConfigManager("config.yaml", schema=AppConfig)
```

---

## Configuration Files

### Supported Formats

ConfigManager supports YAML and JSON configuration files:

**YAML** (Recommended)
```yaml
logging:
  level: INFO
  format: "%(asctime)s - %(message)s"

extractors:
  docx:
    max_paragraph_length: 1000
    skip_empty: true
```

**JSON**
```json
{
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(message)s"
  },
  "extractors": {
    "docx": {
      "max_paragraph_length": 1000,
      "skip_empty": true
    }
  }
}
```

### File Location

By default, ConfigManager looks for configuration files in:
1. Path specified in constructor
2. Current working directory
3. User home directory (`~/.config/data-extractor/`)

```python
# Explicit path
config = ConfigManager("/path/to/config.yaml")

# Relative path
config = ConfigManager("./config/config.yaml")

# From package
from pathlib import Path
config_path = Path(__file__).parent / "config.yaml"
config = ConfigManager(config_path)
```

### Example Configuration

See `src/infrastructure/config_schema.yaml` for a complete example with all supported options and documentation.

---

## Environment Variables

Environment variables provide runtime overrides for configuration values without modifying files.

### Naming Convention

Environment variables use the format:
```
<PREFIX>_<SECTION>_<SUBSECTION>_<KEY>
```

Where:
- `PREFIX`: Set via `env_prefix` parameter (e.g., `DATA_EXTRACTOR`)
- Sections/keys: Uppercase with underscores

### Examples

**Configuration File:**
```yaml
logging:
  level: INFO

extractors:
  docx:
    skip_empty: true
    max_paragraph_length: 1000
```

**Environment Variable Overrides:**
```bash
# Override log level
export DATA_EXTRACTOR_LOGGING_LEVEL=DEBUG

# Override extractor settings
export DATA_EXTRACTOR_EXTRACTORS_DOCX_SKIP_EMPTY=false
export DATA_EXTRACTOR_EXTRACTORS_DOCX_MAX_PARAGRAPH_LENGTH=500

# Add new configuration
export DATA_EXTRACTOR_NEW_SETTING=value
```

### Type Coercion

Environment variables are automatically converted to appropriate types:

| String Value | Python Type | Example |
|--------------|-------------|---------|
| `true`, `yes` | `bool` (True) | `ENABLE_FEATURE=true` |
| `false`, `no` | `bool` (False) | `ENABLE_FEATURE=false` |
| `42` | `int` | `MAX_WORKERS=42` |
| `3.14` | `float` | `THRESHOLD=3.14` |
| Other | `str` | `NAME=my-app` |

### Handling Underscores in Keys

ConfigManager intelligently handles keys that contain underscores:

```yaml
# Configuration file with underscore in key name
extractors:
  docx:
    skip_empty: true
```

```bash
# Environment variable correctly overrides despite underscores
export DATA_EXTRACTOR_EXTRACTORS_DOCX_SKIP_EMPTY=false
```

The smart path matching algorithm:
1. Loads file configuration first
2. Detects existing keys (like `skip_empty`)
3. Matches environment variable paths against existing structure
4. Preserves underscore-containing keys correctly

---

## Priority and Overrides

Configuration values are resolved with the following priority (highest to lowest):

1. **Environment Variables** - Runtime overrides
2. **Configuration File** - Project-specific settings
3. **Defaults** - Fallback values provided in code

### Example

```python
# 1. Define defaults
defaults = {
    "logging": {
        "level": "INFO",
        "format": "%(message)s"
    }
}

# 2. Load from file (overrides defaults)
# config.yaml contains:
#   logging:
#     level: DEBUG

# 3. Environment variables override all
# export DATA_EXTRACTOR_LOGGING_LEVEL=ERROR

config = ConfigManager(
    "config.yaml",
    defaults=defaults,
    env_prefix="DATA_EXTRACTOR"
)

# Result: level="ERROR" (from environment)
# Result: format="%(message)s" (from defaults, not in file or env)
log_level = config.get("logging.level")  # "ERROR"
log_format = config.get("logging.format")  # "%(message)s"
```

### Merging Behavior

Configuration sections are **deep merged**:

```python
# Defaults
defaults = {
    "extractors": {
        "docx": {
            "skip_empty": true,
            "extract_styles": true,
            "max_paragraph_length": 1000
        }
    }
}

# File overrides only specific keys
# config.yaml:
#   extractors:
#     docx:
#       skip_empty: false

# Result: Deep merge preserves non-overridden keys
config = ConfigManager("config.yaml", defaults=defaults)

config.get("extractors.docx.skip_empty")  # false (from file)
config.get("extractors.docx.extract_styles")  # true (from defaults)
config.get("extractors.docx.max_paragraph_length")  # 1000 (from defaults)
```

---

## Validation

ConfigManager integrates with Pydantic for schema validation.

### Defining a Schema

```python
from pydantic import BaseModel, Field

class LoggingConfig(BaseModel):
    level: str = Field("INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: str = "%(message)s"

class ExtractorConfig(BaseModel):
    max_paragraph_length: int | None = Field(None, ge=1)
    skip_empty: bool = True

class AppConfig(BaseModel):
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    extractors: dict[str, ExtractorConfig] = Field(default_factory=dict)
```

### Using Validation

```python
from infrastructure import ConfigManager, ConfigurationError

try:
    config = ConfigManager("config.yaml", schema=AppConfig)
except ConfigurationError as e:
    print(f"Configuration validation failed: {e}")
    # Handle error appropriately
```

### Validation Errors

Pydantic provides detailed validation errors:

```python
# config.yaml with invalid value:
#   logging:
#     level: INVALID_LEVEL  # Not in allowed values

try:
    config = ConfigManager("config.yaml", schema=AppConfig)
except ConfigurationError as e:
    # Error message includes:
    # - Field name (logging.level)
    # - Invalid value (INVALID_LEVEL)
    # - Validation rule (must match pattern)
    # - Allowed values (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    print(e)
```

---

## API Reference

### ConfigManager Class

```python
class ConfigManager:
    """Thread-safe configuration manager."""

    def __init__(
        self,
        config_file: Path | str,
        schema: Type[BaseModel] | None = None,
        defaults: dict | None = None,
        env_prefix: str | None = None
    ):
        """
        Initialize configuration manager.

        Args:
            config_file: Path to YAML or JSON configuration file
            schema: Optional Pydantic model for validation
            defaults: Default configuration values
            env_prefix: Prefix for environment variable overrides
        """
```

### Methods

#### `get(path: str, default: Any = None) -> Any`

Get configuration value by dot-separated path.

```python
# Get simple value
level = config.get("logging.level")

# Get with default
workers = config.get("general.max_workers", default=4)

# Get nested value
length = config.get("extractors.docx.max_paragraph_length")
```

**Raises:** `ConfigurationError` if path not found and no default provided

---

#### `get_section(path: str, default: dict | None = None) -> dict`

Get configuration section as dictionary.

```python
# Get entire section
docx_config = config.get_section("extractors.docx")
# Returns: {"skip_empty": true, "extract_styles": true, ...}

# Use section values
for key, value in docx_config.items():
    print(f"{key}: {value}")
```

**Raises:** `ConfigurationError` if path is not a dictionary section

---

#### `has(path: str) -> bool`

Check if configuration key exists.

```python
if config.has("extractors.pdf.use_ocr"):
    use_ocr = config.get("extractors.pdf.use_ocr")
else:
    use_ocr = False  # Default behavior
```

---

#### `get_all() -> dict`

Get complete configuration as dictionary.

```python
# Get all configuration
all_config = config.get_all()

# Returns copy (safe to modify without affecting ConfigManager)
all_config["new_key"] = "value"  # Does not affect config
```

---

#### `reload() -> None`

Reload configuration from file.

```python
# Initial load
config = ConfigManager("config.yaml")

# ... file is modified externally ...

# Reload to pick up changes
config.reload()

# New values are now available
updated_level = config.get("logging.level")
```

---

### ConfigurationError Exception

```python
class ConfigurationError(Exception):
    """Raised when configuration loading or validation fails."""
```

**Common scenarios:**
- File not found or unreadable
- Invalid YAML/JSON syntax
- Validation failure (when using schema)
- Missing required key (when accessing without default)

---

## Common Patterns

### Pattern 1: Application Initialization

```python
from pathlib import Path
from infrastructure import ConfigManager

# Load configuration early in application lifecycle
def initialize_app():
    # Look for config file
    config_file = Path("config.yaml")

    # Use defaults if file not found
    defaults = {
        "logging": {"level": "INFO"},
        "general": {"max_workers": 4}
    }

    # Create config manager
    config = ConfigManager(
        config_file,
        defaults=defaults,
        env_prefix="DATA_EXTRACTOR"
    )

    # Return for use throughout application
    return config
```

### Pattern 2: Module-Specific Configuration

```python
class DocxExtractor:
    """Extractor that uses configuration."""

    def __init__(self, config: ConfigManager):
        # Get module-specific configuration
        self.config = config.get_section("extractors.docx")

        # Extract specific settings with defaults
        self.max_length = self.config.get("max_paragraph_length", None)
        self.skip_empty = self.config.get("skip_empty", True)
        self.extract_styles = self.config.get("extract_styles", True)
```

### Pattern 3: Environment-Specific Configuration

```python
# Development environment
# .env.development:
#   DATA_EXTRACTOR_LOGGING_LEVEL=DEBUG
#   DATA_EXTRACTOR_PERFORMANCE_ENABLE_CACHE=false

# Production environment
# .env.production:
#   DATA_EXTRACTOR_LOGGING_LEVEL=WARNING
#   DATA_EXTRACTOR_PERFORMANCE_ENABLE_CACHE=true

# Load environment variables from file
from dotenv import load_dotenv

# Load appropriate .env file
env = os.getenv("ENVIRONMENT", "development")
load_dotenv(f".env.{env}")

# ConfigManager picks up environment variables
config = ConfigManager("config.yaml", env_prefix="DATA_EXTRACTOR")
```

### Pattern 4: Configuration Testing

```python
import pytest
from infrastructure import ConfigManager

def test_extractor_with_custom_config(tmp_path):
    """Test extractor with custom configuration."""

    # Create temporary config file
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
    extractors:
      docx:
        max_paragraph_length: 500
        skip_empty: false
    """)

    # Load config and create extractor
    config = ConfigManager(config_file)
    extractor = DocxExtractor(config)

    # Test with custom configuration
    assert extractor.max_length == 500
    assert extractor.skip_empty is False
```

### Pattern 5: Dynamic Reload

```python
import signal
from infrastructure import ConfigManager

# Global config
config = None

def reload_config_handler(signum, frame):
    """Reload configuration on SIGHUP."""
    print("Reloading configuration...")
    config.reload()
    print("Configuration reloaded")

# Initialize
config = ConfigManager("config.yaml")

# Register signal handler
signal.signal(signal.SIGHUP, reload_config_handler)

# Application continues...
# Send SIGHUP to reload: kill -HUP <pid>
```

---

## Troubleshooting

### Issue: Configuration file not found

**Error:**
```
File not found: config.yaml
```

**Solutions:**
1. Check file path is correct (absolute or relative to working directory)
2. Verify file exists: `ls -la config.yaml`
3. Use absolute path: `Path(__file__).parent / "config.yaml"`
4. Provide defaults so missing file is non-fatal

### Issue: Environment variable not overriding

**Problem:**
```bash
export DATA_EXTRACTOR_LOGGING_LEVEL=DEBUG
# But config.get("logging.level") returns "INFO"
```

**Solutions:**
1. Verify `env_prefix` parameter matches: `ConfigManager(..., env_prefix="DATA_EXTRACTOR")`
2. Check environment variable is set: `echo $DATA_EXTRACTOR_LOGGING_LEVEL`
3. Ensure variable format is correct (uppercase, underscores)
4. Restart application (environment variables loaded at startup)

### Issue: KeyError on configuration access

**Error:**
```
ConfigurationError: Configuration key not found: extractors.unknown
```

**Solutions:**
1. Provide default value: `config.get("extractors.unknown", default={})`
2. Check key exists first: `if config.has("extractors.unknown"): ...`
3. Fix key name (check for typos)
4. Ensure configuration file has required keys

### Issue: Validation failure

**Error:**
```
ConfigurationError: Configuration validation failed:
1 validation error for AppConfig
logging -> level
  string does not match regex "^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
```

**Solutions:**
1. Check configuration value matches schema constraints
2. Fix invalid value in config file
3. Update schema to accept current values
4. Use environment variable to override: `DATA_EXTRACTOR_LOGGING_LEVEL=INFO`

### Issue: Type mismatch

**Problem:**
```python
# Config file has: max_workers: "4" (string)
workers = config.get("general.max_workers")
# Expected int, got str
```

**Solutions:**
1. Environment variables are auto-coerced, but file values are not
2. Fix config file to use correct type: `max_workers: 4` (no quotes)
3. Use pydantic schema for automatic type coercion
4. Cast explicitly: `int(config.get("general.max_workers"))`

### Issue: Nested key with underscore not found

**Problem:**
```yaml
extractors:
  docx:
    skip_empty: true
```

```bash
export DATA_EXTRACTOR_EXTRACTORS_DOCX_SKIP_EMPTY=false
# But value is still true
```

**Solution:**
This should work automatically. If not:
1. Verify config file loaded before environment variables
2. Check environment variable is set correctly
3. Ensure `env_prefix` matches
4. File bug report - this is handled by smart path matching

### Debugging Configuration

Enable debug logging to see configuration resolution:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

config = ConfigManager("config.yaml", env_prefix="DATA_EXTRACTOR")

# View final configuration
print(config.get_all())
```

---

## Best Practices

### 1. Use YAML for Human-Editable Config

YAML is more readable and supports comments:

```yaml
# Application configuration
logging:
  level: INFO  # Can be DEBUG, INFO, WARNING, ERROR
```

### 2. Provide Sensible Defaults

Always provide defaults so application works without configuration file:

```python
defaults = {
    "logging": {"level": "INFO"},
    "general": {"max_workers": 4}
}

config = ConfigManager("config.yaml", defaults=defaults)
```

### 3. Use Environment Variables for Secrets

Never commit secrets to configuration files:

```yaml
# config.yaml - NO SECRETS
database:
  host: "localhost"
  port: 5432
  # username and password from environment
```

```bash
# Environment variables
export DATA_EXTRACTOR_DATABASE_USERNAME=admin
export DATA_EXTRACTOR_DATABASE_PASSWORD=secret
```

### 4. Validate Early

Use pydantic schemas to catch configuration errors at startup:

```python
config = ConfigManager("config.yaml", schema=AppConfig)
# Fails fast if configuration invalid
```

### 5. Document Configuration Options

Include comments in config schema file explaining each option:

```yaml
extractors:
  docx:
    # Maximum characters per paragraph before truncation
    # Set to null for no limit
    max_paragraph_length: 1000

    # Skip paragraphs with no text content
    skip_empty: true
```

### 6. Use Dot Notation Consistently

```python
# Consistent style
level = config.get("logging.level")
format = config.get("logging.format")

# Not mixed styles
level = config.get("logging.level")
format = config.get_section("logging")["format"]
```

### 7. Check Keys Before Access

For optional configuration:

```python
if config.has("feature.experimental"):
    enable = config.get("feature.experimental")
else:
    enable = False
```

Or use defaults:

```python
enable = config.get("feature.experimental", default=False)
```

---

## Advanced Topics

### Thread Safety

ConfigManager is thread-safe for concurrent reads and reloads:

```python
from threading import Thread

def worker():
    # Safe: Multiple threads can read concurrently
    level = config.get("logging.level")

# Multiple workers
threads = [Thread(target=worker) for _ in range(10)]
for t in threads:
    t.start()
```

### Custom Type Coercion

For complex types, use pydantic schema:

```python
from pydantic import BaseModel, field_validator

class LoggingConfig(BaseModel):
    level: str
    handlers: list[str]

    @field_validator('handlers', mode='before')
    def parse_handlers(cls, v):
        if isinstance(v, str):
            return v.split(',')
        return v
```

### Configuration Inheritance

Layer configurations for different environments:

```python
# Load base configuration
base_config = ConfigManager("config.base.yaml").get_all()

# Load environment-specific overrides
env_config = ConfigManager("config.production.yaml").get_all()

# Merge (env overrides base)
config = ConfigManager("config.yaml", defaults=base_config)
```

---

## Migration Guide

### From Dict-Based Configuration

**Before:**
```python
config = {
    "max_paragraph_length": 1000,
    "skip_empty": True
}

extractor = DocxExtractor(config=config)
```

**After:**
```python
config_manager = ConfigManager("config.yaml")
extractor_config = config_manager.get_section("extractors.docx")

extractor = DocxExtractor(config=extractor_config)
```

### From Environment Variables Only

**Before:**
```python
import os

log_level = os.getenv("LOG_LEVEL", "INFO")
max_workers = int(os.getenv("MAX_WORKERS", "4"))
```

**After:**
```python
defaults = {
    "logging": {"level": "INFO"},
    "general": {"max_workers": 4}
}

config = ConfigManager(
    "config.yaml",
    defaults=defaults,
    env_prefix="DATA_EXTRACTOR"
)

log_level = config.get("logging.level")
max_workers = config.get("general.max_workers")
```

---

## Further Reading

- `src/infrastructure/config_schema.yaml` - Complete configuration schema
- `tests/test_infrastructure/test_config_manager.py` - Test examples
- `src/infrastructure/config_manager.py` - Implementation details

---

**Questions or Issues?**

- Check [Troubleshooting](#troubleshooting) section
- Review [Common Patterns](#common-patterns)
- Consult test examples for usage patterns
- File issue if you find a bug

---

**Last Updated**: 2025-10-29 | **Version**: 1.0.0 | **Wave**: 2 (Infrastructure)
