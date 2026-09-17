#!/usr/bin/env python3
"""QA gate for the generated area pages.

Run after `python3 src/build.py`. It reads the built HTML in dist/ for every
area in src/data/area-pages.json and fails if any of the SEO invariants that
matter for a programmatic local-SEO set are broken:

  * one page per registry entry, actually written to disk
  * unique <title>, meta description, <h1> and slug across all area pages
  * canonical tag present and matching the sitemap URL for that page
  * no `noindex` on any area page
  * no unrendered Jinja placeholders left in the output
  * FAQ questions and nearby-area link sets differ between pages

Usage:  python3 tools/check-area-pages.py
Exit code 1 on any failure, so it can be used in CI.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
REGISTRY = ROOT / "src" / "data" / "area-pages.json"

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def first(pattern: str, html: str) -> str | None:
    m = re.search(pattern, html, re.I | re.S)
    return m.group(1).strip() if m else None


def main() -> int:
    areas = json.loads(REGISTRY.read_text(encoding="utf-8"))["areas"]
    sitemap = (DIST / "sitemap.xml").read_text(encoding="utf-8")
    sitemap_locs = set(re.findall(r"<loc>([^<]+)</loc>", sitemap))

    seen: dict[str, dict[str, str]] = {}
    titles: dict[str, list[str]] = defaultdict(list)
    descs: dict[str, list[str]] = defaultdict(list)
    h1s: dict[str, list[str]] = defaultdict(list)
    faq_sets: dict[str, str] = {}
    nearby_sets: dict[str, str] = {}

    slugs = [a["slug"] for a in areas]
    if len(set(slugs)) != len(slugs):
        fail("duplicate slugs in area-pages.json registry")

    for area in areas:
        slug = area["slug"]
        path = DIST / slug / "index.html"
        if not path.exists():
            fail(f"{slug}: page was not generated ({path} missing)")
            continue
        html = path.read_text(encoding="utf-8")
        seen[slug] = {}

        title = first(r"<title>(.*?)</title>", html)
        desc = first(r'<meta name="description" content="(.*?)"', html)
        h1 = first(r"<h1[^>]*>(.*?)</h1>", html)
        canonical = first(r'<link rel="canonical" href="(.*?)"', html)

        for label, value in (("title", title), ("meta description", desc),
                             ("h1", h1), ("canonical", canonical)):
            if not value:
                fail(f"{slug}: missing {label}")

        if title:
            titles[title].append(slug)
        if desc:
            descs[desc].append(slug)
        if h1:
            h1s[re.sub(r"<[^>]+>", "", h1)].append(slug)

        if canonical:
            if not canonical.endswith(f"/{slug}/"):
                fail(f"{slug}: canonical {canonical} does not match its own URL")
            if canonical not in sitemap_locs:
                fail(f"{slug}: canonical {canonical} is not in sitemap.xml")

        if re.search(r"noindex", html, re.I):
            fail(f"{slug}: page carries a noindex directive")

        if "{{" in html or "{%" in html:
            fail(f"{slug}: unrendered template placeholder left in output")

        questions = re.findall(r'"@type": "Question",\s*"name": (".*?")', html, re.S)
        if len(questions) < 5:
            fail(f"{slug}: only {len(questions)} FAQs (expected at least 5)")
        key = "|".join(sorted(questions))
        if key and key in faq_sets:
            fail(f"{slug}: FAQ set is identical to {faq_sets[key]}")
        faq_sets.setdefault(key, slug)

        # Scoped to the "Nearby" section only — the site-wide footer links to
        # ten areas on every page, so an unscoped search would look identical
        # everywhere and prove nothing.
        block = re.search(r"Areas we also collect from.*?</section>", html, re.S)
        nearby = re.findall(r'href="\.\./(laundry-service-[^/"]+)/"', block.group(0) if block else "")
        if not nearby:
            fail(f"{slug}: no nearby-area links rendered")
        nkey = "|".join(sorted(set(nearby)))
        if nkey and nkey in nearby_sets:
            fail(f"{slug}: nearby-area link set is identical to {nearby_sets[nkey]}")
        nearby_sets.setdefault(nkey, slug)

    for label, groups in (("title", titles), ("meta description", descs), ("h1", h1s)):
        for value, owners in groups.items():
            if len(owners) > 1:
                fail(f"duplicate {label} shared by {', '.join(owners)}: {value[:70]!r}")

    print(f"Checked {len(seen)} area pages in {DIST}")
    if failures:
        print(f"\n{len(failures)} problem(s):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("All area-page checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
