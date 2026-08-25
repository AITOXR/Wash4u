"""Creates tables (via Alembic in production; via create_all here for a
fast local start) and seeds exactly one owner account from
ADMIN_EMAIL / ADMIN_INITIAL_PASSWORD. Never commit real credentials —
these come from the environment only. Safe to re-run: skips seeding if
the owner already exists.
"""
from __future__ import annotations

from app.config import settings
from app.db import Base, SessionLocal, engine
from app.models import Role, User
from app.security import hash_password


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == settings.admin_email).first()
        if existing:
            print(f"Owner account already exists: {settings.admin_email}")
            return
        user = User(
            email=settings.admin_email,
            password_hash=hash_password(settings.admin_initial_password),
            role=Role.owner,
            must_change_password=True,
        )
        db.add(user)
        db.commit()
        print(f"Seeded owner account: {settings.admin_email} — password change is FORCED on first login.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
