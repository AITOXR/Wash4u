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


def default_props(section_type: str) -> dict:
    schema = get_schema(section_type) or {}
    props = {}
    for field in schema.get("fields", []):
        if field["type"] == "repeater":
            props[field["key"]] = []
        elif field["type"] == "toggle":
            props[field["key"]] = False
        else:
            props[field["key"]] = ""
    return props
