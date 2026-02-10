---
name: change-tracking
description: Use when - (1) Before making commits, (2) After implementing features, (3) Preparing releases, (4) Documenting bug fixes, (5) Any significant code changes. Ensures proper change documentation through CHANGELOG updates and commit tracking. Maintains project history and facilitates collaboration.
---

# Change Tracking Protocol

This skill ensures all changes are properly documented through CHANGELOG maintenance and structured commit tracking.

## Core Principle

**Every change must be documented**

- ALWAYS update CHANGELOG before commits
- Format: Date + categorized changes
- Use conventional commit format
- Track breaking changes explicitly

## CHANGELOG Management

### Standard CHANGELOG Format

```markdown
# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security vulnerability fixes

## [1.2.0] - 2024-01-15

### Added
- User authentication system
- Email notification service
- API rate limiting

### Fixed
- Memory leak in data processor
- SQL injection vulnerability in search
```

### Update CHANGELOG Workflow

```python
def update_changelog(changes):
    """Update CHANGELOG with new changes."""

    changelog_path = Path("CHANGELOG.md")

    # Read existing content
    if changelog_path.exists():
        content = changelog_path.read_text()
    else:
        content = create_initial_changelog()

    # Parse sections
    sections = parse_changelog_sections(content)

    # Add new changes to Unreleased
    for change in changes:
        category = determine_category(change)
        sections['Unreleased'][category].append(
            f"- {change['description']}"
        )

    # Write updated changelog
    new_content = format_changelog(sections)
    changelog_path.write_text(new_content)

    print(f"✅ Updated CHANGELOG with {len(changes)} changes")
```

## Change Categories

```python
def determine_category(change):
    """Determine which CHANGELOG category a change belongs to."""

    keywords = {
        'Added': ['new', 'add', 'create', 'implement', 'introduce'],
        'Changed': ['update', 'modify', 'refactor', 'improve', 'enhance'],
        'Deprecated': ['deprecate', 'obsolete', 'phase out'],
        'Removed': ['remove', 'delete', 'drop', 'eliminate'],
        'Fixed': ['fix', 'resolve', 'repair', 'correct', 'patch'],
        'Security': ['security', 'vulnerability', 'CVE', 'exploit']
    }

    change_lower = change['description'].lower()

    for category, words in keywords.items():
        if any(word in change_lower for word in words):
            return category

    # Default to Changed if unclear
    return 'Changed'
```

## Commit Message Standards

### Conventional Commits Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types and Examples

```python
COMMIT_TYPES = {
    'feat': 'New feature for the user',
    'fix': 'Bug fix for the user',
    'docs': 'Documentation only changes',
    'style': 'Formatting, missing semicolons, etc',
    'refactor': 'Code change that neither fixes a bug nor adds a feature',
    'perf': 'Code change that improves performance',
    'test': 'Adding missing tests',
    'chore': 'Maintain. Changes to build process, etc',
    'revert': 'Reverts a previous commit',
    'build': 'Changes to build system or dependencies',
    'ci': 'Changes to CI configuration files'
}

# Examples
examples = [
    "feat(auth): add OAuth2 login support",
    "fix(api): resolve memory leak in data processor",
    "docs(readme): update installation instructions",
    "refactor(utils): simplify date formatting logic",
    "perf(search): optimize database queries",
    "test(user): add integration tests for registration",
    "chore(deps): update dependencies to latest versions",
    "build(docker): optimize container size",
    "ci(github): add automated testing workflow"
]
```

## Automated Change Detection

```python
def detect_changes_for_changelog():
    """Automatically detect changes for CHANGELOG update."""

    changes = []

    # Get uncommitted changes
    result = subprocess.run(
        ["git", "diff", "--name-status"],
        capture_output=True,
        text=True
    )

    for line in result.stdout.splitlines():
        status, file_path = line.split(None, 1)

        change = {
            'file': file_path,
            'status': status,
            'description': generate_change_description(status, file_path)
        }

        changes.append(change)

    # Group by feature/module
    grouped = group_changes_by_feature(changes)

    return grouped

def generate_change_description(status, file_path):
    """Generate human-readable change description."""

    # Analyze file content for context
    if status == 'A':
        return f"Add {describe_file_purpose(file_path)}"
    elif status == 'M':
        return f"Update {describe_file_purpose(file_path)}"
    elif status == 'D':
        return f"Remove {describe_file_purpose(file_path)}"
    else:
        return f"Modify {file_path}"
```

