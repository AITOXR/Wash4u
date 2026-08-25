#!/usr/bin/env python3
"""Wash4You static site generator — content-plane build.

Reads content/ (YAML + Markdown) + schemas/sections/ (field schemas) and
renders templates/ into dist2/. Pages are one of two kinds:

  - Section pages (content/pages/*.yml): an ordered list of sections, each
    rendered by templates/sections/<type>.html. Adding a section type later
    means one Jinja partial + one schema file — no other code changes.
  - Collection pages (content/products/, content/locations/,
    content/locations_matrix/, content/posts/): one fixed template per
    collection (templates/pages/product.html etc.), fed by that record's
    fields. Every field is still admin-editable — collections just don't
    need a drag-and-drop section list, the same way a WordPress custom
    post type doesn't.

Run `python3 scripts/migrate_content.py` first if content/products,
content/locations, content/locations_matrix, content/posts, content/pricing.yml
or content/packages.yml don't exist yet — they're generated from src/data/.
"""

from __future__ import annotations

import html
import re
import shutil
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

ROOT = Path(__file__).resolve().parent
CONTENT_DIR = ROOT / "content"
SCHEMAS_DIR = ROOT / "schemas" / "sections"
TEMPLATES_DIR = ROOT / "templates"
ASSETS_DIR = ROOT / "src" / "assets"  # not yet migrated to a media library
DIST_DIR = ROOT / "dist2"  # separate from dist/ (the old generator's output) while both exist


def load_yaml(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_schemas() -> dict:
    return {p.stem: load_yaml(p) for p in SCHEMAS_DIR.glob("*.yml")}


def validate_section(section: dict, schemas: dict, page_slug: str) -> list[str]:
    """Check a section's props against its schema's required fields.

    Hand-rolled rather than a jsonschema dependency: the checks needed here
    (required top-level fields present, repeater items carry required
    sub-fields) are a small fixed set, and this project avoids a dependency
    for something this size — same call as markdown_to_html below.
    """
    errors = []
    schema = schemas.get(section["type"])
    if schema is None:
        errors.append(f"{page_slug}: unknown section type '{section['type']}'")
        return errors
    props = section.get("props") or {}
    for field in schema.get("fields", []):
        if not field.get("required"):
            continue
        value = props.get(field["key"])
        if value in (None, "", []):
            errors.append(
                f"{page_slug}: section '{section['id']}' ({section['type']}) "
                f"is missing required field '{field['key']}'"
            )
        if field["type"] == "repeater" and value:
            for i, item in enumerate(value):
                for sub in field.get("item_fields", []):
                    if sub.get("required") and not item.get(sub["key"]):
                        errors.append(
                            f"{page_slug}: section '{section['id']}' "
                            f"({section['type']}) item {i} is missing "
                            f"required field '{sub['key']}'"
                        )
    return errors


def markdown_to_html(text: str) -> str:
    """Small hand-rolled Markdown subset: headings, paragraphs, unordered
    lists, **bold**, *italic*. Ported unchanged from src/build.py — see that
    file's docstring for the full rationale (no dependency, everything
    HTML-escaped first so content can never inject markup).
    """
    if not text:
        return ""
    levels = [len(m.group(1)) for m in re.finditer(r"^(#{1,4})\s", text, re.M)]
    shift = (2 - min(levels)) if levels else 0
    out: list[str] = []
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    def inline(s: str) -> str:
        s = html.escape(s, quote=False)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*([^*\n]+?)\*", r"<em>\1</em>", s)
        return s

    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            close_list()
            continue
        heading = re.match(r"^(#{1,4})\s+(.*)$", line)
        if heading:
            close_list()
            level = min(max(len(heading.group(1)) + shift, 2), 4)
            out.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
        elif re.match(r"^[-*+] ", line):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(line[2:])}</li>")
        else:
            close_list()
            out.append(f"<p>{inline(line)}</p>")
    close_list()
    return "\n".join(out)


