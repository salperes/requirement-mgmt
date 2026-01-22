from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from src.api.deps import get_db, require_permission
from src.api.schemas import ProjectCreate, ProjectOut, ProjectUpdate
from src.db.models import Project, User
from src.services.audit import write_audit
from src.shared.errors import AppError

router = APIRouter(tags=["projects"])


def to_project_out(project: Project) -> ProjectOut:
    return ProjectOut(
        id=str(project.id),
        name=project.name,
        description=project.description,
        enforce_regulatory_mapping=project.enforce_regulatory_mapping,
        created_by_user_id=str(project.created_by_user_id),
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post("/projects", response_model=ProjectOut)
def create_project(
    payload: ProjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("project:create")),
) -> ProjectOut:
    project = Project(
        name=payload.name,
        description=payload.description,
        enforce_regulatory_mapping=payload.enforce_regulatory_mapping,
        created_by_user_id=user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    write_audit(
        db,
        request.state.request_id,
        action="PROJECT_CREATED",
        actor_user_id=str(user.id),
        entity_type="Project",
        entity_id=str(project.id),
        payload={
            "name": project.name,
            "enforce_regulatory_mapping": project.enforce_regulatory_mapping,
        },
    )
    return to_project_out(project)


@router.get("/projects", response_model=List[ProjectOut])
def list_projects(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("project:read")),
) -> List[ProjectOut]:
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return [to_project_out(project) for project in projects]


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("project:read")),
) -> ProjectOut:
    import uuid

    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise AppError("VALIDATION_ERROR", "Invalid project_id.", 400)

    project = db.query(Project).filter(Project.id == project_uuid).one_or_none()
    if not project:
        raise AppError("NOT_FOUND", "Project not found.", 404)
    return to_project_out(project)


@router.patch("/projects/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("project:update")),
) -> ProjectOut:
    import uuid

    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise AppError("VALIDATION_ERROR", "Invalid project_id.", 400)

    project = db.query(Project).filter(Project.id == project_uuid).one_or_none()
    if not project:
        raise AppError("NOT_FOUND", "Project not found.", 404)

    changes = {}
    if payload.name is not None:
        changes["name"] = {"old": project.name, "new": payload.name}
        project.name = payload.name
    if payload.description is not None:
        changes["description"] = {"old": project.description, "new": payload.description}
        project.description = payload.description
    if payload.enforce_regulatory_mapping is not None:
        changes["enforce_regulatory_mapping"] = {
            "old": project.enforce_regulatory_mapping,
            "new": payload.enforce_regulatory_mapping,
        }
        project.enforce_regulatory_mapping = payload.enforce_regulatory_mapping

    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)

    write_audit(
        db,
        request.state.request_id,
        action="PROJECT_UPDATED",
        actor_user_id=str(user.id),
        entity_type="Project",
        entity_id=str(project.id),
        payload=changes,
    )
    return to_project_out(project)
