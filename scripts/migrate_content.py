#!/usr/bin/env python3
"""One-time content migration: src/data/*.json -> content/*.yml.

Run once (`python3 scripts/migrate_content.py`) to regenerate the
data-driven collections (products, locations, locations_matrix, posts,
pricing, packages, proof, testimonials, steam_iron) from the existing
JSON. Safe to re-run — it always overwrites its own output files, never
hand-authored ones like content/pages/*.yml.

Why a script instead of hand-written YAML: these collections are large
(15 services, 10 localities, 70 locality x service combinations, 58 price
items) and already exist as clean structured JSON. Transcribing them by
hand would be slower AND more error-prone than converting them
programmatically — the whole point of "zero hardcoded content" is that
the data already IS structured; it just needs a new home.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC_DATA = ROOT / "src" / "data"
CONTENT = ROOT / "content"


class LiteralStr(str):
    """Marker so long text fields dump as YAML block scalars (readable diffs)."""


def literal_presenter(dumper, data):
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


yaml.add_representer(LiteralStr, literal_presenter)


def dump(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, width=100)
    print(f"wrote {path.relative_to(ROOT)}")


def wrap_long(obj):
    """Recursively mark long strings as literal block scalars for readability."""
    if isinstance(obj, str):
        return LiteralStr(obj) if len(obj) > 80 or "\n" in obj else obj
    if isinstance(obj, list):
        return [wrap_long(v) for v in obj]
    if isinstance(obj, dict):
        return {k: wrap_long(v) for k, v in obj.items()}
    return obj


def load(name: str):
    return json.loads((SRC_DATA / name).read_text(encoding="utf-8"))


def migrate_products():
    services = load("services.json")["services"]
    gen_path = SRC_DATA / "generated" / "services.json"
    gen = {s["slug"]: s for s in json.loads(gen_path.read_text(encoding="utf-8"))["services"]} if gen_path.exists() else {}

    for svc in services:
        merged = dict(svc)
        extra = gen.get(svc["slug"])
        if extra:
            merged.update({k: v for k, v in extra.items() if k != "slug"})
        dump(CONTENT / "products" / f"{svc['slug']}.yml", wrap_long(merged))
    print(f"-> {len(services)} products")


def migrate_locations():
    site = load("site.json")
    locations_legacy = load("locations.json")
    gen_path = SRC_DATA / "generated" / "localities.json"
    gen = {loc["slug"]: loc for loc in json.loads(gen_path.read_text(encoding="utf-8"))["localities"]} if gen_path.exists() else {}

    url_map = {k: v for k, v in site["locality_urls"].items() if not k.startswith("_")}
    legacy_areas = {a["slug"]: a for a in locations_legacy.get("service_areas", [])}
    footer_labels = {a["url"].rstrip("/"): a["label"] for a in site["footer"]["areas"]}

    count = 0
    for loc_slug, url_slug in url_map.items():
        gen_entry = gen.get(loc_slug, {})
        legacy_entry = legacy_areas.get(url_slug, {})
        merged = dict(legacy_entry)
        merged.update({k: v for k, v in gen_entry.items() if k != "slug"})
        merged["loc_slug"] = loc_slug
        merged["url_slug"] = url_slug
        merged["name"] = footer_labels.get(url_slug, loc_slug.replace("-", " ").title())
        dump(CONTENT / "locations" / f"{url_slug}.yml", wrap_long(merged))
        count += 1
    print(f"-> {count} locations")


def migrate_matrix():
    site = load("site.json")
    url_map = {k: v for k, v in site["locality_urls"].items() if not k.startswith("_")}
    gen_path = SRC_DATA / "generated" / "matrix.json"
    if not gen_path.exists():
        print("-> 0 matrix pages (no generated/matrix.json)")
        return
    pages = json.loads(gen_path.read_text(encoding="utf-8"))["pages"]
    count = 0
    for entry in pages:
        loc_url = url_map.get(entry["locality"])
        if not loc_url:
            continue
        slug = f"{entry['service']}-{entry['locality']}"
        merged = dict(entry)
        merged["url_slug"] = slug
        merged["locality_url"] = loc_url
        dump(CONTENT / "locations_matrix" / f"{slug}.yml", wrap_long(merged))
        count += 1
    print(f"-> {count} matrix pages")


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def migrate_posts():
    blog = load("blog.json")
    count = 0
    for post in blog["posts"]:
        slug = post["url"].rstrip("/").rsplit("/", 1)[-1]
        front_matter = {
            "title": post["title"],
            "date": post["date"],
            "excerpt": post["excerpt"],
            "cover_service_slug": post.get("art"),
            "legacy_url": post["url"],
            "status": "published",
        }
        # NOTE: the source data (src/data/blog.json) never had full post
        # bodies — only title/date/excerpt/a (currently broken) URL. There
        # is no article text anywhere in this codebase to migrate. The
        # excerpt is used as a placeholder body so the post is at least
        # renderable; a real body needs to be written by whoever owns this
        # content, not fabricated here.
        body = post["excerpt"]
        content = "---\n" + yaml.dump(front_matter, allow_unicode=True, sort_keys=False) + "---\n\n" + body + "\n"
        path = CONTENT / "posts" / f"{slug}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        count += 1
    print(f"-> {count} posts (excerpt-only bodies — see comment in script)")


def migrate_pricing():
    pricing = load("pricing.json")
    dump(CONTENT / "pricing.yml", wrap_long(pricing))


def migrate_packages():
    packages = load("packages.json")
    dump(CONTENT / "packages.yml", wrap_long(packages))


def migrate_misc():
    dump(CONTENT / "proof.yml", wrap_long(load("proof.json")))
    dump(CONTENT / "testimonials.yml", wrap_long(load("testimonials.json")))
    dump(CONTENT / "steam_iron.yml", wrap_long(load("steam-iron.json")))
    dump(CONTENT / "home_data.yml", wrap_long(load("home.json")))
    dump(CONTENT / "about_data.yml", wrap_long(load("about.json")))
    dump(CONTENT / "pages_data.yml", wrap_long(load("pages.json")))
    dump(CONTENT / "areas_full.yml", wrap_long(load("areas.json")))


if __name__ == "__main__":
    migrate_products()
    migrate_locations()
    migrate_matrix()
    migrate_posts()
    migrate_pricing()
    migrate_packages()
    migrate_misc()
    print("\nDone.")
