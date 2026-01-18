# Migrations Plan — Module-2

## 0003_workflow_collaboration
Creates:
- comments
- comment_mentions
- notifications
- approval_records

Adds:
- indexes as defined in db_schema_module2.md

Notes:
- comments are soft-deleted (deleted_at)
- approval_records are immutable (no update/delete endpoints)
