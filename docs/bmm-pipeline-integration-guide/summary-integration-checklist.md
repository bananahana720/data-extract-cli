# Summary: Integration Checklist

✅ **Before You Start**:
- [ ] Read `docs/architecture/FOUNDATION.md` (data models and interfaces)
- [ ] Review current processor implementations (`src/processors/*.py`)
- [ ] Understand processor ordering mechanism (`_order_processors()`)
- [ ] Study data flow through pipeline (this doc)

✅ **Implementing Your Processor**:
- [ ] Create `src/processors/semantic_analyzer.py`
- [ ] Implement `BaseProcessor` interface
- [ ] Declare dependencies via `get_dependencies()`
- [ ] Set `is_optional()` appropriately
- [ ] Preserve all existing metadata in enriched blocks
- [ ] Preserve media assets (images, tables)
- [ ] Add new `ProcessingStage` enum value
- [ ] Implement error handling (graceful degradation or partial processing)
- [ ] Add logging with structured context

✅ **Configuration**:
- [ ] Define configuration schema (Pydantic model recommended)
- [ ] Add config section to `config.yaml.example`
- [ ] Support constructor injection
- [ ] Support ConfigManager integration
- [ ] Document all configuration options

✅ **Testing**:
- [ ] Write unit tests for semantic extraction logic
- [ ] Write integration tests with real audit documents
- [ ] Test dependency ordering
- [ ] Test error handling (missing libraries, malformed input)
- [ ] Test performance with large documents
- [ ] Verify metadata preservation

✅ **Integration**:
- [ ] Register processor in `src/pipeline/__init__.py`
- [ ] Update CLI to include new processor (if configurable)
- [ ] Update documentation (`README.md`, `USER_GUIDE.md`)
- [ ] Add examples to `examples/` directory

✅ **Validation**:
- [ ] Run full test suite (ensure no regressions)
- [ ] Test on real audit documents (COBIT, NIST, OWASP, GRC exports)
- [ ] Verify pipeline ordering (check logs)
- [ ] Measure performance impact
- [ ] Review output quality

---
