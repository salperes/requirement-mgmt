from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from src.api.deps import get_db, require_permission
from src.api.schemas import AuditLogOut, UserCreate, UserOut, UserRolesUpdate, UserUpdate
from src.db.models import AuditLog, User
from src.services.audit import write_audit
from src.services.auth import get_or_create_role, get_user_roles
from src.shared.errors import AppError
from src.shared.security import get_password_hash

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("admin:users:read")),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
) -> List[UserOut]:
    offset = (page - 1) * page_size
    users = db.query(User).order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
    return [
        UserOut(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            is_active=user.is_active,
            roles=get_user_roles(user),
        )
        for user in users
    ]


@router.post("/users", response_model=UserOut)
def create_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("admin:users:write")),
) -> UserOut:
    existing = db.query(User).filter(User.email == payload.email).one_or_none()
    if existing:
        raise AppError("USER_EXISTS", "User already exists.", 409)

    user = User(
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        display_name=payload.display_name,
        is_active=True,
    )
    roles = [get_or_create_role(db, role_name) for role_name in payload.roles]
    user.roles = roles
    db.add(user)
    db.commit()
    db.refresh(user)

    write_audit(
        db,
        request.state.request_id,
        action="ADMIN_USER_CREATED",
        actor_user_id=str(request.state.current_user.id),
        entity_type="User",
        entity_id=str(user.id),
    )
    return UserOut(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        roles=get_user_roles(user),
    )


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    payload: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("admin:users:write")),
) -> UserOut:
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if not user:
        raise AppError("NOT_FOUND", "User not found.", 404)

    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)

    write_audit(
        db,
        request.state.request_id,
        action="ADMIN_USER_UPDATED",
        actor_user_id=str(request.state.current_user.id),
        entity_type="User",
        entity_id=str(user.id),
        payload={"fields": payload.model_dump(exclude_unset=True)},
    )
    return UserOut(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        roles=get_user_roles(user),
    )


@router.put("/users/{user_id}/roles", response_model=UserOut)
def update_user_roles(
    user_id: str,
    payload: UserRolesUpdate,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("admin:roles:write")),
) -> UserOut:
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if not user:
        raise AppError("NOT_FOUND", "User not found.", 404)

    roles = [get_or_create_role(db, role_name) for role_name in payload.roles]
    user.roles = roles
    db.commit()
    db.refresh(user)

    write_audit(
        db,
        request.state.request_id,
        action="RBAC_ROLE_ASSIGNED",
        actor_user_id=str(request.state.current_user.id),
        entity_type="User",
        entity_id=str(user.id),
        payload={"roles": payload.roles},
    )

    return UserOut(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        roles=get_user_roles(user),
    )


@router.get("/audit", response_model=List[AuditLogOut])
def list_audit_logs(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("audit:read")),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
) -> List[AuditLogOut]:
    offset = (page - 1) * page_size
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return [
        AuditLogOut(
            id=str(log.id),
            request_id=log.request_id,
            actor_user_id=str(log.actor_user_id) if log.actor_user_id else None,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            payload_json=log.payload_json,
            created_at=log.created_at,
        )
        for log in logs
    ]