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
from src.api.schemas import (
    ComplianceGapItem,
    ComplianceGapOut,
    ComplianceMappingCreate,
    ComplianceMappingOut,
    ComplianceReportOut,
    ComplianceRow,
    ComplianceValidationOut,
    StandardClauseCreate,
    StandardClauseOut,
    StandardCreate,
    StandardOut,
    UnmappedRequirementItem,
)
from src.db.models import BaselineItem, ComplianceMapping, Requirement, Standard, StandardClause, User
from src.services.audit import write_audit
from src.services.compliance import (
    build_compliance_rows,
    build_gap_analysis,
    upsert_compliance_mapping,
    validate_regulatory_mapping,
)
from src.shared.errors import AppError

router = APIRouter(tags=["compliance"])


def parse_uuid(value: str, field_name: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise AppError("VALIDATION_ERROR", f"Invalid {field_name}.", 400)


def to_standard_out(standard: Standard) -> StandardOut:
    return StandardOut(
        id=str(standard.id),
        code=standard.code,
        title=standard.title,
        version=standard.version,
        publication_year=standard.publication_year,
        publisher=standard.publisher,
        created_at=standard.created_at,
    )


def to_clause_out(clause: StandardClause) -> StandardClauseOut:
    return StandardClauseOut(
        id=str(clause.id),
        standard_id=str(clause.standard_id),
        clause_code=clause.clause_code,
        title=clause.title,
        text=clause.text,
        created_at=clause.created_at,
    )


def to_mapping_out(mapping: ComplianceMapping) -> ComplianceMappingOut:
    return ComplianceMappingOut(
        id=str(mapping.id),
        requirement_id=str(mapping.requirement_id),
        standard_clause_id=str(mapping.standard_clause_id),
        compliance_status=mapping.compliance_status,
        justification=mapping.justification,
        created_by_user_id=str(mapping.created_by_user_id),
        created_at=mapping.created_at,
    )


@router.post("/standards", response_model=StandardOut)
def create_standard(
    payload: StandardCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("standard:manage")),
) -> StandardOut:
    standard = Standard(
        code=payload.code,
        title=payload.title,
        version=payload.version,
        publication_year=payload.publication_year,
        publisher=payload.publisher,
        created_at=datetime.utcnow(),
    )
    db.add(standard)
    db.commit()
    db.refresh(standard)

    write_audit(
        db,
        request.state.request_id,
        action="STANDARD_CREATED",
        actor_user_id=str(user.id),
        entity_type="Standard",
        entity_id=str(standard.id),
        payload={"code": standard.code},
    )
    return to_standard_out(standard)


@router.get("/standards", response_model=List[StandardOut])
def list_standards(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("compliance:read")),
) -> List[StandardOut]:
    standards = db.query(Standard).order_by(Standard.created_at.desc()).all()
    return [to_standard_out(standard) for standard in standards]


@router.get("/standards/{standard_id}", response_model=StandardOut)
def get_standard(
    standard_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("compliance:read")),
) -> StandardOut:
    standard_uuid = parse_uuid(standard_id, "standard_id")
    standard = db.query(Standard).filter(Standard.id == standard_uuid).one_or_none()
    if not standard:
        raise AppError("NOT_FOUND", "Standard not found.", 404)
    return to_standard_out(standard)


@router.post("/standards/{standard_id}/clauses", response_model=StandardClauseOut)
def create_standard_clause(
    standard_id: str,
    payload: StandardClauseCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("standard:manage")),
) -> StandardClauseOut:
    standard_uuid = parse_uuid(standard_id, "standard_id")
    standard = db.query(Standard).filter(Standard.id == standard_uuid).one_or_none()
    if not standard:
        raise AppError("NOT_FOUND", "Standard not found.", 404)

    clause = StandardClause(
        standard_id=standard_uuid,
        clause_code=payload.clause_code,
        title=payload.title,
        text=payload.text,
        created_at=datetime.utcnow(),
    )
    db.add(clause)
    db.commit()
    db.refresh(clause)

    write_audit(
        db,
        request.state.request_id,
        action="STANDARD_CLAUSE_CREATED",
        actor_user_id=str(user.id),
        entity_type="StandardClause",
        entity_id=str(clause.id),
        payload={"standard_id": str(standard_uuid), "clause_code": clause.clause_code},
    )
    return to_clause_out(clause)


