# Data Extraction Tool - Documentation Index

**Updated**: 2025-12-01
**Status**: V1.0 RELEASED (All 5 Epics COMPLETE)
**Architecture**: 5-Stage Pipeline (Extract → Normalize → Chunk → Semantic → Output)

---

## Quick Start

**New to this project?** Start here:

- **[QUICKSTART.md](./QUICKSTART.md)** - Five-minute installation and first extraction guide
- **[USER_GUIDE.md](./USER_GUIDE.md)** - Non-technical user guide for auditors
- **[PILOT_DISTRIBUTION_README.md](./PILOT_DISTRIBUTION_README.md)** - Pilot program installation and quickstart

---

## Configuration & Operations

- **[CONFIG_GUIDE.md](./CONFIG_GUIDE.md)** - Configuration management with cascade precedence and API reference
- **[LOGGING_GUIDE.md](./LOGGING_GUIDE.md)** - Structured JSON logging with correlation tracking
- **[ERROR_HANDLING_GUIDE.md](./ERROR_HANDLING_GUIDE.md)** - Error codes, exception classes, and recovery patterns
- **[INFRASTRUCTURE_INTEGRATION_GUIDE.md](./INFRASTRUCTURE_INTEGRATION_GUIDE.md)** - Extractor integration patterns for ConfigManager and LoggingFramework

---

## Testing & Development

- **[TESTING-README.md](./TESTING-README.md)** - Test execution guide with markers and coverage commands
- **[automation-guide.md](./automation-guide.md)** - P0 development automation scripts (60% token reduction)
- **[automation-summary.md](./automation-summary.md)** - Greenfield CLI test coverage expansion (52 new tests)
- **[development-operations-guide.md](./development-operations-guide.md)** - Developer and DevOps setup guide
- **[tmux-cli-instructions.md](./tmux-cli-instructions.md)** - tmux-cli tool for automated UAT testing
- **[troubleshooting-spacy.md](./troubleshooting-spacy.md)** - spaCy 3.7.2+ common errors and solutions

### ATDD Acceptance Criteria Checklists

- **[atdd-checklist-3.4.md](./atdd-checklist-3.4.md)** - JSON output format acceptance criteria
- **[atdd-checklist-3.5.md](./atdd-checklist-3.5.md)** - Plain text output format acceptance criteria
- **[atdd-checklist-3.6.md](./atdd-checklist-3.6.md)** - CSV output format acceptance criteria
- **[atdd-checklist-3.7.md](./atdd-checklist-3.7.md)** - Output organization strategies acceptance criteria

### Test Fixtures & QA

- **[test-fixtures-catalog.md](./test-fixtures-catalog.md)** - Real-world test file inventory (13 files, 36.86 MB)
- **[qa-fixtures-maintenance-guide.md](./qa-fixtures-maintenance-guide.md)** - Semantic corpus fixture maintenance instructions

---

## Technical Specifications

### Epic Specifications (Sharded)

- **[tech-spec-epic-1.md](./tech-spec-epic-1.md)** - Epic 1: Foundation and pipeline architecture
- **[tech-spec-epic-2/](./tech-spec-epic-2/)** - Epic 2: Extract & Normalize (11 sections + index)
- **[tech-spec-epic-2.5/](./tech-spec-epic-2.5/)** - Epic 2.5: Refinement & Quality (11 sections + index)
- **[tech-spec-epic-3/](./tech-spec-epic-3/)** - Epic 3: Chunk & Output (9 sections + index)
- **[tech-spec-epic-3.5.md](./tech-spec-epic-3.5.md)** - Epic 3.5: Tooling and semantic preparation bridge
- **[tech-spec-epic-4.md](./tech-spec-epic-4.md)** - Epic 4: Classical NLP knowledge curation
- **[tech-spec-epic-5.md](./tech-spec-epic-5.md)** - Epic 5: Enhanced CLI UX and batch processing

### Planning Documents

- **[PRD/](./PRD/)** - Product Requirements Document (12 sections + index)
- **[architecture/](./architecture/)** - Technical architecture and ADRs (19 files + index)
- **[epics.md](./epics.md)** - Complete epic breakdown for RAG pipeline transformation

---

## Analysis & Architecture (Sharded)

