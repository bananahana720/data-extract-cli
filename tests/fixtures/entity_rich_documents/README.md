# Entity-Rich Document Fixtures

Realistic enterprise audit documents for testing entity-aware chunking (Story 3.2).

## Fixtures

### risk_register.md
- **Purpose:** Test entity preservation rate >95% (AC-3.2-1) and multi-sentence entity definitions (AC-3.2-4)
- **Entity Counts:**
  - 20 RISK-2024-* entities (RISK-2024-001 through RISK-2024-020)
  - 27 CTRL-* entities (CTRL-001 through CTRL-027)
  - 10 POL-* entities (POL-001 through POL-010)
  - **Total: 57 entities**
- **Relationships:** 19+ explicit relationships across 6 types (mitigated by, addresses, implements, maps to, addressed by, requires)
- **Size:** 147 lines, ~5,200 words, 12 KB
- **Key Features:**
  - Multi-sentence entity definitions (e.g., RISK-2024-002 spans 3 sentences)
  - Dense relationship mappings in Risk Relationships Summary section
  - Hierarchical section structure (Executive Summary → Critical Risks → Controls Framework → Policy Framework)
- **Usage:**
  - `test_entity_preservation_rate_exceeds_95_percent` (validates AC-3.2-1)
  - `test_multi_sentence_entity_definitions_preserved` (validates AC-3.2-4)

### policy_document.md
- **Purpose:** Test section detection (AC-3.2-7) and multi-sentence entity definitions with complex structure
- **Entity Counts:**
  - 20 RISK-INFO-* entities (RISK-INFO-001 through RISK-INFO-020)
  - 26 CTRL-SEC-* entities (CTRL-SEC-001 through CTRL-SEC-026)
  - 6 POL-SEC-* entities (POL-SEC-001 through POL-SEC-006)
  - **Total: 52 entities**
- **Structure:** 10 major sections with nested headings (L1 → L2 → L3 hierarchy)
  - Section 1: Introduction (1.1 Purpose, 1.2 Scope)
  - Section 2: Risk Assessment (2.1 Identification, 2.2 Treatment)
  - Sections 3-10: Domain-specific controls (Access, Data, Network, Endpoint, Application, Monitoring, Third-Party, Business Continuity)
- **Size:** 117 lines, ~4,500 words, 12 KB
- **Key Features:**
  - Deep section hierarchy for testing section boundary detection
  - Policy-style document structure (formal enterprise documentation)
  - Control Matrix appendix with explicit mappings
- **Usage:**
  - `test_section_aware_chunking_with_policy_document` (validates AC-3.2-7)
  - `test_entity_definition_boundary_detection` (validates AC-3.2-4)

### audit_mappings.md
- **Purpose:** Test relationship preservation (AC-3.2-3) with dense entity mapping patterns
- **Entity Counts:**
  - 3 CO-* entities (Control Objectives: CO-001, CO-002, CO-003)
  - 6 REQ-* entities (Requirements: REQ-SEC-001/002/003, REQ-PRIV-001/002, REQ-AUDIT-001)
  - 24 CTRL-* entities (Controls: CTRL-IAM-*, CTRL-NET-*, CTRL-DATA-*, CTRL-MON-*)
  - 5 PROC-* entities (Processes: PROC-ACC-001, PROC-NET-001, PROC-DATA-001/002, PROC-AUDIT-001)
  - 14 RISK-* entities (Risks: RISK-AUTH-*, RISK-NET-*, RISK-PRIV-*, RISK-COMP-*, RISK-AUDIT-*)
  - **Total: 52 entities across 5 types**
- **Relationships:** 47+ explicit relationship keywords (maps to, implements, addresses, mitigates, through)
- **Mapping Types:**
  - Control Objective → Controls (e.g., CO-001 maps to CTRL-IAM-001/002/003)
  - Requirements → Controls (e.g., REQ-SEC-001 implements CTRL-IAM-001 through CTRL-IAM-005)
  - Controls → Risks (e.g., CTRL-IAM-001 addresses RISK-AUTH-001)
  - Processes → Controls (e.g., PROC-ACC-001 implements CTRL-IAM-001/006/007)
  - Compliance Framework → Requirements (e.g., GDPR → REQ-PRIV-001/002)
- **Size:** 143 lines, ~4,800 words, 12 KB
- **Key Features:**
  - High-density relationship mappings (every section contains multiple entity-to-entity relationships)
  - Multi-way relationships (e.g., Control → Risk ← Requirement)
  - Compliance framework alignment (GDPR, SOX, ISO 27001)
- **Usage:**
  - `test_relationship_context_preserved` (validates AC-3.2-3)
  - `test_entity_relationship_extraction` (validates relationship pattern detection)

## Total Fixture Size
- **Files:** 3 markdown files
- **Lines:** 407 total (147 + 117 + 143)
- **Words:** ~14,500 (5,200 + 4,500 + 4,800)
- **Disk Size:** ~36 KB (12 KB × 3) - well under 100 MB limit
- **Entities:** 161 unique entities across all fixtures (57 + 52 + 52)
- **Relationships:** 66+ explicit relationship patterns

## Maintenance

### Entity ID Patterns