@router.get("/standards/{standard_id}/clauses", response_model=List[StandardClauseOut])
def list_standard_clauses(
    standard_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("compliance:read")),
) -> List[StandardClauseOut]:
    standard_uuid = parse_uuid(standard_id, "standard_id")
    clauses = (
        db.query(StandardClause)
        .filter(StandardClause.standard_id == standard_uuid)
        .order_by(StandardClause.clause_code.asc())
        .all()
    )
    return [to_clause_out(clause) for clause in clauses]


@router.post("/compliance-mappings", response_model=ComplianceMappingOut)
def create_compliance_mapping(
    payload: ComplianceMappingCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("compliance:map")),
) -> ComplianceMappingOut:
    requirement_uuid = parse_uuid(payload.requirement_id, "requirement_id")
    clause_uuid = parse_uuid(payload.standard_clause_id, "standard_clause_id")

    requirement = db.query(Requirement).filter(Requirement.id == requirement_uuid).one_or_none()
    if not requirement or requirement.deleted_at is not None:
        raise AppError("NOT_FOUND", "Requirement not found.", 404)

    clause = db.query(StandardClause).filter(StandardClause.id == clause_uuid).one_or_none()
    if not clause:
        raise AppError("NOT_FOUND", "Standard clause not found.", 404)

    mapping = upsert_compliance_mapping(
        db,
        requirement_id=str(requirement_uuid),
        standard_clause_id=str(clause_uuid),
        status=payload.compliance_status,
        justification=payload.justification,
        created_by_user_id=user.id,
    )

    write_audit(
        db,
        request.state.request_id,
        action="COMPLIANCE_MAPPED",
        actor_user_id=str(user.id),
        entity_type="ComplianceMapping",
        entity_id=str(mapping.id),
        payload={
            "requirement_id": str(requirement_uuid),
            "standard_clause_id": str(clause_uuid),
            "status": mapping.compliance_status,
        },
    )
    return to_mapping_out(mapping)


def build_report(
    db: Session,
    baseline_id: Optional[str],
    standard_id: Optional[str],
) -> ComplianceReportOut:
    requirement_ids: List[str] = []
    if baseline_id:
        baseline_uuid = parse_uuid(baseline_id, "baseline_id")
        items = db.query(BaselineItem).filter(BaselineItem.baseline_id == baseline_uuid).all()
        if not items:
            raise AppError("NOT_FOUND", "Baseline not found or empty.", 404)
        requirement_ids = [str(item.requirement_id) for item in items]
    else:
        requirement_ids = [str(req.id) for req in db.query(Requirement).filter(Requirement.deleted_at.is_(None)).all()]

    if standard_id:
        standard_uuid = parse_uuid(standard_id, "standard_id")
        clauses = (
            db.query(StandardClause)
            .filter(StandardClause.standard_id == standard_uuid)
            .all()
        )
        clause_ids = [str(clause.id) for clause in clauses]
    else:
        clauses = db.query(StandardClause).all()
        clause_ids = [str(clause.id) for clause in clauses]

    rows = build_compliance_rows(
        db,
        requirement_ids=requirement_ids,
        clause_ids=clause_ids,
        baseline_id=baseline_id,
        standard_id=standard_id,
    )

    gap_raw = build_gap_analysis(rows)
    missing_items = [
        ComplianceGapItem(
            requirement_id=row["requirement_id"],
            req_code=row.get("req_code"),
            standard_clause_id=row["standard_clause_id"],
            clause_code=row.get("clause_code"),
            compliance_status=row.get("compliance_status"),
        )
        for row in gap_raw["missing_mappings"]
    ]
    non_compliant_items = [
        ComplianceGapItem(
            requirement_id=row["requirement_id"],
            req_code=row.get("req_code"),
            standard_clause_id=row["standard_clause_id"],
            clause_code=row.get("clause_code"),
            compliance_status=row.get("compliance_status"),
        )
        for row in gap_raw["non_compliant"]
    ]

    return ComplianceReportOut(
        rows=[ComplianceRow(**row) for row in rows],
        gap_analysis=ComplianceGapOut(
            missing_mappings=missing_items,
            non_compliant=non_compliant_items,
        ),
    )


