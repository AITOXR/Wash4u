from __future__ import annotations

import re
from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DBSession

from app.audit import log_action
from app.db import get_db
from app.deps import require_editor_or_owner
from app.models import BlogPost, User

router = APIRouter(tags=["blog"])
templates = Jinja2Templates(directory="app/templates")


def _slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


@router.get("/admin/blog")
def blog_list(request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    posts = db.query(BlogPost).order_by(BlogPost.created_at.desc()).all()
    return templates.TemplateResponse("blog_list.html", {"request": request, "user": user, "active": "blog", "posts": posts})


@router.get("/admin/blog/new")
def new_post_form(request: Request, user: User = Depends(require_editor_or_owner)):
    return templates.TemplateResponse("blog_edit.html", {"request": request, "user": user, "active": "blog", "post": None})


def _parse_dt(value: str):
    if not value:
        return None
    return datetime.fromisoformat(value)


@router.post("/admin/blog/new")
def create_post(
    request: Request, title: str = Form(...), slug: str = Form(""), excerpt: str = Form(""), body: str = Form(""),
    cover_image: str = Form(""), status: str = Form("draft"), published_at: str = Form(""),
    seo_title: str = Form(""), seo_description: str = Form(""),
    db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner),
):
    slug = slug.strip() or _slugify(title)
    if db.query(BlogPost).filter(BlogPost.slug == slug).first():
        slug = f"{slug}-{db.query(BlogPost).count() + 1}"  # duplicate-slug guard
    post = BlogPost(
        title=title, slug=slug, excerpt=excerpt, body=body, cover_image=cover_image or None,
        author_id=user.id, status=status, published_at=_parse_dt(published_at),
        seo_title=seo_title or None, seo_description=seo_description or None,
    )
    db.add(post)
    db.commit()
    log_action(db, user, "create", entity="post", entity_id=post.id)
    return RedirectResponse("/admin/blog", status_code=303)


@router.get("/admin/blog/{post_id}/edit")
def edit_post_form(post_id: int, request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner)):
    post = db.get(BlogPost, post_id)
    return templates.TemplateResponse("blog_edit.html", {"request": request, "user": user, "active": "blog", "post": post})


@router.post("/admin/blog/{post_id}/edit")
def update_post(
    post_id: int, title: str = Form(...), slug: str = Form(...), excerpt: str = Form(""), body: str = Form(""),
    cover_image: str = Form(""), status: str = Form("draft"), published_at: str = Form(""),
    seo_title: str = Form(""), seo_description: str = Form(""),
    db: DBSession = Depends(get_db), user: User = Depends(require_editor_or_owner),
):
    post = db.get(BlogPost, post_id)
    if post:
        dupe = db.query(BlogPost).filter(BlogPost.slug == slug, BlogPost.id != post_id).first()
        if dupe:
            slug = f"{slug}-{post_id}"
        post.title, post.slug, post.excerpt, post.body = title, slug, excerpt, body
        post.cover_image = cover_image or None
        post.status = status
        post.published_at = _parse_dt(published_at)
        post.seo_title, post.seo_description = seo_title or None, seo_description or None
        db.commit()
        log_action(db, user, "update", entity="post", entity_id=post.id)
    return RedirectResponse("/admin/blog", status_code=303)
