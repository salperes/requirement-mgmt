from __future__ import annotations

from typing import Iterable, List

import uuid
from sqlalchemy.orm import Session

from src.db.models import Link, Suspect, VerificationResult

def get_linked_test_case_ids(session: Session, requirement_id: str) -> List[str]:
    links = (
        session.query(Link)
        .filter(Link.deleted_at.is_(None))
        .filter(Link.source_type == "Requirement")
        .filter(Link.source_id == requirement_id)
        .filter(Link.target_type == "Test")
        .filter(Link.link_type == "VERIFIES")
        .all()
    )
    return [link.target_id for link in links]


def latest_results_by_test_case(
    session: Session,
    requirement_id: str,
    test_case_ids: Iterable[str],
) -> dict[str, VerificationResult]:
    results: dict[str, VerificationResult] = {}
    try:
        requirement_uuid = uuid.UUID(str(requirement_id))
    except ValueError:
        requirement_uuid = requirement_id
    for test_case_id in test_case_ids:
        try:
            test_case_uuid = uuid.UUID(str(test_case_id))
        except ValueError:
            continue
        latest = (
            session.query(VerificationResult)
            .filter(VerificationResult.requirement_id == requirement_uuid)
            .filter(VerificationResult.test_case_id == test_case_uuid)
            .order_by(VerificationResult.executed_at.desc())
            .first()
        )
        if latest:
            results[str(test_case_uuid)] = latest
    return results


def compute_verification_status(
    session: Session,
    requirement_id: str,
    test_case_ids: Iterable[str],
) -> str:
    ids = []
    for test_case_id in test_case_ids:
        try:
            ids.append(str(uuid.UUID(str(test_case_id))))
        except ValueError:
            continue
    if not ids:
        return "NOT_RUN"
    latest_results = latest_results_by_test_case(session, requirement_id, ids)
    if len(latest_results) != len(ids):
        return "NOT_RUN"

    statuses = [result.status for result in latest_results.values()]
    if any(status == "FAIL" for status in statuses):
        return "FAIL"
    if any(status == "BLOCKED" for status in statuses):
        return "BLOCKED"
    if all(status == "PASS" for status in statuses):
        return "PASS"
    return "NOT_RUN"


def maybe_auto_clear_suspect(
    session: Session,
    requirement_id: str,
    test_case_ids: Iterable[str],
) -> bool:
    status = compute_verification_status(session, requirement_id, test_case_ids)
    if status != "PASS":
        return False

    suspect = (
        session.query(Suspect)
        .filter(Suspect.entity_type == "Requirement")
        .filter(Suspect.entity_id == requirement_id)
        .one_or_none()
    )
    if not suspect:
        return True
    session.delete(suspect)
    session.commit()
    return True
