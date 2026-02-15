# Summary: Integration Checklist

✅ **Before You Start**:
- [ ] Read `docs/architecture/index.md` (data models and interfaces)
- [ ] Review active orchestration services (`src/data_extract/services/*.py`)
- [ ] Understand process flow in `src/data_extract/services/pipeline_service.py`
- [ ] Study data flow through pipeline (this doc)

✅ **Implementing Your Processor**:
- [ ] Create/extend semantic stages in `src/data_extract/semantic/*.py`
- [ ] Implement pipeline stage interface (`PipelineStage`) where applicable
- [ ] Declare stage configuration and deterministic defaults
- [ ] Keep stage opt-in behavior explicit in process request/config
- [ ] Preserve all existing metadata in enriched blocks
- [ ] Preserve media assets (images, tables)
- [ ] Implement error handling (graceful degradation or partial processing)
- [ ] Add logging with structured context

✅ **Configuration**:
- [ ] Define configuration schema (Pydantic model recommended)
- [ ] Add config section to `.data-extract.yaml` examples
- [ ] Support constructor injection
- [ ] Support `load_merged_config()` + preset integration
- [ ] Document all configuration options

✅ **Testing**:
- [ ] Write unit tests for semantic extraction logic
- [ ] Write integration tests with real audit documents
- [ ] Test dependency ordering
- [ ] Test error handling (missing libraries, malformed input)
- [ ] Test performance with large documents
- [ ] Verify metadata preservation

✅ **Integration**:
- [ ] Register stage/orchestration in `src/data_extract/services/job_service.py`
- [ ] Update CLI/API/UI request surfaces if configurable
- [ ] Update documentation (`README.md`, `USER_GUIDE.md`)
- [ ] Add examples to `examples/` directory

✅ **Validation**:
- [ ] Run full test suite (ensure no regressions)
- [ ] Test on real audit documents (COBIT, NIST, OWASP, GRC exports)
- [ ] Verify pipeline ordering (check logs)
- [ ] Measure performance impact
- [ ] Review output quality

---
