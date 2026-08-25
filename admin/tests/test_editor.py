from __future__ import annotations

from conftest import login

from app.db import SessionLocal
from app.models import Page, Section


def _home_and_hero_section():
    db = SessionLocal()
    try:
        home = db.query(Page).filter(Page.slug == "").first()
        hero = db.query(Section).filter(Section.page_id == home.id, Section.type == "hero").first()
        return home.id, hero.id
    finally:
        db.close()


def test_field_patch_persists_and_shows_in_the_editor_view(client):
    login(client, "owner@test.local", "TestPassword123!")
    _, hero_id = _home_and_hero_section()
    resp = client.post(f"/admin/api/sections/{hero_id}/field", json={"field": "heading_line1", "value": "Edited via test"})
    assert resp.status_code == 200 and resp.json()["ok"]

    db = SessionLocal()
    section = db.get(Section, hero_id)
    assert section.props["heading_line1"] == "Edited via test"
    db.close()

    page_html = client.get("/admin/edit/").text
    assert "Edited via test" in page_html


def test_staff_cannot_patch_a_field(client):
    login(client, "staff@test.local", "TestPassword123!")
    _, hero_id = _home_and_hero_section()
    resp = client.post(f"/admin/api/sections/{hero_id}/field", json={"field": "heading_line1", "value": "Should not save"}, follow_redirects=False)
    assert resp.status_code == 403  # authenticated, but wrong role — matches test_staff_cannot_reach_settings
    # Confirm it truly did not persist, not just that the request was blocked.
    db = SessionLocal()
    section = db.get(Section, hero_id)
    assert section.props["heading_line1"] != "Should not save"
    db.close()


def test_create_reorder_duplicate_hide_delete_section(client):
    login(client, "owner@test.local", "TestPassword123!")
    page_id, hero_id = _home_and_hero_section()

    # Create a second section (a text_block) right after the hero.
    create = client.post(f"/admin/api/pages/{page_id}/sections/create", json={"type": "text_block", "index": 1})
    assert create.status_code == 200 and create.json()["ok"]
    new_id = create.json()["section_id"]
    assert "w4u-section" in create.json()["html"]

    db = SessionLocal()
    order = [s.id for s in sorted(db.query(Section).filter(Section.page_id == page_id).all(), key=lambda s: s.order)]
    db.close()
    assert order == [hero_id, new_id]

    # Reorder: put the new section first.
    reorder = client.post(f"/admin/api/pages/{page_id}/sections/reorder", json={"order": [new_id, hero_id]})
    assert reorder.status_code == 200 and reorder.json()["ok"]
    db = SessionLocal()
    reordered = [s.id for s in sorted(db.query(Section).filter(Section.page_id == page_id).all(), key=lambda s: s.order)]
    db.close()
    assert reordered == [new_id, hero_id]

    # Duplicate.
    dup = client.post(f"/admin/api/sections/{new_id}/duplicate")
    assert dup.status_code == 200 and dup.json()["ok"]
    dup_id = dup.json()["section_id"]

    # Hide.
    hide = client.post(f"/admin/api/sections/{dup_id}/toggle-visible")
    assert hide.status_code == 200 and hide.json()["visible"] is False

    # Delete — and confirm a revision snapshot was created so it's restorable.
    delete = client.post(f"/admin/api/sections/{dup_id}/delete")
    assert delete.status_code == 200 and delete.json()["ok"]
    db = SessionLocal()
    assert db.get(Section, dup_id) is None
    from app.models import Revision
    revs = db.query(Revision).filter(Revision.entity_type == "page", Revision.entity_id == page_id).all()
    assert len(revs) >= 1
    db.close()


def test_repeater_add_and_remove(client):
    login(client, "owner@test.local", "TestPassword123!")
    db = SessionLocal()
    home = db.query(Page).filter(Page.slug == "").first()
    section = Section(page_id=home.id, type="features_grid", order=5, props={"heading": "Why us", "items": [{"title": "One", "detail": "First"}]})
    db.add(section)
    db.commit()
    section_id = section.id
    db.close()

    add = client.post(f"/admin/api/sections/{section_id}/repeater/add", json={"field": "items"})
    assert add.status_code == 200 and add.json()["ok"]
    assert add.json()["index"] == 1

    render = client.get(f"/admin/api/sections/{section_id}/render")
    assert render.status_code == 200
    assert render.json()["html"].count("w4u-rep-item") == 2

    remove = client.post(f"/admin/api/sections/{section_id}/repeater/remove", json={"field": "items", "index": 0})
    assert remove.status_code == 200 and remove.json()["ok"]

    db = SessionLocal()
    refreshed = db.get(Section, section_id)
    assert len(refreshed.props["items"]) == 1
    assert refreshed.props["items"][0]["title"] != "One"  # the remaining one is the item we added, not the original
    db.close()
