from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from src.api.deps import get_db, require_permission
from src.api.schemas import ImpactOut, ImpactItem, LinkCreate, LinkOut, RTMRow
from src.db.models import BaselineItem, Link, Requirement, Suspect, User
from src.services.audit import write_audit
from src.services.traceability import (
    build_downstream_paths,
    build_rtm_rows,
    detect_derives_cycle,
    ensure_requirement_exists,
    find_links,
    set_suspects_from_requirement,
    validate_link_payload,
)
from src.shared.errors import AppError

router = APIRouter(tags=["traceability"])


def to_link_out(link: Link) -> LinkOut:
    return LinkOut(
        id=str(link.id),
        source_type=link.source_type,
        source_id=link.source_id,
        target_type=link.target_type,
        target_id=link.target_id,
        link_type=link.link_type,
        created_by_user_id=str(link.created_by_user_id),
        created_at=link.created_at,
        deleted_at=link.deleted_at,
    )


@router.post("/links", response_model=LinkOut)
def create_link(
    payload: LinkCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("trace:link:create")),
) -> LinkOut:
    error = validate_link_payload(
        payload.source_type,
        payload.source_id,
        payload.target_type,
        payload.target_id,
        payload.link_type,
    )
    if error:
        raise AppError("VALIDATION_ERROR", error, 400)

    if payload.source_type == "Requirement" and not ensure_requirement_exists(db, payload.source_id):
        raise AppError("NOT_FOUND", "Requirement not found.", 404)

    if payload.link_type == "DERIVES" and detect_derives_cycle(db, payload.source_id, payload.target_id):
        raise AppError("VALIDATION_ERROR", "DERIVES link would create a cycle.", 400)

    existing = (
        db.query(Link)
        .filter(Link.deleted_at.is_(None))
        .filter(Link.source_type == payload.source_type)
        .filter(Link.source_id == payload.source_id)
        .filter(Link.target_type == payload.target_type)
        .filter(Link.target_id == payload.target_id)
        .filter(Link.link_type == payload.link_type)
        .one_or_none()
    )
    if existing:
        return to_link_out(existing)

    link = Link(
        source_type=payload.source_type,
        source_id=payload.source_id,
        target_type=payload.target_type,
        target_id=payload.target_id,
        link_type=payload.link_type,
        created_by_user_id=user.id,
        created_at=datetime.utcnow(),
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    write_audit(
        db,
        request.state.request_id,
        action="TRACE_LINK_CREATED",
        actor_user_id=str(user.id),
        entity_type="Link",
        entity_id=str(link.id),
        payload={
            "source_type": link.source_type,
            "source_id": link.source_id,
            "target_type": link.target_type,
            "target_id": link.target_id,
            "link_type": link.link_type,
        },
    )

    requirement_id = None
    if link.source_type == "Requirement":
        requirement_id = link.source_id
    elif link.target_type == "Requirement":
        requirement_id = link.target_id
    if requirement_id:
        impacts = set_suspects_from_requirement(db, requirement_id, "link_change")
        for entity_type, entity_id, path in impacts:
            write_audit(
                db,
                request.state.request_id,
                action="TRACE_SUSPECT_SET",
                actor_user_id=str(user.id),
                entity_type=entity_type,
                entity_id=entity_id,
                payload={"path": path, "reason": "link_change"},
            )

    return to_link_out(link)


@router.delete("/links/{link_id}", response_model=LinkOut)
def delete_link(
    link_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("trace:link:delete")),
) -> LinkOut:
    link = db.query(Link).filter(Link.id == link_id).one_or_none()
    if not link:
        raise AppError("NOT_FOUND", "Link not found.", 404)
    if link.deleted_at is None:
        link.deleted_at = datetime.utcnow()
        db.commit()
        db.refresh(link)

    write_audit(
        db,
        request.state.request_id,
        action="TRACE_LINK_DELETED",
        actor_user_id=str(user.id),
        entity_type="Link",
        entity_id=str(link.id),
        payload={"link_type": link.link_type},
    )

    requirement_id = None
    if link.source_type == "Requirement":
        requirement_id = link.source_id
    elif link.target_type == "Requirement":
        requirement_id = link.target_id
    if requirement_id:
        impacts = set_suspects_from_requirement(db, requirement_id, "link_delete")
        for entity_type, entity_id, path in impacts:
            write_audit(
                db,
                request.state.request_id,
                action="TRACE_SUSPECT_SET",
                actor_user_id=str(user.id),
                entity_type=entity_type,
                entity_id=entity_id,
                payload={"path": path, "reason": "link_delete"},
            )

    return to_link_out(link)


@router.get("/links", response_model=List[LinkOut])
def list_links(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("trace:link:read")),
    source_type: Optional[str] = None,
    source_id: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    link_type: Optional[str] = None,
) -> List[LinkOut]:
    links = find_links(db, source_type, source_id, target_type, target_id, link_type)
    return [to_link_out(link) for link in links]


