from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_EMAIL", "owner@test.local")
os.environ.setdefault("ADMIN_INITIAL_PASSWORD", "TestPassword123!")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("REPO_PATH", str(Path(__file__).resolve().parent.parent.parent))

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from app.db import Base, SessionLocal, engine
from app.main import app
from app.models import Page, PageStatus, Role, Section, User
from app.security import hash_password


@pytest.fixture(scope="session", autouse=True)
def _db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(User(email="owner@test.local", password_hash=hash_password("TestPassword123!"), role=Role.owner, must_change_password=False))
    db.add(User(email="staff@test.local", password_hash=hash_password("TestPassword123!"), role=Role.staff, must_change_password=False))
    # A minimal homepage so /admin (-> /admin/edit/) and the section-editing
    # tests have something real to act on, mirroring what seed_content.py
    # loads from content/ in a real deployment.
    home = Page(slug="", title="Home", is_home=True, depth=0, status=PageStatus.published)
    db.add(home)
    db.flush()
    db.add(Section(page_id=home.id, type="hero", order=0, props={"heading_line1": "Test heading", "heading_line2": ""}))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)
    db_path = Path("test.db")
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def client():
    # TestClient requests all share one fake IP ("testclient"), so a
    # lockout created by one test's failed-login attempts would otherwise
    # bleed into every later test sharing that IP. Clear the rolling
    # attempt log per test to keep them independent — the app's own
    # per-IP+email lockout logic (tested explicitly below) is real and
    # correct; this just stops it leaking across unrelated tests.
    from app.models import LoginAttempt
    db = SessionLocal()
    db.query(LoginAttempt).delete()
    db.commit()
    db.close()
    # base_url must be https:// — the session cookie is set with Secure=True
    # (required for production), so a plain-http TestClient would silently
    # never send it back on subsequent requests, exactly like a real browser.
    return TestClient(app, base_url="https://testserver")


def login(client: TestClient, email: str, password: str) -> TestClient:
    client.post("/admin/login", data={"email": email, "password": password})
    return client