BRAND_SUFFIXES = (" | Wash4You", " — Wash4You", " - Wash4You", " | Wash4You Gurugram")


def fit_title(title: str, limit: int = 60) -> str:
    """Keep titles inside Google's ~60-character display width. Ported unchanged from src/build.py."""
    if not title or len(title) <= limit:
        return title
    for suffix in sorted(BRAND_SUFFIXES, key=len, reverse=True):
        if title.endswith(suffix):
            trimmed = title[: -len(suffix)].rstrip(" |—-")
            if len(trimmed) <= limit:
                return trimmed
            title = trimmed
            break
    if len(title) <= limit:
        return title
    cut = title[:limit].rsplit(" ", 1)[0]
    cut = cut.rstrip(" |—-,&")
    cut = re.sub(r"\s+(&|and|or|the|of|in|for|to|with|a|an)$", "", cut, flags=re.I)
    return cut.rstrip(" |—-,&")


def fit_description(desc: str, limit: int = 155) -> str:
    """Keep meta descriptions inside the ~155-character snippet width. Ported unchanged from src/build.py."""
    if not desc or len(desc) <= limit:
        return desc
    window = desc[: limit + 1]
    for stop in (". ", "! ", "? "):
        idx = window.rfind(stop)
        if idx > limit * 0.55:
            return window[: idx + 1].strip()
    if desc[:limit].endswith("."):
        return desc[:limit]
    return desc[:limit].rsplit(" ", 1)[0].rstrip(" ,;:—-") + "…"


def build_meta(raw_meta: dict, fallback_title: str) -> dict:
    meta = {"canonical": raw_meta.get("canonical"), "robots": raw_meta.get("robots")}
    meta["og_title"] = raw_meta.get("og_title") or raw_meta.get("title") or fallback_title
    meta["og_description"] = raw_meta.get("og_description") or raw_meta.get("description") or ""
    meta["title"] = fit_title(raw_meta.get("title") or fallback_title)
    meta["description"] = fit_description(raw_meta.get("description") or "")
    return meta


def get_paths(depth: int) -> tuple[str, str]:
    if depth == 0:
        return "", "assets/"
    prefix = "../" * depth
    return prefix, prefix + "assets/"


