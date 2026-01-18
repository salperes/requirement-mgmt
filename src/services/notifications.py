from __future__ import annotations

from sqlalchemy.orm import Session

from src.db.models import Notification


def mark_notification_read(session: Session, notification: Notification) -> Notification:
    notification.is_read = True
    session.commit()
    session.refresh(notification)
    return notification
