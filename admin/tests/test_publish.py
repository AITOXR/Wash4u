from __future__ import annotations

from app.db import SessionLocal
from app.models import Page, PageStatus, Section
from app.publish import collect_pending_changes, page_to_yaml, run_build_check


def test_new_page_with_no_published_snapshot_shows_as_pending():
    db = SessionLocal()
    try:
        page = Page(slug="test-pending-page", title="Test Page", status=PageStatus.draft)
        db.add(page)
        db.commit()
        db.add(Section(page_id=page.id, type="text_block", order=0, props={"body": "hello"}))
        db.commit()

        changes = collect_pending_changes(db)
        assert any(c["entity"] == "page" and c["id"] == page.id for c in changes)
    finally:
        db.close()


def test_page_matching_its_published_snapshot_is_not_pending():
    db = SessionLocal()
    try:
        page = Page(slug="test-clean-page", title="Clean Page", status=PageStatus.published)
        db.add(page)
        db.commit()
        section = Section(page_id=page.id, type="text_block", order=0, props={"body": "hello"}, style={})
        db.add(section)
        db.commit()
        page.published_snapshot = [{"type": "text_block", "props": {"body": "hello"}, "style": {}, "visible": True, "order": 0}]
        db.commit()

        changes = collect_pending_changes(db)
        assert not any(c["entity"] == "page" and c["id"] == page.id for c in changes)
    finally:
        db.close()


def test_page_to_yaml_uses_home_filename_for_empty_slug():
    db = SessionLocal()
    try:
        page = Page(slug="", title="Home", status=PageStatus.draft, is_home=True)
        db.add(page)
        db.commit()
        rel, _content = page_to_yaml(page)
        assert rel == "content/pages/home.yml"
    finally:
        db.close()


def test_build_check_passes_against_the_real_content_directory():
    """Sanity check that the site's own content/ is currently valid — this
    is what Publish runs before ever writing a file."""
    ok, log = run_build_check()
    assert ok, log
