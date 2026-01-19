from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple, Union
import uuid

from sqlalchemy.orm import Session

from src.db.models import ComplianceMapping, Requirement, StandardClause


def ensure_uuid(value: Union[str, uuid.UUID]) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def latest_mappings_for_pairs(
    session: Session,
    requirement_ids: Iterable[str],
    clause_ids: Iterable[str],
) -> Dict[Tuple[str, str], ComplianceMapping]:
    req_ids = [ensure_uuid(rid) for rid in requirement_ids]
    cl_ids = [ensure_uuid(cid) for cid in clause_ids]
    if not req_ids or not cl_ids:
        return {}

    mappings = (
        session.query(ComplianceMapping)
        .filter(ComplianceMapping.requirement_id.in_(req_ids))
        .filter(ComplianceMapping.standard_clause_id.in_(cl_ids))
        .order_by(ComplianceMapping.created_at.desc())
        .all()
    )
    latest: Dict[Tuple[str, str], ComplianceMapping] = {}
    for mapping in mappings:
        key = (str(mapping.requirement_id), str(mapping.standard_clause_id))
        if key not in latest:
            latest[key] = mapping
    return latest


def build_compliance_rows(
    session: Session,
    requirement_ids: Iterable[str],
    clause_ids: Iterable[str],
    baseline_id: Optional[str],
    standard_id: Optional[str],
) -> List[dict]:
    requirement_ids = [ensure_uuid(rid) for rid in requirement_ids]
    clause_ids = [ensure_uuid(cid) for cid in clause_ids]

    requirements = (
        session.query(Requirement)
        .filter(Requirement.id.in_(requirement_ids))
        .filter(Requirement.deleted_at.is_(None))
        .all()
    ) if requirement_ids else []
    clauses = (
        session.query(StandardClause)
        .filter(StandardClause.id.in_(clause_ids))
        .all()
    ) if clause_ids else []

    requirement_map = {str(req.id): req for req in requirements}
    clause_map = {str(clause.id): clause for clause in clauses}

    mapping_lookup = latest_mappings_for_pairs(session, requirement_ids, clause_ids)

    rows: List[dict] = []
    for req_id in requirement_ids:
        req = requirement_map.get(str(req_id))
        if not req:
            continue
        for clause_id in clause_ids:
            clause = clause_map.get(str(clause_id))
            if not clause:
                continue
            key = (str(req.id), str(clause.id))
            mapping = mapping_lookup.get(key)
            rows.append(
                {
                    "baseline_id": baseline_id,
                    "standard_id": standard_id or str(clause.standard_id),
                    "requirement_id": str(req.id),
                    "req_code": req.req_code,
                    "requirement_title": req.title,
                    "standard_clause_id": str(clause.id),
                    "clause_code": clause.clause_code,
                    "clause_title": clause.title,
                    "compliance_status": mapping.compliance_status if mapping else "UNMAPPED",
                    "justification": mapping.justification if mapping else None,
                }
            )
    return rows


def build_gap_analysis(rows: List[dict]) -> dict:
    missing = []
    non_compliant = []
    for row in rows:
        status = row.get("compliance_status")
        if status == "UNMAPPED":
            missing.append(row)
        elif status != "COMPLIANT":
            non_compliant.append(row)
    return {"missing_mappings": missing, "non_compliant": non_compliant}


def upsert_compliance_mapping(
    session: Session,
    requirement_id: str,
    standard_clause_id: str,
    status: str,
    justification: Optional[str],
    created_by_user_id: uuid.UUID,
) -> ComplianceMapping:
    req_id = ensure_uuid(requirement_id)
    clause_id = ensure_uuid(standard_clause_id)
    mapping = (
        session.query(ComplianceMapping)
        .filter(ComplianceMapping.requirement_id == req_id)
        .filter(ComplianceMapping.standard_clause_id == clause_id)
        .one_or_none()
    )
    if mapping:
        mapping.compliance_status = status
        mapping.justification = justification
        mapping.created_by_user_id = created_by_user_id
        mapping.created_at = datetime.utcnow()
        session.commit()
        session.refresh(mapping)
        return mapping

    mapping = ComplianceMapping(
        requirement_id=req_id,
        standard_clause_id=clause_id,
        compliance_status=status,
        justification=justification,
        created_by_user_id=created_by_user_id,
        created_at=datetime.utcnow(),
    )
    session.add(mapping)
    session.commit()
    session.refresh(mapping)
    return mapping
