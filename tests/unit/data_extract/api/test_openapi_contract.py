from __future__ import annotations

import os

os.environ.setdefault("DATA_EXTRACT_UI_HOME", "/tmp/data-extract-ui-tests")

from data_extract.api.main import app


def test_openapi_exposes_v1_contract_paths() -> None:
    schema = app.openapi()
    paths = schema.get("paths", {})

    expected = {
        "/api/v1/jobs/process": {"post"},
        "/api/v1/jobs": {"get"},
        "/api/v1/jobs/{job_id}": {"get"},
        "/api/v1/jobs/{job_id}/retry-failures": {"post"},
        "/api/v1/jobs/{job_id}/artifacts": {"get", "delete"},
        "/api/v1/jobs/{job_id}/artifacts/{artifact_path}": {"get"},
        "/api/v1/sessions": {"get"},
        "/api/v1/sessions/{session_id}": {"get"},
        "/api/v1/config/effective": {"get"},
        "/api/v1/config/current-preset": {"get"},
        "/api/v1/config/presets": {"get"},
        "/api/v1/config/presets/{name}/preview": {"get"},
        "/api/v1/config/presets/{name}/apply": {"post"},
        "/api/v1/health": {"get"},
    }

    for path, methods in expected.items():
        assert path in paths, f"Missing OpenAPI path: {path}"
        actual_methods = set(paths[path].keys())
        assert methods.issubset(
            actual_methods
        ), f"Path {path} is missing methods {methods - actual_methods}"


def test_openapi_process_request_schema_includes_idempotency_key() -> None:
    schema = app.openapi()
    components = schema.get("components", {}).get("schemas", {})

    process_schemas = [
        value
        for value in components.values()
        if isinstance(value, dict) and "properties" in value and "input_path" in value["properties"]
    ]
    assert process_schemas, "Expected a process request schema with input_path"

    has_idempotency = any(
        "idempotency_key" in schema_item.get("properties", {}) for schema_item in process_schemas
    )
    assert has_idempotency, "Expected idempotency_key in process request schema"
