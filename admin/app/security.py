"""Password hashing (argon2) and session tokens (random, server-side
store — the cookie only carries the signed token, per the spec's explicit
requirement not to rely on client-side state for auth)."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.config import settings

_hasher = PasswordHasher()
_serializer = URLSafeTimedSerializer(settings.secret_key, salt="w4u-admin-session")
_reset_serializer = URLSafeTimedSerializer(settings.secret_key, salt="w4u-admin-password-reset")

RESET_TOKEN_MAX_AGE = 60 * 60  # 1 hour


def make_reset_token(user_id: int) -> str:
    return _reset_serializer.dumps({"uid": user_id})


def read_reset_token(token: str) -> int | None:
    try:
        data = _reset_serializer.loads(token, max_age=RESET_TOKEN_MAX_AGE)
        return data.get("uid")
    except BadSignature:
        return None


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def sign_session_cookie(session_id: str) -> str:
    return _serializer.dumps({"sid": session_id})


def unsign_session_cookie(cookie_value: str) -> str | None:
    """Returns the session id, or None if the cookie is missing/tampered/expired.

    max_age matches the session's own expiry so a stolen but stale signed
    cookie can't outlive the server-side session record either way — this
    is a second, independent check, not the only one (deps.py also checks
    the DB-stored Session.expires_at).
    """
    try:
        data = _serializer.loads(cookie_value, max_age=settings.session_max_age_seconds)
        return data.get("sid")
    except BadSignature:
        return None


def session_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=settings.session_max_age_seconds)
