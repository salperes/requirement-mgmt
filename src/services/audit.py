from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from src.db.models import AuditLog


def write_audit(
    session: Session,
    request_id: str,
    action: str,
    actor_user_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    actor_uuid = uuid.UUID(actor_user_id) if actor_user_id else None
    record = AuditLog(
        request_id=request_id,
        actor_user_id=actor_uuid,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        payload_json=payload or {},
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record
