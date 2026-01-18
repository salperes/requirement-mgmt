from src.db.models import BaselineItem, RequirementVersion, User
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


def create_requirement(client, token: str, text: str) -> dict:
    payload = {
        "title": "Req title",
        "text": text,
        "discipline": "System",
        "req_type_primary": "Functional",
    }
    response = client.post("/requirements", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    return response.json()


def test_baseline_create_freezes_latest_versions(client):
    seed_user("owner4@example.com", "Password123!", ["RequirementOwner"])
    token = login(client, "owner4@example.com", "Password123!")

    req1 = create_requirement(client, token, "First requirement")
    req2 = create_requirement(client, token, "Second requirement")

    update = {"text": "Second requirement v2", "change_reason": "clarify"}
    patch = client.patch(
        f"/requirements/{req2['id']}",
        json=update,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert patch.status_code == 200

    baseline_payload = {
        "name": "Baseline A",
        "description": "Test baseline",
        "requirement_ids": [req1["id"], req2["id"]],
    }
    response = client.post("/baselines", json=baseline_payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    baseline_id = response.json()["id"]

    with SessionLocal() as session:
        items = session.query(BaselineItem).filter(BaselineItem.baseline_id == baseline_id).all()
        assert len(items) == 2
        versions = {
            str(item.requirement_id): session.query(RequirementVersion)
            .filter(RequirementVersion.id == item.requirement_version_id)
            .one()
            for item in items
        }
        assert versions[req1["id"]].version_no == 1
        assert versions[req2["id"]].version_no == 2


def test_baseline_export_includes_tag(client):
    seed_user("owner5@example.com", "Password123!", ["RequirementOwner"])
    token = login(client, "owner5@example.com", "Password123!")

    req = create_requirement(client, token, "Export requirement")
    baseline_payload = {"name": "Baseline Export", "requirement_ids": [req["id"]]}
    response = client.post("/baselines", json=baseline_payload, headers={"Authorization": f"Bearer {token}"})
    baseline = response.json()

    export = client.get(
        f"/baselines/{baseline['id']}/export?format=csv",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert export.status_code == 200
    body = export.text
    assert baseline["baseline_tag"] in body
    assert req["req_code"] in body