@router.get("/rtm")
def get_rtm(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("trace:rtm:read")),
    baseline_id: Optional[str] = None,
    format: str = Query("json", pattern="^(json|csv|md)$"),
):
    requirement_ids: List[str] = []
    snapshots: dict[str, dict] = {}

    if baseline_id:
        try:
            baseline_uuid = uuid.UUID(baseline_id)
        except ValueError:
            raise AppError("VALIDATION_ERROR", "Invalid baseline_id.", 400)
        items = db.query(BaselineItem).filter(BaselineItem.baseline_id == baseline_uuid).all()
        if not items:
            raise AppError("NOT_FOUND", "Baseline not found or empty.", 404)
        for item in items:
            requirement_ids.append(str(item.requirement_id))
            snapshots[str(item.requirement_id)] = item.requirement_version.snapshot_json or {}
    else:
        requirements = db.query(Requirement).filter(Requirement.deleted_at.is_(None)).all()
        for req in requirements:
            requirement_ids.append(str(req.id))
            snapshots[str(req.id)] = {
                "req_code": req.req_code,
                "title": req.title,
                "discipline": req.discipline,
                "req_type_primary": req.req_type_primary,
            }

    rows = build_rtm_rows(db, requirement_ids, snapshots)

    if format == "json":
        return [RTMRow(**row) for row in rows]

    output = io.StringIO()
    if format == "csv":
        writer = csv.writer(output)
        writer.writerow(
            [
                "Req Code",
                "Requirement Title",
                "Discipline",
                "Type",
                "Design Artifact ID",
                "Test Case ID",
                "Standard Clause ID",
                "Suspect Flag",
                "Coverage Status",
                "Verification Status",
                "Suspect Auto-Cleared",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row["req_code"] or "",
                    row["requirement_title"] or "",
                    row["discipline"] or "",
                    row["req_type_primary"] or "",
                    ",".join(row["design_artifact_ids"]),
                    ",".join(row["test_case_ids"]),
                    ",".join(row["standard_clause_ids"]),
                    str(row["suspect"]),
                    row["coverage_status"],
                    row["verification_status"],
                    str(row["suspect_auto_cleared"]),
                ]
            )
        return PlainTextResponse(output.getvalue(), media_type="text/csv")

    output.write(
        "| Req Code | Requirement Title | Discipline | Type | Design Artifact ID | Test Case ID | "
        "Standard Clause ID | Suspect Flag | Coverage Status | Verification Status | Suspect Auto-Cleared |\n"
    )
    output.write("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n")
    for row in rows:
        output.write(
            "| "
            + " | ".join(
                [
                    row["req_code"] or "",
                    row["requirement_title"] or "",
                    row["discipline"] or "",
                    row["req_type_primary"] or "",
                    ",".join(row["design_artifact_ids"]),
                    ",".join(row["test_case_ids"]),
                    ",".join(row["standard_clause_ids"]),
                    str(row["suspect"]),
                    row["coverage_status"],
                    row["verification_status"],
                    str(row["suspect_auto_cleared"]),
                ]
            )
            + " |\n"
        )
    return PlainTextResponse(output.getvalue(), media_type="text/markdown")


@router.get("/requirements/{req_id}/impact", response_model=ImpactOut)
def get_impact(
    req_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("trace:impact:read")),
) -> ImpactOut:
    try:
        req_uuid = uuid.UUID(req_id)
    except ValueError:
        raise AppError("VALIDATION_ERROR", "Invalid requirement_id.", 400)
    requirement = db.query(Requirement).filter(Requirement.id == req_uuid).one_or_none()
    if not requirement:
        raise AppError("NOT_FOUND", "Requirement not found.", 404)
    impacts = build_downstream_paths(db, req_id)
    impacted = [
        ImpactItem(entity_type=entity_type, entity_id=entity_id, path=path)
        for entity_type, entity_id, path in impacts
    ]
    return ImpactOut(requirement_id=req_id, impacted=impacted)


@router.post("/suspect/{entity_type}/{entity_id}/clear")
def clear_suspect(
    entity_type: str,
    entity_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("trace:suspect:clear")),
):
    suspect = (
        db.query(Suspect)
        .filter(Suspect.entity_type == entity_type)
        .filter(Suspect.entity_id == entity_id)
        .one_or_none()
    )
    if not suspect:
        raise AppError("NOT_FOUND", "Suspect not found.", 404)
    db.delete(suspect)
    db.commit()

    write_audit(
        db,
        request.state.request_id,
        action="TRACE_SUSPECT_CLEARED",
        actor_user_id=str(user.id),
        entity_type=entity_type,
        entity_id=entity_id,
    )
    return {"status": "cleared"}
