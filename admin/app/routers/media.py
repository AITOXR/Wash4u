from __future__ import annotations

import io
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DBSession

from app.audit import log_action
from app.config import settings
from app.db import get_db
from app.deps import require_editor_or_owner
from app.models import Media, User

router = APIRouter(tags=["media"])
templates = Jinja2Templates(directory="app/templates")

MEDIA_STAGE_DIR = Path(settings.repo_path).resolve() / "content" / "media" / "_staged"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # reject > 10MB per spec
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf"}


@router.get("/admin/media")
def media_list(request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    media = db.query(Media).order_by(Media.uploaded_at.desc()).all()
    return templates.TemplateResponse("media.html", {"request": request, "user": user, "active": "media", "media": media})


@router.post("/admin/media/upload")
async def upload_media(request: Request, file: UploadFile, alt: str = Form(""), db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        return RedirectResponse("/admin/media?error=too_large", status_code=303)

    # Validate the REAL content-type, not just the filename extension.
    content_type = file.content_type
    if content_type not in ALLOWED_MIME:
        return RedirectResponse("/admin/media?error=bad_type", status_code=303)

    MEDIA_STAGE_DIR.mkdir(parents=True, exist_ok=True)
    width = height = None

    if content_type == "application/pdf":
        out_name = file.filename
        (MEDIA_STAGE_DIR / out_name).write_bytes(raw)
    else:
        from PIL import Image
        from PIL import ImageOps

        im = Image.open(io.BytesIO(raw))
        im = ImageOps.exif_transpose(im)  # apply EXIF rotation, then...
        # ...strip EXIF entirely by re-saving without it (Pillow drops
        # metadata by default on save unless you pass exif= explicitly).
        if im.mode in ("P", "LA"):
            im = im.convert("RGBA")
        MAX_DIM = 2000
        if max(im.size) > MAX_DIM:
            ratio = MAX_DIM / max(im.size)
            im = im.resize((round(im.width * ratio), round(im.height * ratio)), Image.LANCZOS)
        width, height = im.size
        stem = Path(file.filename).stem
        out_name = f"{stem}.webp"
        im.save(MEDIA_STAGE_DIR / out_name, "WEBP", quality=82, method=6)

    media = Media(
        filename=out_name, url=f"content/media/_staged/{out_name}", alt=alt or None,
        width=width, height=height, size_bytes=len(raw),
    )
    db.add(media)
    db.commit()
    log_action(db, user, "upload", entity="media", entity_id=media.id)
    return RedirectResponse("/admin/media", status_code=303)


@router.get("/admin/media/{media_id}/file")
def serve_media(media_id: int, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    media = db.get(Media, media_id)
    if not media:
        return RedirectResponse("/admin/media", status_code=303)
    path = Path(settings.repo_path).resolve() / media.url
    return FileResponse(path)


@router.post("/admin/media/{media_id}/delete")
def delete_media(media_id: int, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    media = db.get(Media, media_id)
    if media:
        path = Path(settings.repo_path).resolve() / media.url
        path.unlink(missing_ok=True)
        db.delete(media)
        db.commit()
        log_action(db, user, "delete", entity="media", entity_id=media_id)
    return RedirectResponse("/admin/media", status_code=303)
