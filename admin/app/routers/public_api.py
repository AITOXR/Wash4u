"""Public, unauthenticated endpoints the STATIC site calls cross-origin.

Security posture (per spec): CORS locked to the public site origin only
(configured in app/main.py, not per-route), a honeypot field, a per-IP
rate limit, and strict field validation. No secrets, no admin data, no
PII beyond what the visitor themselves submitted, ever returned.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session as DBSession

from app.db import get_db
from app.models import Lead

router = APIRouter(tags=["public-api"])

_recent_submits: dict[str, list[datetime]] = {}
RATE_LIMIT_PER_HOUR = 10


class ContactSubmission(BaseModel):
    form_type: str = "contact"
    name: str = Field("", max_length=200)
    email: str = Field("", max_length=200)
    phone: str = Field("", max_length=30)
    city: str = Field("", max_length=100)
    service: str = Field("", max_length=200)
    message: str = Field("", max_length=4000)
    honeypot: str = Field("", max_length=200)


def _rate_limited(ip: str) -> bool:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=1)
    hits = [t for t in _recent_submits.get(ip, []) if t > window_start]
    _recent_submits[ip] = hits
    return len(hits) >= RATE_LIMIT_PER_HOUR


@router.post("/api/public/submit", status_code=status.HTTP_201_CREATED)
async def submit_form(request: Request, submission: ContactSubmission, db: DBSession = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"

    if submission.honeypot:
        # A bot filled in the hidden field. Return success anyway so it
        # doesn't learn the honeypot exists, but drop the submission.
        return {"ok": True}

    if _rate_limited(ip):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many submissions. Try again later.")

    if not (submission.name or submission.phone or submission.email):
        raise HTTPException(status_code=422, detail="Please provide at least a name, phone or email.")

    lead = Lead(
        source=submission.form_type, name=submission.name or None, phone=submission.phone or None,
        email=submission.email or None,
        payload={"city": submission.city, "service": submission.service, "message": submission.message},
    )
    db.add(lead)
    db.commit()

    _recent_submits.setdefault(ip, []).append(datetime.now(timezone.utc))

    # NOTE: reCAPTCHA/Turnstile verification goes here once Settings ->
    # Integrations carries the site/secret keys — flagged, not silently
    # skipped: this endpoint currently trusts the honeypot + rate limit
    # alone, which is a real but weaker bot defence than the spec asks for.
    return {"ok": True, "lead_id": lead.id}
