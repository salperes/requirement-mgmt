from src.db.models import AuditLog, User
from src.db.session import SessionLocal
from src.services.auth import get_or_create_role
from src.shared.security import get_password_hash


def seed_user(email: str, password: str, roles: list[str]) -> None:
    with SessionLocal() as session:
        existing = session.query(User).filter(User.email == email).one_or_none()
        if existing:
            existing.password_hash = get_password_hash(password)
            existing.is_active = True
            existing.roles = [get_or_create_role(session, role) for role in roles]
            session.commit()
            return
        user = User(
            email=email,
            display_name="Test User",
            password_hash=get_password_hash(password),
            is_active=True,
        )
        user.roles = [get_or_create_role(session, role) for role in roles]
        session.add(user)
        session.commit()


def test_rbac_deny_is_audited(client):
    seed_user("viewer2@example.com", "Password123!", ["Viewer"])

    login = client.post("/auth/login", json={"email": "viewer2@example.com", "password": "Password123!"})
    token = login.json()["access_token"]

    response = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

    with SessionLocal() as session:
        audit = (
            session.query(AuditLog)
            .filter(AuditLog.action == "RBAC_DENY")
            .order_by(AuditLog.created_at.desc())
            .first()
        )
        assert audit is not None
