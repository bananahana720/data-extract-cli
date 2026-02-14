"""Session authentication API routes and helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

API_KEY_ENV = "DATA_EXTRACT_API_KEY"
SESSION_COOKIE_NAME = "data_extract_session"
SESSION_SECRET_ENV = "DATA_EXTRACT_API_SESSION_SECRET"
SESSION_TTL_ENV = "DATA_EXTRACT_API_SESSION_TTL_SECONDS"
SESSION_TTL_SECONDS_DEFAULT = 900
SESSION_TTL_SECONDS_MAX = 86_400
SESSION_TOKEN_VERSION = 1

# Fallback secret keeps signing stable for the life of the process.
_FALLBACK_SESSION_SECRET = secrets.token_hex(32)


class SessionLoginRequest(BaseModel):
    """Credentials payload for session login."""

    api_key: str


class SessionStatusResponse(BaseModel):
    """Authentication status payload."""

    authenticated: bool
    api_key_configured: bool
    expires_at: datetime | None = None


def _configured_api_key() -> str:
    return os.environ.get(API_KEY_ENV, "").strip()


def _session_ttl_seconds() -> int:
    raw = os.environ.get(SESSION_TTL_ENV, str(SESSION_TTL_SECONDS_DEFAULT)).strip()
    try:
        resolved = int(raw)
    except ValueError:
        resolved = SESSION_TTL_SECONDS_DEFAULT
    return max(1, min(resolved, SESSION_TTL_SECONDS_MAX))


def _session_secret() -> str:
    explicit_secret = os.environ.get(SESSION_SECRET_ENV, "").strip()
    if explicit_secret:
        return explicit_secret
    configured_key = _configured_api_key()
    if configured_key:
        return configured_key
    return _FALLBACK_SESSION_SECRET


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))


def _sign_payload(payload_segment: str) -> str:
    digest = hmac.new(
        _session_secret().encode("utf-8"),
        payload_segment.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(digest)


def _decode_expiry(token: str) -> datetime | None:
    if "." not in token:
        return None

    payload_segment, signature = token.split(".", 1)
    expected_signature = _sign_payload(payload_segment)
    if not hmac.compare_digest(signature, expected_signature):
        return None

    try:
        payload_raw = _b64url_decode(payload_segment)
        payload = json.loads(payload_raw)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None
    if payload.get("v") != SESSION_TOKEN_VERSION:
        return None

    exp = payload.get("exp")
    if not isinstance(exp, int):
        return None

    now_epoch = int(time.time())
    if exp <= now_epoch:
        return None

    return datetime.fromtimestamp(exp, tz=timezone.utc)


def has_valid_session_cookie(request: Request) -> bool:
    """Check whether the incoming request contains a valid auth session cookie."""
    if not _configured_api_key():
        return False
    cookie_value = request.cookies.get(SESSION_COOKIE_NAME, "")
    return _decode_expiry(cookie_value) is not None


def create_session_token() -> tuple[str, datetime]:
    expires_at_epoch = int(time.time()) + _session_ttl_seconds()
    payload_segment = _b64url_encode(
        json.dumps(
            {"v": SESSION_TOKEN_VERSION, "exp": expires_at_epoch},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    token = f"{payload_segment}.{_sign_payload(payload_segment)}"
    return token, datetime.fromtimestamp(expires_at_epoch, tz=timezone.utc)


def _set_auth_cookie(request: Request, response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=_session_ttl_seconds(),
        path="/",
        httponly=True,
        samesite="strict",
        secure=request.url.scheme == "https",
    )


def _clear_auth_cookie(request: Request, response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="strict",
        secure=request.url.scheme == "https",
    )


@router.post("/session", response_model=SessionStatusResponse)
def create_session(
    payload: SessionLoginRequest,
    request: Request,
    response: Response,
) -> SessionStatusResponse:
    """Create short-lived signed session cookie from API key credentials."""
    configured_key = _configured_api_key()
    if not configured_key:
        _clear_auth_cookie(request, response)
        return SessionStatusResponse(authenticated=True, api_key_configured=False)

    if payload.api_key.strip() != configured_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    token, expires_at = create_session_token()
    _set_auth_cookie(request, response, token)
    return SessionStatusResponse(
        authenticated=True,
        api_key_configured=True,
        expires_at=expires_at,
    )


@router.get("/session", response_model=SessionStatusResponse)
def get_session_status(request: Request) -> SessionStatusResponse:
    """Return current session authentication status."""
    configured_key = _configured_api_key()
    if not configured_key:
        return SessionStatusResponse(authenticated=True, api_key_configured=False)

    cookie_value = request.cookies.get(SESSION_COOKIE_NAME, "")
    expires_at = _decode_expiry(cookie_value)
    return SessionStatusResponse(
        authenticated=expires_at is not None,
        api_key_configured=True,
        expires_at=expires_at,
    )


@router.delete("/session", response_model=SessionStatusResponse)
def delete_session(request: Request, response: Response) -> SessionStatusResponse:
    """Clear session cookie and return post-logout status."""
    _clear_auth_cookie(request, response)
    configured_key = _configured_api_key()
    if not configured_key:
        return SessionStatusResponse(authenticated=True, api_key_configured=False)
    return SessionStatusResponse(authenticated=False, api_key_configured=True)
