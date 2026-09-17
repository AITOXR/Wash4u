#!/usr/bin/env python3
"""QA gate for the generated area and coverage pages.

Run after `python3 src/build.py`. It reads the built HTML in dist/ for every
entry in src/data/area-pages.json (Gurugram area pages) and
src/data/coverage-pages.json (the non-Gurugram service-area pages and their
four city hubs) and fails if any of the SEO invariants that matter for a
programmatic local set are broken:

  * one page per registry entry, actually written to disk
  * unique <title>, meta description, <h1> and slug across the WHOLE set,
    both registries together
  * canonical tag present and matching the sitemap URL for that page
  * no `noindex` on any page
  * no unrendered Jinja placeholders left in the output
  * FAQ questions and nearby-area link sets differ between pages
  * every internal ../slug/ link resolves to a page that was built

Coverage pages are additionally checked for the claims they must NOT make:

  * no "nearest store" language, no address outside Gurugram
  * no LocalBusiness / DryCleaningOrLaundry node scoped to the page itself
    (the site-wide one in base.html carries the real Gurugram address and is
    allowed; a second one on a Noida page would not be)
  * the honest coverage disclosure is present in the rendered HTML
  * no turnaround-time or same-day promise

Usage:  python3 tools/check-area-pages.py
Exit code 1 on any failure, so it can be used in CI.
"""

from __future__ import annotations

import html as html_mod
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
AREA_REGISTRY = ROOT / "src" / "data" / "area-pages.json"
COVERAGE_REGISTRY = ROOT / "src" / "data" / "coverage-pages.json"

# Phrases a coverage page must never contain: each one would imply a physical
# presence in a city where there is none, or promise a turnaround we do not
# commit to anywhere else on the site.
FORBIDDEN_ON_COVERAGE = [
    r"nearest store to",
    r"\bnearest (?:store|branch|counter|outlet)\b",
    r"\bour (?:store|shop|branch|counter) in (?:Delhi|Noida|Faridabad|Ghaziabad)",
    r"\bsame[- ]day\b",
    r"\bwithin \d+ (?:hours?|minutes?)\b",
    r"\b\d+[- ]hour (?:delivery|turnaround)\b",
    r"\b24[- ]hour (?:delivery|turnaround)\b",
]
# The disclosure wording rotates, so rather than matching phrases the checker
# asserts that each page renders its own registry `coverage_note` verbatim.

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def first(pattern: str, html: str) -> str | None:
    m = re.search(pattern, html, re.I | re.S)
    return m.group(1).strip() if m else None


