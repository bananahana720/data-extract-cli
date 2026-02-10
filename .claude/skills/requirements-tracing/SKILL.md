---
name: requirements-tracing
description: Use when - (1) Implementing new features, (2) Adding form fields or UI components, (3) Creating API endpoints, (4) Database schema changes, (5) Need to verify full-stack completeness. Ensures complete implementation across all layers (UI → API → Validation → Business Logic → Database). Prevents partial implementations and ensures every UI element has proper backend support.
---

# Requirements Tracing Protocol

This skill ensures that every feature is completely implemented across all layers of the application stack, preventing partial implementations and orphaned components.

## Core Principle

**Every UI element MUST trace through the entire stack**

```
UI Field → API Parameter → Validation Rule → Business Logic → Database Column
```

No layer can be skipped. No component can be orphaned.

## The Full-Stack Tracing Matrix

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│     UI      │ ──► │     API     │ ──► │ Validation  │ ──► │  Business   │ ──► │  Database   │
│   Layer     │     │   Layer     │     │    Layer    │     │    Logic    │     │    Layer    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
     ↓                   ↓                   ↓                   ↓                   ↓
  ✓ Form field      ✓ Endpoint param    ✓ Input rules     ✓ Processing      ✓ Column exists
  ✓ Display comp    ✓ Response field    ✓ Type check      ✓ Calculations    ✓ Correct type
  ✓ Event handler   ✓ Error handling    ✓ Constraints     ✓ Side effects    ✓ Indexes
```

## Requirements Tracing Workflow

### Step 1: Capture Requirements

```python
def capture_requirements(feature_name):
    """Document all requirements for complete implementation."""

    requirements = {
        'feature': feature_name,
        'ui_components': [],
        'api_endpoints': [],
        'data_fields': [],
        'business_rules': [],
        'database_changes': []
    }

    # Extract from requirements doc/user story
    requirements['ui_components'] = [
        {'name': 'userEmail', 'type': 'input', 'validation': 'email'},
        {'name': 'userPhone', 'type': 'input', 'validation': 'phone'},
        {'name': 'submitButton', 'type': 'button', 'action': 'submit'}
    ]

    requirements['api_endpoints'] = [
        {'method': 'POST', 'path': '/api/users', 'params': ['email', 'phone']},
        {'method': 'GET', 'path': '/api/users/{id}', 'response': ['email', 'phone']}
    ]

    requirements['database_changes'] = [
        {'table': 'users', 'column': 'email', 'type': 'VARCHAR(255)', 'constraint': 'UNIQUE'},
        {'table': 'users', 'column': 'phone', 'type': 'VARCHAR(20)', 'constraint': 'NOT NULL'}
    ]

    return requirements
```

### Step 2: Create Traceability Matrix

```python
def create_traceability_matrix(requirements):
    """Build a matrix showing connections between layers."""

    matrix = []

    for ui_component in requirements['ui_components']:
        trace = {
            'ui_field': ui_component['name'],
            'api_param': None,
            'validation': None,
            'business_logic': None,
            'db_column': None,
            'complete': False
        }

        # Trace through each layer
        trace['api_param'] = find_api_param(ui_component['name'])
        trace['validation'] = find_validation_rule(ui_component['name'])
        trace['business_logic'] = find_business_logic(ui_component['name'])
        trace['db_column'] = find_database_column(ui_component['name'])

        # Check completeness
        trace['complete'] = all([
            trace['api_param'],
            trace['validation'],
            trace['business_logic'],
            trace['db_column']
        ])

        matrix.append(trace)

    return matrix
```

### Step 3: Verify Each Layer

#### UI Layer Verification

```javascript
// Check that all required UI components exist
function verifyUILayer(requirements) {
    const missing = [];

    requirements.ui_components.forEach(component => {
        // Check if component exists in code
        const selector = `[data-field="${component.name}"]`;
        if (!document.querySelector(selector)) {
            missing.push(component.name);
        }

        // Check event handlers
        const handler = window[`handle${component.name}Change`];
        if (!handler && component.type === 'input') {
            missing.push(`${component.name} handler`);
        }
    });

    return {
        complete: missing.length === 0,
        missing: missing
    };
}
```

#### API Layer Verification

```python
def verify_api_layer(requirements):
    """Verify all API endpoints and parameters."""

    issues = []

    for endpoint in requirements['api_endpoints']:
        # Check endpoint exists
        route = app.url_map.get(endpoint['path'])
        if not route:
            issues.append(f"Missing endpoint: {endpoint['method']} {endpoint['path']}")

        # Check parameters
        for param in endpoint.get('params', []):
            if param not in route.arguments:
                issues.append(f"Missing parameter: {param} in {endpoint['path']}")

        # Check response fields
        response_schema = get_response_schema(endpoint['path'])
        for field in endpoint.get('response', []):
            if field not in response_schema:
                issues.append(f"Missing response field: {field}")

    return {
        'complete': len(issues) == 0,
        'issues': issues
    }
