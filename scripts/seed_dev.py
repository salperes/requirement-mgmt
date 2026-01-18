import os

from sqlalchemy.orm import Session

from src.db.session import SessionLocal
from src.db.models import User
from src.services.auth import get_or_create_role
from src.shared.security import get_password_hash

ROLE_NAMES = ["Admin", "RequirementOwner", "Reviewer", "Approver", "Viewer"]


def ensure_roles(session: Session) -> None:
    for role_name in ROLE_NAMES:
        get_or_create_role(session, role_name)


def ensure_user(session: Session, email: str, display_name: str, password: str, roles: list[str]) -> None:
    user = session.query(User).filter(User.email == email).one_or_none()
    if user:
        return
    user = User(
        email=email,
        display_name=display_name,
        password_hash=get_password_hash(password),
        is_active=True,
    )
    user.roles = [get_or_create_role(session, role) for role in roles]
    session.add(user)
    session.commit()


def main() -> None:
    password = os.environ.get("RMS_DEV_PASSWORD", "ChangeMe123!")
    with SessionLocal() as session:
        ensure_roles(session)
        ensure_user(session, "admin@example.com", "Admin", password, ["Admin"])
        ensure_user(session, "owner@example.com", "Owner", password, ["RequirementOwner"])
        ensure_user(session, "reviewer@example.com", "Reviewer", password, ["Reviewer"])
        ensure_user(session, "viewer@example.com", "Viewer", password, ["Viewer"])


if __name__ == "__main__":
    main()