## Version Management

```python
def prepare_release(version):
    """Prepare a new release with proper change tracking."""

    # Move Unreleased to new version
    changelog = read_changelog()
    unreleased = changelog.get('Unreleased', {})

    if not any(unreleased.values()):
        raise ValueError("No unreleased changes to release")

    # Create new version entry
    today = datetime.now().strftime("%Y-%m-%d")
    changelog[f"{version} - {today}"] = unreleased
    changelog['Unreleased'] = create_empty_sections()

    # Write updated changelog
    write_changelog(changelog)

    # Create git tag
    subprocess.run(["git", "tag", "-a", version, "-m", f"Release {version}"])

    # Generate release notes
    release_notes = generate_release_notes(unreleased)

    return release_notes
```

## Breaking Changes Tracking

```python
def track_breaking_changes(change):
    """Special handling for breaking changes."""

    indicators = [
        'BREAKING CHANGE:',
        'BREAKING:',
        '!:',  # In commit type
        'incompatible',
        'migration required'
    ]

    if any(ind in change['description'] for ind in indicators):
        # Add to special breaking changes section
        add_to_breaking_changes(change)

        # Suggest major version bump
        current_version = get_current_version()
        suggested = suggest_version_bump(current_version, 'major')

        print(f"⚠️  BREAKING CHANGE detected!")
        print(f"Consider version bump: {current_version} → {suggested}")
```

## Integration with Git Hooks

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check if CHANGELOG was updated
if ! git diff --cached --name-only | grep -q "CHANGELOG.md"; then
    echo "⚠️  Warning: CHANGELOG.md not updated"
    echo "Have you documented your changes?"
    read -p "Continue without updating CHANGELOG? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
```

### Commit Message Validation

```python
def validate_commit_message(message):
    """Validate commit message follows conventions."""

    pattern = r'^(feat|fix|docs|style|refactor|perf|test|chore|revert|build|ci)(\(.+\))?: .+'

    lines = message.strip().split('\n')
    if not lines:
        return False, "Empty commit message"

    if not re.match(pattern, lines[0]):
        return False, f"Invalid format. Expected: type(scope): subject"

    # Check for breaking changes
    if 'BREAKING' in message:
        if 'BREAKING CHANGE:' not in message:
            return False, "Breaking changes must use 'BREAKING CHANGE:' format"

    return True, "Valid commit message"
```

## Change Summary Generation

```python
def generate_change_summary(start_date=None, end_date=None):
    """Generate a summary of changes for a time period."""

    if not start_date:
        start_date = datetime.now() - timedelta(days=7)
    if not end_date:
        end_date = datetime.now()

    # Get commits in date range
    commits = get_commits_in_range(start_date, end_date)

    summary = {
        'period': f"{start_date:%Y-%m-%d} to {end_date:%Y-%m-%d}",
        'total_commits': len(commits),
        'contributors': set(),
        'changes_by_type': {},
        'files_changed': set()
    }

    for commit in commits:
        # Parse commit type
        commit_type = extract_commit_type(commit['message'])
        summary['changes_by_type'][commit_type] = \
            summary['changes_by_type'].get(commit_type, 0) + 1

        # Track contributors
        summary['contributors'].add(commit['author'])

        # Track files
        summary['files_changed'].update(commit['files'])

    return format_summary_report(summary)
```

## Scripts

### CHANGELOG Updater
See [scripts/update_changelog.py](scripts/update_changelog.py) - Automated CHANGELOG updates

### Change Analyzer
See [scripts/analyze_changes.py](scripts/analyze_changes.py) - Analyzes uncommitted changes

## References

- Keep a Changelog: [references/keep_a_changelog.md](references/keep_a_changelog.md)
- Semantic Versioning: [references/semver.md](references/semver.md)

## Critical Reminders

- **Update Before Commit**: CHANGELOG should reflect current state
- **Be Specific**: Vague entries like "bug fixes" are useless
- **Track Breaking Changes**: Users need migration guidance
- **Maintain History**: Never delete old entries
