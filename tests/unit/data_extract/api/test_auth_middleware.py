from __future__ import annotations

import asyncio
import os

os.environ.setdefault("DATA_EXTRACT_UI_HOME", "/tmp/data-extract-ui-tests")

from starlette.requests import Request

from data_extract.api import main as main_module


def _request_for(path: str, api_key: str | None = None) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if api_key is not None:
        headers.append((b"x-api-key", api_key.encode("utf-8")))
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": headers,
        "query_string": b"",
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
    }
    return Request(scope)  # type: ignore[arg-type]


def test_api_key_guard_requires_header_when_configured(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DATA_EXTRACT_API_KEY", "test-secret")

    async def fake_call_next(_request: Request):
        from fastapi.responses import JSONResponse

        return JSONResponse({"ok": True}, status_code=200)

    unauthorized = asyncio.run(
        main_module.api_key_guard(_request_for("/api/v1/health"), fake_call_next)
    )
    authorized = asyncio.run(
        main_module.api_key_guard(
            _request_for("/api/v1/health", api_key="test-secret"), fake_call_next
        )
    )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
