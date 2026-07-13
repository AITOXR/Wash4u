#!/usr/bin/env python3
"""Wash4You static site generator."""

import json
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = ROOT / "templates"
DATA_DIR = ROOT / "data"
ASSETS_DIR = ROOT / "assets"
DIST_DIR = ROOT.parent / "dist"


def load_json(path: Path) -> dict | list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_paths(depth: int) -> tuple[str, str]:
    """Return (root_path, asset_path) for a page at given directory depth."""
    if depth == 0:
        return "", "assets/"
    prefix = "../" * depth
    return prefix, prefix + "assets/"


def write_html(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build() -> None:
    # Clean and recreate dist
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # Copy assets
    shutil.copytree(ASSETS_DIR, DIST_DIR / "assets")

    # Copy images to dist root for root-relative access
    images_src = ASSETS_DIR / "images"
    images_dst = DIST_DIR / "images"
    shutil.copytree(images_src, images_dst)

    # Load data
    site = load_json(DATA_DIR / "site.json")
    home = load_json(DATA_DIR / "home.json")
    about = load_json(DATA_DIR / "about.json")
    services = load_json(DATA_DIR / "services.json")
    pricing = load_json(DATA_DIR / "pricing.json")
    steam = load_json(DATA_DIR / "steam-iron.json")
    blog = load_json(DATA_DIR / "blog.json")
    locations = load_json(DATA_DIR / "locations.json")
    policies = load_json(DATA_DIR / "policies.json")
    pages = load_json(DATA_DIR / "pages.json")

    # Jinja environment
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), trim_blocks=True, lstrip_blocks=True)

    # Page registry
    pages_to_build = []

    # Home
    pages_to_build.append(("index.html", "page-home.html", {
        "meta": home["meta"],
        "home": home,
        "services": services,
        "depth": 0,
    }))

    # About
    pages_to_build.append(("about-us/index.html", "page-about.html", {
        "meta": about["meta"],
        "about": about,
        "depth": 1,
    }))

    # Services list
    pages_to_build.append(("services/index.html", "page-services-list.html", {
        "meta": services["meta"],
        "services": services,
        "depth": 1,
    }))

    # Service detail pages
    for service in services["services"]:
        pages_to_build.append((
            f"services/{service['slug']}/index.html",
            "page-service-detail.html",
            {
                "meta": {
                    "title": f"{service['name']} – Wash4You",
                    "description": service["short_description"],
                    "canonical": f"https://wash4you.in/services/{service['slug']}/",
                    "og_title": f"{service['name']} – Wash4You",
                    "og_description": service["short_description"],
                },
                "service": service,
                "depth": 2,
            }
        ))

    # Pricing
    pages_to_build.append(("pricing/index.html", "page-pricing.html", {
        "meta": pricing["meta"],
        "pricing": pricing,
        "depth": 1,
    }))

    # Steam Iron
    pages_to_build.append(("steam-iron/index.html", "page-steam-iron.html", {
        "meta": steam["meta"],
        "steam": steam,
        "depth": 1,
    }))

    # Blog
    pages_to_build.append(("blog/index.html", "page-blog-list.html", {
        "meta": blog["meta"],
        "blog": blog,
        "depth": 1,
    }))

    # Contact
    pages_to_build.append(("contact-us/index.html", "page-contact.html", {
        "meta": pages["contact"]["meta"],
        "pages": pages,
        "depth": 1,
    }))

    # Locate Us
    pages_to_build.append(("locate-us/index.html", "page-locate-us.html", {
        "meta": locations["meta"],
        "locations": locations,
        "depth": 1,
    }))

    # Location pages
    for area in locations["service_areas"]:
        pages_to_build.append((
            f"{area['slug']}/index.html",
            "page-location.html",
            {
                "meta": {
                    "title": area["title"],
                    "description": area["description"],
                    "canonical": f"https://wash4you.in/{area['slug']}/",
                    "og_title": area["title"],
                    "og_description": area["description"],
                },
                "area": area,
                "depth": 1,
            }
        ))

    # Policy pages
    for policy in policies["policies"]:
        pages_to_build.append((
            f"{policy['slug']}/index.html",
            "page-policy.html",
            {
                "meta": {
                    "title": policy["meta_title"],
                    "description": policy["meta_description"],
                    "canonical": policy["canonical"],
                    "og_title": policy["meta_title"],
                    "og_description": policy["meta_description"],
                },
                "policy": policy,
                "depth": 1,
            }
        ))

    # 404
    pages_to_build.append(("404.html", "page-404.html", {
        "meta": pages["not_found"]["meta"],
        "pages": pages,
        "depth": 0,
    }))

    # Render all pages
    template_cache = {}
    for rel_path, template_name, context in pages_to_build:
        template = template_cache.get(template_name)
        if template is None:
            template = env.get_template(template_name)
            template_cache[template_name] = template

        depth = context.pop("depth")
        root_path, asset_path = get_paths(depth)
        context["site"] = site
        context["root_path"] = root_path
        context["asset_path"] = asset_path

        html = template.render(**context)
        write_html(DIST_DIR / rel_path, html)
        print(f"Built: {rel_path}")

    print(f"\nDone. Generated {len(pages_to_build)} pages in {DIST_DIR}")


if __name__ == "__main__":
    try:
        build()
    except Exception as e:
        print(f"Build failed: {e}", file=sys.stderr)
        raise
