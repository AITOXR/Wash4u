from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DBSession

from app.audit import log_action
from app.db import get_db
from app.deps import require_editor_or_owner
from app.models import Product, User

router = APIRouter(tags=["products"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin/products")
def products_list(request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    products = db.query(Product).order_by(Product.order).all()
    return templates.TemplateResponse("products_list.html", {"request": request, "user": user, "active": "products", "products": products})


@router.get("/admin/products/new")
def new_product_form(request: Request, user: User = Depends(require_editor_or_owner)):
    return templates.TemplateResponse("product_edit.html", {"request": request, "user": user, "active": "products", "product": None})


@router.post("/admin/products/new")
def create_product(
    request: Request, name: str = Form(...), slug: str = Form(...), short_desc: str = Form(""),
    long_desc: str = Form(""), price: str = Form(""), sale_price: str = Form(""), unit_label: str = Form(""),
    images: str = Form(""), is_active: bool = Form(False),
    db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner),
):
    product = Product(
        name=name, slug=slug, short_desc=short_desc, long_desc=long_desc, price=price,
        sale_price=sale_price or None, unit_label=unit_label or None,
        images=[i.strip() for i in images.split(",") if i.strip()], is_active=is_active,
    )
    db.add(product)
    db.commit()
    log_action(db, user, "create", entity="product", entity_id=product.id)
    return RedirectResponse("/admin/products", status_code=303)


@router.get("/admin/products/{product_id}/edit")
def edit_product_form(product_id: int, request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    product = db.get(Product, product_id)
    return templates.TemplateResponse("product_edit.html", {"request": request, "user": user, "active": "products", "product": product})


@router.post("/admin/products/{product_id}/edit")
def update_product(
    product_id: int, name: str = Form(...), slug: str = Form(...), short_desc: str = Form(""),
    long_desc: str = Form(""), price: str = Form(""), sale_price: str = Form(""), unit_label: str = Form(""),
    images: str = Form(""), is_active: bool = Form(False),
    db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner),
):
    product = db.get(Product, product_id)
    if product:
        product.name, product.slug = name, slug
        product.short_desc, product.long_desc = short_desc, long_desc
        product.price, product.sale_price = price, sale_price or None
        product.unit_label = unit_label or None
        product.images = [i.strip() for i in images.split(",") if i.strip()]
        product.is_active = is_active
        db.commit()
        log_action(db, user, "update", entity="product", entity_id=product.id)
    return RedirectResponse("/admin/products", status_code=303)
