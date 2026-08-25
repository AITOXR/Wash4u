from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import AuditLog, User


def log_action(db: Session, user: User | None, action: str, entity: str | None = None,
                entity_id: int | None = None, diff: dict | None = None, ip: str | None = None) -> None:
    db.add(AuditLog(
        user_id=user.id if user else None,
        action=action, entity=entity, entity_id=entity_id, diff=diff, ip=ip,
    ))
    db.commit()
