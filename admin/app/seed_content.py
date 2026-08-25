"""Loads content/pages/*.yml + content/products/*.yml + content/posts/*.md
into the database as PUBLISHED rows, so the admin starts out mirroring
exactly what's already live — matching the spec's Foundation/Migration
phases ("seed the DB with the current live content"). Safe to re-run:
skips any page/product/post whose slug already exists.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from app.db import Base, SessionLocal, engine
from app.models import BlogPost, Page, PageStatus, Product, Section

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONTENT_DIR = REPO_ROOT / "content"


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        created_pages = created_products = created_posts = 0
        for path in sorted((CONTENT_DIR / "pages").glob("*.yml")):
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
            if db.query(Page).filter(Page.slug == doc["slug"]).first():
                continue
            seo = doc.get("seo") or {}
            page = Page(
                slug=doc["slug"], title=doc["title"], depth=doc.get("depth", 1),
                seo_title=seo.get("title"), seo_description=seo.get("description"),
                canonical=seo.get("canonical"), og_title=seo.get("og_title"), og_description=seo.get("og_description"),
                is_home=(doc["slug"] == ""), status=PageStatus.published,
            )
            db.add(page)
            db.flush()
            snapshot = []
            for i, s in enumerate(doc["sections"]):
                db.add(Section(page_id=page.id, type=s["type"], order=i, is_visible=s.get("visible", True), props=s.get("props", {}), style=s.get("style", {})))
                snapshot.append({"type": s["type"], "props": s.get("props", {}), "style": s.get("style", {}), "visible": s.get("visible", True), "order": i})
            page.published_snapshot = snapshot
            created_pages += 1

        products_dir = CONTENT_DIR / "products"
        if products_dir.exists():
            for path in sorted(products_dir.glob("*.yml")):
                doc = yaml.safe_load(path.read_text(encoding="utf-8"))
                if db.query(Product).filter(Product.slug == doc["slug"]).first():
                    continue
                db.add(Product(
                    slug=doc["slug"], name=doc["name"], short_desc=doc.get("short_description"),
                    long_desc=doc.get("body") or doc.get("description"),
                    images=[doc["image"]] if doc.get("image") else [],
                    is_active=True, status=PageStatus.published,
                ))
                created_products += 1

        posts_dir = CONTENT_DIR / "posts"
        if posts_dir.exists():
            for path in sorted(posts_dir.glob("*.md")):
                text = path.read_text(encoding="utf-8")
                m = re.match(r"^---\n(.*?)\n---\n\n?(.*)$", text, re.S)
                front = yaml.safe_load(m.group(1)) if m else {}
                body = m.group(2).strip() if m else text
                slug = path.stem
                if db.query(BlogPost).filter(BlogPost.slug == slug).first():
                    continue
                db.add(BlogPost(
                    slug=slug, title=front.get("title", slug), excerpt=front.get("excerpt"),
                    body=body, status="published",
                ))
                created_posts += 1

        db.commit()
        print(f"Seeded {created_pages} pages, {created_products} products, {created_posts} posts.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
