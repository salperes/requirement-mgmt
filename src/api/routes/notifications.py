from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.deps import get_db, require_permission
from src.api.schemas import NotificationOut
from src.db.models import Notification, User
from src.services.notifications import mark_notification_read
from src.shared.errors import AppError

router = APIRouter(prefix="/notifications", tags=["notifications"])


def to_notification_out(notification: Notification) -> NotificationOut:
    return NotificationOut(
        id=str(notification.id),
        type=notification.type,
        title=notification.title,
        body=notification.body,
        entity_type=notification.entity_type,
        entity_id=notification.entity_id,
        is_read=notification.is_read,
        created_at=notification.created_at,
    )


@router.get("", response_model=List[NotificationOut])
def list_notifications(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("notif:read")),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    unread_only: bool = False,
) -> List[NotificationOut]:
    offset = (page - 1) * page_size
    q = db.query(Notification).filter(Notification.user_id == user.id)
    if unread_only:
        q = q.filter(Notification.is_read.is_(False))
    notifications = q.order_by(Notification.created_at.desc()).offset(offset).limit(page_size).all()
    return [to_notification_out(notification) for notification in notifications]


@router.post("/{notification_id}/read", response_model=NotificationOut)
def read_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("notif:mark_read")),
) -> NotificationOut:
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .filter(Notification.user_id == user.id)
        .one_or_none()
    )
    if not notification:
        raise AppError("NOT_FOUND", "Notification not found.", 404)
    updated = mark_notification_read(db, notification)
    return to_notification_out(updated)