def write_html(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_markdown_post(path: Path) -> dict:
    """content/posts/<slug>.md: YAML front matter between --- lines, then a Markdown body."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n\n?(.*)$", text, re.S)
    if not m:
        raise ValueError(f"{path}: missing YAML front matter (expected --- ... ---)")
    front = yaml.safe_load(m.group(1)) or {}
    front["body"] = m.group(2).strip()
    front["slug"] = path.stem
    return front


def build(check_only: bool = False) -> None:
    schemas = load_schemas()

    site_yml = load_yaml(CONTENT_DIR / "site.yml")
    nav_yml = load_yaml(CONTENT_DIR / "navigation.yml")
    areas_yml = load_yaml(CONTENT_DIR / "areas.yml")

    site = dict(site_yml)
    site["nav"] = {"main": nav_yml["header_main"], "cta": nav_yml["header_cta"]}
    site["footer"] = {
        "explore": nav_yml["footer_explore"],
        "areas": nav_yml["footer_areas"],
        "support": nav_yml["footer_support"],
    }

    areas_total_all = sum(c["count"] for c in areas_yml["cities"])
    other_cities = [c["name"] for c in areas_yml["cities"] if c["name"] != "Gurugram (Gurgaon)"]

    # ---- Collections ----
    products_dir = CONTENT_DIR / "products"
    products = [load_yaml(p) for p in sorted(products_dir.glob("*.yml"))] if products_dir.exists() else []
    products.sort(key=lambda p: p.get("_order", 0))

    locations_dir = CONTENT_DIR / "locations"
    locations = [load_yaml(p) for p in sorted(locations_dir.glob("*.yml"))] if locations_dir.exists() else []

    matrix_dir = CONTENT_DIR / "locations_matrix"
    matrix_entries = [load_yaml(p) for p in sorted(matrix_dir.glob("*.yml"))] if matrix_dir.exists() else []

    posts_dir = CONTENT_DIR / "posts"
    all_posts = [parse_markdown_post(p) for p in sorted(posts_dir.glob("*.md"))] if posts_dir.exists() else []

    pricing_path = CONTENT_DIR / "pricing.yml"
    pricing = load_yaml(pricing_path) if pricing_path.exists() else {"categories": []}
    packages_path = CONTENT_DIR / "packages.yml"
    packages = load_yaml(packages_path) if packages_path.exists() else {"plans": []}

    services = {"services": [{"slug": p["slug"], "name": p["name"]} for p in products]}
    blog = {"posts": [{"title": p["title"], "url": p.get("legacy_url") or f"{site['urls']['base']}/blog/{p['slug']}/"} for p in all_posts]}

    price_index = {
        item["slug"]: item
        for category in pricing["categories"]
        for item in category["items"]
        if item.get("slug")
    }
    price_count = sum(len(c["items"]) for c in pricing["categories"])
    price_min = min((i["amount"] for c in pricing["categories"] for i in c["items"] if not i.get("unit")), default=0)
    search_pricing_items = [
        {"name": item["name"], "cat_index": cat_i}
        for cat_i, category in enumerate(pricing["categories"])
        for item in category["items"]
        if item.get("name")
    ]

    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        trim_blocks=True, lstrip_blocks=True, autoescape=True,
    )
    env.filters["markdown"] = lambda s: Markup(markdown_to_html(s))
    env.globals["edit_mode"] = False
    # No admin/editor rendering pass in the static build — cms() is a no-op,
    # matching production mode in the old generator.
    env.globals["cms"] = lambda *a, **k: ""

    # ---- Validate section pages ----
    errors: list[str] = []
    section_pages = []
    for page_path in sorted((CONTENT_DIR / "pages").glob("*.yml")):
        page = load_yaml(page_path)
        for section in page["sections"]:
            errors.extend(validate_section(section, schemas, page["slug"]))
        section_pages.append(page)

    if errors:
        for e in errors:
            print(f"CONTENT ERROR: {e}", file=sys.stderr)
        sys.exit(f"\nBuild failed: {len(errors)} content error(s). No output written.")

    if check_only:
        print(f"OK: {len(section_pages)} section page(s), {len(products)} products, "
              f"{len(locations)} locations, {len(matrix_entries)} matrix pages, "
              f"{len(all_posts)} posts — validated against {len(schemas)} section schemas, no errors.")
        return

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    if ASSETS_DIR.exists():
        shutil.copytree(ASSETS_DIR, DIST_DIR / "assets")
        images_src = ASSETS_DIR / "images"
        if images_src.exists():
            shutil.copytree(images_src, DIST_DIR / "images")

    # Media Library uploads (admin/app/routers/{media,editor}.py) land in
    # content/media/ — copy them alongside the other assets so an image
    # swapped in the editor actually appears on the published site, not
    # just in the admin's own preview.
    media_src = CONTENT_DIR / "media"
    if media_src.exists():
        shutil.copytree(media_src, DIST_DIR / "assets" / "media", dirs_exist_ok=True)

    common = dict(
        site=site, services=services, blog=blog, all_posts=all_posts,
        products=products, pricing=pricing, packages=packages,
        price_index=price_index, price_count=price_count, price_min=price_min,
        search_pricing_items=search_pricing_items,
        areas_total_all=areas_total_all, other_cities=other_cities,
    )

    urls: list[tuple[str, str]] = []  # (loc, priority) for sitemap.xml
    built = 0

    def render_page(template_name: str, out_rel: str, depth: int, meta: dict, **ctx):
        nonlocal built
        root_path, asset_path = get_paths(depth)
        rendered = env.get_template(template_name).render(
            meta=meta, root_path=root_path, asset_path=asset_path, **common, **ctx,
        )
        if out_rel == "index.html":
            out_path = DIST_DIR / "index.html"
            loc_path = ""
        elif out_rel == "404.html":
            out_path = DIST_DIR / "404.html"
            loc_path = None  # not in sitemap
        else:
            out_path = DIST_DIR / out_rel / "index.html"
            loc_path = out_rel + "/"
        write_html(out_path, rendered)
        built += 1
        print(f"Built: {out_path.relative_to(DIST_DIR)}")
        if loc_path is not None and meta.get("robots") != "noindex, follow":
            urls.append((f"{site['urls']['base']}/{loc_path}", "0.7"))

    # ---- Section pages ----
    for page in section_pages:
        depth = page.get("depth", 1)
        meta = build_meta(page.get("seo") or {}, page["title"])
        out_rel = "index.html" if page["slug"] == "" else ("404.html" if page["slug"] == "404" else page["slug"])
        render_page("pages/generic.html", out_rel, depth, meta, page=page)

    # ---- Products (services/<slug>/) ----
    for product in products:
        meta = build_meta(
            {"title": product.get("meta_title") or f"{product['name']} – Wash4You",
             "description": product.get("meta_description") or product.get("short_description"),
             "canonical": f"{site['urls']['base']}/services/{product['slug']}/"},
            product["name"],
        )
        render_page("pages/product.html", f"services/{product['slug']}", 2, meta, product=product)

    # ---- Locations (<url_slug>/) ----
    for loc in locations:
        meta = build_meta(
            {"title": loc.get("meta_title") or loc.get("title"),
             "description": loc.get("meta_description") or loc.get("description"),
             "canonical": f"{site['urls']['base']}/{loc['url_slug']}/"},
            loc.get("name", loc["url_slug"]),
        )
        render_page("pages/location.html", loc["url_slug"], 1, meta, location=loc)

    # ---- Matrix pages (<service>-<locality>/) ----
    for entry in matrix_entries:
        meta = build_meta(
            {"title": entry.get("meta_title"), "description": entry.get("meta_description"),
             "canonical": f"{site['urls']['base']}/{entry['url_slug']}/"},
            entry.get("h1", entry["url_slug"]),
        )
        render_page("pages/matrix.html", entry["url_slug"], 1, meta, entry=entry)

    # ---- Blog list + posts ----
    meta = build_meta(
        {"title": "Laundry & Dry Cleaning Blog | Wash4You",
         "description": "Guides on stains, fabrics, footwear and monsoon drying.",
         "canonical": f"{site['urls']['base']}/blog/"},
        "Blog",
    )
    render_page("pages/blog_list.html", "blog", 1, meta)
    for post in all_posts:
        meta = build_meta(
            {"title": f"{post['title']} | Wash4You Blog", "description": post.get("excerpt"),
             "canonical": f"{site['urls']['base']}/blog/{post['slug']}/"},
            post["title"],
        )
        render_page("pages/post.html", f"blog/{post['slug']}", 2, meta, post=post)

    # ---- sitemap.xml + robots.txt ----
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, prio in urls:
        sitemap.append(f"  <url><loc>{html.escape(loc)}</loc><priority>{prio}</priority></url>")
    sitemap.append("</urlset>")
    (DIST_DIR / "sitemap.xml").write_text("\n".join(sitemap) + "\n", encoding="utf-8")
    (DIST_DIR / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {site['urls']['base']}/sitemap.xml\n", encoding="utf-8"
    )
    (DIST_DIR / ".nojekyll").write_text("", encoding="utf-8")

    print(f"\nDone. Generated {built} page(s) + sitemap ({len(urls)} URLs) in {DIST_DIR}")


if __name__ == "__main__":
    try:
        build(check_only="--check" in sys.argv)
    except Exception as e:
        print(f"Build failed: {e}", file=sys.stderr)
        raise