- **[brownfield-assessment/](./brownfield-assessment/)** - Legacy codebase analysis (10 sections + index)
- **[bmm-pipeline-integration-guide/](./bmm-pipeline-integration-guide/)** - Pipeline integration patterns (13 sections)
- **[bmm-processor-chain-analysis/](./bmm-processor-chain-analysis/)** - Processor chain architecture (10 sections)
- **[implementation-readiness-report-2025-11-10/](./implementation-readiness-report-2025-11-10/)** - Epic 3 readiness assessment (13 sections + index)
- **[development-operations-guide-2025-11-13/](./development-operations-guide-2025-11-13/)** - Complete dev/ops reference (11 sections)

### Single-File Analysis

- **[bmm-index.md](./bmm-index.md)** - BMad Method documentation navigation index
- **[bmm-project-overview.md](./bmm-project-overview.md)** - Enterprise document extraction project overview
- **[bmm-source-tree-analysis.md](./bmm-source-tree-analysis.md)** - Source code organization reference (913 lines)
- **[ci-cd-infrastructure-analysis.md](./ci-cd-infrastructure-analysis.md)** - CI/CD quality gate pipeline analysis
- **[cli-entry-points-analysis.md](./cli-entry-points-analysis.md)** - CLI entry points and 15 utility scripts
- **[config-management-analysis.md](./config-management-analysis.md)** - Four-tier cascade configuration architecture
- **[technology-stack-analysis.md](./technology-stack-analysis.md)** - Python 3.12+ modular pipeline stack
- **[test-infrastructure-analysis.md](./test-infrastructure-analysis.md)** - 83 test files with pytest markers

---

## Output Format References

- **[json-schema-reference.md](./json-schema-reference.md)** - JSON chunk output with Draft 7 schema validation
- **[txt-format-reference.md](./txt-format-reference.md)** - Plain text format optimized for LLM upload
- **[csv-format-reference.md](./csv-format-reference.md)** - RFC 4180 CSV with 10-column schema
- **[organizer-reference.md](./organizer-reference.md)** - BY_DOCUMENT/BY_ENTITY/FLAT organization strategies

---

## Performance & Baselines

- **[performance-baselines-epic-3.md](./performance-baselines-epic-3.md)** - Chunking engine and JSON formatter metrics
- **[performance-baselines-story-2.5.1.md](./performance-baselines-story-2.5.1.md)** - Greenfield architecture 100-file baselines
- **[performance-bottlenecks-story-2.5.1.md](./performance-bottlenecks-story-2.5.1.md)** - cProfile I/O and process pool analysis

---

## CI/CD & Pipeline

- **[ci-cd-pipeline.md](./ci-cd-pipeline.md)** - GitHub Actions workflows and quality gates
- **[test-design-epic-3.md](./test-design-epic-3.md)** - Risk assessment with 68.5-hour test effort
- **[test-design-epic-5.md](./test-design-epic-5.md)** - UAT framework design with 56 scenarios

---

## Traceability & Quality Gates

- **[traceability-matrix.md](./traceability-matrix.md)** - Epic 3 requirements traceability and gate decision
- **[traceability-matrix-epic-3.md](./traceability-matrix-epic-3.md)** - Detailed Epic 3 AC coverage (1448 lines)
- **[traceability-matrix-epic-5.md](./traceability-matrix-epic-5.md)** - Epic 5: 95.9% coverage across 74 criteria
- **[traceability-epic-1-foundation.md](./traceability-epic-1-foundation.md)** - Epic 1 requirements-to-tests mapping
- **[traceability-epic-2-extract-normalize.md](./traceability-epic-2-extract-normalize.md)** - Epic 2: 100% coverage across 6 stories
- **[traceability-epic-2.5-refinement-quality.md](./traceability-epic-2.5-refinement-quality.md)** - Epic 2.5 NFR trade-off documentation
- **[traceability-master-epic-1-2-consolidated.md](./traceability-master-epic-1-2-consolidated.md)** - Consolidated Epics 1-2.5 quality metrics
- **[gate-decision-epic-5.md](./gate-decision-epic-5.md)** - Epic 5 PASS with 806+ tests
- **[gate-decision-story-2.5.md](./gate-decision-story-2.5.md)** - Story 2.5 gate blocked by missing CI data

---

## Epic 4 Documentation

