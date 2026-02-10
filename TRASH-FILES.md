# Trashed Files

tests/unit/test_cli/test_story_5_2/test_config_models.py - moved to TRASH/ - large 967-line file split into 6 domain-based files
tests/unit/test_cli/test_story_5_1/test_models.py - moved to TRASH/ - split into 7 domain-based files for better maintainability
tests/unit/test_cli/test_story_5_2/test_config_validation.py - moved to TRASH/ - 878-line file split into 6 domain-based validation files
tests/unit/test_validation/test_semantic_validator.py - moved to TRASH/ - orphaned test for deleted semantic_validator.py module (Wave 3 cleanup oversight)
tests/fixtures/test_fixtures.py - moved to TRASH/ - placeholder fixture template with TODOs, no real implementation
tests/unit/test_misc/test_test.py - moved to TRASH/ - placeholder test template with TODOs, broken fixtures
src/data_extract/cli/base.py.backup - moved to TRASH/ - backup file after successful migration

## V1.0 Brownfield Removal (2025-11-30)

src/cli/ - moved to TRASH/src_cli/ - brownfield Click CLI replaced by greenfield Typer commands
src/core/ - moved to TRASH/src_core/ - brownfield core models replaced by greenfield data_extract.core
src/extractors/ - moved to TRASH/src_extractors/ - brownfield extractors replaced by greenfield data_extract.extract
src/processors/ - moved to TRASH/src_processors/ - brownfield processors replaced by greenfield data_extract.normalize
src/formatters/ - moved to TRASH/src_formatters/ - brownfield formatters replaced by greenfield data_extract.output
src/infrastructure/ - moved to TRASH/src_infrastructure/ - brownfield infrastructure replaced by greenfield modules
src/pipeline/ - moved to TRASH/src_pipeline/ - brownfield pipeline replaced by greenfield data_extract.core.pipeline
tests/test_extractors/ - moved to TRASH/tests_test_extractors/ - brownfield extractor tests (greenfield tests in tests/unit/data_extract/extract/)
tests/test_formatters/ - moved to TRASH/tests_test_formatters/ - brownfield formatter tests (greenfield tests in tests/unit/data_extract/output/)
tests/test_processors/ - moved to TRASH/tests_test_processors/ - brownfield processor tests (greenfield tests in tests/unit/data_extract/normalize/)
tests/test_pipeline/ - moved to TRASH/tests_test_pipeline/ - brownfield pipeline tests (greenfield tests in tests/integration/)

## V1.0 Session 2 Cleanup (2025-11-30)

tests/unit/data_extract/extract/test_registry.py - moved to TRASH/ - brownfield adapter tests with 90 F821 errors (module-skipped, greenfield registry uses different pattern)
tests/unit/data_extract/extract/test_pdf.py - moved to TRASH/ - brownfield adapter tests with 63 F821 errors (greenfield PDF extractor in src/data_extract/extract/pdf.py)
tests/unit/data_extract/extract/test_pptx.py - moved to TRASH/ - brownfield adapter tests with 63 F821 errors (greenfield PPTX extractor in src/data_extract/extract/pptx.py)
tests/unit/data_extract/extract/test_excel.py - moved to TRASH/ - brownfield adapter tests with 9 F821 errors (greenfield Excel extractor in src/data_extract/extract/excel.py)
