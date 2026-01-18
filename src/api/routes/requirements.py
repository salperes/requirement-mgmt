from __future__ import annotations

from typing import List, Optional
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from src.api.deps import get_db, require_permission
from src.api.schemas import (
    RequirementCreate,
    RequirementOut,
    RequirementUpdate,
    RequirementVersionOut,
    Discipline,
    RequirementType,
    WorkflowStatus,
)
from src.db.models import Requirement, RequirementVersion, User
from src.services.audit import write_audit
from src.services.requirements import (
    apply_requirement_updates,
    create_requirement_version,
    filter_requirements_query,
    generate_req_code,
)
from src.shared.errors import AppError

router = APIRouter(prefix="/requirements", tags=["requirements"])


def to_requirement_out(req: Requirement) -> RequirementOut:
    return RequirementOut(
        id=str(req.id),
        req_code=req.req_code,
        title=req.title,
        text=req.text,
        discipline=req.discipline,
        req_type_primary=req.req_type_primary,
        req_type_secondary=req.req_type_secondary,
        is_explanation=req.is_explanation,
        status=req.status,
        owner_user_id=str(req.owner_user_id),
        source=req.source,
        created_at=req.created_at,
        updated_at=req.updated_at,
        deleted_at=req.deleted_at,
    )


@router.post("", response_model=RequirementOut)
def create_requirement(
    payload: RequirementCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("req:create")),
) -> RequirementOut:
    if payload.owner_user_id:
        try:
            owner_user_id = uuid.UUID(payload.owner_user_id)
        except ValueError:
            raise AppError("VALIDATION_ERROR", "Invalid owner_user_id.", 400)
    else:
        owner_user_id = user.id
    req = Requirement(
        req_code=generate_req_code(db),
        title=payload.title,
        text=payload.text,
        discipline=payload.discipline,
        req_type_primary=payload.req_type_primary,
        req_type_secondary=payload.req_type_secondary,
        is_explanation=payload.is_explanation,
        status=payload.status,
        owner_user_id=owner_user_id,
        source=payload.source,
    )
    db.add(req)
    db.flush()

    create_requirement_version(db, req, user.id, change_reason="create")
    db.commit()
    db.refresh(req)

    write_audit(
        db,
        request.state.request_id,
        action="REQ_CREATED",
        actor_user_id=str(user.id),
        entity_type="Requirement",
        entity_id=str(req.id),
        payload={"req_code": req.req_code},
    )
    return to_requirement_out(req)


@router.get("", response_model=List[RequirementOut])
def list_requirements(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("req:read")),
    query: Optional[str] = None,
    discipline: Optional[Discipline] = None,
    req_type_primary: Optional[RequirementType] = Query(None, alias="type"),
    status: Optional[WorkflowStatus] = None,
    owner: Optional[str] = None,
    include_deleted: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
) -> List[RequirementOut]:
    offset = (page - 1) * page_size
    q = filter_requirements_query(
        db,
        query=query,
        discipline=discipline,
        req_type_primary=req_type_primary,
        status=status,
        owner=owner,
        include_deleted=include_deleted,
    )
    reqs = q.order_by(Requirement.created_at.desc()).offset(offset).limit(page_size).all()
    return [to_requirement_out(req) for req in reqs]


@router.get("/{req_id}", response_model=RequirementOut)
def get_requirement(
    req_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("req:read")),
) -> RequirementOut:
    req = db.query(Requirement).filter(Requirement.id == req_id).one_or_none()
    if not req:
        raise AppError("NOT_FOUND", "Requirement not found.", 404)
    return to_requirement_out(req)


@router.patch("/{req_id}", response_model=RequirementOut)
def update_requirement(
    req_id: str,
    payload: RequirementUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("req:update")),
) -> RequirementOut:
    req = db.query(Requirement).filter(Requirement.id == req_id).one_or_none()
    if not req:
        raise AppError("NOT_FOUND", "Requirement not found.", 404)

    updates = payload.model_dump(exclude_unset=True)
    change_reason = updates.pop("change_reason", None)
    if "owner_user_id" in updates and updates["owner_user_id"] is not None:
        try:
            updates["owner_user_id"] = uuid.UUID(updates["owner_user_id"])
        except ValueError:
            raise AppError("VALIDATION_ERROR", "Invalid owner_user_id.", 400)
    changed = apply_requirement_updates(req, updates)
    if not changed:
        raise AppError("NO_CHANGES", "No updates provided.", 400)

    create_requirement_version(db, req, user.id, change_reason=change_reason)
    db.commit()
    db.refresh(req)

    write_audit(
        db,
        request.state.request_id,
        action="REQ_UPDATED",
        actor_user_id=str(user.id),
        entity_type="Requirement",
        entity_id=str(req.id),
        payload={"fields": updates},
    )
    return to_requirement_out(req)


@router.delete("/{req_id}", response_model=RequirementOut)
def delete_requirement(
    req_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("req:delete")),
) -> RequirementOut:
    req = db.query(Requirement).filter(Requirement.id == req_id).one_or_none()
    if not req:
        raise AppError("NOT_FOUND", "Requirement not found.", 404)
    if req.deleted_at is None:
        req.deleted_at = datetime.utcnow()
        req.updated_at = datetime.utcnow()
        create_requirement_version(db, req, user.id, change_reason="delete")
        db.commit()
        db.refresh(req)

    write_audit(
        db,
        request.state.request_id,
        action="REQ_DELETED",
        actor_user_id=str(user.id),
        entity_type="Requirement",
        entity_id=str(req.id),
    )
    return to_requirement_out(req)


@router.get("/{req_id}/versions", response_model=List[RequirementVersionOut])
def list_requirement_versions(
    req_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("req:versions:read")),
) -> List[RequirementVersionOut]:
    versions = (
        db.query(RequirementVersion)
        .filter(RequirementVersion.requirement_id == req_id)
        .order_by(RequirementVersion.version_no.desc())
        .all()
    )
    return [
        RequirementVersionOut(
            id=str(version.id),
            requirement_id=str(version.requirement_id),
            version_no=version.version_no,
            snapshot_json=version.snapshot_json,
            changed_by_user_id=str(version.changed_by_user_id),
            change_reason=version.change_reason,
            created_at=version.created_at,
        )
        for version in versions
    ]


@router.get("/{req_id}/versions/{version_no}", response_model=RequirementVersionOut)
def get_requirement_version(
    req_id: str,
    version_no: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("req:versions:read")),
) -> RequirementVersionOut:
    version = (
        db.query(RequirementVersion)
        .filter(
            RequirementVersion.requirement_id == req_id,
            RequirementVersion.version_no == version_no,
        )
        .one_or_none()
    )
    if not version:
        raise AppError("NOT_FOUND", "Requirement version not found.", 404)
    return RequirementVersionOut(
        id=str(version.id),
        requirement_id=str(version.requirement_id),
        version_no=version.version_no,
        snapshot_json=version.snapshot_json,
        changed_by_user_id=str(version.changed_by_user_id),
        change_reason=version.change_reason,
        created_at=version.created_at,
    )