```

#### Validation Layer Verification

```python
def verify_validation_layer(requirements):
    """Ensure all inputs have proper validation."""

    validation_rules = {}
    missing_validations = []

    for field in requirements['data_fields']:
        # Check validation exists
        validator = get_validator(field['name'])

        if not validator:
            missing_validations.append(field['name'])
            continue

        # Check validation completeness
        validation_rules[field['name']] = {
            'type_check': hasattr(validator, 'type'),
            'constraints': hasattr(validator, 'constraints'),
            'sanitization': hasattr(validator, 'sanitize'),
            'error_messages': hasattr(validator, 'error_messages')
        }

        # Verify specific rules
        if field.get('validation') == 'email':
            if not validator.includes_email_check():
                missing_validations.append(f"{field['name']} email validation")

        if field.get('required'):
            if not validator.includes_required_check():
                missing_validations.append(f"{field['name']} required validation")

    return {
        'complete': len(missing_validations) == 0,
        'missing': missing_validations,
        'rules': validation_rules
    }
```

#### Business Logic Verification

```python
def verify_business_logic(requirements):
    """Verify business logic handles all fields correctly."""

    logic_coverage = {}
    issues = []

    for rule in requirements['business_rules']:
        # Find implementation
        implementation = find_business_logic_implementation(rule['name'])

        if not implementation:
            issues.append(f"Missing business logic: {rule['name']}")
            continue

        # Check all required fields are processed
        for field in rule['required_fields']:
            if field not in implementation.processed_fields:
                issues.append(f"Business logic doesn't process: {field}")

        # Check calculations/transformations
        if rule.get('calculations'):
            for calc in rule['calculations']:
                if not implementation.includes_calculation(calc):
                    issues.append(f"Missing calculation: {calc}")

        logic_coverage[rule['name']] = {
            'implemented': True,
            'fields_processed': implementation.processed_fields,
            'side_effects': implementation.side_effects
        }

    return {
        'complete': len(issues) == 0,
        'issues': issues,
        'coverage': logic_coverage
    }
```

#### Database Layer Verification

```sql
-- Verify database schema matches requirements
CREATE OR REPLACE FUNCTION verify_database_layer(requirements JSONB)
RETURNS TABLE(
    layer_complete BOOLEAN,
    missing_columns TEXT[],
    type_mismatches TEXT[],
    missing_constraints TEXT[]
) AS $$
DECLARE
    req RECORD;
    col_exists BOOLEAN;
    col_type TEXT;
    issues TEXT[] := '{}';
BEGIN
    FOR req IN SELECT * FROM jsonb_array_elements(requirements->'database_changes')
    LOOP
        -- Check column exists
        SELECT EXISTS(
            SELECT 1 FROM information_schema.columns
            WHERE table_name = req->>'table'
            AND column_name = req->>'column'
        ) INTO col_exists;

        IF NOT col_exists THEN
            missing_columns := array_append(missing_columns,
                format('%s.%s', req->>'table', req->>'column'));
        ELSE
            -- Check type matches
            SELECT data_type INTO col_type
            FROM information_schema.columns
            WHERE table_name = req->>'table'
            AND column_name = req->>'column';

            IF col_type != req->>'type' THEN
                type_mismatches := array_append(type_mismatches,
                    format('%s.%s: expected %s, got %s',
                        req->>'table', req->>'column', req->>'type', col_type));
            END IF;
        END IF;

        -- Check constraints
        -- Additional constraint checking logic here
    END LOOP;

    layer_complete := (
        array_length(missing_columns, 1) IS NULL AND
        array_length(type_mismatches, 1) IS NULL AND
        array_length(missing_constraints, 1) IS NULL
    );

    RETURN QUERY SELECT layer_complete, missing_columns, type_mismatches, missing_constraints;
