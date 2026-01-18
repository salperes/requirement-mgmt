from __future__ import annotations

from typing import List, Optional
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from src.api.deps import get_db, require_permission
from src.api.schemas import (
    ApprovalRequest,
    ApprovalRecordOut,
    RequirementCreate,
    RequirementOut,
    RequirementUpdate,
    RequirementVersionOut,
    StatusChangeRequest,
    Discipline,
    RequirementType,
    WorkflowStatus,
)
from src.db.models import ApprovalRecord, Notification, Requirement, RequirementVersion, User
from src.services.audit import write_audit
from src.services.requirements import (
    apply_requirement_updates,
    create_requirement_version,
    filter_requirements_query,
    generate_req_code,
)
from src.services.workflow import resolve_allowed_transition
from src.services.traceability import set_suspects_from_requirement
from src.shared.errors import AppError

router = APIRouter(prefix="/requirements", tags=["requirements"])


def parse_uuid(value: str, field_name: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise AppError("VALIDATION_ERROR", f"Invalid {field_name}.", 400)


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
    req_uuid = parse_uuid(req_id, "requirement_id")
    req = db.query(Requirement).filter(Requirement.id == req_uuid).one_or_none()
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
    req_uuid = parse_uuid(req_id, "requirement_id")
    req = db.query(Requirement).filter(Requirement.id == req_uuid).one_or_none()
    if not req:
        raise AppError("NOT_FOUND", "Requirement not found.", 404)

    updates = payload.model_dump(exclude_unset=True)
    change_reason = updates.pop("change_reason", None)
    if "status" in updates:
        raise AppError(
            "VALIDATION_ERROR",
            "Status changes must use the workflow endpoint.",
            400,
        )
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
    if "text" in updates:
        impacts = set_suspects_from_requirement(db, str(req.id), "requirement_update")
        for entity_type, entity_id, path in impacts:
            write_audit(
                db,
                request.state.request_id,
                action="TRACE_SUSPECT_SET",
                actor_user_id=str(user.id),
                entity_type=entity_type,
                entity_id=entity_id,
                payload={"path": path, "reason": "requirement_update"},
            )
    return to_requirement_out(req)


@router.post("/{req_id}/status", response_model=RequirementOut)
def change_requirement_status(
    req_id: str,
    payload: StatusChangeRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("req:status:change")),
) -> RequirementOut:
    req_uuid = parse_uuid(req_id, "requirement_id")
    req = db.query(Requirement).filter(Requirement.id == req_uuid).one_or_none()
    if not req:
        raise AppError("NOT_FOUND", "Requirement not found.", 404)
    if req.status == payload.to_status:
        raise AppError("NO_CHANGES", "Requirement already in requested status.", 400)
    if payload.to_status in ("Approved", "Rejected"):
        raise AppError("VALIDATION_ERROR", "Use approval endpoint for Approved/Rejected.", 400)

    role_names = [role.name for role in user.roles]
    if not resolve_allowed_transition(req.status, payload.to_status, role_names):
        raise AppError("VALIDATION_ERROR", "Invalid workflow transition.", 400)

    previous_status = req.status
    req.status = payload.to_status
    req.updated_at = datetime.utcnow()
    create_requirement_version(db, req, user.id, change_reason=payload.reason)
    if user.id != req.owner_user_id:
        db.add(
            Notification(
                user_id=req.owner_user_id,
                type="WORKFLOW",
                title=f"Requirement moved to {payload.to_status}",
                body=payload.reason,
                entity_type="Requirement",
                entity_id=str(req.id),
                is_read=False,
            )
        )
    db.commit()
    db.refresh(req)

    write_audit(
        db,
        request.state.request_id,
        action="REQ_STATUS_CHANGED",
        actor_user_id=str(user.id),
        entity_type="Requirement",
        entity_id=str(req.id),
        payload={
            "requirement_id": str(req.id),
            "req_code": req.req_code,
            "from_status": previous_status,
            "to_status": payload.to_status,
            "reason": payload.reason,
        },
    )
    impacts = set_suspects_from_requirement(db, str(req.id), "status_change")
    for entity_type, entity_id, path in impacts:
        write_audit(
            db,
            request.state.request_id,
            action="TRACE_SUSPECT_SET",
            actor_user_id=str(user.id),
            entity_type=entity_type,
            entity_id=entity_id,
            payload={"path": path, "reason": "status_change"},
        )
    return to_requirement_out(req)


