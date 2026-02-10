#!/usr/bin/env python3
"""
Package skills into .skill files (zip archives with .skill extension)
"""

import os
import zipfile
from pathlib import Path


def package_skill(skill_dir, output_dir):
    """Package a skill directory into a .skill file."""
    skill_name = os.path.basename(skill_dir)
    skill_file = os.path.join(output_dir, f"{skill_name}.skill.zip")

    print(f"Packaging {skill_name}...")

    with zipfile.ZipFile(skill_file, "w", zipfile.ZIP_DEFLATED) as zf:
        # Walk through the skill directory
        for root, dirs, files in os.walk(skill_dir):
            # Skip the TRASH directory
            if "TRASH" in dirs:
                dirs.remove("TRASH")

            for file in files:
                file_path = os.path.join(root, file)
                # Calculate the archive name (relative path from skill dir)
                arcname = os.path.relpath(file_path, os.path.dirname(skill_dir))
                zf.write(file_path, arcname)
                print(f"  Added: {arcname}")

    print(f"✅ Created: {skill_file}")
    return skill_file


def main():
    """Package all skills."""
    # Use project's .claude/skills directory
    script_dir = Path(__file__).parent
    skills_dir = script_dir
    output_dir = skills_dir / "packaged"

    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True)

    # List of skills to package
    skills = [
        "git-safety",
        "root-cause-analysis",
        "verification-loop",
        "scope-completeness",
        "no-deviation",
        "requirements-tracing",
        "design-patterns",
        "modern-tools",
        "infrastructure-orchestration",
        "file-organization",
        "change-tracking",
        "async-python-patterns",
        "langchain-architecture",
        "llm-evaluation",
        "ml-pipeline-workflow",
        "prompt-engineering-patterns",
        "python-packaging",
        "python-performance-optimization",
        "python-testing-patterns",
        "rag-implementation",
        "uv-package-manager",
    ]

    print("Packaging Claude Code Skills")
    print("=" * 40)

    packaged = []
    for skill in skills:
        skill_path = skills_dir / skill
        if skill_path.exists():
            result = package_skill(skill_path, output_dir)
            packaged.append(result)
        else:
            print(f"⚠️  Skill not found: {skill}")

    print("\n" + "=" * 40)
    print(f"✅ Packaged {len(packaged)} skills:")
    for pkg in packaged:
        print(f"  - {os.path.basename(pkg)}")


if __name__ == "__main__":
    main()
