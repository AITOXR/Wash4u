from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession

from app.db import get_db
from app.deps import require_any_role
from app.models import CustomerTask, Lead, LeadStatus, Order, User

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin/dashboard")
def dashboard(request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_any_role)):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)

    orders_today = db.query(Order).filter(Order.created_at >= today_start).count()
    orders_week = db.query(Order).filter(Order.created_at >= week_start).count()
    by_status = dict(
        db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    )
    by_status = {k.value: v for k, v in by_status.items()}

    from app.models import Customer
    new_customers = db.query(Customer).filter(Customer.tags.isnot(None)).count()  # simplified for a first pass
    repeat_customers = db.query(Customer).filter(Customer.total_orders >= 2).count()
    pending_leads = db.query(Lead).filter(Lead.status == LeadStatus.new).count()
    pending_tasks = db.query(CustomerTask).filter(CustomerTask.done.is_(False)).count()
    recent_leads = db.query(Lead).order_by(Lead.created_at.desc()).limit(5).all()

    stats = dict(
        orders_today=orders_today, orders_week=orders_week, by_status=by_status,
        new_customers=new_customers, repeat_customers=repeat_customers,
        pending_leads=pending_leads, pending_tasks=pending_tasks, recent_leads=recent_leads,
    )
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "active": "dashboard", "stats": stats})
