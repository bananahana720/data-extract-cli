# Script Pruning - Wave 1 Kill List

## Scripts Moved to TRASH Directory (2025-11-18)

### Duplicate Scripts
smoke-test-semantic.py - moved to TRASH/ - DUPLICATE of smoke_test_semantic.py (454 lines removed)
run_quality_gates_windows.cmd - moved to TRASH/ - Duplicates run_quality_gates.py functionality (43 lines removed)
check_dependency_changes.py - moved to TRASH/ - Superseded by audit_dependencies.py (183 lines removed)
test_dependency_hook.py - moved to TRASH/ - Orphaned test for removed hook (102 lines removed)

### Legacy/Unused Scripts
analyze_profile.py - moved to TRASH/ - Never referenced (67 lines removed)
build_package.bat - moved to TRASH/ - Unused packaging script (167 lines combined removed)
build_package.sh - moved to TRASH/ - Unused packaging script (see above)
create_dev_package.sh - moved to TRASH/ - Obsolete packaging (213 lines removed)
fix_import_paths.py - moved to TRASH/ - One-time migration script (83 lines removed)
regenerate_gold_standard.py - moved to TRASH/ - Obsolete fixture script (37 lines removed)
setup.py - moved to TRASH/ - Old setuptools, project uses pyproject.toml (91 lines removed)
verify_package.sh - moved to TRASH/ - Obsolete verification (57 lines removed)

### Specialized Fixture Generators (Consolidated into generate_fixtures.py)
generate_large_excel_fixture.py - moved to TRASH/ - Consolidated into generate_fixtures.py (216 lines removed)
generate_large_pdf_fixture.py - moved to TRASH/ - Consolidated into generate_fixtures.py (449 lines removed)
generate_scanned_pdf_fixture.py - moved to TRASH/ - Consolidated into generate_fixtures.py (279 lines removed)
create_fixtures.py - moved to TRASH/ - Superseded by generate_fixtures.py (43 lines removed)

### Test/Debug Scripts
test_installation.py - moved to TRASH/ - One-time validation (205 lines removed)
test_progress_display.py - moved to TRASH/ - UI testing script (163 lines removed)
diagnose_ocr.py - moved to TRASH/ - Debug utility (255 lines removed)
check_package_contents.py - moved to TRASH/ - Package debug tool (95 lines removed)

## Total Lines Removed: 7,708

## Note
All scripts have been moved to `/scripts/TRASH/` for safety. They can be permanently deleted after verification.
