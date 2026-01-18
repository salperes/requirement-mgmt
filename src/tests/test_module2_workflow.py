from src.db.models import ApprovalRecord, AuditLog, Notification, User
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
        "discipline": "Software",
        "req_type_primary": "Functional",
    }
    response = client.post("/requirements", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    return response.json()


def test_status_change_creates_audit(client):
    seed_user("owner-module2@example.com", "Password123!", ["RequirementOwner"])
    token = login(client, "owner-module2@example.com", "Password123!")

    req = create_requirement(client, token, "Workflow requirement")
    response = client.post(
        f"/requirements/{req['id']}/status",
        json={"to_status": "Review", "reason": "ready"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Review"

    with SessionLocal() as session:
        audit = (
            session.query(AuditLog)
            .filter(AuditLog.action == "REQ_STATUS_CHANGED")
            .order_by(AuditLog.created_at.desc())
            .first()
        )
        assert audit is not None
        assert audit.payload_json.get("to_status") == "Review"


def test_viewer_status_change_denied_audited(client):
    seed_user("viewer-module2@example.com", "Password123!", ["Viewer"])
    seed_user("owner-module2b@example.com", "Password123!", ["RequirementOwner"])
    owner_token = login(client, "owner-module2b@example.com", "Password123!")
    req = create_requirement(client, owner_token, "Denied workflow requirement")

    token = login(client, "viewer-module2@example.com", "Password123!")
    response = client.post(
        f"/requirements/{req['id']}/status",
        json={"to_status": "Review"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403

    with SessionLocal() as session:
        audit = (
            session.query(AuditLog)
            .filter(AuditLog.action == "RBAC_DENY")
            .order_by(AuditLog.created_at.desc())
            .first()
        )
        assert audit is not None


def test_approval_reject_requires_reason_and_records(client):
    seed_user("owner-module2c@example.com", "Password123!", ["RequirementOwner"])
    seed_user("approver-module2@example.com", "Password123!", ["Approver"])

    owner_token = login(client, "owner-module2c@example.com", "Password123!")
    approver_token = login(client, "approver-module2@example.com", "Password123!")

    req = create_requirement(client, owner_token, "Approval requirement")
    review = client.post(
        f"/requirements/{req['id']}/status",
        json={"to_status": "Review"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert review.status_code == 200

    reject_missing = client.post(
        f"/requirements/{req['id']}/approve",
        json={"decision": "REJECT"},
        headers={"Authorization": f"Bearer {approver_token}"},
    )
    assert reject_missing.status_code == 400

    reject = client.post(
        f"/requirements/{req['id']}/approve",
        json={"decision": "REJECT", "reason": "needs changes"},
        headers={"Authorization": f"Bearer {approver_token}"},
    )
    assert reject.status_code == 200
    assert reject.json()["status"] == "Rejected"

    with SessionLocal() as session:
        approval = (
            session.query(ApprovalRecord)
            .filter(ApprovalRecord.requirement_id == req["id"])
            .order_by(ApprovalRecord.signed_at.desc())
            .first()
        )
        assert approval is not None
        assert approval.decision == "REJECT"


def test_comment_mentions_create_notification_and_mark_read(client):
    seed_user("owner-module2d@example.com", "Password123!", ["RequirementOwner"])
    seed_user("viewer-module2d@example.com", "Password123!", ["Viewer"])

    owner_token = login(client, "owner-module2d@example.com", "Password123!")
    viewer_token = login(client, "viewer-module2d@example.com", "Password123!")

    req = create_requirement(client, owner_token, "Comment mention requirement")

    comment = client.post(
        f"/requirements/{req['id']}/comments",
        json={"text": "Please review @viewer-module2d@example.com"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert comment.status_code == 200

    with SessionLocal() as session:
        viewer = session.query(User).filter(User.email == "viewer-module2d@example.com").one()
        notification = (
            session.query(Notification)
            .filter(Notification.user_id == viewer.id)
            .filter(Notification.type == "MENTION")
            .order_by(Notification.created_at.desc())
            .first()
        )
        assert notification is not None
        notification_id = notification.id

    read = client.post(
        f"/notifications/{notification_id}/read",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert read.status_code == 200
    assert read.json()["is_read"] is True


def test_comment_edit_delete_audited_and_ownership(client):
    seed_user("owner-module2e@example.com", "Password123!", ["RequirementOwner"])
    seed_user("reviewer-module2@example.com", "Password123!", ["Reviewer"])

    owner_token = login(client, "owner-module2e@example.com", "Password123!")
    reviewer_token = login(client, "reviewer-module2@example.com", "Password123!")

    req = create_requirement(client, owner_token, "Comment edit requirement")

    comment = client.post(
        f"/requirements/{req['id']}/comments",
        json={"text": "Initial comment"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert comment.status_code == 200
    comment_id = comment.json()["id"]

    forbidden = client.patch(
        f"/comments/{comment_id}",
        json={"text": "Reviewer edit"},
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert forbidden.status_code == 403

    updated = client.patch(
        f"/comments/{comment_id}",
        json={"text": "Owner edit"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert updated.status_code == 200

    deleted = client.delete(
        f"/comments/{comment_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert deleted.status_code == 200

    with SessionLocal() as session:
        actions = {
            record.action
            for record in session.query(AuditLog)
            .filter(AuditLog.action.in_(["REQ_COMMENT_CREATED", "REQ_COMMENT_EDITED", "REQ_COMMENT_DELETED"]))
            .all()
        }
        assert "REQ_COMMENT_CREATED" in actions
        assert "REQ_COMMENT_EDITED" in actions
        assert "REQ_COMMENT_DELETED" in actions
