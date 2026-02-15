# Epic 5 Technical Specification - Enhanced CLI UX & Batch Processing

**Epic ID**: Epic 5
**Epic Type**: Feature Epic (CLI Experience Enhancement)
**Dependencies**: Epic 4 (complete), UX design directions (complete)
**Owner**: PM (John) + Dev (Charlie, Elena) + QA (Dana)
**Status**: Specification Draft - Ready for Story Implementation
**Created**: 2025-11-25
**Last Updated**: 2025-11-25 (created from Epic 4 retrospective planning)

---

## 1. Overview & Purpose

### 1.1 Epic Goal

Epic 5 transforms the data-extraction-tool CLI from functional to professional-grade, implementing the **"Tool as Teacher"** philosophy defined in the UX Design Specification. This epic delivers rich interactive feedback, configuration management, error recovery, and batch optimization.

### 1.2 Value Proposition

**User Experience Transformation:**
- From: Command-line tool with basic output
- To: Interactive CLI with Rich panels, progress bars, and contextual help

**Key Capabilities:**
1. **Pre-flight Validation**: See issues before processing starts
2. **Progress Feedback**: Real-time status for long operations
3. **Error Recovery**: Graceful handling with resume capability
4. **Configuration Presets**: Reproducible workflows
5. **Incremental Processing**: Only process changed files

### 1.3 Strategic Foundation

**UX Design Specification**: `docs/ux-design-directions.html`
- 7 user journeys defined with UAT assertions
- Component library (Rich panels, progress bars, tables)
- Git-style subcommand pattern

**UAT Testing Strategy**: tmux-cli automation
- Every PR validates UX compliance
- Automated journey testing
- Rich component detection

---

## 2. Scope & Deliverables

### 2.1 Stories Overview

| Story | Title | Priority | Dependencies |
|-------|-------|----------|--------------|
| 5-0 | UAT Testing Framework | P0 | None (foundation) |
| 5-1 | Refactored Command Structure | P0 | 5-0 |
| 5-2 | Configuration Management System | P1 | 5-0 |
| 5-3 | Real-Time Progress Indicators | P1 | 5-0 |
| 5-4 | Summary Statistics and Reporting | P1 | 5-0, 5-3 |
| 5-5 | Preset Configurations | P2 | 5-0, 5-2 |
| 5-6 | Graceful Error Handling | P1 | 5-0 |
| 5-7 | Batch Processing Optimization | P2 | 5-0, 5-1 |

### 2.2 User Journeys (from UX Spec)

| Journey | Description | Primary Story |
|---------|-------------|---------------|
| 1 | First-Time Setup | 5-1, 5-2 |
| 2 | Batch Processing | 5-3, 5-4 |
| 3 | Semantic Analysis | 5-4 (extends Epic 4) |
| 4 | Learning Mode | 5-1 |
| 5 | Preset Configuration | 5-5 |
| 6 | Error Recovery | 5-6 |
| 7 | Incremental Batch Updates | 5-7 |

### 2.3 Success Criteria

Epic 5 is complete when:
1. All 8 stories delivered and passing quality gates
2. All 7 UAT journey tests pass on every PR
3. CLI achieves "Tool as Teacher" UX goals
4. Performance maintained (<5s startup, <100ms response)
5. Error recovery enables session resume
6. Preset configurations reproducible

### 2.4 Out of Scope

- Full TUI application (Textual) - deferred to future epic
- GUI or web interface
- Real-time streaming (batch mode only)
- Multi-language CLI messages

---

## 3. Architecture & Design

### 3.1 CLI Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    data-extract CLI                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Commands  │  │   Config    │  │   Output    │          │
│  │   (Typer)   │  │   Cascade   │  │   (Rich)    │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
│         │                │                │                  │
│         ▼                ▼                ▼                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Command Router                          │    │
│  │  • process, extract, analyze, report                │    │
│  │  • config, cache, validate                          │    │
│  │  • semantic (from Epic 4)                           │    │
│  └─────────────────────────────────────────────────────┘    │
│         │                │                │                  │
│         ▼                ▼                ▼                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Pre-flight │  │  Progress   │  │  Error      │          │
│  │  Validation │  │  Tracking   │  │  Recovery   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Configuration Cascade

```
Priority (highest to lowest):
1. CLI arguments (--option=value)
2. Environment variables (DATA_EXTRACT_OPTION)
3. Project config (.data-extract.yaml)
4. User config (~/.data-extract/config.yaml)
5. Preset config (~/.data-extract/presets/*.yaml)
6. Defaults (hardcoded)
```

### 3.3 Progress Tracking Architecture

```python
# Rich Progress integration pattern
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
) as progress:
    task = progress.add_task("Processing files...", total=len(files))
    for file in files:
        process_file(file)
        progress.update(task, advance=1)
```

### 3.4 Error Recovery Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Error Recovery Flow                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Processing Start                                            │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────┐                                            │
│  │ Create      │  → .data-extract-session/                  │
│  │ Session     │     └── session-{timestamp}.json           │
│  └─────────────┘                                            │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────┐     ┌─────────────┐                        │
│  │ Process     │ ──► │ Update      │  (after each file)     │
│  │ File        │     │ Progress    │                        │
│  └─────────────┘     └─────────────┘                        │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────┐                                            │
│  │ Error?      │                                            │
│  └──────┬──────┘                                            │
│    Yes  │  No                                               │
│         ▼                                                    │
│  ┌─────────────┐     ┌─────────────┐                        │
│  │ Prompt User │     │ Continue    │                        │
│  │ (Skip/Stop/ │     │ Processing  │                        │
│  │  Retry)     │     └─────────────┘                        │
│  └─────────────┘                                            │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────┐                                            │
│  │ Save State  │  → Enables resume on next run              │
│  └─────────────┘                                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Story Specifications

