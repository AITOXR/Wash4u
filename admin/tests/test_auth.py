from __future__ import annotations

from conftest import login


def test_unauthenticated_admin_redirects_to_login(client):
    resp = client.get("/admin", follow_redirects=False)
    assert resp.status_code == 303
    assert "/admin/login" in resp.headers["location"]


def test_login_wrong_password_fails(client):
    resp = client.post("/admin/login", data={"email": "owner@test.local", "password": "wrong"})
    assert resp.status_code == 401


def test_login_correct_password_succeeds_and_sets_cookie(client):
    resp = client.post("/admin/login", data={"email": "owner@test.local", "password": "TestPassword123!"}, follow_redirects=False)
    assert resp.status_code == 303
    assert "w4u_admin_session" in resp.cookies


def test_rate_limit_locks_out_after_five_failures(client):
    for _ in range(5):
        client.post("/admin/login", data={"email": "lockout-test@test.local", "password": "wrong"})
    resp = client.post("/admin/login", data={"email": "lockout-test@test.local", "password": "wrong"})
    assert resp.status_code == 429


def test_logged_in_owner_can_reach_dashboard(client):
    login(client, "owner@test.local", "TestPassword123!")
    resp = client.get("/admin")
    assert resp.status_code == 200


def test_staff_cannot_reach_settings(client):
    login(client, "staff@test.local", "TestPassword123!")
    resp = client.get("/admin/settings", follow_redirects=False)
    assert resp.status_code == 403


def test_staff_can_reach_orders(client):
    login(client, "staff@test.local", "TestPassword123!")
    resp = client.get("/admin/orders")
    assert resp.status_code == 200
