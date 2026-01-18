# Collaboration: Comments & Mentions (Module-2)

## Comment Model
- A comment belongs to a Requirement.
- Edits are allowed but must be audited.
- Deletes are soft deletes.

## Mention Syntax (MVP)
- Recognize `@email` (contains @ + domain), or `@username` mapped to a user.
- On comment creation, parse mentions and create notifications for mentioned users.

## Audit Events
- `REQ_COMMENT_CREATED`
- `REQ_COMMENT_EDITED`
- `REQ_COMMENT_DELETED`
Payload includes:
- requirement_id, comment_id, mention list
