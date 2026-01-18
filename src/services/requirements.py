from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
import uuid

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from src.db.models import Requirement, RequirementVersion


def generate_req_code(session: Session) -> str:
    if session.bind and session.bind.dialect.name == "postgresql":
        next_val = session.execute(select(text("nextval('req_code_seq')"))).scalar_one()
        return f"REQ-{int(next_val):06d}"

    max_code = session.execute(select(Requirement.req_code).order_by(Requirement.req_code.desc())).scalar()
    if not max_code:
        return "REQ-000001"
    try:
        numeric = int(max_code.split("-")[-1])
    except (ValueError, AttributeError):
        numeric = 0
    return f"REQ-{numeric + 1:06d}"


def requirement_snapshot(requirement: Requirement) -> Dict[str, Any]:
    def _dt(value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None

    return {
        "id": str(requirement.id),
        "req_code": requirement.req_code,
        "title": requirement.title,
        "text": requirement.text,
        "discipline": requirement.discipline,
        "req_type_primary": requirement.req_type_primary,
        "req_type_secondary": requirement.req_type_secondary,
        "is_explanation": requirement.is_explanation,
        "status": requirement.status,
        "owner_user_id": str(requirement.owner_user_id),
        "source": requirement.source,
        "created_at": _dt(requirement.created_at),
        "updated_at": _dt(requirement.updated_at),
        "deleted_at": _dt(requirement.deleted_at),
    }


def next_version_no(session: Session, requirement_id: str) -> int:
    try:
        requirement_uuid = uuid.UUID(str(requirement_id))
    except ValueError:
        requirement_uuid = requirement_id
    max_version = (
        session.query(func.max(RequirementVersion.version_no))
        .filter(RequirementVersion.requirement_id == requirement_uuid)
        .scalar()
    )
    return int(max_version or 0) + 1


def create_requirement_version(
    session: Session,
    requirement: Requirement,
    changed_by_user_id: str,
    change_reason: Optional[str] = None,
) -> RequirementVersion:
    version = RequirementVersion(
        requirement_id=requirement.id,
        version_no=next_version_no(session, str(requirement.id)),
        snapshot_json=requirement_snapshot(requirement),
        changed_by_user_id=changed_by_user_id,
        change_reason=change_reason,
    )
    session.add(version)
    return version


def apply_requirement_updates(requirement: Requirement, updates: Dict[str, Any]) -> bool:
    changed = False
    for field, value in updates.items():
        if hasattr(requirement, field) and value is not None:
            if getattr(requirement, field) != value:
                setattr(requirement, field, value)
                changed = True
    if changed:
        requirement.updated_at = datetime.utcnow()
    return changed


def filter_requirements_query(
    session: Session,
    query: Optional[str],
    discipline: Optional[str],
    req_type_primary: Optional[str],
    status: Optional[str],
    owner: Optional[str],
    include_deleted: bool,
):
    q = session.query(Requirement)
    if query:
        like = f"%{query}%"
        q = q.filter((Requirement.req_code.ilike(like)) | (Requirement.text.ilike(like)))
    if discipline:
        q = q.filter(Requirement.discipline == discipline)
    if req_type_primary:
        q = q.filter(Requirement.req_type_primary == req_type_primary)
    if status:
        q = q.filter(Requirement.status == status)
    if owner:
        try:
            owner_uuid = uuid.UUID(str(owner))
        except ValueError:
            owner_uuid = owner
        q = q.filter(Requirement.owner_user_id == owner_uuid)
    if not include_deleted:
        q = q.filter(Requirement.deleted_at.is_(None))
    return q
