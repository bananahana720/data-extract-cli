---
name: design-patterns
description: Use when - (1) Creating UI components, (2) Implementing new features, (3) Architecture decisions, (4) Writing new modules, (5) Need to maintain consistency. Enforces design consistency by studying and reusing existing patterns before creating new components. Prevents reinventing the wheel and ensures design coherence.
---

# Design Patterns Protocol

This skill ensures design consistency by studying existing patterns before implementation, preventing redundant solutions and maintaining coherence.

## Core Principle

**Study existing patterns BEFORE creating anything new**

- MUST study 3-5 existing similar components/patterns
- MUST extract and document patterns found
- MUST reuse existing components (create new ONLY if no alternative)
- MUST maintain consistency with established patterns

## Pattern Discovery Workflow

### Step 1: Identify Similar Implementations

```python
def find_similar_patterns(task_type, feature_name):
    """Find existing patterns similar to what needs implementing."""

    patterns_found = {
        'ui_components': [],
        'api_patterns': [],
        'data_structures': [],
        'workflows': []
    }

    # Search strategies
    search_terms = generate_search_terms(task_type, feature_name)

    for term in search_terms:
        # Search UI components
        ui_matches = search_codebase(f"component.*{term}", "tsx", "jsx")
        patterns_found['ui_components'].extend(ui_matches)

        # Search API patterns
        api_matches = search_codebase(f"route.*{term}|endpoint.*{term}", "py", "js")
        patterns_found['api_patterns'].extend(api_matches)

    return patterns_found
```

### Step 2: Extract Patterns

```python
def extract_patterns(similar_implementations):
    """Extract reusable patterns from existing code."""

    patterns = {
        'colors': set(),
        'typography': set(),
        'spacing': set(),
        'components': set(),
        'layouts': set(),
        'api_structure': set(),
        'error_handling': set()
    }

    for impl in similar_implementations:
        # Extract visual patterns
        patterns['colors'].update(extract_colors(impl))
        patterns['typography'].update(extract_fonts(impl))
        patterns['spacing'].update(extract_spacing(impl))

        # Extract structural patterns
        patterns['components'].update(extract_components(impl))
        patterns['api_structure'].update(extract_api_patterns(impl))

    return consolidate_patterns(patterns)
```

### Step 3: Document Findings

```markdown
## Pattern Analysis Report

### Similar Implementations Found
1. UserProfileCard component - src/components/UserProfileCard.tsx
2. TeamMemberCard component - src/components/TeamMemberCard.tsx
3. ContactCard component - src/components/ContactCard.tsx

### Extracted Patterns
- **Colors**: Primary: #007bff, Secondary: #6c757d, Background: #f8f9fa
- **Typography**: Headers: Roboto 24px bold, Body: Open Sans 16px
- **Spacing**: Padding: 16px, Margin: 8px between elements
- **Components**: All use Card wrapper, Avatar component, ActionButtons
- **Layout**: Flexbox column, centered alignment, 320px max-width

### Recommendation
✅ REUSE: Extend existing Card component
❌ AVOID: Creating new card from scratch
```

## UI Pattern Compliance

```javascript
// Before implementing any UI
function enforceDesignConsistency(newComponent) {
    // Step 1: Find similar components
    const similar = findSimilarComponents(newComponent.type);

    if (similar.length === 0) {
        console.warn("No similar components found - document new pattern");
        return createNewPattern(newComponent);
    }

    // Step 2: Extract patterns
    const patterns = {
        colors: extractColors(similar),
        fonts: extractTypography(similar),
        spacing: extractSpacing(similar),
        components: extractReusableComponents(similar)
    };

    // Step 3: Apply patterns
    return applyPatterns(newComponent, patterns);
}
```

## API Pattern Compliance

```python
def enforce_api_patterns(new_endpoint):
    """Ensure API follows existing patterns."""

    # Find similar endpoints
    similar_endpoints = find_similar_api_endpoints(new_endpoint.resource)

    if not similar_endpoints:
        raise DesignError("No similar API patterns found - consult team")

    # Extract patterns
    patterns = {
        'url_structure': extract_url_pattern(similar_endpoints),
        'http_methods': extract_method_patterns(similar_endpoints),
        'response_format': extract_response_format(similar_endpoints),
        'error_handling': extract_error_patterns(similar_endpoints),
        'authentication': extract_auth_pattern(similar_endpoints)
    }

    # Apply patterns
    return apply_api_patterns(new_endpoint, patterns)
```

## Common Pattern Categories

### Visual Patterns
- Color schemes
- Typography scales
- Spacing systems
- Border styles
- Shadow effects
- Animation timings

### Component Patterns
- Form layouts
- Navigation structures
- Modal behaviors
- List presentations
- Card designs
- Button variants

### Code Patterns
- Error handling
- State management
- API communication
- Data validation
- Testing approaches
- Documentation style

## Pattern Reuse Decision Tree

```
Need to implement X
        ↓
Search for similar X
        ↓
Found similar?
    ├─Yes→ Can extend/modify?
    │       ├─Yes→ EXTEND existing
    │       └─No→ Why not? Document reason
    └─No→ Search broader patterns
            ↓
        Found patterns?
            ├─Yes→ APPLY patterns to new implementation
            └─No→ CREATE new pattern (document thoroughly)
```

## Integration with BMAD

When working with BMAD agents/workflows:
1. Check agent-manifest.csv for similar agents
2. Review workflow-manifest.csv for existing workflows
3. Study files-manifest.csv for file patterns
4. Maintain consistency with manifest structures

## Scripts

### Pattern Finder
See [scripts/find_patterns.py](scripts/find_patterns.py) - Discovers existing patterns

### Pattern Validator
See [scripts/validate_pattern_compliance.py](scripts/validate_pattern_compliance.py) - Ensures pattern compliance

## Critical Reminders

- **Research First**: Always search before creating
- **Document Patterns**: Record why patterns were chosen
- **Maintain Consistency**: Small deviations compound into chaos
- **Reuse > Create**: Extending is better than duplicating
