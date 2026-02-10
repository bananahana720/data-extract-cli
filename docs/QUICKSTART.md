# Quickstart

This guide gets you from install to a complete local run using the current command surface.

## 1. Install

```bash
pip install .
```

Verify:

```bash
data-extract --version
data-extract --help
```

## 2. Process Documents (CLI)

Run the full pipeline (`extract -> normalize -> chunk -> output`):

```bash
data-extract process ./documents --output ./output --format json --non-interactive
```

Supported extensions: `.txt`, `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.csv`, `.tsv`.

Useful options:

```bash
# Only new/changed files
data-extract process ./documents --output ./output --incremental

# Resume an incomplete session
data-extract process ./documents --resume

# Retry failures from last session
data-extract retry --last

# Inspect corpus status and drift
data-extract status ./documents --output ./output --json
```

## 3. Launch Local UI

Start API + UI runtime:

```bash
data-extract ui
```

The command starts a local server (default `http://127.0.0.1:8765`) and opens the browser.
New Run defaults to `Local Path` mode. Switch to `Upload Files/Folder` when needed; only the selected source is submitted.
Inline validation enforces source requirements and chunk size minimum (`>= 32`).
From job details, use `Retry Failed`, `Cleanup Artifacts`, and `Copy Output Path` from the action panel.

Run startup checks only:

```bash
data-extract ui --check
```

## 4. Validate Installation

```bash
python scripts/validate_installation.py
```

When `DATA_EXTRACT_UI_HOME` is not set, validation uses a temporary runtime home outside the repo.
This verifies current CLI commands, a real process/status workflow, and UI startup checks.
