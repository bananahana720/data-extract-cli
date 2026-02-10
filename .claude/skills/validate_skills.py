#!/usr/bin/env python3
"""
Validate packaged .skill files
"""

import os
import zipfile
from pathlib import Path


def validate_skill(skill_file):
    """Validate a packaged .skill file."""
    skill_name = os.path.basename(skill_file).replace(".skill", "")

    validation = {
        "name": skill_name,
        "file": skill_file,
        "exists": os.path.exists(skill_file),
        "size": 0,
        "is_valid_zip": False,
        "has_skill_md": False,
        "contents": [],
        "errors": [],
    }

    if not validation["exists"]:
        validation["errors"].append("File does not exist")
        return validation

    # Get file size
    validation["size"] = os.path.getsize(skill_file)

    # Validate it's a valid zip file
    try:
        with zipfile.ZipFile(skill_file, "r") as zf:
            validation["is_valid_zip"] = True

            # List contents
            validation["contents"] = zf.namelist()

            # Check for required SKILL.md
            skill_md_candidates = [f for f in validation["contents"] if f.endswith("SKILL.md")]
            validation["has_skill_md"] = len(skill_md_candidates) > 0

            if not validation["has_skill_md"]:
                validation["errors"].append("Missing SKILL.md file")

            # Verify zip integrity
            bad_file = zf.testzip()
            if bad_file:
                validation["errors"].append(f"Corrupt file in archive: {bad_file}")

    except zipfile.BadZipFile:
        validation["errors"].append("Invalid zip file format")
    except Exception as e:
        validation["errors"].append(f"Error reading archive: {str(e)}")

    return validation


def main():
    """Validate all packaged skills."""
    skills_dir = Path(__file__).parent / "packaged"

    if not skills_dir.exists():
        print("❌ Packaged directory not found")
        return

    skill_files = list(skills_dir.glob("*.skill"))

    if not skill_files:
        print("❌ No .skill files found")
        return

    print("Validating Claude Code Skills")
    print("=" * 60)

    results = []
    for skill_file in sorted(skill_files):
        result = validate_skill(skill_file)
        results.append(result)

    # Print summary
    print("\n📊 Validation Summary")
    print("=" * 60)

    total = len(results)
    valid = sum(1 for r in results if r["is_valid_zip"] and r["has_skill_md"] and not r["errors"])
    invalid = total - valid

    print(f"Total skills: {total}")
    print(f"Valid: {valid}")
    print(f"Invalid: {invalid}")
    print()

    # Detailed results
    for result in results:
        status = (
            "✅"
            if (result["is_valid_zip"] and result["has_skill_md"] and not result["errors"])
            else "❌"
        )
        size_kb = result["size"] / 1024 if result["size"] > 0 else 0

        print(f"{status} {result['name']:30s} ({size_kb:6.1f} KB)")

        if result["errors"]:
            for error in result["errors"]:
                print(f"    ⚠️  {error}")
        else:
            print(f"    📦 {len(result['contents'])} files")

    print("\n" + "=" * 60)

    if invalid == 0:
        print("✅ All skills validated successfully!")
    else:
        print(f"⚠️  {invalid} skill(s) failed validation")

    # Print file list for each skill
    print("\n\n📁 Detailed Contents")
    print("=" * 60)
    for result in results:
        if result["is_valid_zip"]:
            print(f"\n{result['name']}:")
            for content in sorted(result["contents"]):
                print(f"  - {content}")


if __name__ == "__main__":
    main()
