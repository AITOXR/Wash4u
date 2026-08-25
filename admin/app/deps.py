from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as DBSession

from app.config import settings
from app.db import get_db
from app.models import Role, Session as SessionModel, User
from app.security import unsign_session_cookie


class RedirectToLogin(Exception):
    """Raised by web routes to redirect an unauthenticated visitor. Deny by
    default: every /admin/* route depends on get_current_web_user (or a
    role-checked variant) except the login page itself, which is the one
    explicit allowlist entry."""
    def __init__(self, next_path: str = "/admin"):
        self.next_path = next_path


def _load_user_from_cookie(request: Request, db: DBSession) -> User | None:
    raw = request.cookies.get(settings.session_cookie_name)
    if not raw:
        return None
    session_id = unsign_session_cookie(raw)
    if not session_id:
        return None
    sess = db.get(SessionModel, session_id)
    if not sess:
        return None
    if sess.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        db.delete(sess)
        db.commit()
        return None
    user = db.get(User, sess.user_id)
    if not user or not user.is_active:
        return None
    return user


def get_current_user_optional(request: Request, db: DBSession = Depends(get_db)) -> User | None:
    return _load_user_from_cookie(request, db)


def require_web_user(request: Request, db: DBSession = Depends(get_db)) -> User:
    """For HTML admin pages: unauthenticated -> redirect to /admin/login."""
    user = _load_user_from_cookie(request, db)
    if not user:
        raise RedirectToLogin(next_path=str(request.url.path))
    return user


def require_api_user(request: Request, db: DBSession = Depends(get_db)) -> User:
    """For /api/admin/* JSON endpoints: unauthenticated -> 401, never a redirect."""
    user = _load_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def require_role(*roles: Role, api: bool = False):
    """Role check, enforced server-side — never trust the UI to hide a
    button. `api=True` returns 403 JSON instead of a redirect, matching the
    acceptance test: 'a staff user calling a publish endpoint gets 403'."""
    dependency = require_api_user if api else require_web_user

    def _check(user: User = Depends(dependency)) -> User:
        if user.role not in roles:
            if api:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to do that.")
        return user

    return _check


# Convenience role dependencies used throughout the routers.
require_owner = require_role(Role.owner)
require_editor_or_owner = require_role(Role.owner, Role.editor)
require_any_role = require_role(Role.owner, Role.editor, Role.staff)