@router.post("/{req_id}/approve", response_model=RequirementOut)
def approve_requirement(
    req_id: str,
    payload: ApprovalRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("req:approve")),
) -> RequirementOut:
    req_uuid = parse_uuid(req_id, "requirement_id")
    req = db.query(Requirement).filter(Requirement.id == req_uuid).one_or_none()
    if not req:
        raise AppError("NOT_FOUND", "Requirement not found.", 404)
    if req.status != "Review":
        raise AppError("VALIDATION_ERROR", "Requirement must be in Review.", 400)

    decision = payload.decision
    if decision == "REJECT" and not payload.reason:
        raise AppError("VALIDATION_ERROR", "Reason required for rejection.", 400)

    target_status = "Approved" if decision == "APPROVE" else "Rejected"
    role_names = [role.name for role in user.roles]
    if not resolve_allowed_transition(req.status, target_status, role_names):
        raise AppError("VALIDATION_ERROR", "Invalid workflow transition.", 400)

    approval = ApprovalRecord(
        requirement_id=req.id,
        approver_user_id=user.id,
        decision=decision,
        reason=payload.reason,
        signature_provider="placeholder",
        signature_metadata={
            "ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "reauth_password_provided": bool(payload.reauth_password),
        },
        signed_at=datetime.utcnow(),
    )
    db.add(approval)
    db.add(
        Notification(
            user_id=req.owner_user_id,
            type="APPROVAL",
            title=f"Requirement {target_status}",
            body=payload.reason,
            entity_type="Requirement",
            entity_id=str(req.id),
            is_read=False,
        )
    )

    previous_status = req.status
    req.status = target_status
    req.updated_at = datetime.utcnow()
    create_requirement_version(db, req, user.id, change_reason=payload.reason)
    db.commit()
    db.refresh(req)

    write_audit(
        db,
        request.state.request_id,
        action="REQ_STATUS_CHANGED",
        actor_user_id=str(user.id),
        entity_type="Requirement",
        entity_id=str(req.id),
        payload={
            "requirement_id": str(req.id),
            "req_code": req.req_code,
            "from_status": previous_status,
            "to_status": target_status,
            "reason": payload.reason,
        },
    )
    write_audit(
        db,
        request.state.request_id,
        action="REQ_APPROVAL_DECISION",
        actor_user_id=str(user.id),
        entity_type="ApprovalRecord",
        entity_id=str(approval.id),
        payload={
            "requirement_id": str(req.id),
            "decision": decision,
            "reason": payload.reason,
        },
    )
    impacts = set_suspects_from_requirement(db, str(req.id), "approval_decision")
    for entity_type, entity_id, path in impacts:
        write_audit(
            db,
            request.state.request_id,
            action="TRACE_SUSPECT_SET",
            actor_user_id=str(user.id),
            entity_type=entity_type,
            entity_id=entity_id,
            payload={"path": path, "reason": "approval_decision"},
        )
    return to_requirement_out(req)


@router.get("/{req_id}/approvals", response_model=List[ApprovalRecordOut])
def list_requirement_approvals(
    req_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("req:read")),
) -> List[ApprovalRecordOut]:
    req_uuid = parse_uuid(req_id, "requirement_id")
    req = db.query(Requirement).filter(Requirement.id == req_uuid).one_or_none()
    if not req:
        raise AppError("NOT_FOUND", "Requirement not found.", 404)
    approvals = (
        db.query(ApprovalRecord)
        .filter(ApprovalRecord.requirement_id == req_uuid)
        .order_by(ApprovalRecord.signed_at.desc())
        .all()
    )
    return [
        ApprovalRecordOut(
            id=str(approval.id),
            requirement_id=str(approval.requirement_id),
            approver_user_id=str(approval.approver_user_id),
            decision=approval.decision,
            reason=approval.reason,
            signature_provider=approval.signature_provider,
            signature_metadata=approval.signature_metadata,
            signed_at=approval.signed_at,
        )
        for approval in approvals
    ]


@router.delete("/{req_id}", response_model=RequirementOut)
def delete_requirement(
    req_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("req:delete")),
) -> RequirementOut:
    req_uuid = parse_uuid(req_id, "requirement_id")
    req = db.query(Requirement).filter(Requirement.id == req_uuid).one_or_none()
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
    impacts = set_suspects_from_requirement(db, str(req.id), "requirement_delete")
    for entity_type, entity_id, path in impacts:
        write_audit(
            db,
            request.state.request_id,
            action="TRACE_SUSPECT_SET",
            actor_user_id=str(user.id),
            entity_type=entity_type,
            entity_id=entity_id,
            payload={"path": path, "reason": "requirement_delete"},
        )
    return to_requirement_out(req)


@router.get("/{req_id}/versions", response_model=List[RequirementVersionOut])
def list_requirement_versions(
    req_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("req:versions:read")),
) -> List[RequirementVersionOut]:
    req_uuid = parse_uuid(req_id, "requirement_id")
    versions = (
        db.query(RequirementVersion)
        .filter(RequirementVersion.requirement_id == req_uuid)
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
    req_uuid = parse_uuid(req_id, "requirement_id")
    version = (
        db.query(RequirementVersion)
        .filter(
            RequirementVersion.requirement_id == req_uuid,
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
