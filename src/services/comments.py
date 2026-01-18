from __future__ import annotations

import re
from typing import Iterable, List, Set, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.db.models import Comment, CommentMention, Notification, User


EMAIL_MENTION_RE = re.compile(r"@([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})")
USERNAME_MENTION_RE = re.compile(r"@([A-Za-z0-9._-]{2,32})")


def extract_mentions(text: str) -> Tuple[Set[str], Set[str]]:
    emails = {match.group(1) for match in EMAIL_MENTION_RE.finditer(text)}
    scrubbed = EMAIL_MENTION_RE.sub(" ", text)
    usernames = {match.group(1) for match in USERNAME_MENTION_RE.finditer(scrubbed)}
    return emails, usernames


def resolve_users_by_mentions(session: Session, emails: Iterable[str], usernames: Iterable[str]) -> List[User]:
    users: dict[str, User] = {}
    email_list = list(emails)
    if email_list:
        for user in session.query(User).filter(User.email.in_(email_list)).all():
            users[str(user.id)] = user

    for username in usernames:
        lowered = username.lower()
        user = (
            session.query(User)
            .filter(func.lower(User.display_name) == lowered)
            .one_or_none()
        )
        if not user:
            user = (
                session.query(User)
                .filter(func.lower(User.email).like(f"{lowered}@%"))
                .one_or_none()
            )
        if user:
            users[str(user.id)] = user
    return list(users.values())


def sync_comment_mentions(
    session: Session,
    comment: Comment,
    mentioned_users: Iterable[User],
) -> List[User]:
    mentioned_list = list(mentioned_users)
    mentioned_ids = {user.id for user in mentioned_list}

    existing_mentions = list(comment.mentions)
    existing_ids = {mention.mentioned_user_id for mention in existing_mentions}

    for mention in existing_mentions:
        if mention.mentioned_user_id not in mentioned_ids:
            session.delete(mention)

    for user in mentioned_list:
        if user.id not in existing_ids:
            session.add(CommentMention(comment_id=comment.id, mentioned_user_id=user.id))

    return mentioned_list


def create_mention_notifications(
    session: Session,
    comment: Comment,
    mentioned_users: Iterable[User],
) -> None:
    for user in mentioned_users:
        if user.id == comment.author_user_id:
            continue
        notification = Notification(
            user_id=user.id,
            type="MENTION",
            title="Mentioned in requirement comment",
            body=comment.text,
            entity_type="Comment",
            entity_id=str(comment.id),
            is_read=False,
        )
        session.add(notification)
