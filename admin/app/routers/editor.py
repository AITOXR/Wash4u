"""The WYSIWYG editor: 'the website is the editor'. GET /admin/edit/<slug>
serves the live page full-width with the overlay injected; every edit
(text, image, repeater add/remove, section add/move/duplicate/hide/delete)
is a small JSON PATCH from admin/app/static/editor.js against the
/admin/api/* routes below — never a form submit, never a full reload.
"""
from __future__ import annotations

import io
from pathlib import Path

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session as DBSession

from app.audit import log_action
from app.config import settings as app_settings
from app.db import get_db
from app.deps import require_any_role, require_editor_or_owner
from app.models import Media, Page, PageStatus, Revision, Section, User
from app.publish import collect_pending_changes
from app.section_schemas import default_props, get_schema, load_section_schemas
from app.site_preview import render_page_edit, render_section_html

router = APIRouter(tags=["editor"])
MEDIA_STAGE_DIR = Path(app_settings.repo_path).resolve() / "content" / "media" / "_staged"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@router.get("/admin", include_in_schema=False)
def admin_root(user: User = Depends(require_any_role)):
    # "The website IS the editor" — logging in lands you on the live
    # homepage in edit mode, not a dashboard. Dashboard/orders/CRM/etc.
    # live behind the menu button the editor injects into every page
    # (see templates/base.html's edit_mode block + static/editor.js).
    return RedirectResponse("/admin/edit/", status_code=303)


@router.get("/admin/edit/{slug:path}", response_class=HTMLResponse)
def edit_page(slug: str, request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_any_role)):
    slug = slug.strip("/")
    page = db.query(Page).filter(Page.slug == slug).first()
    if not page:
        return RedirectResponse("/admin/edit/", status_code=303) if slug else HTMLResponse("No homepage found — run `python3 -m app.seed_content` first.", status_code=404)
    pending_count = len(collect_pending_changes(db))
    # The rendered HTML IS the editor: templates/base.html injects the
    # overlay's CSS/JS itself once edit_mode is true (see that template) —
    # there's no separate wrapper page.
    return HTMLResponse(render_page_edit(page, user=user, pending_count=pending_count))


