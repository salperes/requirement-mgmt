from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from src.api.deps import get_db, require_permission
from src.api.schemas import TestCaseCreate, TestCaseOut, TestCaseUpdate
from src.db.models import TestCase, User
from src.services.audit import write_audit
from src.services.test_cases import apply_test_case_updates, generate_test_code
from src.shared.errors import AppError

router = APIRouter(prefix="/test-cases", tags=["test-cases"])


def to_test_case_out(test_case: TestCase) -> TestCaseOut:
    return TestCaseOut(
        id=str(test_case.id),
        test_code=test_case.test_code,
        title=test_case.title,
        description=test_case.description,
        verification_method=test_case.verification_method,
        owner_user_id=str(test_case.owner_user_id),
        created_at=test_case.created_at,
        updated_at=test_case.updated_at,
        deleted_at=test_case.deleted_at,
    )


@router.post("", response_model=TestCaseOut)
def create_test_case(
    payload: TestCaseCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("test:create")),
) -> TestCaseOut:
    owner_user_id = user.id
    if payload.owner_user_id:
        try:
            owner_user_id = uuid.UUID(payload.owner_user_id)
        except ValueError:
            raise AppError("VALIDATION_ERROR", "Invalid owner_user_id.", 400)

    test_case = TestCase(
        test_code=generate_test_code(db),
        title=payload.title,
        description=payload.description,
        verification_method=payload.verification_method,
        owner_user_id=owner_user_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(test_case)
    db.commit()
    db.refresh(test_case)

    write_audit(
        db,
        request.state.request_id,
        action="TEST_CASE_CREATED",
        actor_user_id=str(user.id),
        entity_type="TestCase",
        entity_id=str(test_case.id),
        payload={"test_code": test_case.test_code},
    )
    return to_test_case_out(test_case)


@router.get("", response_model=List[TestCaseOut])
def list_test_cases(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("test:read")),
    include_deleted: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
) -> List[TestCaseOut]:
    offset = (page - 1) * page_size
    q = db.query(TestCase)
    if not include_deleted:
        q = q.filter(TestCase.deleted_at.is_(None))
    items = q.order_by(TestCase.created_at.desc()).offset(offset).limit(page_size).all()
    return [to_test_case_out(item) for item in items]


@router.get("/{test_case_id}", response_model=TestCaseOut)
def get_test_case(
    test_case_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("test:read")),
) -> TestCaseOut:
    try:
        test_uuid = uuid.UUID(test_case_id)
    except ValueError:
        raise AppError("VALIDATION_ERROR", "Invalid test_case_id.", 400)
    test_case = db.query(TestCase).filter(TestCase.id == test_uuid).one_or_none()
    if not test_case:
        raise AppError("NOT_FOUND", "Test case not found.", 404)
    return to_test_case_out(test_case)


@router.patch("/{test_case_id}", response_model=TestCaseOut)
def update_test_case(
    test_case_id: str,
    payload: TestCaseUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("test:update")),
) -> TestCaseOut:
    try:
        test_uuid = uuid.UUID(test_case_id)
    except ValueError:
        raise AppError("VALIDATION_ERROR", "Invalid test_case_id.", 400)
    test_case = db.query(TestCase).filter(TestCase.id == test_uuid).one_or_none()
    if not test_case or test_case.deleted_at is not None:
        raise AppError("NOT_FOUND", "Test case not found.", 404)

    updates = payload.model_dump(exclude_unset=True)
    if "owner_user_id" in updates and updates["owner_user_id"] is not None:
        try:
            updates["owner_user_id"] = uuid.UUID(updates["owner_user_id"])
        except ValueError:
            raise AppError("VALIDATION_ERROR", "Invalid owner_user_id.", 400)

    changed = apply_test_case_updates(test_case, updates)
    if not changed:
        raise AppError("NO_CHANGES", "No updates provided.", 400)

    db.commit()
    db.refresh(test_case)

    write_audit(
        db,
        request.state.request_id,
        action="TEST_CASE_UPDATED",
        actor_user_id=str(user.id),
        entity_type="TestCase",
        entity_id=str(test_case.id),
        payload={"fields": updates},
    )
    return to_test_case_out(test_case)


@router.delete("/{test_case_id}", response_model=TestCaseOut)
def delete_test_case(
    test_case_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("test:update")),
) -> TestCaseOut:
    try:
        test_uuid = uuid.UUID(test_case_id)
    except ValueError:
        raise AppError("VALIDATION_ERROR", "Invalid test_case_id.", 400)
    test_case = db.query(TestCase).filter(TestCase.id == test_uuid).one_or_none()
    if not test_case:
        raise AppError("NOT_FOUND", "Test case not found.", 404)
    if test_case.deleted_at is None:
        test_case.deleted_at = datetime.utcnow()
        test_case.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(test_case)

    write_audit(
        db,
        request.state.request_id,
        action="TEST_CASE_DELETED",
        actor_user_id=str(user.id),
        entity_type="TestCase",
        entity_id=str(test_case.id),
    )
    return to_test_case_out(test_case)
