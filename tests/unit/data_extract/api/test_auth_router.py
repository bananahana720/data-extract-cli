from __future__ import annotations

import pytest
from fastapi import HTTPException, Response
from starlette.requests import Request

from data_extract.api.routers import auth as auth_router_module


def _request_for(path: str, session_cookie: str | None = None) -> Request:
    headers: list[tuple[bytes, bytes]] = []
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


def test_create_session_sets_cookie_when_api_key_matches(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_EXTRACT_API_KEY", "test-secret")
    monkeypatch.setenv("DATA_EXTRACT_API_SESSION_SECRET", "session-secret")

    request = _request_for("/api/v1/auth/session")
    response = Response()
    payload = auth_router_module.SessionLoginRequest(api_key="test-secret")
    result = auth_router_module.create_session(payload, request, response)

    assert result.authenticated is True
    assert result.api_key_configured is True
    assert result.expires_at is not None
    set_cookie = response.headers.get("set-cookie", "")
    assert auth_router_module.SESSION_COOKIE_NAME in set_cookie

    token = set_cookie.split(f"{auth_router_module.SESSION_COOKIE_NAME}=", 1)[1].split(";", 1)[0]
    authenticated_request = _request_for("/api/v1/health", session_cookie=token)
    assert auth_router_module.has_valid_session_cookie(authenticated_request) is True


def test_create_session_rejects_invalid_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_EXTRACT_API_KEY", "test-secret")
    monkeypatch.setenv("DATA_EXTRACT_API_SESSION_SECRET", "session-secret")

    request = _request_for("/api/v1/auth/session")
    response = Response()
    payload = auth_router_module.SessionLoginRequest(api_key="wrong-secret")

    with pytest.raises(HTTPException) as exc_info:
        auth_router_module.create_session(payload, request, response)
    assert exc_info.value.status_code == 401


def test_get_session_status_reflects_cookie_validity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_EXTRACT_API_KEY", "test-secret")
    monkeypatch.setenv("DATA_EXTRACT_API_SESSION_SECRET", "session-secret")

    token, _expires_at = auth_router_module.create_session_token()
    authenticated = auth_router_module.get_session_status(
        _request_for("/api/v1/auth/session", session_cookie=token)
    )
    unauthenticated = auth_router_module.get_session_status(_request_for("/api/v1/auth/session"))

    assert authenticated.authenticated is True
    assert authenticated.api_key_configured is True
    assert authenticated.expires_at is not None
    assert unauthenticated.authenticated is False
    assert unauthenticated.api_key_configured is True


def test_delete_session_clears_cookie(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_EXTRACT_API_KEY", "test-secret")

    request = _request_for("/api/v1/auth/session")
    response = Response()
    result = auth_router_module.delete_session(request, response)

    assert result.authenticated is False
    assert result.api_key_configured is True
    assert auth_router_module.SESSION_COOKIE_NAME in response.headers.get("set-cookie", "")
