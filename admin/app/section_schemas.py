"""Loads schemas/sections/*.yml (shared with build.py at the repo root) so
the admin can auto-generate an edit form for any section type without
hand-written forms per type. Adding a new section type: drop in one
schemas/sections/<type>.yml + one templates/sections/<type>.html at the
repo root, and it appears in the "+ Add Section" picker automatically."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from app.config import settings

SCHEMAS_DIR = Path(settings.repo_path).resolve() / "schemas" / "sections"


@lru_cache(maxsize=1)
def load_section_schemas() -> dict:
    schemas = {}
    if not SCHEMAS_DIR.exists():
        return schemas
    for path in sorted(SCHEMAS_DIR.glob("*.yml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["_type"] = path.stem
        schemas[path.stem] = data
    return schemas


def get_schema(section_type: str) -> dict | None:
    return load_section_schemas().get(section_type)


_PLACEHOLDER_BY_KEY = {
    "heading": "New heading", "heading_line1": "New heading", "title": "New title",
    "eyebrow": "Label", "subheading": "A short supporting line goes here.",
    "text": "A short supporting line goes here.", "body": "Click to edit this text. Write a sentence or two here.",
    "detail": "Describe this here.", "quote": "A short customer quote goes here.",
    "cta_label": "Click here", "label": "Click here", "q": "A frequently asked question?",
    "a": "The answer goes here.", "name": "Customer name", "attribution": "Location",
}


def _placeholder_for(field: dict) -> object:
    if field["type"] == "toggle":
        return False
    if field["type"] == "number":
        return 5 if field["key"] == "rating" else 0
    if field["type"] == "repeater":
        # One sample item, not an empty list — "pre-filled with sensible
        # placeholder content he can immediately click and edit", not a
        # blank section that looks broken until someone adds a first row.
        item = {}
        for sub in field.get("item_fields", []):
            item[sub["key"]] = _placeholder_for(sub)
        return [item]
    return _PLACEHOLDER_BY_KEY.get(field["key"], "Click to edit")


def default_props(section_type: str) -> dict:
    schema = get_schema(section_type) or {}
    return {field["key"]: _placeholder_for(field) for field in schema.get("fields", [])}