- **[epic-4-value-proposition.md](./epic-4-value-proposition.md)** - 98.5% LLM cost reduction through classical NLP
- **[epic-4-integration-test-design.md](./epic-4-integration-test-design.md)** - Semantic analysis integration test requirements
- **[epic-4-sprint-execution-roadmap.md](./epic-4-sprint-execution-roadmap.md)** - Multi-agent orchestration sprint plan
- **[epic-4-5-action-plan-2025-11-20.md](./epic-4-5-action-plan-2025-11-20.md)** - Epic 4 completion and Epic 5 transition

---

## UX Design (Epic 5)

- **[ux-design-specification.md](./ux-design-specification.md)** - "Tool as Teacher" CLI philosophy with 7 user journeys
- **[ux-color-themes.html](./ux-color-themes.html)** - Rich console color theme visualizations
- **[ux-design-directions.html](./ux-design-directions.html)** - UX design direction explorations

---

## Playbooks & Learning Resources

- **[playbooks/semantic-analysis-intro.ipynb](./playbooks/semantic-analysis-intro.ipynb)** - Interactive TF-IDF/LSA tutorial (Jupyter notebook)
- **[playbooks/semantic-analysis-reference.md](./playbooks/semantic-analysis-reference.md)** - TF-IDF/LSA API reference and troubleshooting

---

## Project Management

- **[sprint-status.yaml](./sprint-status.yaml)** - Authoritative development status tracking
- **[bmm-workflow-status.yaml](./bmm-workflow-status.yaml)** - BMad Method workflow status
- **[backlog.md](./backlog.md)** - Engineering backlog for cross-cutting improvements
- **[retrospective-lessons.md](./retrospective-lessons.md)** - Consolidated lessons from Epics 1-4

---

## UV Package Manager Migration

- **[uv-migration-guide.md](./uv-migration-guide.md)** - Migration from pip to uv (10-100x faster)
- **[UV_MIGRATION_SUMMARY.md](./UV_MIGRATION_SUMMARY.md)** - Migration completion summary (2025-11-29)

---

## Test Reviews & Reports

- **[test-review.md](./test-review.md)** - General test review documentation
- **[test-review-epic3.md](./test-review-epic3.md)** - Epic 3 test review findings
- **[test-review-epic-5-cli.md](./test-review-epic-5-cli.md)** - Epic 5 CLI test review
- **[test-review-epic-5-cli-split-summary.md](./test-review-epic-5-cli-split-summary.md)** - CLI test file split summary
- **[test-summary-story-5-5.md](./test-summary-story-5-5.md)** - Story 5-5 test execution summary

---

## Completion Summaries

- **[p0-1-completion-summary.md](./p0-1-completion-summary.md)** - P0-1 automation completion
- **[p0-2-completion-summary.md](./p0-2-completion-summary.md)** - P0-2 automation completion
- **[story-3.5-1-completion-summary.md](./story-3.5-1-completion-summary.md)** - Story 3.5-1 completion
- **[automation-summary-story-3.7.md](./automation-summary-story-3.7.md)** - Story 3.7 automation summary
- **[automation-summary-epic-4-prep.md](./automation-summary-epic-4-prep.md)** - Epic 4 preparation automation

---

## Additional Documentation

- **[epic-3-reference.md](./epic-3-reference.md)** - Entity-aware chunking patterns reference
- **[development-automation-strategy.md](./development-automation-strategy.md)** - Development automation approach
- **[brainstorming-session-results-2025-11-07.md](./brainstorming-session-results-2025-11-07.md)** - Self-explanatory CLI brainstorming
- **[code-review-2025-11-18-claude-md.md](./code-review-2025-11-18-claude-md.md)** - CLAUDE.md code review findings
- **[architecture-refactoring-scan-security.md](./architecture-refactoring-scan-security.md)** - Security scanning refactoring
- **[project-maintenance-report-2025-11-14.md](./project-maintenance-report-2025-11-14.md)** - Documentation and technical debt analysis

### Data Files

- **[guide-generation-summary-2025-11-13.json](./guide-generation-summary-2025-11-13.json)** - Guide generation metadata
- **[project-scan-report.json](./project-scan-report.json)** - Project scan findings metadata

---

## Subdirectories

### stories/

Individual story specifications with acceptance criteria and context files for Epics 1-5.

- 80+ story files (.md and .context.xml)
- Naming: `{epic}-{story}-{title}.md`

### artifacts/

Session artifacts, completion reports, and implementation summaries.

- Wave completion reports
- Test fixture delivery summaries
- Code review remediation plans

### retrospectives/

Epic retrospectives capturing lessons learned.

