# Release Notes — Module-0

Date: 2026-01-18

## Highlights
- FastAPI service skeleton with health check.
- Local auth (JWT), RBAC permissions, and admin user management.
- Immutable audit logging for critical actions.
- Alembic migrations and dev seed users.
- Dockerized runtime with Postgres.

## API (Module-0)
- `GET /health`
- `POST /auth/login`, `GET /auth/me`
- Admin: `GET /admin/users`, `POST /admin/users`, `PATCH /admin/users/{id}`, `PUT /admin/users/{id}/roles`, `GET /admin/audit`

## Database
- Core tables: `users`, `roles`, `user_roles`, `audit_log`.
- Migration: `0001_init`.

## Operational Notes
- Docker entrypoint runs migrations and seeds dev users.
- Default dev password can be set with `RMS_DEV_PASSWORD`.

## Known TODOs (tracked in roadmap)
- Audit immutability (DB-level guardrails).
- Audit payload schema standardization.
- Document Alembic migration metadata.
- Production env var documentation.
- Optional logout behavior decision.