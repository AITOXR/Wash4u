from __future__ import annotations

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DBSession

from app.db import get_db
from app.deps import require_any_role
from app.models import Customer, CustomerTask, CustomerTimelineEvent, User

router = APIRouter(tags=["crm"])
templates = Jinja2Templates(directory="app/templates")


def _filtered(db: DBSession, q: str, tag: str):
    query = db.query(Customer)
    if q:
        query = query.filter((Customer.name.ilike(f"%{q}%")) | (Customer.phone.ilike(f"%{q}%")))
    if tag:
        query = query.filter(Customer.tags.contains([tag]))
    return query.order_by(Customer.lifetime_value.desc())


@router.get("/admin/crm")
def crm_list(request: Request, q: str = "", tag: str = "", db: DBSession = Depends(get_db), user: User = Depends(require_any_role)):
    customers = _filtered(db, q, tag).all()
    return templates.TemplateResponse("crm_list.html", {
        "request": request, "user": user, "active": "crm", "customers": customers, "q": q, "tag_filter": tag,
        "request_qs": f"q={q}&tag={tag}",
    })


@router.get("/admin/crm/export")
def crm_export(q: str = "", tag: str = "", db: DBSession = Depends(get_db), user: User = Depends(require_any_role)):
    customers = _filtered(db, q, tag).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Name", "Phone", "Email", "Tags", "Total orders", "Lifetime value", "Last order"])
    for c in customers:
        writer.writerow([c.name, c.phone, c.email, ";".join(c.tags or []), c.total_orders, c.lifetime_value, c.last_order_at])
    buf.seek(0)
    return StreamingResponse(buf, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=customers.csv"})


@router.get("/admin/crm/{customer_id}")
def customer_detail(customer_id: int, request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_any_role)):
    customer = db.get(Customer, customer_id)
    tasks = db.query(CustomerTask).filter(CustomerTask.customer_id == customer_id).order_by(CustomerTask.done, CustomerTask.due_at).all()
    timeline = db.query(CustomerTimelineEvent).filter(CustomerTimelineEvent.customer_id == customer_id).order_by(CustomerTimelineEvent.created_at.desc()).all()
    return templates.TemplateResponse("customer_detail.html", {
        "request": request, "user": user, "active": "crm", "customer": customer, "tasks": tasks, "timeline": timeline,
    })


@router.post("/admin/crm/{customer_id}/notes")
def update_customer_notes(customer_id: int, notes: str = Form(""), db: DBSession = Depends(get_db), user: User = Depends(require_any_role)):
    customer = db.get(Customer, customer_id)
    if customer:
        customer.notes = notes
        db.add(CustomerTimelineEvent(customer_id=customer_id, kind="note", detail="Notes updated"))
        db.commit()
    return RedirectResponse(f"/admin/crm/{customer_id}", status_code=303)


@router.post("/admin/crm/{customer_id}/tasks")
def add_customer_task(customer_id: int, title: str = Form(...), due_date: str = Form(""), db: DBSession = Depends(get_db), user: User = Depends(require_any_role)):
    due_at = datetime.fromisoformat(due_date) if due_date else None
    db.add(CustomerTask(customer_id=customer_id, title=title, due_at=due_at))
    db.commit()
    return RedirectResponse(f"/admin/crm/{customer_id}", status_code=303)


@router.post("/admin/crm/{customer_id}/tasks/{task_id}/done")
def complete_task(customer_id: int, task_id: int, db: DBSession = Depends(get_db), user: User = Depends(require_any_role)):
    task = db.get(CustomerTask, task_id)
    if task:
        task.done = True
        db.commit()
    return RedirectResponse(f"/admin/crm/{customer_id}", status_code=303)
