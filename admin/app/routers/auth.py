from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DBSession

from app.audit import log_action
from app.config import settings
from app.db import get_db
from app.deps import get_current_user_optional
from app.models import Session as SessionModel, User
from app.rate_limit import is_locked_out, record_attempt
from app.security import (
    hash_password, new_session_token, read_reset_token, make_reset_token,
    session_expiry, sign_session_cookie, verify_password,
)

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.get("/admin/login", response_class=HTMLResponse)
def login_form(request: Request, user: User | None = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "user": None})


@router.post("/admin/login")
def login_submit(
    request: Request, email: str = Form(...), password: str = Form(...),
    db: DBSession = Depends(get_db),
):
    ip = _client_ip(request)
    if is_locked_out(db, email, ip):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "user": None,
             "error": "Too many failed attempts. Try again in 15 minutes."},
            status_code=429,
        )

    user = db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
    ok = bool(user) and verify_password(password, user.password_hash)
    record_attempt(db, email, ip, success=ok)

    if not ok:
        log_action(db, None, "login_failed", entity="user", ip=ip)
        return templates.TemplateResponse(
            "login.html", {"request": request, "user": None, "error": "Incorrect email or password."},
            status_code=401,
        )

    session_id = new_session_token()
    db.add(SessionModel(
        id=session_id, user_id=user.id, expires_at=session_expiry(),
        user_agent=request.headers.get("user-agent"), ip=ip,
    ))
    db.commit()
    log_action(db, user, "login", entity="user", entity_id=user.id, ip=ip)

    resp = RedirectResponse(
        "/admin/change-password?forced=1" if user.must_change_password else "/admin",
        status_code=303,
    )
    resp.set_cookie(
        settings.session_cookie_name, sign_session_cookie(session_id),
        max_age=settings.session_max_age_seconds, httponly=True, secure=True, samesite="lax",
    )
    return resp


@router.post("/admin/logout")
def logout(request: Request, db: DBSession = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    raw = request.cookies.get(settings.session_cookie_name)
    if raw:
        from app.security import unsign_session_cookie
        sid = unsign_session_cookie(raw)
        if sid:
            sess = db.get(SessionModel, sid)
            if sess:
                db.delete(sess)
                db.commit()
    if user:
        log_action(db, user, "logout", entity="user", entity_id=user.id)
    resp = RedirectResponse("/admin/login", status_code=303)
    resp.delete_cookie(settings.session_cookie_name)
    return resp


@router.post("/admin/logout-all-devices")
def logout_all_devices(request: Request, db: DBSession = Depends(get_db), user: User = Depends(get_current_user_optional)):
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    db.query(SessionModel).filter(SessionModel.user_id == user.id).delete()
    db.commit()
    log_action(db, user, "logout_all_devices", entity="user", entity_id=user.id)
    resp = RedirectResponse("/admin/login", status_code=303)
    resp.delete_cookie(settings.session_cookie_name)
    return resp


@router.get("/admin/change-password", response_class=HTMLResponse)
def change_password_form(request: Request, forced: int = 0, user: User | None = Depends(get_current_user_optional)):
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    return templates.TemplateResponse("change_password.html", {"request": request, "user": user, "forced": bool(forced)})


@router.post("/admin/change-password")
def change_password_submit(
    request: Request, current_password: str = Form(...), new_password: str = Form(...),
    confirm_password: str = Form(...), db: DBSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    ctx = {"request": request, "user": user}
    if not verify_password(current_password, user.password_hash):
        return templates.TemplateResponse("change_password.html", {**ctx, "error": "Current password is incorrect."}, status_code=400)
    if new_password != confirm_password:
        return templates.TemplateResponse("change_password.html", {**ctx, "error": "New passwords don't match."}, status_code=400)
    if len(new_password) < 10:
        return templates.TemplateResponse("change_password.html", {**ctx, "error": "Password must be at least 10 characters."}, status_code=400)

    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    db.commit()
    log_action(db, user, "change_password", entity="user", entity_id=user.id)
    return RedirectResponse("/admin", status_code=303)


@router.get("/admin/forgot-password", response_class=HTMLResponse)
def forgot_password_form(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request, "user": None})


@router.post("/admin/forgot-password")
def forgot_password_submit(request: Request, email: str = Form(...), db: DBSession = Depends(get_db)):
    # Deliberately does not reveal whether the email exists (same response
    # either way) — this is an admin login, not a public account signup.
    user = db.query(User).filter(User.email == email).first()
    if user:
        token = make_reset_token(user.id)
        reset_link = f"https://admin.wash4you.in/admin/reset-password?token={token}"
        # NOTE: actually SENDING this email needs SMTP/Resend credentials
        # (Settings -> Integrations). Logged here rather than silently
        # dropped so this is visibly a stub, not a broken feature.
        print(f"[password reset] would email {email}: {reset_link}")
    return templates.TemplateResponse("forgot_password.html", {"request": request, "user": None, "sent": True})


@router.get("/admin/reset-password", response_class=HTMLResponse)
def reset_password_form(request: Request, token: str):
    return templates.TemplateResponse("reset_password.html", {"request": request, "user": None, "token": token})


@router.post("/admin/reset-password")
def reset_password_submit(request: Request, token: str = Form(...), new_password: str = Form(...), db: DBSession = Depends(get_db)):
    uid = read_reset_token(token)
    if not uid:
        return templates.TemplateResponse(
            "reset_password.html", {"request": request, "user": None, "token": token, "error": "This reset link has expired. Request a new one."},
            status_code=400,
        )
    user = db.get(User, uid)
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    db.commit()
    log_action(db, user, "reset_password", entity="user", entity_id=user.id)
    return RedirectResponse("/admin/login", status_code=303)
