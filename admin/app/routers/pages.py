from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DBSession

from app.audit import log_action
from app.db import get_db
from app.deps import require_any_role, require_editor_or_owner
from app.models import Page, PageStatus, Revision, Section, User
from app.publish import collect_pending_changes, publish, PublishError
from app.section_schemas import default_props, get_schema, load_section_schemas

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin/pages")
def pages_list(request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    pages = db.query(Page).order_by(Page.order).all()
    return templates.TemplateResponse("pages_list.html", {"request": request, "user": user, "active": "pages", "pages": pages})


@router.get("/admin/pages/new")
def new_page(db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    page = Page(slug=f"new-page-{db.query(Page).count() + 1}", title="New page", status=PageStatus.draft)
    db.add(page)
    db.commit()
    return RedirectResponse(f"/admin/pages/{page.id}/edit", status_code=303)


@router.get("/admin/pages/{page_id}/edit")
def edit_page(page_id: int, request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    page = db.get(Page, page_id)
    if not page:
        return RedirectResponse("/admin/pages", status_code=303)
    schemas = load_section_schemas()
    pending = [c for c in collect_pending_changes(db) if c["entity"] == "page" and c["id"] == page.id]
    return templates.TemplateResponse("page_edit.html", {
        "request": request, "user": user, "active": "pages", "page": page,
        "sections": sorted(page.sections, key=lambda s: s.order),
        "schemas": schemas, "pending_count": len(pending),
    })


@router.post("/admin/pages/{page_id}/settings")
def save_page_settings(
    page_id: int, title: str = Form(...), slug: str = Form(""), seo_title: str = Form(""),
    seo_description: str = Form(""), canonical: str = Form(""), og_title: str = Form(""),
    og_description: str = Form(""), db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner),
):
    page = db.get(Page, page_id)
    if page:
        page.title = title
        if not page.is_home:
            page.slug = slug.strip("/")
        page.seo_title = seo_title
        page.seo_description = seo_description
        page.canonical = canonical or None
        page.og_title = og_title or None
        page.og_description = og_description or None
        page.status = PageStatus.draft
        db.commit()
        log_action(db, user, "update", entity="page", entity_id=page.id)
    return RedirectResponse(f"/admin/pages/{page_id}/edit", status_code=303)


@router.get("/admin/pages/{page_id}/sections/new")
def new_section_form(page_id: int, type: str, request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    schema = get_schema(type)
    if not schema:
        return RedirectResponse(f"/admin/pages/{page_id}/edit", status_code=303)
    return templates.TemplateResponse("section_form.html", {
        "request": request, "user": user, "page_id": page_id, "schema": schema,
        "props": default_props(type), "style": {}, "section_type": type, "is_new": True,
    })


@router.post("/admin/pages/{page_id}/sections/new")
async def create_section(page_id: int, type: str, request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    page = db.get(Page, page_id)
    schema = get_schema(type)
    if not page or not schema:
        return RedirectResponse(f"/admin/pages/{page_id}/edit", status_code=303)
    form = await request.form()
    props = _props_from_form(schema, form)
    max_order = max([s.order for s in page.sections], default=-1)
    section = Section(page_id=page.id, type=type, order=max_order + 1, props=props, style={"hide_on_mobile": bool(form.get("hide_on_mobile"))})
    db.add(section)
    page.status = PageStatus.draft
    db.commit()
    log_action(db, user, "create", entity="section", entity_id=section.id, diff={"type": type})
    return RedirectResponse(f"/admin/pages/{page_id}/edit", status_code=303)


@router.get("/admin/pages/{page_id}/sections/{section_id}/edit")
def edit_section_form(page_id: int, section_id: int, request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    section = db.get(Section, section_id)
    if not section:
        return RedirectResponse(f"/admin/pages/{page_id}/edit", status_code=303)
    schema = get_schema(section.type)
    return templates.TemplateResponse("section_form.html", {
        "request": request, "user": user, "page_id": page_id, "schema": schema,
        "props": section.props or {}, "style": section.style or {}, "section_type": section.type, "is_new": False,
    })


@router.post("/admin/pages/{page_id}/sections/{section_id}/edit")
async def update_section(page_id: int, section_id: int, request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    section = db.get(Section, section_id)
    if not section:
        return RedirectResponse(f"/admin/pages/{page_id}/edit", status_code=303)
    schema = get_schema(section.type)
    form = await request.form()
    before = dict(section.props or {})
    section.props = _props_from_form(schema, form)
    section.style = {**(section.style or {}), "hide_on_mobile": bool(form.get("hide_on_mobile"))}
    page = db.get(Page, page_id)
    page.status = PageStatus.draft
    db.commit()
    log_action(db, user, "update", entity="section", entity_id=section.id, diff={"before": before, "after": section.props})
    return RedirectResponse(f"/admin/pages/{page_id}/edit", status_code=303)


def _props_from_form(schema: dict, form) -> dict:
    props = {}
    for field in schema.get("fields", []):
        key = field["key"]
        if field["type"] == "toggle":
            props[key] = bool(form.get(key))
        elif field["type"] == "repeater":
            raw = form.get(f"{key}__json", "[]")
            try:
                props[key] = json.loads(raw)
            except (ValueError, TypeError):
                props[key] = []
        else:
            props[key] = form.get(key, "")
    return props


@router.post("/admin/pages/{page_id}/sections/{section_id}/move")
def move_section(page_id: int, section_id: int, direction: str = Form(...), db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    page = db.get(Page, page_id)
    sections = sorted(page.sections, key=lambda s: s.order)
    idx = next((i for i, s in enumerate(sections) if s.id == section_id), None)
    if idx is not None:
        swap_with = idx - 1 if direction == "up" else idx + 1
        if 0 <= swap_with < len(sections):
            sections[idx].order, sections[swap_with].order = sections[swap_with].order, sections[idx].order
            page.status = PageStatus.draft
            db.commit()
    return RedirectResponse(f"/admin/pages/{page_id}/edit", status_code=303)


@router.post("/admin/pages/{page_id}/sections/{section_id}/duplicate")
def duplicate_section(page_id: int, section_id: int, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    section = db.get(Section, section_id)
    if section:
        page = db.get(Page, page_id)
        max_order = max([s.order for s in page.sections], default=-1)
        db.add(Section(page_id=page_id, type=section.type, order=max_order + 1, props=dict(section.props or {}), style=dict(section.style or {})))
        page.status = PageStatus.draft
        db.commit()
        log_action(db, user, "duplicate", entity="section", entity_id=section.id)
    return RedirectResponse(f"/admin/pages/{page_id}/edit", status_code=303)


@router.post("/admin/pages/{page_id}/sections/{section_id}/toggle-visible")
def toggle_section_visible(page_id: int, section_id: int, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    section = db.get(Section, section_id)
    if section:
        section.is_visible = not section.is_visible
        db.get(Page, page_id).status = PageStatus.draft
        db.commit()
    return RedirectResponse(f"/admin/pages/{page_id}/edit", status_code=303)


@router.post("/admin/pages/{page_id}/sections/{section_id}/delete")
def delete_section(page_id: int, section_id: int, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    section = db.get(Section, section_id)
    page = db.get(Page, page_id)
    if section and page:
        # Soft delete via a revision snapshot BEFORE removing it, so
        # "restore from revision history" (acceptance test) works even for
        # a deleted section — the revision captures the whole page, which
        # includes it.
        db.add(Revision(
            entity_type="page", entity_id=page.id,
            snapshot=[{"type": s.type, "props": s.props, "style": s.style, "visible": s.is_visible, "order": s.order} for s in page.sections],
            label=f"Before deleting a {section.type} section", author_id=user.id,
        ))
        db.delete(section)
        page.status = PageStatus.draft
        db.commit()
        log_action(db, user, "delete", entity="section", entity_id=section_id)
    return RedirectResponse(f"/admin/pages/{page_id}/edit", status_code=303)


@router.get("/admin/pages/{page_id}/revisions")
def list_revisions(page_id: int, request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    page = db.get(Page, page_id)
    revisions = db.query(Revision).filter(Revision.entity_type == "page", Revision.entity_id == page_id).order_by(Revision.created_at.desc()).all()
    return templates.TemplateResponse("revisions.html", {"request": request, "user": user, "page": page, "revisions": revisions})


@router.get("/admin/pages/{page_id}/revisions/{revision_id}/restore")
def restore_revision(page_id: int, revision_id: int, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    page = db.get(Page, page_id)
    revision = db.get(Revision, revision_id)
    if page and revision:
        for s in list(page.sections):
            db.delete(s)
        db.flush()
        for item in revision.snapshot:
            db.add(Section(page_id=page.id, type=item["type"], order=item["order"], props=item["props"], style=item["style"], is_visible=item["visible"]))
        page.status = PageStatus.draft
        db.commit()
        log_action(db, user, "restore_revision", entity="page", entity_id=page.id, diff={"revision_id": revision_id})
    return RedirectResponse(f"/admin/pages/{page_id}/edit", status_code=303)


@router.get("/admin/preview/{page_id}", response_class=HTMLResponse)
def preview_page(page_id: int, db: DBSession = Depends(get_db), user: User = Depends(require_any_role)):
    """Server-renders the REAL public-site templates with this page's draft
    sections — not a mock. See app/site_preview.py."""
    from app.site_preview import render_page_preview
    page = db.get(Page, page_id)
    if not page:
        return HTMLResponse("Page not found", status_code=404)
    html = render_page_preview(page)
    return HTMLResponse(html)


@router.get("/admin/publish")
def publish_confirm(request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    changes = collect_pending_changes(db)
    return templates.TemplateResponse("publish_confirm.html", {"request": request, "user": user, "changes": changes})


@router.post("/admin/publish")
async def publish_submit(request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    form = await request.form()
    publish_all = bool(form.get("publish_all"))
    page_ids = None if publish_all else [int(v) for v in form.getlist("page_ids")]
    post_ids = None if publish_all else [int(v) for v in form.getlist("post_ids")]
    try:
        log_entry = publish(db, user, page_ids=page_ids, post_ids=post_ids)
        log_action(db, user, "publish", entity="publish_log", entity_id=log_entry.id, diff={"summary": log_entry.summary})
    except PublishError as e:
        return templates.TemplateResponse(
            "publish_confirm.html",
            {"request": request, "user": user, "changes": collect_pending_changes(db), "error": str(e)},
            status_code=400,
        )
    return RedirectResponse("/admin/pages", status_code=303)
