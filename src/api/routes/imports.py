from __future__ import annotations

from datetime import datetime
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.orm import Session

from src.api.deps import get_db, require_permission
from src.api.schemas import ClauseAcceptRequest, ImportSessionOut, ImportedClauseOut, RequirementOut
from src.db.models import ImportSession, ImportedClause, Requirement, SourceReference, User
from src.services.audit import write_audit
from src.services.imports import infer_file_type, segment_clauses
from src.services.requirements import create_requirement_version, generate_req_code
from src.shared.errors import AppError

router = APIRouter(prefix="/imports", tags=["imports"])


def to_import_session_out(session: ImportSession) -> ImportSessionOut:
    return ImportSessionOut(
        id=str(session.id),
        file_name=session.file_name,
        file_type=session.file_type,
        uploaded_by_user_id=str(session.uploaded_by_user_id),
        uploaded_at=session.uploaded_at,
        status=session.status,
    )


def to_clause_out(clause: ImportedClause) -> ImportedClauseOut:
    return ImportedClauseOut(
        id=str(clause.id),
        import_session_id=str(clause.import_session_id),
        raw_text=clause.raw_text,
        location_ref=clause.location_ref,
        clause_index=clause.clause_index,
        parsed_metadata=clause.parsed_metadata or {},
        created_at=clause.created_at,
    )


def to_requirement_out(req: Requirement) -> RequirementOut:
    return RequirementOut(
        id=str(req.id),
        req_code=req.req_code,
        title=req.title,
        text=req.text,
        discipline=req.discipline,
        req_type_primary=req.req_type_primary,
        req_type_secondary=req.req_type_secondary,
        is_explanation=req.is_explanation,
        status=req.status,
        owner_user_id=str(req.owner_user_id),
        source=req.source,
        created_at=req.created_at,
        updated_at=req.updated_at,
        deleted_at=req.deleted_at,
    )


def parse_uuid(value: str, field_name: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise AppError("VALIDATION_ERROR", f"Invalid {field_name}.", 400)


@router.post("", response_model=ImportSessionOut)
def create_import_session(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("import:upload")),
) -> ImportSessionOut:
    file_type = infer_file_type(file.filename)
    if not file_type:
        raise AppError("VALIDATION_ERROR", "Unsupported file type.", 400)

    session = ImportSession(
        file_name=file.filename or "upload",
        file_type=file_type,
        uploaded_by_user_id=user.id,
        uploaded_at=datetime.utcnow(),
        status="IN_PROGRESS",
    )
    db.add(session)
    db.flush()

    try:
        raw_bytes = file.file.read()
        text = raw_bytes.decode("utf-8", errors="ignore")
        clauses = segment_clauses(text, file_type)
        for clause in clauses:
            record = ImportedClause(
                import_session_id=session.id,
                raw_text=clause["raw_text"],
                location_ref=clause["location_ref"],
                clause_index=clause["clause_index"],
                parsed_metadata=clause["parsed_metadata"],
                created_at=datetime.utcnow(),
            )
            db.add(record)
        session.status = "COMPLETED"
    except Exception as exc:
        session.status = "FAILED"
        db.commit()
        raise AppError("IMPORT_FAILED", "Import processing failed.", 400) from exc

    db.commit()
    db.refresh(session)

    write_audit(
        db,
        request.state.request_id,
        action="IMPORT_SESSION_CREATED",
        actor_user_id=str(user.id),
        entity_type="ImportSession",
        entity_id=str(session.id),
        payload={"file_name": session.file_name, "file_type": session.file_type},
    )

    return to_import_session_out(session)


@router.get("", response_model=List[ImportSessionOut])
def list_import_sessions(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("import:read")),
) -> List[ImportSessionOut]:
    sessions = db.query(ImportSession).order_by(ImportSession.uploaded_at.desc()).all()
    return [to_import_session_out(session) for session in sessions]


@router.get("/{import_id}", response_model=ImportSessionOut)
def get_import_session(
    import_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("import:read")),
) -> ImportSessionOut:
    session_id = parse_uuid(import_id, "import_id")
    session = db.query(ImportSession).filter(ImportSession.id == session_id).one_or_none()
    if not session:
        raise AppError("NOT_FOUND", "Import session not found.", 404)
    return to_import_session_out(session)


@router.get("/{import_id}/clauses", response_model=List[ImportedClauseOut])
def list_import_clauses(
    import_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("import:read")),
) -> List[ImportedClauseOut]:
    session_id = parse_uuid(import_id, "import_id")
    session = db.query(ImportSession).filter(ImportSession.id == session_id).one_or_none()
    if not session:
        raise AppError("NOT_FOUND", "Import session not found.", 404)
    clauses = (
        db.query(ImportedClause)
        .filter(ImportedClause.import_session_id == session_id)
        .order_by(ImportedClause.clause_index.asc())
        .all()
    )
    return [to_clause_out(clause) for clause in clauses]


