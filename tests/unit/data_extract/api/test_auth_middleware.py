from __future__ import annotations

import asyncio
import os

os.environ.setdefault("DATA_EXTRACT_UI_HOME", "/tmp/data-extract-ui-tests")

from starlette.requests import Request

from data_extract.api import main as main_module
from data_extract.api.routers import auth as auth_router_module


def _request_for(
    path: str,
    api_key: str | None = None,
    session_cookie: str | None = None,
) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if api_key is not None:
        headers.append((b"x-api-key", api_key.encode("utf-8")))
    if session_cookie is not None:
        cookie = f"{auth_router_module.SESSION_COOKIE_NAME}={session_cookie}"
        headers.append((b"cookie", cookie.encode("utf-8")))
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


def test_api_key_guard_requires_header_or_session_cookie_when_configured(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DATA_EXTRACT_API_KEY", "test-secret")
    monkeypatch.setenv("DATA_EXTRACT_API_SESSION_SECRET", "test-session-secret")

    async def fake_call_next(_request: Request):
        from fastapi.responses import JSONResponse

        return JSONResponse({"ok": True}, status_code=200)

    valid_token, _expires_at = auth_router_module.create_session_token()
    unauthorized = asyncio.run(
        main_module.api_key_guard(_request_for("/api/v1/health"), fake_call_next)
    )
    header_authorized = asyncio.run(
        main_module.api_key_guard(
            _request_for("/api/v1/health", api_key="test-secret"), fake_call_next
        )
    )
    cookie_authorized = asyncio.run(
        main_module.api_key_guard(
            _request_for("/api/v1/health", session_cookie=valid_token), fake_call_next
        )
    )
    invalid_cookie = asyncio.run(
        main_module.api_key_guard(
            _request_for("/api/v1/health", session_cookie="invalid-session-token"),
            fake_call_next,
        )
    )

    assert unauthorized.status_code == 401
    assert header_authorized.status_code == 200
    assert cookie_authorized.status_code == 200
    assert invalid_cookie.status_code == 401


def test_api_key_guard_allows_auth_session_bootstrap_without_prior_auth(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DATA_EXTRACT_API_KEY", "test-secret")

    async def fake_call_next(_request: Request):
        from fastapi.responses import JSONResponse

        return JSONResponse({"ok": True}, status_code=200)

    response = asyncio.run(
        main_module.api_key_guard(_request_for("/api/v1/auth/session"), fake_call_next)
    )

    assert response.status_code == 200
