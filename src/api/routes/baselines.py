from __future__ import annotations

import csv
import io
import uuid
from typing import List, Literal

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from src.api.deps import get_db, require_permission
from src.api.schemas import BaselineCreate, BaselineItemOut, BaselineOut
from src.db.models import Baseline, BaselineItem, Requirement, User
from src.services.audit import write_audit
from src.services.baselines import create_baseline_items, generate_baseline_tag, get_latest_versions
from src.shared.errors import AppError

router = APIRouter(prefix="/baselines", tags=["baselines"])


def to_baseline_out(baseline: Baseline) -> BaselineOut:
    return BaselineOut(
        id=str(baseline.id),
        baseline_tag=baseline.baseline_tag,
        name=baseline.name,
        description=baseline.description,
        created_by_user_id=str(baseline.created_by_user_id),
        created_at=baseline.created_at,
    )


@router.post("", response_model=BaselineOut)
def create_baseline(
    payload: BaselineCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("baseline:create")),
) -> BaselineOut:
    unique_ids = []
    for req_id in dict.fromkeys(payload.requirement_ids):
        try:
            unique_ids.append(uuid.UUID(req_id))
        except ValueError:
            raise AppError("VALIDATION_ERROR", "Invalid requirement_id.", 400)
    requirements = (
        db.query(Requirement)
        .filter(Requirement.id.in_(unique_ids))
        .filter(Requirement.deleted_at.is_(None))
        .all()
    )
    if len(requirements) != len(unique_ids):
        raise AppError("NOT_FOUND", "One or more requirements not found.", 404)

    baseline = Baseline(
        baseline_tag=generate_baseline_tag(db),
        name=payload.name,
        description=payload.description,
        created_by_user_id=user.id,
    )
    db.add(baseline)
    db.flush()

    versions = get_latest_versions(db, unique_ids)
    if len(versions) != len(unique_ids):
        raise AppError("NOT_FOUND", "Missing requirement versions.", 404)

    create_baseline_items(db, baseline, unique_ids, versions)
    db.commit()
    db.refresh(baseline)

    write_audit(
        db,
        request.state.request_id,
        action="BASELINE_CREATED",
        actor_user_id=str(user.id),
        entity_type="Baseline",
        entity_id=str(baseline.id),
        payload={"baseline_tag": baseline.baseline_tag, "requirements": [str(req_id) for req_id in unique_ids]},
    )
    return to_baseline_out(baseline)


@router.get("", response_model=List[BaselineOut])
def list_baselines(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("baseline:read")),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
) -> List[BaselineOut]:
    offset = (page - 1) * page_size
    baselines = (
        db.query(Baseline)
        .order_by(Baseline.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return [to_baseline_out(baseline) for baseline in baselines]


@router.get("/{baseline_id}", response_model=BaselineOut)
def get_baseline(
    baseline_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("baseline:read")),
) -> BaselineOut:
    try:
        baseline_uuid = uuid.UUID(baseline_id)
    except ValueError:
        raise AppError("VALIDATION_ERROR", "Invalid baseline_id.", 400)
    baseline = db.query(Baseline).filter(Baseline.id == baseline_uuid).one_or_none()
    if not baseline:
        raise AppError("NOT_FOUND", "Baseline not found.", 404)
    return to_baseline_out(baseline)


@router.get("/{baseline_id}/items", response_model=List[BaselineItemOut])
def list_baseline_items(
    baseline_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("baseline:read")),
) -> List[BaselineItemOut]:
    try:
        baseline_uuid = uuid.UUID(baseline_id)
    except ValueError:
        raise AppError("VALIDATION_ERROR", "Invalid baseline_id.", 400)
    items = db.query(BaselineItem).filter(BaselineItem.baseline_id == baseline_uuid).all()
    return [
        BaselineItemOut(
            baseline_id=str(item.baseline_id),
            requirement_id=str(item.requirement_id),
            requirement_version_id=str(item.requirement_version_id),
            version_no=item.requirement_version.version_no,
            snapshot_json=item.requirement_version.snapshot_json,
        )
        for item in items
    ]


@router.get("/{baseline_id}/export")
def export_baseline(
    baseline_id: str,
    request: Request,
    format: Literal["md", "csv"] = "md",
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("baseline:export")),
):
    try:
        baseline_uuid = uuid.UUID(baseline_id)
    except ValueError:
        raise AppError("VALIDATION_ERROR", "Invalid baseline_id.", 400)
    baseline = db.query(Baseline).filter(Baseline.id == baseline_uuid).one_or_none()
    if not baseline:
        raise AppError("NOT_FOUND", "Baseline not found.", 404)

    items = db.query(BaselineItem).filter(BaselineItem.baseline_id == baseline_uuid).all()

    rows = []
    for item in items:
        version = item.requirement_version
        snapshot = version.snapshot_json or {}
        rows.append(
            {
                "baseline_tag": baseline.baseline_tag,
                "req_code": snapshot.get("req_code"),
                "title": snapshot.get("title"),
                "text": snapshot.get("text"),
                "discipline": snapshot.get("discipline"),
                "req_type_primary": snapshot.get("req_type_primary"),
                "status": snapshot.get("status"),
                "owner_user_id": snapshot.get("owner_user_id"),
                "version_no": version.version_no,
            }
        )

    write_audit(
        db,
        request_id=request.state.request_id,
        action="BASELINE_EXPORTED",
        actor_user_id=str(user.id),
        entity_type="Baseline",
        entity_id=str(baseline.id),
        payload={"baseline_tag": baseline.baseline_tag, "format": format},
    )

    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "baseline_tag",
                "req_code",
                "title",
                "text",
                "discipline",
                "req_type_primary",
                "status",
                "owner_user_id",
                "version_no",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
        return PlainTextResponse(output.getvalue(), media_type="text/csv")

    markdown = io.StringIO()
    markdown.write(f"# Baseline {baseline.baseline_tag}\n\n")
    markdown.write(f"Name: {baseline.name}\n\n")
    markdown.write("| Req Code | Title | Discipline | Type | Status | Owner | Version |\n")
    markdown.write("| --- | --- | --- | --- | --- | --- | --- |\n")
    for row in rows:
        markdown.write(
            f"| {row.get('req_code','')} | {row.get('title','')} | {row.get('discipline','')} | "
            f"{row.get('req_type_primary','')} | {row.get('status','')} | {row.get('owner_user_id','')} | "
            f"{row.get('version_no','')} |\n"
        )
    return PlainTextResponse(markdown.getvalue(), media_type="text/markdown")