@router.post("/{import_id}/clauses/{clause_id}/accept", response_model=RequirementOut)
def accept_imported_clause(
    import_id: str,
    clause_id: str,
    payload: ClauseAcceptRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("import:review")),
) -> RequirementOut:
    session_id = parse_uuid(import_id, "import_id")
    clause_uuid = parse_uuid(clause_id, "clause_id")

    clause = (
        db.query(ImportedClause)
        .filter(ImportedClause.id == clause_uuid)
        .filter(ImportedClause.import_session_id == session_id)
        .one_or_none()
    )
    if not clause:
        raise AppError("NOT_FOUND", "Imported clause not found.", 404)

    metadata = dict(clause.parsed_metadata or {})
    decision = metadata.get("decision")
    if decision == "ACCEPTED":
        requirement_id = metadata.get("requirement_id")
        if requirement_id:
            try:
                requirement_uuid = uuid.UUID(str(requirement_id))
            except ValueError:
                requirement_uuid = requirement_id
            existing = db.query(Requirement).filter(Requirement.id == requirement_uuid).one_or_none()
            if existing:
                return to_requirement_out(existing)
    if decision == "REJECTED":
        raise AppError("VALIDATION_ERROR", "Clause already rejected.", 400)

    owner_user_id = user.id
    if payload.owner_user_id:
        owner_user_id = parse_uuid(payload.owner_user_id, "owner_user_id")

    requirement = Requirement(
        req_code=generate_req_code(db),
        title=payload.title,
        text=clause.raw_text,
        discipline=payload.discipline or "Other",
        req_type_primary=payload.req_type_primary or "Functional",
        req_type_secondary=payload.req_type_secondary,
        is_explanation=payload.is_explanation,
        status=payload.status,
        owner_user_id=owner_user_id,
        source="import",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(requirement)
    db.flush()

    create_requirement_version(db, requirement, user.id, change_reason="import_accept")

    source_ref = SourceReference(
        requirement_id=requirement.id,
        import_session_id=session_id,
        imported_clause_id=clause.id,
        created_at=datetime.utcnow(),
    )
    db.add(source_ref)

    metadata.update(
        {
            "decision": "ACCEPTED",
            "requirement_id": str(requirement.id),
            "reviewed_by_user_id": str(user.id),
            "reviewed_at": datetime.utcnow().isoformat(),
        }
    )
    clause.parsed_metadata = metadata

    db.commit()
    db.refresh(requirement)

    write_audit(
        db,
        request.state.request_id,
        action="IMPORT_CLAUSE_ACCEPTED",
        actor_user_id=str(user.id),
        entity_type="ImportedClause",
        entity_id=str(clause.id),
        payload={"requirement_id": str(requirement.id)},
    )
    write_audit(
        db,
        request.state.request_id,
        action="SOURCE_REFERENCE_CREATED",
        actor_user_id=str(user.id),
        entity_type="SourceReference",
        entity_id=str(source_ref.id),
        payload={"requirement_id": str(requirement.id)},
    )

    return to_requirement_out(requirement)


@router.post("/{import_id}/clauses/{clause_id}/reject", response_model=ImportedClauseOut)
def reject_imported_clause(
    import_id: str,
    clause_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("import:review")),
) -> ImportedClauseOut:
    session_id = parse_uuid(import_id, "import_id")
    clause_uuid = parse_uuid(clause_id, "clause_id")

    clause = (
        db.query(ImportedClause)
        .filter(ImportedClause.id == clause_uuid)
        .filter(ImportedClause.import_session_id == session_id)
        .one_or_none()
    )
    if not clause:
        raise AppError("NOT_FOUND", "Imported clause not found.", 404)

    metadata = dict(clause.parsed_metadata or {})
    decision = metadata.get("decision")
    if decision == "ACCEPTED":
        raise AppError("VALIDATION_ERROR", "Clause already accepted.", 400)

    metadata.update(
        {
            "decision": "REJECTED",
            "reviewed_by_user_id": str(user.id),
            "reviewed_at": datetime.utcnow().isoformat(),
        }
    )
    clause.parsed_metadata = metadata
    db.commit()

    write_audit(
        db,
        request.state.request_id,
        action="IMPORT_CLAUSE_REJECTED",
        actor_user_id=str(user.id),
        entity_type="ImportedClause",
        entity_id=str(clause.id),
    )

    return to_clause_out(clause)