def strip_tags(s: str) -> str:
    """Visible text, with entities decoded so `&amp;` matches a registry `&`."""
    return html_mod.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def main() -> int:
    areas = json.loads(AREA_REGISTRY.read_text(encoding="utf-8"))["areas"]
    coverage = json.loads(COVERAGE_REGISTRY.read_text(encoding="utf-8"))
    cov_areas, cov_hubs = coverage["areas"], coverage["hubs"]

    sitemap = (DIST / "sitemap.xml").read_text(encoding="utf-8")
    sitemap_locs = set(re.findall(r"<loc>([^<]+)</loc>", sitemap))

    # (slug, kind) for everything we check. kind drives the extra assertions.
    notes = {c["slug"]: c["coverage_note"] for c in cov_areas}
    notes.update({h["slug"]: h["coverage_note"] for h in cov_hubs})

    targets = (
        [(a["slug"], "area") for a in areas]
        + [(c["slug"], "coverage") for c in cov_areas]
        + [(h["slug"], "hub") for h in cov_hubs]
    )

    slugs = [s for s, _ in targets]
    dupes = {s for s in slugs if slugs.count(s) > 1}
    if dupes:
        fail(f"duplicate slugs across the two registries: {sorted(dupes)}")

    checked = 0
    titles: dict[str, list[str]] = defaultdict(list)
    descs: dict[str, list[str]] = defaultdict(list)
    h1s: dict[str, list[str]] = defaultdict(list)
    faq_sets: dict[str, str] = {}
    nearby_sets: dict[str, str] = {}

    for slug, kind in targets:
        path = DIST / slug / "index.html"
        if not path.exists():
            fail(f"{slug}: page was not generated ({path} missing)")
            continue
        html = path.read_text(encoding="utf-8")
        checked += 1

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
            h1s[strip_tags(h1)].append(slug)

        if canonical:
            if not canonical.endswith(f"/{slug}/"):
                fail(f"{slug}: canonical {canonical} does not match its own URL")
            if canonical not in sitemap_locs:
                fail(f"{slug}: canonical {canonical} is not in sitemap.xml")

        if re.search(r"noindex", html, re.I):
            fail(f"{slug}: page carries a noindex directive")

        if "{{" in html or "{%" in html:
            fail(f"{slug}: unrendered template placeholder left in output")

        # Every internal link must resolve to a page that was actually built.
        for target in set(re.findall(r'href="\.\./([^"#?]+?)/"', html)):
            if not (DIST / target / "index.html").exists():
                fail(f"{slug}: links to ../{target}/ which was not built")

        questions = re.findall(r'"@type": "Question",\s*"name": (".*?")', html, re.S)
        min_faqs = 5 if kind != "hub" else 0
        if len(questions) < min_faqs:
            fail(f"{slug}: only {len(questions)} FAQs (expected at least {min_faqs})")
        key = "|".join(sorted(questions))
        if key and kind == "area":
            # Gurugram pages are hand-written, so an identical FAQ set means
            # someone copy-pasted. Coverage FAQs rotate from a shared pool by
            # design, so they are checked for spread rather than uniqueness.
            if key in faq_sets:
                fail(f"{slug}: FAQ set is identical to {faq_sets[key]}")
            faq_sets.setdefault(key, slug)

        block = re.search(r"(?:Areas we also collect from|on the same coverage list).*?</section>", html, re.S)
        nearby = re.findall(r'href="\.\./(laundry-service-[^/"]+)/"', block.group(0) if block else "")
        if kind != "hub":
            if not nearby:
                fail(f"{slug}: no nearby-area links rendered")
            nkey = "|".join(sorted(set(nearby)))
            if nkey and nkey in nearby_sets:
                fail(f"{slug}: nearby-area link set is identical to {nearby_sets[nkey]}")
            nearby_sets.setdefault(nkey, slug)

        if kind in ("coverage", "hub"):
            text = strip_tags(html)
            for pattern in FORBIDDEN_ON_COVERAGE:
                m = re.search(pattern, text, re.I)
                if m:
                    fail(f"{slug}: coverage page contains a claim it cannot back: {m.group(0)!r}")
            flat = re.sub(r"\s+", " ", text)
            note = re.sub(r"\s+", " ", notes.get(slug, "")).strip()
            if not note or note not in flat:
                fail(f"{slug}: coverage page does not render its no-local-branch disclosure")
            # Exactly one DryCleaningOrLaundry node — the site-wide Gurugram
            # one from base.html. A second would be a fake local listing.
            if html.count('"@type": "DryCleaningOrLaundry"') != 1:
                fail(f"{slug}: unexpected number of DryCleaningOrLaundry nodes")
            for locality in re.findall(r'"addressLocality": "([^"]+)"', html):
                if locality != "Gurugram":
                    fail(f"{slug}: postal address claims addressLocality {locality!r}")

    # Coverage FAQ spread: the pool is shared, so require that no single FAQ
    # set is used by more than a handful of pages.
    cov_faq_counts: dict[str, int] = defaultdict(int)
    for c in cov_areas:
        cov_faq_counts["|".join(f["q"] for f in c["faqs"])] += 1
    worst = max(cov_faq_counts.values()) if cov_faq_counts else 0
    if worst > 5:
        fail(f"coverage FAQ sets repeat too often — one set is used on {worst} pages")

    for label, groups in (("title", titles), ("meta description", descs), ("h1", h1s)):
        for value, owners in groups.items():
            if len(owners) > 1:
                fail(f"duplicate {label} shared by {', '.join(owners)}: {value[:70]!r}")

    print(f"Checked {checked} pages in {DIST} "
          f"({len(areas)} Gurugram area, {len(cov_areas)} coverage, {len(cov_hubs)} city hub)")
    if failures:
        print(f"\n{len(failures)} problem(s):")
        for f in failures[:80]:
            print(f"  - {f}")
        if len(failures) > 80:
            print(f"  ... and {len(failures) - 80} more")
        return 1
    print("All area-page checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
