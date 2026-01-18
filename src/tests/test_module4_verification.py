import uuid

from src.db.models import Evidence, Suspect, TestCase, User, VerificationResult
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
        "title": "Req title",
        "text": "Requirement text",
        "discipline": "Software",
        "req_type_primary": "Functional",
    }
    response = client.post("/requirements", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    return response.json()


def create_test_case(client, token: str, title: str) -> dict:
    payload = {"title": title, "description": "desc", "verification_method": "TEST"}
    response = client.post("/test-cases", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    return response.json()


def link_requirement_test(client, token: str, requirement_id: str, test_case_id: str) -> None:
    payload = {
        "source_type": "Requirement",
        "source_id": requirement_id,
        "target_type": "Test",
        "target_id": test_case_id,
        "link_type": "VERIFIES",
    }
    response = client.post("/links", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_test_case_create_and_viewer_denied(client):
    seed_user("owner-m4@example.com", "Password123!", ["RequirementOwner"])
    seed_user("viewer-m4@example.com", "Password123!", ["Viewer"])

    owner_token = login(client, "owner-m4@example.com", "Password123!")
    viewer_token = login(client, "viewer-m4@example.com", "Password123!")

    payload = {"title": "TC one", "description": "desc", "verification_method": "TEST"}
    create = client.post("/test-cases", json=payload, headers={"Authorization": f"Bearer {owner_token}"})
    assert create.status_code == 200

    denied = client.post("/test-cases", json=payload, headers={"Authorization": f"Bearer {viewer_token}"})
    assert denied.status_code == 403


def test_reviewer_can_submit_verification_and_evidence(client):
    seed_user("owner-m4b@example.com", "Password123!", ["RequirementOwner"])
    seed_user("reviewer-m4@example.com", "Password123!", ["Reviewer"])

    owner_token = login(client, "owner-m4b@example.com", "Password123!")
    reviewer_token = login(client, "reviewer-m4@example.com", "Password123!")

    req = create_requirement(client, owner_token)
    test_case = create_test_case(client, owner_token, "TC verify")
    link_requirement_test(client, owner_token, req["id"], test_case["id"])

    payload = {"test_case_id": test_case["id"], "requirement_id": req["id"], "status": "PASS"}
    result = client.post("/verification-results", json=payload, headers={"Authorization": f"Bearer {reviewer_token}"})
    assert result.status_code == 200
    result_id = result.json()["id"]

    evidence_payload = {
        "related_type": "VerificationResult",
        "related_id": result_id,
        "evidence_type": "LINK",
        "uri_or_text": "https://example.com/report",
    }
    evidence = client.post("/evidence", json=evidence_payload, headers={"Authorization": f"Bearer {reviewer_token}"})
    assert evidence.status_code == 200

    with SessionLocal() as session:
        stored = (
            session.query(Evidence)
            .filter(Evidence.id == uuid.UUID(evidence.json()["id"]))
            .one_or_none()
        )
        assert stored is not None


def test_pass_clears_suspect_when_all_tests_pass(client):
    seed_user("owner-m4c@example.com", "Password123!", ["RequirementOwner"])
    seed_user("reviewer-m4c@example.com", "Password123!", ["Reviewer"])

    owner_token = login(client, "owner-m4c@example.com", "Password123!")
    reviewer_token = login(client, "reviewer-m4c@example.com", "Password123!")

    req = create_requirement(client, owner_token)
    test_case1 = create_test_case(client, owner_token, "TC-A")
    test_case2 = create_test_case(client, owner_token, "TC-B")

    link_requirement_test(client, owner_token, req["id"], test_case1["id"])
    link_requirement_test(client, owner_token, req["id"], test_case2["id"])

    with SessionLocal() as session:
        suspect = Suspect(entity_type="Requirement", entity_id=req["id"], reason="impact")
        session.add(suspect)
        session.commit()

    payload = {"test_case_id": test_case1["id"], "requirement_id": req["id"], "status": "PASS"}
    first = client.post("/verification-results", json=payload, headers={"Authorization": f"Bearer {reviewer_token}"})
    assert first.status_code == 200

    payload2 = {"test_case_id": test_case2["id"], "requirement_id": req["id"], "status": "PASS"}
    second = client.post("/verification-results", json=payload2, headers={"Authorization": f"Bearer {reviewer_token}"})
    assert second.status_code == 200

    with SessionLocal() as session:
        remaining = (
            session.query(Suspect)
            .filter(Suspect.entity_type == "Requirement")
            .filter(Suspect.entity_id == req["id"])
            .one_or_none()
        )
        assert remaining is None

    rtm = client.get("/rtm?format=json", headers={"Authorization": f"Bearer {owner_token}"})
    assert rtm.status_code == 200
    rows = rtm.json()
    matched = [row for row in rows if row["req_code"] == req["req_code"]]
    assert matched
    assert matched[0]["verification_status"] == "PASS"