END;
$$ LANGUAGE plpgsql;
```

### Step 4: Generate Completeness Report

```python
def generate_completeness_report(feature_name):
    """Generate comprehensive traceability report."""

    report = {
        'feature': feature_name,
        'timestamp': datetime.now().isoformat(),
        'layers': {},
        'overall_complete': False,
        'missing_implementations': []
    }

    # Check each layer
    layers = {
        'ui': verify_ui_layer,
        'api': verify_api_layer,
        'validation': verify_validation_layer,
        'business_logic': verify_business_logic,
        'database': verify_database_layer
    }

    for layer_name, verifier in layers.items():
        result = verifier(get_requirements(feature_name))
        report['layers'][layer_name] = result

        if not result['complete']:
            report['missing_implementations'].extend([
                f"{layer_name}: {issue}" for issue in result.get('issues', [])
            ])

    # Overall completeness
    report['overall_complete'] = all(
        layer['complete'] for layer in report['layers'].values()
    )

    # Generate markdown report
    markdown = f"""
# Requirements Traceability Report: {feature_name}

## Summary
- **Feature**: {feature_name}
- **Status**: {'✅ COMPLETE' if report['overall_complete'] else '❌ INCOMPLETE'}
- **Generated**: {report['timestamp']}

## Layer Status

| Layer | Status | Issues |
|-------|--------|--------|
| UI | {'✅' if report['layers']['ui']['complete'] else '❌'} | {len(report['layers']['ui'].get('missing', []))} |
| API | {'✅' if report['layers']['api']['complete'] else '❌'} | {len(report['layers']['api'].get('issues', []))} |
| Validation | {'✅' if report['layers']['validation']['complete'] else '❌'} | {len(report['layers']['validation'].get('missing', []))} |
| Business Logic | {'✅' if report['layers']['business_logic']['complete'] else '❌'} | {len(report['layers']['business_logic'].get('issues', []))} |
| Database | {'✅' if report['layers']['database']['complete'] else '❌'} | {len(report['layers']['database'].get('issues', []))} |

## Missing Implementations
{chr(10).join(f"- {impl}" for impl in report['missing_implementations']) if report['missing_implementations'] else "None - All layers complete!"}

## Traceability Matrix
{generate_matrix_table(report)}
"""

    return report, markdown
```

## Common Incomplete Patterns

### Pattern 1: UI Without Backend

```javascript
// ❌ INCOMPLETE - UI field with no backend
<input name="userMiddleName" onChange={handleChange} />

// But in API:
// No 'middleName' parameter
// No database column
// No validation rule
```

### Pattern 2: Database Without UI

```sql
-- ❌ INCOMPLETE - Database column with no UI
ALTER TABLE users ADD COLUMN preferred_language VARCHAR(10);

-- But in UI:
-- No input field for preferred_language
-- No display component
-- No API endpoint parameter
```

### Pattern 3: API Without Validation

```python
# ❌ INCOMPLETE - API accepts parameter without validation
@app.route('/api/users', methods=['POST'])
def create_user():
    email = request.json.get('email')  # No validation!
    phone = request.json.get('phone')  # No format check!
    # Process without validating...
```

## Integration Patterns

### With verification-loop
```python
# requirements-tracing identifies missing pieces
missing = trace_requirements(feature)

# verification-loop ensures they're all implemented
for layer in missing:
    implement_layer(layer)
    verify_implementation(layer)
    # Loop until complete
```

### With scope-completeness
```python
# scope-completeness finds all files
all_files = find_all_components()

# requirements-tracing ensures they're connected
for file in all_files:
    verify_traces_properly(file)
```

## End-to-End Testing Template

```python
def test_feature_completeness(feature_name):
    """Test that feature works end-to-end."""

    # 1. UI can submit data
    ui_response = simulate_ui_submission({
        'email': 'test@example.com',
        'phone': '555-1234'
    })
    assert ui_response.status == 200

    # 2. API processes correctly
    api_response = call_api_endpoint('/api/users', {
        'email': 'test@example.com',
        'phone': '555-1234'
    })
    assert api_response.status == 201

    # 3. Validation works
    invalid_response = call_api_endpoint('/api/users', {
        'email': 'not-an-email',
        'phone': 'invalid'
    })
    assert invalid_response.status == 400
    assert 'email' in invalid_response.errors

    # 4. Business logic executes
    user = get_user_by_email('test@example.com')
    assert user.phone_formatted == '+1 (555) 123-4567'  # Business logic formatted it

    # 5. Database stores correctly
    db_record = query_database(
        "SELECT email, phone FROM users WHERE email = %s",
        ['test@example.com']
    )
    assert db_record.email == 'test@example.com'
    assert db_record.phone == '5551234'  # Stored normalized

    return "✅ Feature complete across all layers"
```

## Scripts

### Traceability Analyzer
See [scripts/analyze_traces.py](scripts/analyze_traces.py) - Analyzes codebase for traceability

### Layer Validator
See [scripts/validate_layers.py](scripts/validate_layers.py) - Validates each layer implementation

## References

- Full-stack patterns: [references/fullstack_patterns.md](references/fullstack_patterns.md)
- Layer communication: [references/layer_communication.md](references/layer_communication.md)

## Critical Reminders

- **No Orphans**: Every UI element must have backend support
- **No Ghosts**: Every database field must be accessible from UI
- **Complete Chain**: Data must flow through all layers
- **Bidirectional**: Both create/update AND read/display must work
