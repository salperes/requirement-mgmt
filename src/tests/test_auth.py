from sqlalchemy.orm import Session

from src.db.models import User
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


def test_login_success_and_me(client):
    seed_user("admin@example.com", "Password123!", ["Admin"])

    response = client.post("/auth/login", json={"email": "admin@example.com", "password": "Password123!"})
    assert response.status_code == 200
    token = response.json()["access_token"]

    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    payload = me_response.json()
    assert payload["email"] == "admin@example.com"
    assert "Admin" in payload["roles"]


def test_login_invalid_password_audited(client):
    seed_user("viewer@example.com", "Password123!", ["Viewer"])

    response = client.post("/auth/login", json={"email": "viewer@example.com", "password": "wrong"})
    assert response.status_code == 401
