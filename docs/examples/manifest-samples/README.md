# Manifest Sample Files

This directory contains sample manifest.json files demonstrating the organization traceability metadata.

## Files

| File | Description | Organization Strategy |
|------|-------------|----------------------|
| `manifest-by-document.json` | BY_DOCUMENT strategy | One folder per source document |
| `manifest-by-entity.json` | BY_ENTITY strategy | Folders by entity type (risks/, controls/, etc.) |
| `manifest-flat.json` | FLAT strategy | Single directory with all outputs |

## Manifest Schema

All manifests include comprehensive traceability metadata per Story 3.7:

### Core Fields
- `organization_strategy` - Strategy used (by_document, by_entity, flat)
- `generated_at` - ISO 8601 timestamp
- `config_snapshot` - Chunking/formatter configuration
- `total_chunks` - Total chunks organized
- `folders` - Folder → chunk mapping

### Enrichment Fields (Story 3.7)
- `source_hashes` - Source file → SHA-256 hash mapping
- `entity_summary` - Entity statistics and counts
- `quality_summary` - Quality score aggregations

## Usage

These manifests demonstrate:
1. **Reproducibility:** config_snapshot enables exact reproduction of results
2. **Traceability:** source_hashes verify source file integrity
3. **Quality Monitoring:** quality_summary tracks trends across batches
4. **Entity Analysis:** entity_summary provides cross-document entity counts

## Validation

All samples can be validated with:

```bash
# JSON structure validation
jq . manifest-by-document.json

# Python validation
python -c "import json; json.load(open('manifest-by-document.json'))"

# Node.js validation
node -e "JSON.parse(require('fs').readFileSync('manifest-by-document.json'))"
```

## Integration Examples

See corresponding CSV samples in `docs/examples/csv-output-samples/` for organized output examples using these manifest patterns.
