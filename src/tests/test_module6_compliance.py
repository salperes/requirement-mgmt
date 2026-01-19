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


def login(client, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def create_requirement(client, token: str) -> dict:
    payload = {
        "title": "Compliance req",
        "text": "Requirement text",
        "discipline": "Software",
        "req_type_primary": "Regulatory",
    }
    response = client.post("/requirements", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    return response.json()


def test_admin_can_create_standards_and_clauses(client):
    seed_user("admin-m6@example.com", "Password123!", ["Admin"])
    token = login(client, "admin-m6@example.com", "Password123!")

    standard = client.post(
        "/standards",
        json={"code": "ISO 26262", "title": "Functional safety", "version": "2018"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert standard.status_code == 200
    standard_id = standard.json()["id"]

    clause = client.post(
        f"/standards/{standard_id}/clauses",
        json={"clause_code": "5.1", "title": "Safety lifecycle", "text": "Clause text"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert clause.status_code == 200


def test_owner_can_map_and_viewer_denied(client):
    seed_user("admin-m6b@example.com", "Password123!", ["Admin"])
    seed_user("owner-m6@example.com", "Password123!", ["RequirementOwner"])
    seed_user("viewer-m6@example.com", "Password123!", ["Viewer"])

    admin_token = login(client, "admin-m6b@example.com", "Password123!")
    owner_token = login(client, "owner-m6@example.com", "Password123!")
    viewer_token = login(client, "viewer-m6@example.com", "Password123!")

    standard = client.post(
        "/standards",
        json={"code": "IEC 61508", "title": "Functional safety", "version": "2010"},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()
    clause = client.post(
        f"/standards/{standard['id']}/clauses",
        json={"clause_code": "7.2", "title": "Concept", "text": "Clause text"},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    requirement = create_requirement(client, owner_token)

    mapping = client.post(
        "/compliance-mappings",
        json={
            "requirement_id": requirement["id"],
            "standard_clause_id": clause["id"],
            "compliance_status": "COMPLIANT",
            "justification": "covered",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert mapping.status_code == 200

    denied = client.post(
        "/compliance-mappings",
        json={
            "requirement_id": requirement["id"],
            "standard_clause_id": clause["id"],
            "compliance_status": "NON_COMPLIANT",
        },
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert denied.status_code == 403


def test_export_includes_baseline_and_status(client):
    seed_user("admin-m6c@example.com", "Password123!", ["Admin"])
    seed_user("owner-m6c@example.com", "Password123!", ["RequirementOwner"])

    admin_token = login(client, "admin-m6c@example.com", "Password123!")
    owner_token = login(client, "owner-m6c@example.com", "Password123!")

    standard = client.post(
        "/standards",
        json={"code": "ANSI Z10", "title": "Occupational Health"},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()
    clause = client.post(
        f"/standards/{standard['id']}/clauses",
        json={"clause_code": "4.2", "title": "Planning", "text": "Clause text"},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    requirement = create_requirement(client, owner_token)

    client.post(
        "/compliance-mappings",
        json={
            "requirement_id": requirement["id"],
            "standard_clause_id": clause["id"],
            "compliance_status": "COMPLIANT",
            "justification": "aligned",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    baseline = client.post(
        "/baselines",
        json={"name": "Compliance BL", "description": "", "requirement_ids": [requirement["id"]]},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert baseline.status_code == 200
    baseline_id = baseline.json()["id"]

    export = client.get(
        f"/compliance/export?format=csv&baseline_id={baseline_id}&standard_id={standard['id']}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert export.status_code == 200
    body = export.text
    assert baseline_id in body
    assert "COMPLIANT" in body