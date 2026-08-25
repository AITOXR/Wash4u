from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DBSession

from app.audit import log_action
from app.db import get_db
from app.deps import require_any_role, require_editor_or_owner
from app.models import Page, PageStatus, Revision, Section, User
from app.publish import collect_pending_changes, publish, PublishError

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
    return RedirectResponse(f"/admin/edit/{page.slug}", status_code=303)


@router.get("/admin/pages/{page_id}/edit")
def edit_page_redirect(page_id: int, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    """The inline editor (GET /admin/edit/<slug>) is the real editing UI now
    — this old URL just forwards to it, so existing links/bookmarks keep working."""
    page = db.get(Page, page_id)
    if not page:
        return RedirectResponse("/admin/pages", status_code=303)
    return RedirectResponse(f"/admin/edit/{page.slug}", status_code=303)


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
        return RedirectResponse(f"/admin/edit/{page.slug}", status_code=303)
    return RedirectResponse("/admin/pages", status_code=303)


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
        return RedirectResponse(f"/admin/edit/{page.slug}", status_code=303)
    return RedirectResponse("/admin/pages", status_code=303)


@router.get("/admin/preview/{page_id}", response_class=HTMLResponse)
def preview_page(page_id: int, db: DBSession = Depends(get_db), user: User = Depends(require_any_role)):
    """A plain (no editor chrome/JS) render of this page's current draft —
    for the shareable/'look before you publish' preview."""
    from app.site_preview import render_page_edit
    page = db.get(Page, page_id)
    if not page:
        return HTMLResponse("Page not found", status_code=404)
    return HTMLResponse(render_page_edit(page))


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
    return RedirectResponse("/admin/edit/", status_code=303)
