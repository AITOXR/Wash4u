"""Read/write helpers for the content JSON the admin edits.

A binding is "<store>:<dotted.path>" — e.g. "home:banner.headline_line1" or
"home:how_it_works.steps.0.title". <store> maps to src/data/<store>.json; the
path is the key/index route into that structure. These helpers resolve and
mutate exactly that location and nothing else, so an edit to one field never
disturbs the rest of the file.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Stores the admin is allowed to touch. Keeps a stray/hostile binding from
# reading or writing an arbitrary file on disk.
ALLOWED_STORES = {
    "site", "home", "about", "services", "pricing", "packages",
    "steam-iron", "blog", "locations", "policies", "pages",
    "proof", "testimonials",
    # Drives the home page coverage band (city names, per-city area counts,
    # the 456 total summed from them) and the /locate-us/ page. Was missing,
    # so none of that was editable.
    "areas",
    # src/data/generated/services.json. This is NOT a duplicate of "services":
    # build.py merges it ON TOP of services.json (see the gen_services loop),
    # so for the 15 service pages it is the real source of h1, lede, body,
    # meta_title, meta_description, faqs and what_we_clean. Editing the same
    # field in "services" has NO visible effect — a trap worth closing.
    "generated-services",
}

# Stores whose file does not sit directly at src/data/<name>.json.
_STORE_FILES = {
    "generated-services": "generated/services.json",
}

_KEY_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")


def _store_file(store: str) -> Path:
    if store not in ALLOWED_STORES:
        raise ValueError(f"unknown store: {store!r}")
    return DATA_DIR / _STORE_FILES.get(store, f"{store}.json")


def load_store(store: str) -> dict | list:
    with open(_store_file(store), encoding="utf-8") as f:
        return json.load(f)


def save_store(store: str, data) -> None:
    # 2-space indent + trailing newline matches the existing data files, so a
    # single-field edit produces a small, reviewable diff.
    with open(_store_file(store), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _split(path: str) -> list:
    if not path or not _KEY_RE.match(path):
        raise ValueError(f"invalid path: {path!r}")
    return [int(p) if p.isdigit() else p for p in path.split(".")]


def parse_binding(binding: str) -> tuple[str, str]:
    if ":" not in binding:
        raise ValueError(f"invalid binding: {binding!r}")
    store, path = binding.split(":", 1)
    return store, path


def _resolve(data, keys: list):
    cur = data
    for key in keys:
        cur = cur[key]
    return cur


def get_binding(binding: str):
    store, path = parse_binding(binding)
    return _resolve(load_store(store), _split(path))


def set_binding(binding: str, value) -> None:
    """Set one binding's value, loading and saving its store."""
    store, path = parse_binding(binding)
    data = load_store(store)
    keys = _split(path)
    parent = _resolve(data, keys[:-1])
    parent[keys[-1]] = value
    save_store(store, data)


def apply_edits(edits: list[dict]) -> dict:
    """Apply many edits, batching writes so each store is saved once.

    edits: [{"binding": "home:why.title", "value": "..."}]
    Returns {store: count} of fields changed per store.
    """
    by_store: dict[str, list[tuple[list, object]]] = {}
    for e in edits:
        store, path = parse_binding(e["binding"])
        by_store.setdefault(store, []).append((_split(path), e["value"]))

    changed: dict[str, int] = {}
    for store, items in by_store.items():
        data = load_store(store)
        for keys, value in items:
            parent = _resolve(data, keys[:-1])
            parent[keys[-1]] = value
        save_store(store, data)
        changed[store] = len(items)
    return changed
