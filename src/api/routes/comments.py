from __future__ import annotations

from datetime import datetime
import uuid
from typing import List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from src.api.deps import get_db, require_permission
from src.api.schemas import CommentCreate, CommentOut, CommentUpdate
from src.db.models import Comment, Requirement, User
from src.services.audit import write_audit
from src.services.comments import (
    create_mention_notifications,
    extract_mentions,
    resolve_users_by_mentions,
    sync_comment_mentions,
)
from src.shared.errors import AppError

router = APIRouter(tags=["comments"])


def is_admin(user: User) -> bool:
    return any(role.name == "Admin" for role in user.roles)


def to_comment_out(comment: Comment) -> CommentOut:
    return CommentOut(
        id=str(comment.id),
        requirement_id=str(comment.requirement_id),
        author_user_id=str(comment.author_user_id),
        text=comment.text,
        created_at=comment.created_at,
        edited_at=comment.edited_at,
        deleted_at=comment.deleted_at,
    )


@router.get("/requirements/{req_id}/comments", response_model=List[CommentOut])
def list_comments(
    req_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("req:read")),
) -> List[CommentOut]:
    try:
        req_uuid = uuid.UUID(req_id)
    except ValueError:
        raise AppError("VALIDATION_ERROR", "Invalid requirement_id.", 400)
    requirement = db.query(Requirement).filter(Requirement.id == req_uuid).one_or_none()
    if not requirement:
        raise AppError("NOT_FOUND", "Requirement not found.", 404)
    comments = (
        db.query(Comment)
        .filter(Comment.requirement_id == req_id)
        .filter(Comment.deleted_at.is_(None))
        .order_by(Comment.created_at.asc())
        .all()
    )
    return [to_comment_out(comment) for comment in comments]


@router.post("/requirements/{req_id}/comments", response_model=CommentOut)
def create_comment(
    req_id: str,
    payload: CommentCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("req:comment:create")),
) -> CommentOut:
    try:
        req_uuid = uuid.UUID(req_id)
    except ValueError:
        raise AppError("VALIDATION_ERROR", "Invalid requirement_id.", 400)
    requirement = db.query(Requirement).filter(Requirement.id == req_uuid).one_or_none()
    if not requirement:
        raise AppError("NOT_FOUND", "Requirement not found.", 404)

    comment = Comment(
        requirement_id=req_uuid,
        author_user_id=user.id,
        text=payload.text,
        created_at=datetime.utcnow(),
    )
    db.add(comment)
    db.flush()

    emails, usernames = extract_mentions(payload.text)
    mentioned_users = resolve_users_by_mentions(db, emails, usernames)
    sync_comment_mentions(db, comment, mentioned_users)
    create_mention_notifications(db, comment, mentioned_users)

    db.commit()
    db.refresh(comment)

    write_audit(
        db,
        request.state.request_id,
        action="REQ_COMMENT_CREATED",
        actor_user_id=str(user.id),
        entity_type="Comment",
        entity_id=str(comment.id),
        payload={
            "requirement_id": str(req_id),
            "comment_id": str(comment.id),
            "mentions": sorted(emails),
        },
    )
    return to_comment_out(comment)


@router.patch("/comments/{comment_id}", response_model=CommentOut)
def update_comment(
    comment_id: str,
    payload: CommentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("req:comment:edit")),
) -> CommentOut:
    try:
        comment_uuid = uuid.UUID(comment_id)
    except ValueError:
        raise AppError("VALIDATION_ERROR", "Invalid comment_id.", 400)
    comment = db.query(Comment).filter(Comment.id == comment_uuid).one_or_none()
    if not comment or comment.deleted_at is not None:
        raise AppError("NOT_FOUND", "Comment not found.", 404)
    if comment.author_user_id != user.id and not is_admin(user):
        raise AppError("RBAC_FORBIDDEN", "Cannot edit another user's comment.", 403)

    previous_mentions = {mention.mentioned_user_id for mention in comment.mentions}

    comment.text = payload.text
    comment.edited_at = datetime.utcnow()

    emails, usernames = extract_mentions(payload.text)
    mentioned_users = resolve_users_by_mentions(db, emails, usernames)
    sync_comment_mentions(db, comment, mentioned_users)

    new_mentions = [user for user in mentioned_users if user.id not in previous_mentions]
    create_mention_notifications(db, comment, new_mentions)

    db.commit()
    db.refresh(comment)

    write_audit(
        db,
        request.state.request_id,
        action="REQ_COMMENT_EDITED",
        actor_user_id=str(user.id),
        entity_type="Comment",
        entity_id=str(comment.id),
        payload={
            "requirement_id": str(comment.requirement_id),
            "comment_id": str(comment.id),
            "mentions": sorted(emails),
        },
    )
    return to_comment_out(comment)


@router.delete("/comments/{comment_id}", response_model=CommentOut)
def delete_comment(
    comment_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("req:comment:delete")),
) -> CommentOut:
    try:
        comment_uuid = uuid.UUID(comment_id)
    except ValueError:
        raise AppError("VALIDATION_ERROR", "Invalid comment_id.", 400)
    comment = db.query(Comment).filter(Comment.id == comment_uuid).one_or_none()
    if not comment or comment.deleted_at is not None:
        raise AppError("NOT_FOUND", "Comment not found.", 404)
    if comment.author_user_id != user.id and not is_admin(user):
        raise AppError("RBAC_FORBIDDEN", "Cannot delete another user's comment.", 403)

    comment.deleted_at = datetime.utcnow()
    db.commit()
    db.refresh(comment)

    write_audit(
        db,
        request.state.request_id,
        action="REQ_COMMENT_DELETED",
        actor_user_id=str(user.id),
        entity_type="Comment",
        entity_id=str(comment.id),
        payload={
            "requirement_id": str(comment.requirement_id),
            "comment_id": str(comment.id),
        },
    )
    return to_comment_out(comment)
