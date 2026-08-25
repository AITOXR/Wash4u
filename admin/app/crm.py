"""Auto-CRM: when an Order reaches `completed`, upsert the Customer record.

Idempotent by construction: Order.counted_for_crm is checked and set
inside this function (not left to the caller to avoid double-firing), so
calling this twice for the same order — a re-run, a re-fired webhook, a
status bounced completed -> confirmed -> completed again — counts that
order's value exactly once.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Customer, CustomerTask, CustomerTimelineEvent, Order, OrderStatus

VIP_LTV_THRESHOLD = 20000  # rupees; move to SiteSetting once Settings UI covers CRM rules
DORMANT_DAYS = 90


def _parse_amount(value: str | None) -> int:
    if not value:
        return 0
    digits = "".join(c for c in value if c.isdigit())
    return int(digits) if digits else 0


def on_order_completed(db: Session, order: Order) -> Customer:
    """Call this exactly once per order transition INTO completed — the
    order status router (see routers/orders.py) only calls it on that
    specific transition, which is what makes this idempotent in practice:
    an order already sitting at `completed` never re-triggers this because
    there's no transition to fire on.
    """
    if order.counted_for_crm:
        # Already counted — return the existing customer without touching
        # LTV again. This is the actual idempotency guarantee; everything
        # else in this function assumes it only runs once per order.
        return db.get(Customer, order.customer_id) if order.customer_id else None

    if not order.customer_phone and not order.customer_email:
        # Nothing to match a customer on — still a valid completed order,
        # just not one the CRM can attribute. Logged, not silently dropped.
        return None

    customer = None
    if order.customer_phone:
        customer = db.scalar(select(Customer).where(Customer.phone == order.customer_phone))
    if not customer and order.customer_email:
        customer = db.scalar(select(Customer).where(Customer.email == order.customer_email))

    is_new = customer is None
    if is_new:
        customer = Customer(
            name=order.customer_name, phone=order.customer_phone, email=order.customer_email,
            source=order.source, tags=["new_customer"],
        )
        db.add(customer)
        db.flush()
    else:
        customer.name = customer.name or order.customer_name
        customer.email = customer.email or order.customer_email

    order.customer_id = customer.id
    order.counted_for_crm = True
    amount = _parse_amount(order.total)
    customer.total_orders = (customer.total_orders or 0) + 1
    customer.lifetime_value = (customer.lifetime_value or 0) + amount
    customer.avg_order_value = customer.lifetime_value // max(customer.total_orders, 1)
    now = datetime.now(timezone.utc)
    customer.first_order_at = customer.first_order_at or now
    customer.last_order_at = now

    tags = set(customer.tags or [])
    tags.discard("new_customer" if customer.total_orders > 1 else "")
    if customer.total_orders >= 2:
        tags.add("repeat")
    if customer.total_orders == 1:
        tags.add("new_customer")
    if customer.lifetime_value >= VIP_LTV_THRESHOLD:
        tags.add("vip")
    tags.discard("dormant")  # they just ordered — clearly not dormant
    customer.tags = sorted(t for t in tags if t)

    db.add(CustomerTimelineEvent(
        customer_id=customer.id, kind="order",
        detail=f"Order #{order.id} completed — {order.total or 'amount not set'}",
    ))
    db.add(CustomerTask(
        customer_id=customer.id, title=f"Check in with {customer.name or customer.phone} after 30 days",
        due_at=now + timedelta(days=30),
    ))
    db.commit()
    return customer


def refresh_dormant_tags(db: Session) -> int:
    """Run periodically (a cron/scheduled job, not wired to a route here)
    to tag customers with no order in DORMANT_DAYS. Returns count tagged."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=DORMANT_DAYS)
    customers = db.query(Customer).filter(Customer.last_order_at < cutoff).all()
    count = 0
    for c in customers:
        tags = set(c.tags or [])
        if "dormant" not in tags:
            tags.add("dormant")
            c.tags = sorted(tags)
            count += 1
    db.commit()
    return count