#### risk_register.md
- **RISK entities:** `RISK-YYYY-NNN` (e.g., RISK-2024-001)
- **CTRL entities:** `CTRL-NNN` (e.g., CTRL-001)
- **POL entities:** `POL-NNN` (e.g., POL-001)

#### policy_document.md
- **RISK entities:** `RISK-INFO-NNN` (e.g., RISK-INFO-001)
- **CTRL entities:** `CTRL-SEC-NNN` (e.g., CTRL-SEC-001)
- **POL entities:** `POL-SEC-NNN` (e.g., POL-SEC-001)

#### audit_mappings.md
- **Control Objectives:** `CO-NNN` (e.g., CO-001)
- **Requirements:** `REQ-{DOMAIN}-NNN` (e.g., REQ-SEC-001, REQ-PRIV-001)
- **Controls:** `CTRL-{DOMAIN}-NNN` (e.g., CTRL-IAM-001, CTRL-NET-001, CTRL-DATA-001)
- **Processes:** `PROC-{DOMAIN}-NNN` (e.g., PROC-ACC-001, PROC-NET-001)
- **Risks:** `RISK-{DOMAIN}-NNN` (e.g., RISK-AUTH-001, RISK-NET-001, RISK-PRIV-001)

### Relationship Patterns

Story 3.2 tests the following relationship keyword patterns:

1. **"mitigated by"** - Risk → Control (active mitigation)
2. **"addresses"** - Control → Risk (passive mitigation) or Policy → Requirement
3. **"implements"** - Policy → Standard or Process → Control
4. **"maps to"** - Control → Requirement (compliance mapping)
5. **"addressed by"** - Risk → Control (passive voice)
6. **"requires"** - Policy → Control (dependency)
7. **"through"** - Relationship qualifier (e.g., "mitigates RISK through CTRL")

### Updating Fixtures

When modifying fixtures, maintain these invariants:

1. **Entity ID Consistency:** Use sequential numbering (001, 002, 003...) within each domain
2. **Relationship Format:** Preserve keyword patterns exactly as listed above
3. **Multi-Sentence Definitions:** Keep at least 3 entities with definitions spanning 2+ sentences (tests AC-3.2-4)
4. **Section Hierarchy:** Maintain nested heading structure in policy_document.md (L1 → L2 → L3)
5. **Entity Count Thresholds:** Do not drop below minimum counts to ensure test validity:
   - risk_register.md: ≥50 entities (currently 57)
   - policy_document.md: ≥50 entities, ≥8 sections (currently 52 entities, 10 sections)
   - audit_mappings.md: ≥45 entities, ≥40 relationships (currently 52 entities, 47+ relationships)

### Regeneration Guidelines

If fixtures require regeneration:

1. **Preserve Test Coverage:**
   - Ensure entities span multiple sentences (AC-3.2-4)
   - Include dense relationship patterns (AC-3.2-3)
   - Maintain hierarchical section structure (AC-3.2-7)
   - Verify entity preservation rate >95% (AC-3.2-1)

2. **Validation Commands:**
   ```bash
   # Count entities
   rg -o 'RISK-[0-9]{4}-[0-9]{3}' risk_register.md | sort -u | wc -l
   rg -o 'CTRL-[0-9]{3}' risk_register.md | sort -u | wc -l
   rg -o 'POL-[0-9]{3}' risk_register.md | sort -u | wc -l

   # Count relationships
   rg 'mitigated by|addresses|implements|maps to|addressed by|requires' risk_register.md | wc -l

   # Verify file size
   du -h *.md
   ```

3. **Test Integration:**
   - Run `pytest tests/integration/test_chunk/test_entity_aware_integration.py -v` to validate fixtures
   - Ensure all AC-3.2-* tests pass with regenerated fixtures
   - Verify entity preservation rate ≥95% across all test cases

## Story 3.2 Context

These fixtures support entity-aware chunking tests that validate:

- **AC-3.2-1:** Entity preservation rate >95% (risk_register.md provides 57 entities for statistical validation)
- **AC-3.2-3:** Relationship preservation across chunk boundaries (audit_mappings.md provides 47+ relationships)
- **AC-3.2-4:** Multi-sentence entity definition boundaries (risk_register.md has 3+ multi-sentence entities)
- **AC-3.2-7:** Section-aware context preservation (policy_document.md provides 10-section hierarchy)

## Fixture Design Principles

1. **Realism:** Fixtures mirror actual enterprise audit documents (risk registers, policy docs, compliance mappings)
2. **Density:** High entity and relationship density tests chunking engine's ability to preserve context
3. **Complexity:** Multi-sentence definitions and nested structures test boundary detection
4. **Size:** Each fixture ~10-15KB ensures testability without excessive file sizes
5. **Diversity:** Different document types (risk register, policy, mappings) test generalization across formats

## Related Documentation

- Story 3.2 specification: `docs/stories/3-2-entity-aware-chunking.md`
- Story 3.2 context: `docs/stories/3-2-entity-aware-chunking.context.xml`
- Test implementation: `tests/integration/test_chunk/test_entity_aware_integration.py`
- ATDD checklist: `docs/atdd-checklist-3.2.md`
