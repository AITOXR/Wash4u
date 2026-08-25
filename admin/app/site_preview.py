"""Renders live pages using the REAL public-site Jinja templates
(templates/pages/generic.html + templates/sections/*.html at the repo
root) fed with DRAFT sections straight from the database — not a mock,
not a second copy of the markup. This is what makes both the WYSIWYG
editor and the old iframe preview trustworthy: what you see is what
build.py would also produce once you publish.

Two render modes share the same context-building code:
  - render_page_edit(page)  -> the full page, edit_mode=True, with the
    editor overlay's data-* attributes baked in by templates/_editor.html's
    macros. This is what GET /admin/edit/<slug> serves.
  - render_section_html(page, section) -> ONE section's markup, used to
    inject a freshly-created section into the DOM without a full reload
    (see routers/editor.py's create-section endpoint).
"""
from __future__ import annotations

import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

from app.config import settings
from app.models import Page, Section

REPO_ROOT = Path(settings.repo_path).resolve()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import build as site_build  # the repo-root generator — reused, not duplicated

_env = None


def _get_env() -> Environment:
    global _env
    if _env is None:
        _env = Environment(loader=FileSystemLoader(REPO_ROOT / "templates"), trim_blocks=True, lstrip_blocks=True, autoescape=True)
        _env.filters["markdown"] = lambda s: Markup(site_build.markdown_to_html(s))
    return _env


def _shared_context(edit_mode: bool) -> dict:
    site_yml = site_build.load_yaml(site_build.CONTENT_DIR / "site.yml")
    nav_yml = site_build.load_yaml(site_build.CONTENT_DIR / "navigation.yml")
    areas_yml = site_build.load_yaml(site_build.CONTENT_DIR / "areas.yml")

    site = dict(site_yml)
    site["nav"] = {"main": nav_yml["header_main"], "cta": nav_yml["header_cta"]}
    site["footer"] = {
        "explore": nav_yml["footer_explore"], "areas": nav_yml["footer_areas"], "support": nav_yml["footer_support"],
    }
    areas_total_all = sum(c["count"] for c in areas_yml["cities"])
    other_cities = [c["name"] for c in areas_yml["cities"] if c["name"] != "Gurugram (Gurgaon)"]

    products_dir = site_build.CONTENT_DIR / "products"
    products = [site_build.load_yaml(p) for p in sorted(products_dir.glob("*.yml"))] if products_dir.exists() else []
    pricing_path = site_build.CONTENT_DIR / "pricing.yml"
    pricing = site_build.load_yaml(pricing_path) if pricing_path.exists() else {"categories": []}
    packages_path = site_build.CONTENT_DIR / "packages.yml"
    packages = site_build.load_yaml(packages_path) if packages_path.exists() else {"plans": []}
    posts_dir = site_build.CONTENT_DIR / "posts"
    all_posts = [site_build.parse_markdown_post(p) for p in sorted(posts_dir.glob("*.md"))] if posts_dir.exists() else []

    services = {"services": [{"slug": p["slug"], "name": p["name"]} for p in products]}
    blog = {"posts": [{"title": p["title"], "url": f"/blog/{p['slug']}/"} for p in all_posts]}
    price_index = {i["slug"]: i for c in pricing["categories"] for i in c["items"] if i.get("slug")}
    price_count = sum(len(c["items"]) for c in pricing["categories"])
    price_min = min((i["amount"] for c in pricing["categories"] for i in c["items"] if not i.get("unit")), default=0)

    env = _get_env()
    env.globals["edit_mode"] = edit_mode
    # No cms() binding in the new system — the _editor.html macros (ed/rep/
    # rep_item) are the equivalent for this generator. cms() is kept as a
    # harmless no-op only because base.html (copied from the live site)
    # still calls it in a couple of spots.
    env.globals["cms"] = lambda *a, **k: ""

    return dict(
        site=site, services=services, blog=blog, all_posts=all_posts, products=products,
        pricing=pricing, packages=packages, price_index=price_index, price_count=price_count, price_min=price_min,
        search_pricing_items=[], areas_total_all=areas_total_all, other_cities=other_cities,
    )


def _section_dict(section: Section) -> dict:
    return {
        "type": section.type, "id": f"s{section.id}", "db_id": section.id,
        "visible": section.is_visible, "props": section.props or {}, "style": section.style or {},
    }


def render_page_edit(page: Page, user=None, pending_count: int = 0) -> str:
    ctx = _shared_context(edit_mode=True)
    page_dict = {
        "title": page.title, "slug": page.slug, "db_id": page.id,
        "sections": [_section_dict(s) for s in sorted(page.sections, key=lambda s: s.order)],
    }
    # Served by THIS admin app (see main.py's /assets mounts), not the live
    # site — the editor previews draft content that may not match what's
    # actually published, so it must never depend on the live domain being
    # in sync (and, as of this fix, the live wash4you.in domain turns out to
    # be running WordPress, not this generator's output at all — see the
    # note this fix shipped with).
    asset_path = "/assets/"

    template = _get_env().get_template("pages/generic.html")
    return template.render(
        page=page_dict, user=user, pending_count=pending_count,
        meta={"title": page.seo_title or page.title, "description": page.seo_description or "", "canonical": None, "og_title": page.title, "og_description": ""},
        root_path="/", asset_path=asset_path,
        **ctx,
    )


def render_section_html(page: Page, section: Section) -> str:
    """Renders ONE section (wrapped exactly as generic.html wraps it) for
    injecting into the DOM after it's created — see routers/editor.py."""
    ctx = _shared_context(edit_mode=True)
    asset_path = "/assets/"  # served by this admin app — see render_page_edit's comment above
    section_dict = _section_dict(section)
    page_dict = {"title": page.title, "slug": page.slug, "db_id": page.id}

    env = _get_env()
    # base.html normally supplies these via one {% from %} inside its own
    # <body> block; a standalone fragment render (no base.html) needs the
    # same import repeated here or every section template's ui(...) calls
    # raise UndefinedError.
    tpl_src = (
        '{% from "_icons.html" import ui, care_symbol, care_tag, service_icon %}'
        '{% include "sections/" ~ section.type ~ ".html" %}'
    )
    fragment_tpl = env.from_string(tpl_src)
    inner_html = fragment_tpl.render(section=section_dict, page=page_dict, root_path="/", asset_path=asset_path, **ctx)
    order_index = sorted(page.sections, key=lambda s: s.order).index(section) if section in page.sections else 0
    return (
        f'<div class="w4u-section" data-section-id="{section.id}" '
        f'data-section-type="{section.type}" data-section-index="{order_index}">{inner_html}</div>'
    )
