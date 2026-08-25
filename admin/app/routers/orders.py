from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DBSession

from app.audit import log_action
from app.crm import on_order_completed
from app.db import get_db
from app.deps import require_any_role
from app.models import Order, OrderStatus, OrderStatusLog, User

router = APIRouter(tags=["orders"])
templates = Jinja2Templates(directory="app/templates")

STATUSES = [s.value for s in OrderStatus]


@router.get("/admin/orders")
def orders_list(request: Request, q: str = "", status: str = "", db: DBSession = Depends(get_db), user: User = Depends(require_any_role)):
    query = db.query(Order)
    if q:
        query = query.filter((Order.customer_name.ilike(f"%{q}%")) | (Order.customer_phone.ilike(f"%{q}%")))
    if status:
        query = query.filter(Order.status == status)
    orders = query.order_by(Order.created_at.desc()).limit(200).all()
    return templates.TemplateResponse("orders_list.html", {
        "request": request, "user": user, "active": "orders", "orders": orders,
        "statuses": STATUSES, "q": q, "status_filter": status,
    })


@router.get("/admin/orders/new")
def new_order_form(request: Request, user: User = Depends(require_any_role)):
    return templates.TemplateResponse("order_new.html", {"request": request, "user": user, "active": "orders"})


@router.post("/admin/orders/new")
def create_order(
    customer_name: str = Form(""), customer_phone: str = Form(...), customer_email: str = Form(""),
    address: str = Form(""), slot: str = Form(""), items_raw: str = Form(""), total: str = Form(""),
    db: DBSession = Depends(get_db), user: User = Depends(require_any_role),
):
    items = []
    for line in items_raw.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 1 and parts[0]:
            items.append({"name": parts[0], "qty": parts[1] if len(parts) > 1 else "1", "price": parts[2] if len(parts) > 2 else ""})
    order = Order(
        customer_name=customer_name or None, customer_phone=customer_phone, customer_email=customer_email or None,
        address=address or None, slot=slot or None, items=items, total=total or None, source="manual",
    )
    db.add(order)
    db.commit()
    db.add(OrderStatusLog(order_id=order.id, from_status=None, to_status=OrderStatus.new.value, changed_by=user.id))
    db.commit()
    log_action(db, user, "create", entity="order", entity_id=order.id)
    return RedirectResponse(f"/admin/orders/{order.id}", status_code=303)


@router.get("/admin/orders/{order_id}")
def order_detail(order_id: int, request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_any_role)):
    order = db.get(Order, order_id)
    status_log = db.query(OrderStatusLog).filter(OrderStatusLog.order_id == order_id).order_by(OrderStatusLog.created_at).all()
    return templates.TemplateResponse("order_detail.html", {"request": request, "user": user, "active": "orders", "order": order, "statuses": STATUSES, "status_log": status_log})


@router.post("/admin/orders/{order_id}/status")
def update_order_status(order_id: int, status: str = Form(...), db: DBSession = Depends(get_db), user: User = Depends(require_any_role)):
    order = db.get(Order, order_id)
    if order:
        old = order.status.value
        if old != status:
            order.status = status
            db.add(OrderStatusLog(order_id=order.id, from_status=old, to_status=status, changed_by=user.id))
            db.commit()
            log_action(db, user, "status_change", entity="order", entity_id=order.id, diff={"from": old, "to": status})
            # Auto-CRM fires exactly on the transition INTO completed — see
            # app/crm.py's idempotency note.
            if status == OrderStatus.completed.value and old != OrderStatus.completed.value:
                on_order_completed(db, order)
    return RedirectResponse(f"/admin/orders/{order_id}", status_code=303)


@router.post("/admin/orders/{order_id}/notes")
def update_order_notes(order_id: int, internal_notes: str = Form(""), db: DBSession = Depends(get_db), user: User = Depends(require_any_role)):
    order = db.get(Order, order_id)
    if order:
        order.internal_notes = internal_notes
        db.commit()
    return RedirectResponse(f"/admin/orders/{order_id}", status_code=303)
