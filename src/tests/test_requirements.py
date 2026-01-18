from sqlalchemy.orm import Session

from src.db.models import RequirementVersion, User
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


def login(client, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_create_requirement_creates_version(client):
    seed_user("owner@example.com", "Password123!", ["RequirementOwner"])
    token = login(client, "owner@example.com", "Password123!")

    payload = {
        "title": "Req title",
        "text": "Initial requirement text",
        "discipline": "Software",
        "req_type_primary": "Functional",
    }
    response = client.post("/requirements", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    requirement_id = response.json()["id"]

    with SessionLocal() as session:
        version = (
            session.query(RequirementVersion)
            .filter(RequirementVersion.requirement_id == requirement_id)
            .first()
        )
        assert version is not None
        assert version.version_no == 1


def test_update_requirement_creates_new_version(client):
    seed_user("owner2@example.com", "Password123!", ["RequirementOwner"])
    token = login(client, "owner2@example.com", "Password123!")

    payload = {
        "title": "Req title",
        "text": "Initial requirement text",
        "discipline": "Software",
        "req_type_primary": "Functional",
    }
    response = client.post("/requirements", json=payload, headers={"Authorization": f"Bearer {token}"})
    requirement = response.json()

    update = {"text": "Updated requirement text", "change_reason": "clarify"}
    patch = client.patch(
        f"/requirements/{requirement['id']}",
        json=update,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert patch.status_code == 200

    with SessionLocal() as session:
        versions = (
            session.query(RequirementVersion)
            .filter(RequirementVersion.requirement_id == requirement["id"])
            .order_by(RequirementVersion.version_no.asc())
            .all()
        )
        assert len(versions) == 2
        assert versions[0].snapshot_json["text"] == "Initial requirement text"
        assert versions[1].snapshot_json["text"] == "Updated requirement text"


def test_delete_requirement_soft_delete(client):
    seed_user("owner3@example.com", "Password123!", ["RequirementOwner"])
    token = login(client, "owner3@example.com", "Password123!")

    payload = {
        "title": "Req title",
        "text": "Requirement text",
        "discipline": "Mechanical",
        "req_type_primary": "Performance",
    }
    response = client.post("/requirements", json=payload, headers={"Authorization": f"Bearer {token}"})
    requirement_id = response.json()["id"]

    delete = client.delete(f"/requirements/{requirement_id}", headers={"Authorization": f"Bearer {token}"})
    assert delete.status_code == 200
    assert delete.json()["deleted_at"] is not None

    list_default = client.get("/requirements", headers={"Authorization": f"Bearer {token}"})
    assert all(item["id"] != requirement_id for item in list_default.json())

    list_all = client.get("/requirements?include_deleted=true", headers={"Authorization": f"Bearer {token}"})
    assert any(item["id"] == requirement_id for item in list_all.json())
