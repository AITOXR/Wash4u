from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DBSession

from app.audit import log_action
from app.db import get_db
from app.deps import require_owner
from app.models import Role, User
from app.security import hash_password

router = APIRouter(tags=["users"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin/users")
def users_list(request: Request, db: DBSession = Depends(get_db), user: User = Depends(require_owner)):
    users = db.query(User).order_by(User.email).all()
    return templates.TemplateResponse("users.html", {"request": request, "user": user, "active": "users", "users": users, "current_user": user})


@router.post("/admin/users/new")
def create_user(email: str = Form(...), password: str = Form(...), role: str = Form("editor"), db: DBSession = Depends(get_db), user: User = Depends(require_owner)):
    if db.query(User).filter(User.email == email).first():
        return RedirectResponse("/admin/users?error=exists", status_code=303)
    new_user = User(email=email, password_hash=hash_password(password), role=Role(role), must_change_password=True)
    db.add(new_user)
    db.commit()
    log_action(db, user, "create", entity="user", entity_id=new_user.id, diff={"role": role})
    return RedirectResponse("/admin/users", status_code=303)


@router.post("/admin/users/{user_id}/deactivate")
def deactivate_user(user_id: int, db: DBSession = Depends(get_db), user: User = Depends(require_owner)):
    target = db.get(User, user_id)
    if target and target.id != user.id:
        target.is_active = False
        db.commit()
        log_action(db, user, "deactivate", entity="user", entity_id=target.id)
    return RedirectResponse("/admin/users", status_code=303)
