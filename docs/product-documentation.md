# Data Extraction Tool Product Documentation

## Product summary

The Data Extraction Tool is a dual-part platform:

- **Backend API + CLI**: deterministic pipelines, job lifecycle management, and storage
- **UI**: guided operator workflows with readiness gates and result review

It is designed for teams that need reliable, repeatable document conversion and analysis with clear operational signals.

## Who this is for

- ML/NLP teams preparing context for retrieval-augmented generation
- Compliance and knowledge teams handling unstructured corpora
- Operations teams building resilient extraction runbooks
- Product teams evaluating file-to-knowledge workflows at scale

## Core capabilities

- Multi-format extraction: PDF, DOCX, XLSX, PPTX, CSV, TXT, and image-based workflows
- Normalized, typed output for downstream systems
- Semantic analysis modules:
  - Similarity and deduplication
  - Topic extraction
  - Cluster generation
  - Readability/quality metrics
- Session-based execution model with resume/retry behavior
- CLI-first automation and UI for operator-led operations

## Product architecture overview

The platform follows a fixed execution flow:

`extract -> normalize -> chunk -> semantic -> output`

- API and CLI surface the same runtime capabilities.
- Services orchestrate job state, retries, and persistence.
- The UI is served either in dev mode or through backend assets for integrated deployments.

## User journeys

### Operator journey

1. Upload or stage input files
2. Run validation and preprocessing checks
3. Start a run (manual or scripted)
4. Review integrity / quality indicators
5. Retry failures where needed
6. Export JSON/CSV/TXT output

### Integrator journey

1. Configure pipelines with `.data-extract.yaml` or environment variables
2. Trigger jobs via CLI or API
3. Poll job/session endpoints for status
4. Retrieve artifacts and report outputs programmatically

## Product guarantees and tradeoffs

- Deterministic processing for fixed configuration and input
- Explicit intermediate state (`session`) for failure recovery
- No silent errors: user-facing validation and recovery commands are expected in normal flow
- OCR/advanced linguistic features depend on external runtime dependencies

## Non-functional expectations

- Observability via command outputs and session/job status models
- Recoverability through persisted sessions and resume/retry pathways
- Security controls via API key and session secret when needed
- Extensibility via presets and centralized config layering

## Deployment and operations model

- **Single-server mode**: backend serves UI bundle and API from one process
- **Split-client mode**: UI and API deployed separately with matching `apiBaseUrl` contracts
- Production hardening priorities:
  - Environment-based secret management
  - Host binding and API access policy
  - Migration/version alignment
  - Disk policy for output and cache retention

## Documentation map

- Operator docs: [User Guide](user-guide.md)
- Backend engineering docs: [Architecture - Backend](architecture-backend.md), [API Contracts - Backend](api-contracts-backend.md)
- UI engineering docs: [Architecture - UI](architecture-ui.md), [API Contracts - UI](api-contracts-ui.md)
- Process and support docs: [Development Guide - Backend](development-guide-backend.md), [Development Guide - UI](development-guide-ui.md), [Deployment Guide](deployment-guide.md)
