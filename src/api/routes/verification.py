from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from src.api.deps import get_db, require_permission
from src.api.schemas import EvidenceCreate, EvidenceOut, VerificationResultCreate, VerificationResultOut
from src.db.models import Evidence, Requirement, TestCase, User, VerificationResult
from src.services.audit import write_audit
from src.services.verification import get_linked_test_case_ids, maybe_auto_clear_suspect
from src.shared.errors import AppError

router = APIRouter(tags=["verification"])


def to_verification_out(result: VerificationResult) -> VerificationResultOut:
    return VerificationResultOut(
        id=str(result.id),
        test_case_id=str(result.test_case_id),
        requirement_id=str(result.requirement_id),
        baseline_id=str(result.baseline_id) if result.baseline_id else None,
        status=result.status,
        executed_by_user_id=str(result.executed_by_user_id),
        executed_at=result.executed_at,
        comment=result.comment,
    )


def to_evidence_out(record: Evidence) -> EvidenceOut:
    return EvidenceOut(
        id=str(record.id),
        related_type=record.related_type,
        related_id=str(record.related_id),
        evidence_type=record.evidence_type,
        uri_or_text=record.uri_or_text,
        checksum=record.checksum,
        uploaded_by_user_id=str(record.uploaded_by_user_id),
        created_at=record.created_at,
    )


@router.post("/verification-results", response_model=VerificationResultOut)
def create_verification_result(
    payload: VerificationResultCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("verify:execute")),
) -> VerificationResultOut:
    try:
        test_case_id = uuid.UUID(payload.test_case_id)
        requirement_id = uuid.UUID(payload.requirement_id)
    except ValueError:
        raise AppError("VALIDATION_ERROR", "Invalid test_case_id or requirement_id.", 400)

    baseline_id = None
    if payload.baseline_id:
        try:
            baseline_id = uuid.UUID(payload.baseline_id)
        except ValueError:
            raise AppError("VALIDATION_ERROR", "Invalid baseline_id.", 400)

    test_case = db.query(TestCase).filter(TestCase.id == test_case_id).one_or_none()
    if not test_case or test_case.deleted_at is not None:
        raise AppError("NOT_FOUND", "Test case not found.", 404)
    requirement = db.query(Requirement).filter(Requirement.id == requirement_id).one_or_none()
    if not requirement or requirement.deleted_at is not None:
        raise AppError("NOT_FOUND", "Requirement not found.", 404)

    result = VerificationResult(
        test_case_id=test_case_id,
        requirement_id=requirement_id,
        baseline_id=baseline_id,
        status=payload.status,
        executed_by_user_id=user.id,
        executed_at=datetime.utcnow(),
        comment=payload.comment,
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    write_audit(
        db,
        request.state.request_id,
        action="VERIFICATION_RECORDED",
        actor_user_id=str(user.id),
        entity_type="VerificationResult",
        entity_id=str(result.id),
        payload={
            "test_case_id": str(result.test_case_id),
            "requirement_id": str(result.requirement_id),
            "status": result.status,
        },
    )

    if result.status == "PASS":
        test_case_ids = get_linked_test_case_ids(db, str(requirement_id))
        cleared = maybe_auto_clear_suspect(db, str(requirement_id), test_case_ids)
        if cleared and test_case_ids:
            write_audit(
                db,
                request.state.request_id,
                action="TRACE_SUSPECT_AUTO_CLEARED",
                actor_user_id=str(user.id),
                entity_type="Requirement",
                entity_id=str(requirement_id),
                payload={"requirement_id": str(requirement_id), "test_case_ids": test_case_ids},
            )

    return to_verification_out(result)


@router.get("/verification-results", response_model=List[VerificationResultOut])
def list_verification_results(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("verify:read")),
    requirement_id: Optional[str] = None,
    baseline_id: Optional[str] = None,
) -> List[VerificationResultOut]:
    q = db.query(VerificationResult)
    if requirement_id:
        q = q.filter(VerificationResult.requirement_id == requirement_id)
    if baseline_id:
        q = q.filter(VerificationResult.baseline_id == baseline_id)
    results = q.order_by(VerificationResult.executed_at.desc()).all()
    return [to_verification_out(result) for result in results]


@router.post("/evidence", response_model=EvidenceOut)
def create_evidence(
    payload: EvidenceCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evidence:attach")),
) -> EvidenceOut:
    try:
        related_id = uuid.UUID(payload.related_id)
    except ValueError:
        raise AppError("VALIDATION_ERROR", "Invalid related_id.", 400)

    if payload.related_type == "TestCase":
        test_case = db.query(TestCase).filter(TestCase.id == related_id).one_or_none()
        if not test_case:
            raise AppError("NOT_FOUND", "Test case not found.", 404)
    elif payload.related_type == "VerificationResult":
        result = db.query(VerificationResult).filter(VerificationResult.id == related_id).one_or_none()
        if not result:
            raise AppError("NOT_FOUND", "Verification result not found.", 404)
    else:
        raise AppError("VALIDATION_ERROR", "Invalid related_type.", 400)

    evidence = Evidence(
        related_type=payload.related_type,
        related_id=related_id,
        evidence_type=payload.evidence_type,
        uri_or_text=payload.uri_or_text,
        checksum=payload.checksum,
        uploaded_by_user_id=user.id,
        created_at=datetime.utcnow(),
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    write_audit(
        db,
        request.state.request_id,
        action="EVIDENCE_ATTACHED",
        actor_user_id=str(user.id),
        entity_type="Evidence",
        entity_id=str(evidence.id),
        payload={"related_type": evidence.related_type, "related_id": str(evidence.related_id)},
    )
    return to_evidence_out(evidence)


@router.get("/evidence", response_model=List[EvidenceOut])
def list_evidence(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("verify:read")),
    related_type: Optional[str] = None,
    related_id: Optional[str] = None,
) -> List[EvidenceOut]:
    q = db.query(Evidence)
    if related_type:
        q = q.filter(Evidence.related_type == related_type)
    if related_id:
        try:
            related_uuid = uuid.UUID(related_id)
        except ValueError:
            raise AppError("VALIDATION_ERROR", "Invalid related_id.", 400)
        q = q.filter(Evidence.related_id == related_uuid)
    records = q.order_by(Evidence.created_at.desc()).all()
    return [to_evidence_out(record) for record in records]
