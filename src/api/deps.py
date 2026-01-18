from __future__ import annotations

import uuid
from typing import Callable, Generator, Optional

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from src.db.models import User
from src.db.session import SessionLocal
from src.services.audit import write_audit
from src.services.rbac import has_permission
from src.shared.errors import AppError
from src.shared.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
        subject = payload.get("sub")
        if not subject:
            raise ValueError("Missing subject")
        user_id = uuid.UUID(subject)
    except (JWTError, ValueError) as exc:
        raise AppError("AUTH_INVALID", "Invalid authentication token.", 401)

    user = db.query(User).filter(User.id == user_id).one_or_none()
    if not user or not user.is_active:
        raise AppError("AUTH_INVALID", "Invalid authentication token.", 401)

    request.state.current_user = user
    return user


def require_permission(permission: str) -> Callable:
    def dependency(
        request: Request,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        role_names = [role.name for role in user.roles]
        if not has_permission(role_names, permission):
            write_audit(
                db,
                request.state.request_id,
                action="RBAC_DENY",
                actor_user_id=str(user.id),
                payload={"permission": permission, "roles": role_names},
            )
            raise AppError(
                "RBAC_FORBIDDEN",
                "You do not have permission to perform this action.",
                403,
                {"permission": permission, "request_id": request.state.request_id},
            )
        return user

    return dependency