### 4.1 Story 5-0: UAT Testing Framework

**File**: `tests/uat/README.md`

**Purpose**: Foundation story that enables automated validation of all subsequent CLI work.

**Key Deliverables**:
- `tests/uat/` directory structure
- `TmuxSession` wrapper for tmux-cli
- `UXAssertion` engine for Rich component detection
- Journey tests for Journeys 1-4
- GitHub Actions CI integration

**Blocks**: All other Epic 5 stories

### 4.2 Story 5-1 through 5-7

See story tracking in `docs/epics.md` and implementation details in this specification.

**Story Creation Pattern**:
```bash
# Use story template generator from Epic 3.5
python scripts/generate_story_template.py \
  --epic 5 \
  --story-num 1 \
  --title "Refactored Command Structure with Pipeline Support"
```

---

## 5. Technical Requirements

### 5.1 Dependencies

**Existing (from Epic 4)**:
- Typer (type-safe CLI - primary framework per ADR-001)
- Rich (terminal formatting)
- Click (internal dependency of Typer)

**New Dependencies**:
- InquirerPy (interactive prompts) - optional
- tmux-cli (UAT testing) - dev dependency

### 5.2 Performance Requirements

| Metric | Requirement |
|--------|-------------|
| CLI startup time | <2 seconds |
| Command response | <100ms (excluding processing) |
| Progress update frequency | ~10 updates/second max |
| Memory overhead | <50MB for CLI infrastructure |

### 5.3 Compatibility Requirements

- Python 3.11+
- Linux, macOS, Windows (via WSL for tmux-cli)
- Terminal: 80+ columns, 256 colors (fallback to basic)
- NO_COLOR environment variable respected

---

## 6. Testing Strategy

### 6.1 UAT Testing (Story 5-0)

**Framework**: tmux-cli + pytest

**Test Categories**:
1. **Journey Tests**: Validate complete user flows
2. **Component Tests**: Validate individual Rich components
3. **Regression Tests**: Catch UX regressions

**CI Integration**:
- Run on every PR
- Ubuntu runner with tmux
- 5-minute timeout per journey

### 6.2 Unit Testing

- Continue existing pytest patterns
- Mock Rich console for component tests
- Test configuration cascade independently

### 6.3 Integration Testing

- End-to-end CLI command tests
- File system interaction tests
- Configuration file parsing tests

---

## 7. Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| tmux-cli CI issues | Low | High | Test locally first, document WSL fallback |
| Rich component detection fragile | Medium | Medium | Use stable Rich API, version pin |
| Configuration cascade complexity | Medium | Low | Extensive unit tests, clear precedence docs |
| Performance regression | Low | Medium | Maintain existing benchmarks |

---

## 8. References

### 8.1 Related Documents

- UX Design Specification: `docs/ux-design-directions.html`
- tmux-cli Instructions: `docs/tmux-cli-instructions.md`
- Epic 4 Retrospective: historical context tracked in `docs/DOC_STATUS.md`
- Epic 4 Tech Spec: `docs/tech-spec-epic-4.md`

### 8.2 External References

- [Rich Documentation](https://rich.readthedocs.io/)
- [Click Documentation](https://click.palletsprojects.com/)
- [Typer Documentation](https://typer.tiangolo.com/)

---

## Appendix A: Story Dependency Graph

```
                    ┌─────────┐
                    │  5-0    │  UAT Testing Framework (P0)
                    └────┬────┘
                         │
         ┌───────────────┼───────────────┬───────────────┐
         │               │               │               │
         ▼               ▼               ▼               ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │  5-1    │    │  5-2    │    │  5-3    │    │  5-6    │
    │ Command │    │ Config  │    │Progress │    │ Error   │
    └────┬────┘    └────┬────┘    └────┬────┘    └─────────┘
         │               │               │
         │               ▼               ▼
         │         ┌─────────┐    ┌─────────┐
         │         │  5-5    │    │  5-4    │
         │         │ Presets │    │ Summary │
         │         └─────────┘    └─────────┘
         │
         ▼
    ┌─────────┐
    │  5-7    │
    │ Batch   │
    └─────────┘
```

---

## Appendix B: UAT Journey Coverage Matrix

| Story | J1 | J2 | J3 | J4 | J5 | J6 | J7 |
|-------|----|----|----|----|----|----|-----|
| 5-0 | ✓ | ✓ | ✓ | ✓ | | | |
| 5-1 | ✓ | | | ✓ | | | |
| 5-2 | ✓ | | | | P | | |
| 5-3 | | ✓ | ✓ | | | | |
| 5-4 | | ✓ | ✓ | | | | |
| 5-5 | | | | | ✓ | | |
| 5-6 | | | | | | ✓ | |
| 5-7 | | | | | | | ✓ |

**Legend**: ✓ = Primary, P = Partial

---

_Technical Specification created 2025-11-25 | Based on Epic 4 Retrospective decisions_
