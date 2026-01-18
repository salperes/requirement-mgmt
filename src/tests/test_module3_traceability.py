from src.db.models import Link, Suspect, User
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


def create_requirement(client, token: str, req_type_primary: str = "Functional") -> dict:
    payload = {
        "title": "Req title",
        "text": "Initial requirement text",
        "discipline": "Software",
        "req_type_primary": req_type_primary,
    }
    response = client.post("/requirements", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    return response.json()


def create_test_case(client, token: str) -> dict:
    payload = {
        "title": "Test case title",
        "description": "Test case description",
        "verification_method": "TEST",
    }
    response = client.post("/test-cases", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    return response.json()


def test_link_create_permission_and_impact(client):
    seed_user("owner-trace@example.com", "Password123!", ["RequirementOwner"])
    seed_user("viewer-trace@example.com", "Password123!", ["Viewer"])

    owner_token = login(client, "owner-trace@example.com", "Password123!")
    viewer_token = login(client, "viewer-trace@example.com", "Password123!")

    req = create_requirement(client, owner_token)

    link_payload = {
        "source_type": "Requirement",
        "source_id": req["id"],
        "target_type": "Test",
        "target_id": "TC-1",
        "link_type": "VERIFIES",
    }
    create = client.post("/links", json=link_payload, headers={"Authorization": f"Bearer {owner_token}"})
    assert create.status_code == 200

    denied = client.post("/links", json=link_payload, headers={"Authorization": f"Bearer {viewer_token}"})
    assert denied.status_code == 403

    with SessionLocal() as session:
        stored = session.query(Link).filter(Link.source_id == req["id"]).one_or_none()
        assert stored is not None


def test_requirement_update_sets_suspect_and_rtm_flag(client):
    seed_user("owner-impact@example.com", "Password123!", ["RequirementOwner"])
    seed_user("admin-impact@example.com", "Password123!", ["Admin"])

    owner_token = login(client, "owner-impact@example.com", "Password123!")
    admin_token = login(client, "admin-impact@example.com", "Password123!")

    req = create_requirement(client, owner_token)

    link_payload = {
        "source_type": "Requirement",
        "source_id": req["id"],
        "target_type": "Test",
        "target_id": "TC-99",
        "link_type": "VERIFIES",
    }
    link = client.post("/links", json=link_payload, headers={"Authorization": f"Bearer {owner_token}"})
    assert link.status_code == 200

    update = client.patch(
        f"/requirements/{req['id']}",
        json={"text": "Updated requirement text"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert update.status_code == 200

    with SessionLocal() as session:
        suspect = (
            session.query(Suspect)
            .filter(Suspect.entity_type == "Test")
            .filter(Suspect.entity_id == "TC-99")
            .one_or_none()
        )
        assert suspect is not None

    impact = client.get(
        f"/requirements/{req['id']}/impact",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert impact.status_code == 200
    impacted = impact.json()["impacted"]
    assert any(item["entity_id"] == "TC-99" for item in impacted)

    rtm = client.get("/rtm?format=csv", headers={"Authorization": f"Bearer {owner_token}"})
    assert rtm.status_code == 200
    assert "True" in rtm.text

    clear = client.post(
        "/suspect/Test/TC-99/clear",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert clear.status_code == 200


def test_orphan_report_lists_unlinked_tests(client):
    seed_user("owner-orphan@example.com", "Password123!", ["RequirementOwner"])
    owner_token = login(client, "owner-orphan@example.com", "Password123!")

    test_case = create_test_case(client, owner_token)

    report = client.get("/orphans", headers={"Authorization": f"Bearer {owner_token}"})
    assert report.status_code == 200
    tests = report.json()["tests"]
    assert any(item["entity_id"] == test_case["id"] for item in tests)

    req = create_requirement(client, owner_token)
    link_payload = {
        "source_type": "Requirement",
        "source_id": req["id"],
        "target_type": "Test",
        "target_id": test_case["id"],
        "link_type": "VERIFIES",
    }
    link = client.post("/links", json=link_payload, headers={"Authorization": f"Bearer {owner_token}"})
    assert link.status_code == 200

    report_after = client.get("/orphans", headers={"Authorization": f"Bearer {owner_token}"})
    assert report_after.status_code == 200
    tests_after = report_after.json()["tests"]
    assert all(item["entity_id"] != test_case["id"] for item in tests_after)
