"""Renders a live-preview page using the REAL public-site Jinja templates
(templates/pages/generic.html + templates/sections/*.html at the repo
root) fed with this page's DRAFT sections straight from the database —
not a mock, not a second copy of the markup. This is what makes the
editor's preview trustworthy: what you see here is what build.py would
also produce once you publish.
"""
from __future__ import annotations

import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

from app.config import settings
from app.models import Page

REPO_ROOT = Path(settings.repo_path).resolve()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import build as site_build  # the repo-root generator — reused, not duplicated


def render_page_preview(page: Page) -> str:
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

    env = Environment(loader=FileSystemLoader(REPO_ROOT / "templates"), trim_blocks=True, lstrip_blocks=True, autoescape=True)
    env.filters["markdown"] = lambda s: Markup(site_build.markdown_to_html(s))
    env.globals["edit_mode"] = False
    env.globals["cms"] = lambda *a, **k: ""

    page_dict = {
        "title": page.title, "slug": page.slug,
        "sections": [
            {"type": s.type, "id": f"preview_{s.id}", "visible": s.is_visible, "props": s.props or {}, "style": s.style or {}}
            for s in sorted(page.sections, key=lambda s: s.order)
        ],
    }
    root_path, asset_path = site_build.get_paths(page.depth or 1)
    # Assets are served by the public site, not this admin app — point the
    # preview at the live domain for images/CSS so it renders correctly
    # without also serving static files from here.
    asset_path = f"{site['urls']['base']}/assets/"

    template = env.get_template("pages/generic.html")
    return template.render(
        page=page_dict,
        meta={"title": page.seo_title or page.title, "description": page.seo_description or "", "canonical": None, "og_title": page.title, "og_description": ""},
        site=site, services=services, blog=blog, all_posts=all_posts, products=products,
        pricing=pricing, packages=packages, price_index=price_index, price_count=price_count, price_min=price_min,
        search_pricing_items=[], areas_total_all=areas_total_all, other_cities=other_cities,
        root_path="/", asset_path=asset_path,
    )
