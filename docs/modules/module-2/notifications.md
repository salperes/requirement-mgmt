# Notifications (Module-2, MVP)

## Purpose
Provide an in-app notification inbox. No external delivery yet.

## Notification Types
- MENTION: user mentioned in a comment
- WORKFLOW: requirement status changed (Draft/Review transitions)
- APPROVAL: requirement approved/rejected

## Read Model
- Stored in DB and fetched by the user.
- Mark-as-read supported.
- Inbox sorts unread first, then newest.
