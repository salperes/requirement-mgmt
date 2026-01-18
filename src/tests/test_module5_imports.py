from src.db.models import Requirement, User
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


def upload_import(client, token: str, content: str) -> dict:
    files = {
        "file": (
            "sample.docx",
            content.encode("utf-8"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    response = client.post("/imports", files=files, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    return response.json()


def test_owner_can_upload_and_viewer_denied(client):
    seed_user("owner-m5@example.com", "Password123!", ["RequirementOwner"])
    seed_user("viewer-m5@example.com", "Password123!", ["Viewer"])

    owner_token = login(client, "owner-m5@example.com", "Password123!")
    viewer_token = login(client, "viewer-m5@example.com", "Password123!")

    content = "1. Clause one\n- Clause two"
    files = {
        "file": (
            "sample.docx",
            content.encode("utf-8"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    allowed = client.post("/imports", files=files, headers={"Authorization": f"Bearer {owner_token}"})
    assert allowed.status_code == 200

    denied = client.post("/imports", files=files, headers={"Authorization": f"Bearer {viewer_token}"})
    assert denied.status_code == 403


def test_clause_parsing_is_deterministic(client):
    seed_user("owner-m5b@example.com", "Password123!", ["RequirementOwner"])
    token = login(client, "owner-m5b@example.com", "Password123!")

    content = "1. First clause\ncontinued line\n- Bullet clause\n2. Second clause\n\nTrailing text"
    session = upload_import(client, token, content)

    clauses = client.get(
        f"/imports/{session['id']}/clauses",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert clauses.status_code == 200
    data = clauses.json()
    assert len(data) == 4
    assert data[0]["raw_text"] == "1. First clause\ncontinued line"
    assert data[1]["raw_text"] == "- Bullet clause"
    assert data[2]["raw_text"] == "2. Second clause"
    assert data[3]["raw_text"] == "Trailing text"


def test_accept_reject_and_source_trace(client):
    seed_user("owner-m5c@example.com", "Password123!", ["RequirementOwner"])
    token = login(client, "owner-m5c@example.com", "Password123!")

    content = "1. Clause A\n2. Clause B"
    session = upload_import(client, token, content)

    clauses = client.get(
        f"/imports/{session['id']}/clauses",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    accept = client.post(
        f"/imports/{session['id']}/clauses/{clauses[0]['id']}/accept",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert accept.status_code == 200
    requirement = accept.json()
    assert requirement["source"] == "import"

    reject = client.post(
        f"/imports/{session['id']}/clauses/{clauses[1]['id']}/reject",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert reject.status_code == 200

    source = client.get(
        f"/requirements/{requirement['id']}/source",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert source.status_code == 200
    payload = source.json()
    assert payload["sources"]
    assert payload["sources"][0]["file_name"] == "sample.docx"
    assert payload["sources"][0]["clause_text"] == clauses[0]["raw_text"]

    with SessionLocal() as session_db:
        rejected = (
            session_db.query(Requirement)
            .filter(Requirement.text == clauses[1]["raw_text"])
            .one_or_none()
        )
        assert rejected is None
