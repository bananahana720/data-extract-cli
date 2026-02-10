#!/usr/bin/env python3
"""
Create 100-file performance test batch by duplicating existing fixtures.

This script creates a batch of 100 files for performance testing:
- 40 PDFs (mix of sizes: 1-50 pages)
- 30 DOCX files (mix of sizes: 1-20 pages)
- 20 XLSX files (mix of sizes: 10-1000 rows)
- 10 mixed files (PPTX, CSV, images)

Strategy: Duplicate existing fixtures with numbered names to reach target counts.
This is sufficient for performance testing (throughput and memory validation).
"""

import shutil
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent

# Source and target paths
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"
BATCH_DIR = PROJECT_ROOT / "tests" / "performance" / "batch_100_files"

# Ensure batch directory exists
(BATCH_DIR / "pdfs").mkdir(parents=True, exist_ok=True)
(BATCH_DIR / "docx").mkdir(parents=True, exist_ok=True)
(BATCH_DIR / "xlsx").mkdir(parents=True, exist_ok=True)
(BATCH_DIR / "mixed").mkdir(parents=True, exist_ok=True)


def copy_files_with_duplication(
    source_pattern: str, target_dir: Path, target_count: int, file_type: str
):
    """Copy files from source, duplicating as needed to reach target count."""
    # Find all source files
    source_files = list(FIXTURES_DIR.rglob(source_pattern))

    if not source_files:
        print(f"Warning: No {file_type} files found matching {source_pattern}")
        return 0

    print(f"Found {len(source_files)} {file_type} source files")

    # Copy files in round-robin fashion until we reach target count
    copied_count = 0
    file_index = 0

    while copied_count < target_count:
        source_file = source_files[file_index % len(source_files)]
        target_file = target_dir / f"{file_type}_{copied_count + 1:03d}{source_file.suffix}"

        shutil.copy2(source_file, target_file)
        copied_count += 1
        file_index += 1

        if copied_count % 10 == 0:
            print(f"  Copied {copied_count}/{target_count} {file_type} files...")

    print(f"[OK] Completed {copied_count} {file_type} files")
    return copied_count


def main():
    """Create the 100-file performance batch."""
    print("Creating 100-file performance test batch...")
    print(f"Source: {FIXTURES_DIR}")
    print(f"Target: {BATCH_DIR}")
    print()

    total_files = 0

    # 40 PDFs
    print("1. Creating PDF batch (40 files)...")
    total_files += copy_files_with_duplication("*.pdf", BATCH_DIR / "pdfs", 40, "pdf")
    print()

    # 30 DOCX
    print("2. Creating DOCX batch (30 files)...")
    total_files += copy_files_with_duplication("*.docx", BATCH_DIR / "docx", 30, "docx")
    print()

    # 20 XLSX
    print("3. Creating XLSX batch (20 files)...")
    total_files += copy_files_with_duplication("*.xlsx", BATCH_DIR / "xlsx", 20, "xlsx")
    print()

    # 10 mixed (PPTX, CSV, images)
    print("4. Creating mixed batch (10 files)...")
    mixed_count = 0

    # PPTX files
    pptx_files = list(FIXTURES_DIR.rglob("*.pptx"))
    for i, source_file in enumerate(pptx_files[:5]):  # Up to 5 PPTX
        if mixed_count >= 10:
            break
        target_file = BATCH_DIR / "mixed" / f"mixed_{mixed_count + 1:03d}{source_file.suffix}"
        shutil.copy2(source_file, target_file)
        mixed_count += 1

    # If we don't have enough PPTX, duplicate
    while mixed_count < 5 and pptx_files:
        source_file = pptx_files[0]
        target_file = BATCH_DIR / "mixed" / f"mixed_{mixed_count + 1:03d}{source_file.suffix}"
        shutil.copy2(source_file, target_file)
        mixed_count += 1

    # CSV files (if any exist)
    csv_files = list(FIXTURES_DIR.rglob("*.csv"))
    for i, source_file in enumerate(csv_files[:3]):  # Up to 3 CSV
        if mixed_count >= 10:
            break
        target_file = BATCH_DIR / "mixed" / f"mixed_{mixed_count + 1:03d}{source_file.suffix}"
        shutil.copy2(source_file, target_file)
        mixed_count += 1

    # Image files (PNG, JPG)
    image_files = list(FIXTURES_DIR.rglob("*.png")) + list(FIXTURES_DIR.rglob("*.jpg"))
    for i, source_file in enumerate(image_files):
        if mixed_count >= 10:
            break
        target_file = BATCH_DIR / "mixed" / f"mixed_{mixed_count + 1:03d}{source_file.suffix}"
        shutil.copy2(source_file, target_file)
        mixed_count += 1

    # If still not enough, duplicate existing mixed files
    if mixed_count < 10:
        existing_mixed = list((BATCH_DIR / "mixed").glob("*"))
        if existing_mixed:
            while mixed_count < 10:
                source_file = existing_mixed[mixed_count % len(existing_mixed)]
                target_file = (
                    BATCH_DIR / "mixed" / f"mixed_{mixed_count + 1:03d}{source_file.suffix}"
                )
                shutil.copy2(source_file, target_file)
                mixed_count += 1

    total_files += mixed_count
    print(f"[OK] Completed {mixed_count} mixed files")
    print()

    print("=" * 60)
    print(f"[OK] Performance batch created: {total_files} files")
    print(f"  Location: {BATCH_DIR}")
    print("  Breakdown:")
    print(f"    - PDFs:  40 files in {BATCH_DIR / 'pdfs'}")
    print(f"    - DOCX:  30 files in {BATCH_DIR / 'docx'}")
    print(f"    - XLSX:  20 files in {BATCH_DIR / 'xlsx'}")
    print(f"    - Mixed: {mixed_count} files in {BATCH_DIR / 'mixed'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
