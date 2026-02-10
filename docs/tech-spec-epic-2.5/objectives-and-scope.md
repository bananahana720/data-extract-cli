# Objectives and Scope

**In Scope:**
- Performance validation and optimization for 100-file batches (<10 min, <2GB memory per NFR-P1, NFR-P2)
- Profiling and bottleneck identification in extraction and normalization stages
- spaCy 3.7.2 installation and `en_core_web_md` model integration
- spaCy sentence segmentation testing and validation (95%+ accuracy)
- Utility function for Epic 3: `get_sentence_boundaries()` for semantic chunking
- Large document test fixtures: 50+ page PDF, 10K+ row Excel, scanned PDF
- Integration tests for large file processing and memory monitoring
- UAT testing workflow creation for systematic acceptance criteria validation
- CLAUDE.md documentation updates with Epic 2 lessons learned
- Resolution of Story 2.5 code review blockers (Mypy violations, unused variables)

**Out of Scope:**
- Actual semantic chunking implementation (Epic 3, Story 3.1)
- Advanced spaCy features beyond sentence segmentation (entity recognition covered in Epic 2)
- Performance optimization beyond critical bottlenecks (diminishing returns)
- GUI or web interface for testing
- Production deployment configuration
