from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DBSession

from app.audit import log_action
from app.db import get_db
from app.deps import require_any_role
from app.models import Lead, User

router = APIRouter(tags=["leads"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin/leads")
def leads_list(request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_any_role)):
    leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
    return templates.TemplateResponse("leads_list.html", {"request": request, "user": user, "active": "leads", "leads": leads})


@router.get("/admin/leads/{lead_id}")
def lead_detail(lead_id: int, request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_any_role)):
    lead = db.get(Lead, lead_id)
    return templates.TemplateResponse("lead_detail.html", {"request": request, "user": user, "active": "leads", "lead": lead})


@router.post("/admin/leads/{lead_id}/status")
def update_lead_status(lead_id: int, status: str = Form(...), db: DBSession = Depends(get_db), user: User = Depends(require_any_role)):
    lead = db.get(Lead, lead_id)
    if lead:
        lead.status = status
        db.commit()
        log_action(db, user, "status_change", entity="lead", entity_id=lead.id, diff={"to": status})
    return RedirectResponse("/admin/leads", status_code=303)


@router.post("/admin/leads/{lead_id}/notes")
def update_lead_notes(lead_id: int, notes: str = Form(""), db: DBSession = Depends(get_db), user: User = Depends(require_any_role)):
    lead = db.get(Lead, lead_id)
    if lead:
        lead.notes = notes
        db.commit()
    return RedirectResponse(f"/admin/leads/{lead_id}", status_code=303)
