# Post-Review Follow-ups

- **Story 3.4:** Propagate chunking configuration and source-document metadata through `ChunkMetadata` so JsonFormatter headers report real chunk_size/overlap and source paths.
- **Story 3.4:** Normalize `ChunkMetadata.to_dict()` to emit every mandated field without `null` values (source_file, created_at, quality, etc.) before schema validation.
- **Story 3.4:** Restore UTF-8 BOM support (or a configurable `utf-8-sig` option) in JsonFormatter output so Windows-compatible consumers ingest files without manual fixes.
- **Story 3.4:** Treat schema validation failures as blocking errors instead of silent `FormatResult.errors` entries to prevent invalid JSON from leaking downstream.
- **Story 3.4:** Update Story documentation/File List to capture formatter base, unit tests, and JSON schema reference updates for traceability.
- **Story 3.6:** Build the OutputWriter/organization wiring and expose `--format csv` so CsvFormatter can be invoked via CLI/pipeline, then re-enable the CSV integration tests.
- **Story 3.6:** Add pandas/csvkit dependencies plus Excel/Sheets validation artifacts so AC-3.6-4/7 have real coverage instead of skipped checks.
