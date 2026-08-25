from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import LoginAttempt


def is_locked_out(db: Session, email: str, ip: str) -> bool:
    """5 failed attempts (per email OR per IP) in the lockout window blocks
    further tries, even a correct password — this is deliberate: it stops
    both a targeted password-guessing attack on one account AND a
    credential-stuffing sweep from one IP across many emails."""
    window_start = datetime.now(timezone.utc) - timedelta(seconds=settings.login_lockout_seconds)
    q = select(func.count()).select_from(LoginAttempt).where(
        LoginAttempt.created_at >= window_start,
        LoginAttempt.success.is_(False),
        (LoginAttempt.email == email) | (LoginAttempt.ip == ip),
    )
    count = db.scalar(q) or 0
    return count >= settings.login_max_attempts


def record_attempt(db: Session, email: str, ip: str, success: bool) -> None:
    db.add(LoginAttempt(email=email, ip=ip, success=success))
    db.commit()
