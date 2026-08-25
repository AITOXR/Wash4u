from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DBSession

from app.audit import log_action
from app.db import get_db
from app.deps import require_owner
from app.models import (
    BlogPost, Customer, Lead, Order, Page, Product, Section, SiteSetting, User,
)

router = APIRouter(tags=["settings"])
templates = Jinja2Templates(directory="app/templates")


def _get(db: DBSession, key: str, default: dict) -> dict:
    row = db.get(SiteSetting, key)
    return row.value if row else default


def _set(db: DBSession, key: str, value: dict) -> None:
    row = db.get(SiteSetting, key)
    if row:
        row.value = value
    else:
        db.add(SiteSetting(key=key, value=value))
    db.commit()


@router.get("/admin/settings")
def settings_page(request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_owner)):
    return templates.TemplateResponse("settings.html", {
        "request": request, "user": user, "active": "settings",
        "branding": _get(db, "branding", {}),
        "business": _get(db, "business", {}),
        "seo": _get(db, "seo", {}),
        "announcement": _get(db, "announcement", {}),
        "maintenance": _get(db, "maintenance", {}),
    })


@router.post("/admin/settings/branding")
def save_branding(
    logo: str = Form(""), favicon: str = Form(""), primary_color: str = Form(""), accent_color: str = Form(""),
    db: DBSession = Depends(get_db), user: User = Depends(require_owner),
):
    _set(db, "branding", {"logo": logo, "favicon": favicon, "primary_color": primary_color, "accent_color": accent_color})
    log_action(db, user, "update", entity="settings", diff={"key": "branding"})
    return RedirectResponse("/admin/settings", status_code=303)


@router.post("/admin/settings/business")
def save_business(
    name: str = Form(""), phone: str = Form(""), whatsapp: str = Form(""), email: str = Form(""), address: str = Form(""),
    db: DBSession = Depends(get_db), user: User = Depends(require_owner),
):
    _set(db, "business", {"name": name, "phone": phone, "whatsapp": whatsapp, "email": email, "address": address})
    log_action(db, user, "update", entity="settings", diff={"key": "business"})
    return RedirectResponse("/admin/settings", status_code=303)


@router.post("/admin/settings/seo")
def save_seo(title_suffix: str = Form(""), default_description: str = Form(""), ga_id: str = Form(""), db: DBSession = Depends(get_db), user: User = Depends(require_owner)):
    _set(db, "seo", {"title_suffix": title_suffix, "default_description": default_description, "ga_id": ga_id})
    return RedirectResponse("/admin/settings", status_code=303)


@router.post("/admin/settings/announcement")
def save_announcement(enabled: bool = Form(False), text: str = Form(""), db: DBSession = Depends(get_db), user: User = Depends(require_owner)):
    _set(db, "announcement", {"enabled": enabled, "text": text})
    return RedirectResponse("/admin/settings", status_code=303)


@router.post("/admin/settings/maintenance")
def save_maintenance(enabled: bool = Form(False), message: str = Form(""), db: DBSession = Depends(get_db), user: User = Depends(require_owner)):
    _set(db, "maintenance", {"enabled": enabled, "message": message})
    return RedirectResponse("/admin/settings", status_code=303)


@router.get("/admin/settings/export")
def export_all(db: DBSession = Depends(get_db), user: User = Depends(require_owner)):
    """'Export all content as JSON' — a full backup independent of the git
    history, per the spec's reliability requirements."""
    data = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "pages": [
            {"slug": p.slug, "title": p.title, "sections": [
                {"type": s.type, "props": s.props, "style": s.style, "order": s.order, "visible": s.is_visible}
                for s in p.sections
            ]} for p in db.query(Page).all()
        ],
        "products": [{"slug": p.slug, "name": p.name, "price": p.price} for p in db.query(Product).all()],
        "blog_posts": [{"slug": p.slug, "title": p.title, "status": p.status} for p in db.query(BlogPost).all()],
        "settings": {row.key: row.value for row in db.query(SiteSetting).all()},
    }
    buf = json.dumps(data, indent=2, default=str)
    return StreamingResponse(iter([buf]), media_type="application/json", headers={"Content-Disposition": "attachment; filename=wash4you-export.json"})
