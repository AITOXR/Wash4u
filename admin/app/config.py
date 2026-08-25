"""All configuration comes from environment variables. Nothing sensitive
is ever hardcoded or committed — see ../.env.example for the full list."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database. Defaults to a local SQLite file for development; set
    # DATABASE_URL to a Postgres DSN in production (Railway provides one
    # automatically when you attach a Postgres plugin).
    database_url: str = "sqlite:///./admin.db"

    # Session cookies. SECRET_KEY signs them — rotate it to invalidate
    # every session at once. Generate one with: python3 -c "import secrets; print(secrets.token_hex(32))"
    secret_key: str = "dev-only-insecure-secret-change-me"
    session_cookie_name: str = "w4u_admin_session"
    session_max_age_seconds: int = 60 * 60 * 24 * 7  # 7 days, per spec

    # Seeded owner account (Phase: Foundation). Change the password on
    # first login — the app forces this the first time this account signs in.
    admin_email: str = "owner@example.com"
    admin_initial_password: str = "change-me-immediately"

    # Login rate limiting.
    login_max_attempts: int = 5
    login_lockout_seconds: int = 15 * 60

    # Publish pipeline: a fine-grained GitHub PAT or GitHub App
    # installation token, scoped to `contents:write` on this one repo only.
    # Never logged, never sent to the browser. If unset, Publish falls back
    # to a local `git commit` (useful for local dev without GitHub wired up).
    github_token: str = ""
    github_repo: str = ""  # "owner/repo"
    github_branch: str = "main"

    # CORS for the public API (contact form, enquiry/order submissions).
    public_site_origin: str = "https://wash4you.in"

    # Media storage for large files (video, PDFs > 10MB) that shouldn't be
    # committed to the repo. Small optimised images still go to content/media/.
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = ""

    # Path to the site repo checkout this admin publishes into. Defaults to
    # the parent of this admin/ directory, i.e. the repo root.
    repo_path: str = ".."


settings = Settings()