- **[epic-1-retro-20251110.md](./retrospectives/epic-1-retro-20251110.md)** - Epic 1 retrospective
- **[epic-2-retro-20250111.md](./retrospectives/epic-2-retro-20250111.md)** - Epic 2 retrospective
- **[epic-2.5-retro-2025-11-13.md](./retrospectives/epic-2.5-retro-2025-11-13.md)** - Epic 2.5 retrospective
- **[epic-3-retro-2025-11-16.md](./retrospectives/epic-3-retro-2025-11-16.md)** - Epic 3 retrospective
- **[epic-3.5-retro-2025-11-18.md](./retrospectives/epic-3.5-retro-2025-11-18.md)** - Epic 3.5 retrospective
- **[epic-4-retro-2025-11-25.md](./retrospectives/epic-4-retro-2025-11-25.md)** - Epic 4 retrospective

### reviews/

Code reviews, audit reports, and validation findings.

- Story validation reports
- Housekeeping findings
- Source tree analyses

### test-plans/

Test plans and policies for specific components.

- Excel/PPTX extractor test plans
- CLI TDD test plans
- Skip cleanup policies

### uat/

User acceptance testing framework and results.

- Test cases and evidence
- Session summaries
- tmux-cli documentation

### examples/

Sample outputs demonstrating formatter capabilities.

- **[txt-output-samples/](./examples/txt-output-samples/)** - Plain text formatter examples
- **[csv-output-samples/](./examples/csv-output-samples/)** - CSV formatter examples
- **[manifest-samples/](./examples/manifest-samples/)** - Organization manifest examples

### api/

Generated API documentation.

- Module, class, and function references

### implementation/

Implementation patterns and refactoring reports.

- Epic 4 implementation patterns
- Scripts refactoring inventory

### processes/

Development process documentation.

- Test dependency audit procedures

### reports/

Generated reports and metrics.

- Velocity history tracking

### research/

Technical research and recommendations.

- Integration strategy
- Script automation research

### tech-debt/

Technical debt tracking and remediation.

### testing/

Testing infrastructure documentation.

### archive/

Archived original monolithic documents (pre-sharding).

---

## Quick Navigation by Task

| I want to... | Start here |
|--------------|------------|
| **Set up the project** | [QUICKSTART.md](./QUICKSTART.md) |
| **Understand the architecture** | [architecture/](./architecture/) |
| **Run tests** | [TESTING-README.md](./TESTING-README.md) |
| **Configure the tool** | [CONFIG_GUIDE.md](./CONFIG_GUIDE.md) |
| **Use automation scripts** | [automation-guide.md](./automation-guide.md) |
| **Learn TF-IDF/LSA** | [playbooks/semantic-analysis-intro.ipynb](./playbooks/semantic-analysis-intro.ipynb) |
| **Troubleshoot spaCy** | [troubleshooting-spacy.md](./troubleshooting-spacy.md) |
| **Check project status** | [sprint-status.yaml](./sprint-status.yaml) |
| **Review performance** | [performance-baselines-epic-3.md](./performance-baselines-epic-3.md) |
| **Understand output formats** | [json-schema-reference.md](./json-schema-reference.md) |
| **See UX design** | [ux-design-specification.md](./ux-design-specification.md) |
| **Find epic specs** | [PRD/](./PRD/), tech-spec-epic-*.md files |
| **Learn CI/CD** | [ci-cd-pipeline.md](./ci-cd-pipeline.md) |
| **Use uv package manager** | [uv-migration-guide.md](./uv-migration-guide.md) |

---

## Documentation Statistics

- **Root-level files**: 83 markdown/YAML/JSON/HTML files
- **Sharded documentation**: 10+ large documents split into section files
- **Subdirectories**: 26 (including sharded doc folders)
- **Story files**: 80+ (Epics 1-5)
- **Total documentation**: 200+ files

---

**Last Updated**: 2025-12-01
**Major Changes**:
- **V1.0 RELEASED**: All 5 epics complete (2025-12-01)
- Epic 5 COMPLETE: Enhanced CLI UX and batch processing
- Epic 4 COMPLETE: Knowledge curation via classical NLP (TF-IDF, LSA, similarity)
- UV migration complete (2025-11-29)
- 66 UAT tests passing across 7 user journeys
- 3,575 total tests (Core: 971, CLI: 674, UAT: 66, Scripts: 170)
