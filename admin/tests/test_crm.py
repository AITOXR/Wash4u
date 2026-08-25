from __future__ import annotations

from app.crm import on_order_completed
from app.db import SessionLocal
from app.models import Customer, Order, OrderStatus


def test_first_completed_order_creates_customer_with_new_tag():
    db = SessionLocal()
    try:
        order = Order(customer_phone="+919999900001", customer_name="Test One", status=OrderStatus.completed, total="₹500")
        db.add(order)
        db.commit()
        customer = on_order_completed(db, order)
        assert customer.total_orders == 1
        assert customer.lifetime_value == 500
        assert "new_customer" in customer.tags
        assert "repeat" not in customer.tags
    finally:
        db.close()


def test_second_order_same_phone_tags_repeat_and_sums_ltv():
    db = SessionLocal()
    try:
        phone = "+919999900002"
        o1 = Order(customer_phone=phone, customer_name="Test Two", status=OrderStatus.completed, total="₹500")
        db.add(o1)
        db.commit()
        on_order_completed(db, o1)

        o2 = Order(customer_phone=phone, customer_name="Test Two", status=OrderStatus.completed, total="₹700")
        db.add(o2)
        db.commit()
        customer = on_order_completed(db, o2)

        assert customer.total_orders == 2
        assert customer.lifetime_value == 1200
        assert "repeat" in customer.tags
    finally:
        db.close()


def test_re_running_on_order_completed_for_the_same_order_does_not_double_count():
    """Per spec: 're-completing or re-firing a webhook must not double-count
    LTV'. Order.counted_for_crm makes this idempotent regardless of how
    many times — or from how many call sites — this function fires for the
    same order."""
    db = SessionLocal()
    try:
        order = Order(customer_phone="+919999900003", customer_name="Test Three", status=OrderStatus.completed, total="₹100")
        db.add(order)
        db.commit()
        on_order_completed(db, order)
        c2 = on_order_completed(db, order)  # deliberately called again
        assert c2.lifetime_value == 100
        assert c2.total_orders == 1
    finally:
        db.close()
