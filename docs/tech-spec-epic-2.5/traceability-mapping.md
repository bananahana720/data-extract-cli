# Traceability Mapping

| Acceptance Criteria | Spec Section | Component | Test Approach |
|---------------------|--------------|-----------|---------------|
| AC-2.5.1.1: 100-file batch <10 min | Performance / NFR-P1 | tests/performance/test_throughput.py | Automated test with timer |
| AC-2.5.1.2: Memory <2GB | Performance / NFR-P2 | tests/performance/test_throughput.py | psutil memory monitoring |
| AC-2.5.1.3: Bottlenecks identified | Detailed Design / Workflows | cProfile output analysis | Manual profile review |
| AC-2.5.1.4: Bottlenecks optimized | Performance / NFR-P1 | Pipeline code optimizations | Before/after benchmarks |
| AC-2.5.1.5: Performance test suite | Services and Modules | tests/performance/test_throughput.py | Test execution verification |
| AC-2.5.1.6: Baseline documented | Observability / NFR-O1 | Test docstrings / metrics file | Documentation review |
| AC-2.5.2.1: spaCy installed | Dependencies | pyproject.toml, spaCy CLI | `python -m spacy validate` |
| AC-2.5.2.2: Model downloaded | Dependencies | en_core_web_md | Model load test |
| AC-2.5.2.3: 95%+ accuracy | APIs and Interfaces | Sentence segmentation tests | Gold standard corpus test |
| AC-2.5.2.4: get_sentence_boundaries() | Data Models / APIs | src/data_extract/utils/nlp.py | Function implementation review |
| AC-2.5.2.5: Unit tests | APIs and Interfaces | tests/unit/test_nlp.py | Unit test execution |
| AC-2.5.2.6: Integration tests | APIs and Interfaces | tests/integration/test_spacy_integration.py | Integration test execution |
| AC-2.5.2.7: Documentation updated | Dependencies | CLAUDE.md, README.md | Documentation review |
| AC-2.5.3.1: Large PDF fixture | Services and Modules | tests/fixtures/pdfs/large/ | Fixture file verification |
| AC-2.5.3.2: Large Excel fixture | Services and Modules | tests/fixtures/xlsx/large/ | Fixture file verification |
| AC-2.5.3.3: Scanned PDF fixture | Services and Modules | tests/fixtures/pdfs/scanned/ | Fixture file verification |
| AC-2.5.3.4: Fixture docs | Services and Modules | tests/fixtures/README.md | Documentation review |
| AC-2.5.3.5: Large file tests | APIs and Interfaces | tests/integration/test_large_files.py | Integration test execution |
| AC-2.5.3.6: Memory monitoring | Reliability / NFR-R2 | psutil integration | Memory spike detection test |
| AC-2.5.3.7: UAT workflow design | Services and Modules | bmad:bmm:workflows:create-test-cases | Design document review |
| AC-2.5.3.8: CLAUDE.md lessons | System Architecture | CLAUDE.md | Documentation review |
| AC-2.5.3.9: Code review blockers | APIs and Interfaces | src/data_extract/normalize/validation.py | Quality gate execution |

**Epic 2.5 → PRD Traceability:**
- **NFR-P1 (Performance)** → Story 2.5.1 → Validates 100-file batch throughput
- **NFR-P2 (Memory)** → Story 2.5.1 → Validates streaming architecture memory limits
- **NFR-R2 (Graceful Degradation)** → Story 2.5.3 → Large file processing without crashes
- **NFR-M4 (Testability)** → All Stories → Comprehensive test coverage expansion
- **NFR-C1 (Python 3.12)** → Story 2.5.2 → spaCy compatibility validation

**Epic 2.5 → Epic 3 Preparation:**
- Story 2.5.2 → Epic 3 Story 3.1 → `get_sentence_boundaries()` enables semantic chunking
- Story 2.5.1 → Epic 3 → Performance baselines detect chunking overhead
- Story 2.5.3 → Epic 3 → Large fixtures support chunk quality validation