@router.post("/admin/api/upload")
async def api_upload(file: UploadFile, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    """JSON-returning upload used by the inline image-swap chip in the
    editor overlay — same processing as /admin/media/upload (WebP convert,
    EXIF strip, resize, MIME + size validation), but returns {ok, url}
    directly instead of redirecting to the Media Library page, so the
    overlay can patch the field and update the <img> in place immediately."""
    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        return JSONResponse({"ok": False, "error": "File is larger than 10MB"}, status_code=400)
    if file.content_type not in ALLOWED_IMAGE_MIME:
        return JSONResponse({"ok": False, "error": "Only JPEG/PNG/WebP/GIF images are accepted"}, status_code=400)

    from PIL import Image, ImageOps
    MEDIA_STAGE_DIR.mkdir(parents=True, exist_ok=True)
    im = Image.open(io.BytesIO(raw))
    im = ImageOps.exif_transpose(im)
    if im.mode in ("P", "LA"):
        im = im.convert("RGBA")
    MAX_DIM = 2000
    if max(im.size) > MAX_DIM:
        ratio = MAX_DIM / max(im.size)
        im = im.resize((round(im.width * ratio), round(im.height * ratio)), Image.LANCZOS)
    stem = Path(file.filename).stem or "upload"
    out_name = f"{stem}.webp"
    counter = 1
    while (MEDIA_STAGE_DIR / out_name).exists():
        out_name = f"{stem}-{counter}.webp"
        counter += 1
    im.save(MEDIA_STAGE_DIR / out_name, "WEBP", quality=82, method=6)

    rel_url = f"media/_staged/{out_name}"  # relative to the site's asset root — see build.py's media copy step
    media = Media(filename=out_name, url=f"content/{rel_url}", width=im.width, height=im.height, size_bytes=len(raw))
    db.add(media)
    db.commit()
    log_action(db, user, "upload", entity="media", entity_id=media.id)
    return JSONResponse({"ok": True, "url": rel_url, "media_id": media.id})


@router.get("/admin/api/section-types")
def section_types(user: User = Depends(require_editor_or_owner)):
    schemas = load_section_schemas()
    return JSONResponse([
        {"type": t, "label": s.get("label", t), "description": s.get("description", ""), "icon": s.get("icon", "square")}
        for t, s in sorted(schemas.items(), key=lambda kv: kv[1].get("label", kv[0]))
    ])


@router.post("/admin/api/sections/{section_id}/field")
async def patch_field(section_id: int, request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    body = await request.json()
    field, value = body.get("field"), body.get("value")
    section = db.get(Section, section_id)
    if not section or field is None:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    props = dict(section.props or {})
    _set_nested(props, field, value)
    section.props = props
    page = db.get(Page, section.page_id)
    page.status = PageStatus.draft
    db.commit()
    log_action(db, user, "update", entity="section", entity_id=section.id, diff={"field": field})
    return JSONResponse({"ok": True})


def _set_nested(props: dict, field: str, value):
    """field is either a top-level key ("heading") or "repeaterKey.index.subkey"
    for an item inside a repeater (e.g. "items.2.title")."""
    parts = field.split(".")
    if len(parts) == 1:
        props[parts[0]] = value
        return
    key, index, sub = parts[0], int(parts[1]), parts[2]
    items = props.setdefault(key, [])
    while len(items) <= index:
        items.append({})
    items[index][sub] = value


@router.get("/admin/api/sections/{section_id}/render")
def api_render_section(section_id: int, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    """Returns this section's current HTML — used to refresh just this one
    section's DOM after a repeater add/remove, instead of a full page
    reload (its item cards use shared macros the browser can't safely
    fabricate client-side, e.g. review_card's star-rating loop)."""
    section = db.get(Section, section_id)
    if not section:
        return JSONResponse({"ok": False}, status_code=404)
    page = db.get(Page, section.page_id)
    return JSONResponse({"ok": True, "html": render_section_html(page, section)})


@router.post("/admin/api/sections/{section_id}/repeater/add")
async def repeater_add(section_id: int, request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    body = await request.json()
    field = body.get("field")
    section = db.get(Section, section_id)
    if not section:
        return JSONResponse({"ok": False}, status_code=404)
    schema = get_schema(section.type) or {}
    field_schema = next((f for f in schema.get("fields", []) if f["key"] == field), None)
    item = {}
    if field_schema:
        for sub in field_schema.get("item_fields", []):
            if sub["type"] == "toggle":
                item[sub["key"]] = False
            elif sub["type"] == "number":
                item[sub["key"]] = 5 if sub["key"] == "rating" else 0
            else:
                item[sub["key"]] = "New " + sub["label"].lower() if sub.get("required") else ""
    props = dict(section.props or {})
    items = list(props.get(field, []))
    items.append(item)
    props[field] = items
    section.props = props
    db.get(Page, section.page_id).status = PageStatus.draft
    db.commit()
    return JSONResponse({"ok": True, "index": len(items) - 1, "item": item})


@router.post("/admin/api/sections/{section_id}/repeater/remove")
async def repeater_remove(section_id: int, request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    body = await request.json()
    field, index = body.get("field"), body.get("index")
    section = db.get(Section, section_id)
    if not section:
        return JSONResponse({"ok": False}, status_code=404)
    props = dict(section.props or {})
    items = list(props.get(field, []))
    if 0 <= index < len(items):
        items.pop(index)
    props[field] = items
    section.props = props
    db.get(Page, section.page_id).status = PageStatus.draft
    db.commit()
    return JSONResponse({"ok": True})


@router.post("/admin/api/sections/{section_id}/duplicate")
def api_duplicate(section_id: int, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    section = db.get(Section, section_id)
    if not section:
        return JSONResponse({"ok": False}, status_code=404)
    page = db.get(Page, section.page_id)
    max_order = max([s.order for s in page.sections], default=-1)
    new_section = Section(page_id=page.id, type=section.type, order=max_order + 1, props=dict(section.props or {}), style=dict(section.style or {}))
    db.add(new_section)
    page.status = PageStatus.draft
    db.commit()
    db.refresh(new_section)
    html = render_section_html(page, new_section)
    log_action(db, user, "duplicate", entity="section", entity_id=section.id)
    return JSONResponse({"ok": True, "html": html, "section_id": new_section.id})


@router.post("/admin/api/sections/{section_id}/toggle-visible")
def api_toggle_visible(section_id: int, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    section = db.get(Section, section_id)
    if not section:
        return JSONResponse({"ok": False}, status_code=404)
    section.is_visible = not section.is_visible
    db.get(Page, section.page_id).status = PageStatus.draft
    db.commit()
    return JSONResponse({"ok": True, "visible": section.is_visible})


@router.post("/admin/api/sections/{section_id}/delete")
def api_delete(section_id: int, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    section = db.get(Section, section_id)
    if not section:
        return JSONResponse({"ok": False}, status_code=404)
    page = db.get(Page, section.page_id)
    db.add(Revision(
        entity_type="page", entity_id=page.id,
        snapshot=[{"type": s.type, "props": s.props, "style": s.style, "visible": s.is_visible, "order": s.order} for s in page.sections],
        label=f"Before deleting a {section.type} section", author_id=user.id,
    ))
    db.delete(section)
    page.status = PageStatus.draft
    db.commit()
    log_action(db, user, "delete", entity="section", entity_id=section_id)
    return JSONResponse({"ok": True})


@router.post("/admin/api/sections/{section_id}/style")
async def api_style(section_id: int, request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    body = await request.json()
    section = db.get(Section, section_id)
    if not section:
        return JSONResponse({"ok": False}, status_code=404)
    style = dict(section.style or {})
    style.update(body)
    section.style = style
    db.get(Page, section.page_id).status = PageStatus.draft
    db.commit()
    return JSONResponse({"ok": True})


@router.post("/admin/api/pages/{page_id}/sections/reorder")
async def api_reorder(page_id: int, request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    body = await request.json()
    order = body.get("order", [])  # list of section ids, in the new order
    for index, section_id in enumerate(order):
        section = db.get(Section, section_id)
        if section and section.page_id == page_id:
            section.order = index
    db.get(Page, page_id).status = PageStatus.draft
    db.commit()
    return JSONResponse({"ok": True})


@router.post("/admin/api/pages/{page_id}/sections/create")
async def api_create_section(page_id: int, request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    body = await request.json()
    section_type, at_index = body.get("type"), body.get("index", 0)
    if not get_schema(section_type):
        return JSONResponse({"ok": False, "error": "unknown section type"}, status_code=400)
    page = db.get(Page, page_id)
    if not page:
        return JSONResponse({"ok": False}, status_code=404)

    sections = sorted(page.sections, key=lambda s: s.order)
    for s in sections[at_index:]:
        s.order += 1
    section = Section(page_id=page.id, type=section_type, order=at_index, props=default_props(section_type), style={})
    db.add(section)
    page.status = PageStatus.draft
    db.commit()
    db.refresh(section)
    html = render_section_html(page, section)
    log_action(db, user, "create", entity="section", entity_id=section.id, diff={"type": section_type})
    return JSONResponse({"ok": True, "html": html, "section_id": section.id})
