from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from src.db.models import Role, User
from src.shared.security import create_access_token, verify_password


def authenticate_user(session: Session, email: str, password: str) -> Optional[User]:
    user = session.query(User).filter(User.email == email).one_or_none()
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def get_user_roles(user: User) -> list[str]:
    return [role.name for role in user.roles]


def create_user_token(user: User) -> str:
    return create_access_token(str(user.id), {"roles": get_user_roles(user)})


def get_or_create_role(session: Session, role_name: str) -> Role:
    role = session.query(Role).filter(Role.name == role_name).one_or_none()
    if role:
        return role
    role = Role(name=role_name)
    session.add(role)
    session.commit()
    session.refresh(role)
    return role