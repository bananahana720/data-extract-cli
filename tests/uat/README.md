# UAT Testing Framework

User Acceptance Testing framework for CLI validation using tmux-cli.

**Story**: 5-0 UAT Testing Framework
**Epic**: 5 - Enhanced CLI UX & Batch Processing

## Overview

This framework provides automated UAT testing for the `data-extract` CLI by:
- Launching CLI commands in tmux panes
- Capturing terminal output (including Rich formatting)
- Validating UX components (panels, progress bars, tables)
- Running complete user journey tests

## Directory Structure

```
tests/uat/
├── __init__.py              # Package marker
├── conftest.py              # pytest fixtures (tmux_session, sample_corpus)
├── README.md                # This file
├── framework/               # Core testing framework
│   ├── __init__.py          # Exports all framework components
│   ├── tmux_wrapper.py      # TmuxSession class for tmux-cli
│   ├── ux_assertions.py     # Rich component assertions
│   └── journey_runner.py    # Journey orchestration
├── journeys/                # Journey test files
│   ├── __init__.py
│   ├── test_journey_1_first_time_setup.py
│   ├── test_journey_2_batch_processing.py
│   ├── test_journey_3_semantic_analysis.py
│   └── test_journey_4_learning_mode.py
└── fixtures/                # Test data
    ├── sample_corpus/       # 10+ test documents (PDF, DOCX, XLSX)
    ├── expected_outputs/    # Golden output templates
    └── generate_corpus.py   # Fixture generation script
```

## Prerequisites

### System Requirements
- **tmux**: Terminal multiplexer (pre-installed on Ubuntu runners)
- **tmux-cli**: CLI tool for tmux automation

### Installation

```bash
# Install tmux (Ubuntu/Debian)
sudo apt-get install tmux

# Install tmux-cli via uv
uv tool install tmux-cli

# Or install the package with dev dependencies
pip install -e ".[dev]"
```

### Windows/WSL
tmux is Unix/Linux only. On Windows, run UAT tests from WSL:
```bash
wsl
cd /mnt/c/path/to/project
pytest tests/uat/ -v
```

## Running Tests

### Run All UAT Tests
```bash
pytest tests/uat/ -v
```

### Run Specific Journey
```bash
pytest tests/uat/journeys/test_journey_3_semantic_analysis.py -v
```

### Run with Markers
```bash
# Run only UAT tests
pytest -m uat -v

# Run only journey tests
pytest -m journey -v

# Skip journey tests (run framework tests only)
pytest tests/uat/ -v -m "not journey"
```

### Run with Timeout
```bash
pytest tests/uat/ -v --timeout=300
```

## Framework Components

### TmuxSession

Context manager for tmux pane lifecycle:

```python
from tests.uat.framework import TmuxSession

with TmuxSession() as session:
    session.send("data-extract --help")
    session.wait_idle()
    output = session.capture()
    assert "process" in output
```

**Methods:**
- `launch(command)` - Start a command in new pane
- `send(text, enter=True)` - Send input to pane
- `capture()` - Get current pane output
- `wait_idle(idle_time=2.0)` - Wait for output to stabilize
- `kill()` - Terminate pane

### UX Assertions

Validate Rich terminal components:

```python
from tests.uat.framework import (
    assert_panel_displayed,
    assert_progress_bar_shown,
    assert_table_rendered,
    assert_color_present,
    strip_ansi,
)

output = session.capture()

# Panel validation
assert_panel_displayed(output, title="Analysis Summary")

# Progress bar validation
assert_progress_bar_shown(output)

# Table validation
assert_table_rendered(output, headers=["File", "Status", "Quality"])

# Color validation
assert_color_present(output, "green")  # Success color

# Strip ANSI codes for text matching
clean = strip_ansi(output)
assert "Complete" in clean
```

### JourneyRunner

Orchestrate multi-step journey tests:

```python
from tests.uat.framework import JourneyRunner, JourneyStep

steps = [
    JourneyStep(
        name="Launch CLI",
        command="data-extract --help",
        assertions=[lambda o: assert_contains(o, "process")],
    ),
    JourneyStep(
        name="Run Analysis",
        command="data-extract semantic analyze ./corpus/",
        assertions=[
            lambda o: assert_panel_displayed(o, "Analysis"),
            lambda o: assert_progress_bar_shown(o),
        ],
        timeout=60.0,
    ),
]

runner = JourneyRunner(session, steps)
results = runner.run_all()
print(runner.get_summary())
```

## Test Status

| Journey | Tests | Status |
|---------|-------|--------|
| Journey 1: First-Time Setup | 5 | Skipped (Story 5-1+) |
| Journey 2: Batch Processing | 5 | Skipped (Story 5-1+) |
| Journey 3: Semantic Analysis | 5 | Skipped (Story 5-1+) |
| Journey 4: Learning Mode | 5 | Skipped (Story 5-1+) |

Tests are marked `@pytest.mark.skip` until the corresponding CLI features are implemented in Stories 5-1 through 5-7.

## Sample Corpus

The `fixtures/sample_corpus/` directory contains 10 test documents:

| Type | Count | Files |
|------|-------|-------|
| PDF | 5 | Audit reports, compliance reviews, risk assessments |
| DOCX | 3 | Policies, procedures, project summaries |
| XLSX | 2 | Financial summaries, audit findings |

All files are:
- PII-free (synthetic content)
- Deterministic (reproducible)
- Enterprise-relevant (audit/compliance domain)

Regenerate corpus:
```bash
python tests/uat/fixtures/generate_corpus.py
```

## CI Integration

UAT tests run automatically on every PR via GitHub Actions:
- File: `.github/workflows/uat.yaml`
- Triggers: PR to main, push to main, manual dispatch
- Environment: Ubuntu with tmux pre-installed
- Timeout: 15 minutes

## Debugging

### Capture Screenshots
The framework can save terminal output for debugging:
```python
runner.capture_screenshot()  # Saves to tests/uat/screenshots/
```

### View Raw Output
```python
output = session.capture()
print(repr(output))  # Shows ANSI codes
print(strip_ansi(output))  # Clean text
```

### Manual tmux Inspection
```bash
# List tmux sessions
tmux list-sessions

# Attach to session
tmux attach -t <session-name>

# Kill all sessions
tmux kill-server
```

## Related Documentation

- [UX Design Specification](../../docs/ux-design-specification.md) - Journey definitions
- [tmux-cli Instructions](../../docs/tmux-cli-instructions.md) - tmux-cli usage guide
- [Epic 5 Tech Spec](../../docs/tech-spec-epic-5.md) - Technical specification
