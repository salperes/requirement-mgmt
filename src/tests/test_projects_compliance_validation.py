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


def test_admin_can_create_project_with_enforce_regulatory_mapping(client):
    seed_user("admin-proj@example.com", "Password123!", ["Admin"])
    token = login(client, "admin-proj@example.com", "Password123!")

    # Create project with enforce_regulatory_mapping=true
    response = client.post(
        "/projects",
        json={
            "name": "Test Project",
            "description": "Project for testing",
            "enforce_regulatory_mapping": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    project = response.json()
    assert project["name"] == "Test Project"
    assert project["enforce_regulatory_mapping"] is True


def test_admin_can_update_project_settings(client):
    seed_user("admin-proj2@example.com", "Password123!", ["Admin"])
    token = login(client, "admin-proj2@example.com", "Password123!")

    # Create project
    create_response = client.post(
        "/projects",
        json={"name": "Update Test Project", "enforce_regulatory_mapping": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_response.status_code == 200
    project_id = create_response.json()["id"]

    # Update project
    update_response = client.patch(
        f"/projects/{project_id}",
        json={"enforce_regulatory_mapping": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["enforce_regulatory_mapping"] is True


def test_non_admin_cannot_create_project(client):
    seed_user("viewer-proj@example.com", "Password123!", ["Viewer"])
    token = login(client, "viewer-proj@example.com", "Password123!")

    response = client.post(
        "/projects",
        json={"name": "Should Fail"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_all_users_can_read_projects(client):
    seed_user("admin-proj3@example.com", "Password123!", ["Admin"])
    seed_user("viewer-proj2@example.com", "Password123!", ["Viewer"])
    admin_token = login(client, "admin-proj3@example.com", "Password123!")
    viewer_token = login(client, "viewer-proj2@example.com", "Password123!")

    # Admin creates project
    client.post(
        "/projects",
        json={"name": "Readable Project"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Viewer can list projects
    response = client.get("/projects", headers={"Authorization": f"Bearer {viewer_token}"})
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_validation_returns_unmapped_regulatory_requirements(client):
    seed_user("admin-val@example.com", "Password123!", ["Admin"])
    seed_user("owner-val@example.com", "Password123!", ["RequirementOwner"])
    admin_token = login(client, "admin-val@example.com", "Password123!")
    owner_token = login(client, "owner-val@example.com", "Password123!")

    # Create project with enforcement enabled
    project = client.post(
        "/projects",
        json={"name": "Validation Project", "enforce_regulatory_mapping": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    # Create a regulatory requirement
    req = client.post(
        "/requirements",
        json={
            "title": "Regulatory Req",
            "text": "Must comply with standard X",
            "discipline": "Software",
            "req_type_primary": "Regulatory",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    ).json()

    # Validate - should show unmapped
    validation = client.get(
        f"/compliance/validate?project_id={project['id']}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert validation.status_code == 200
    result = validation.json()
    assert result["enforce_regulatory_mapping"] is True
    assert result["valid"] is False
    assert len(result["unmapped_regulatory_requirements"]) >= 1

    unmapped_ids = [r["id"] for r in result["unmapped_regulatory_requirements"]]
    assert req["id"] in unmapped_ids


def test_validation_passes_when_enforcement_disabled(client):
    seed_user("admin-val2@example.com", "Password123!", ["Admin"])
    seed_user("owner-val2@example.com", "Password123!", ["RequirementOwner"])
    admin_token = login(client, "admin-val2@example.com", "Password123!")
    owner_token = login(client, "owner-val2@example.com", "Password123!")

    # Create project with enforcement disabled
    project = client.post(
        "/projects",
        json={"name": "No Enforce Project", "enforce_regulatory_mapping": False},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    # Create a regulatory requirement (unmapped)
    client.post(
        "/requirements",
        json={
            "title": "Unmapped Regulatory",
            "text": "Unmapped requirement",
            "discipline": "Software",
            "req_type_primary": "Regulatory",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    # Validate - should pass because enforcement is disabled
    validation = client.get(
        f"/compliance/validate?project_id={project['id']}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert validation.status_code == 200
    result = validation.json()
    assert result["enforce_regulatory_mapping"] is False
    assert result["valid"] is True  # Valid even with unmapped requirements


def test_validation_passes_when_regulatory_requirement_is_mapped(client):
    seed_user("admin-val3@example.com", "Password123!", ["Admin"])
    seed_user("owner-val3@example.com", "Password123!", ["RequirementOwner"])
    admin_token = login(client, "admin-val3@example.com", "Password123!")
    owner_token = login(client, "owner-val3@example.com", "Password123!")

    # Create project with enforcement enabled
    project = client.post(
        "/projects",
        json={"name": "Mapped Project", "enforce_regulatory_mapping": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    # Create a regulatory requirement
    req = client.post(
        "/requirements",
        json={
            "title": "Mapped Regulatory",
            "text": "Will be mapped",
            "discipline": "Software",
            "req_type_primary": "Regulatory",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    ).json()

    # Create standard and clause
    standard = client.post(
        "/standards",
        json={"code": "ISO-VAL", "title": "Validation Standard"},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()
    clause = client.post(
        f"/standards/{standard['id']}/clauses",
        json={"clause_code": "1.1", "title": "Test Clause", "text": "Clause text"},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    # Map the requirement
    client.post(
        "/compliance-mappings",
        json={
            "requirement_id": req["id"],
            "standard_clause_id": clause["id"],
            "compliance_status": "COMPLIANT",
            "justification": "Mapped for testing",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    # Validate - should pass now
    validation = client.get(
        f"/compliance/validate?project_id={project['id']}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert validation.status_code == 200
    result = validation.json()
    assert result["enforce_regulatory_mapping"] is True

    # The specific requirement should not be in unmapped list
    unmapped_ids = [r["id"] for r in result["unmapped_regulatory_requirements"]]
    assert req["id"] not in unmapped_ids