@router.get("/compliance", response_model=ComplianceReportOut)
def get_compliance_report(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("compliance:read")),
    baseline_id: Optional[str] = None,
    standard_id: Optional[str] = None,
) -> ComplianceReportOut:
    return build_report(db, baseline_id, standard_id)


@router.get("/compliance/export")
def export_compliance(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("compliance:export")),
    baseline_id: Optional[str] = None,
    standard_id: Optional[str] = None,
    format: str = Query("csv", pattern="^(csv|md|xlsx)$"),
):
    report = build_report(db, baseline_id, standard_id)
    rows = report.rows

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Baseline ID",
                "Standard ID",
                "Requirement ID",
                "Req Code",
                "Requirement Title",
                "Standard Clause ID",
                "Clause Code",
                "Clause Title",
                "Compliance Status",
                "Justification",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.baseline_id or "",
                    row.standard_id or "",
                    row.requirement_id,
                    row.req_code or "",
                    row.requirement_title or "",
                    row.standard_clause_id,
                    row.clause_code,
                    row.clause_title or "",
                    row.compliance_status,
                    row.justification or "",
                ]
            )
        return PlainTextResponse(output.getvalue(), media_type="text/csv")

    if format == "xlsx":
        output = io.StringIO()
        writer = csv.writer(output, delimiter="\t")
        writer.writerow(
            [
                "Baseline ID",
                "Standard ID",
                "Requirement ID",
                "Req Code",
                "Requirement Title",
                "Standard Clause ID",
                "Clause Code",
                "Clause Title",
                "Compliance Status",
                "Justification",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.baseline_id or "",
                    row.standard_id or "",
                    row.requirement_id,
                    row.req_code or "",
                    row.requirement_title or "",
                    row.standard_clause_id,
                    row.clause_code,
                    row.clause_title or "",
                    row.compliance_status,
                    row.justification or "",
                ]
            )
        return PlainTextResponse(
            output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    output = io.StringIO()
    output.write(
        "| Baseline ID | Standard ID | Requirement ID | Req Code | Requirement Title | "
        "Standard Clause ID | Clause Code | Clause Title | Compliance Status | Justification |\n"
    )
    output.write("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n")
    for row in rows:
        output.write(
            "| "
            + " | ".join(
                [
                    row.baseline_id or "",
                    row.standard_id or "",
                    row.requirement_id,
                    row.req_code or "",
                    row.requirement_title or "",
                    row.standard_clause_id,
                    row.clause_code,
                    row.clause_title or "",
                    row.compliance_status,
                    row.justification or "",
                ]
            )
            + " |\n"
        )
    return PlainTextResponse(output.getvalue(), media_type="text/markdown")


@router.get("/compliance/validate", response_model=ComplianceValidationOut)
def validate_compliance(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("compliance:read")),
    baseline_id: Optional[str] = None,
    project_id: Optional[str] = None,
) -> ComplianceValidationOut:
    """
    Validate that all regulatory requirements have at least one compliance mapping.
    When enforce_regulatory_mapping is enabled on the project, returns valid=false
    if any regulatory requirements are unmapped.
    """
    result = validate_regulatory_mapping(db, baseline_id, project_id)
    return ComplianceValidationOut(
        valid=result["valid"],
        enforce_regulatory_mapping=result["enforce_regulatory_mapping"],
        unmapped_regulatory_requirements=[
            UnmappedRequirementItem(
                id=item["id"],
                req_code=item["req_code"],
                title=item["title"],
            )
            for item in result["unmapped_regulatory_requirements"]
        ],
    )
