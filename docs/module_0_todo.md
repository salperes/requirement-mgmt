# Module-0 TODO

## Audit Immutability (Phase: post Module-1)
- Add DB-level guardrails to prevent updates/deletes on `audit_log` (trigger or permissions).

## Audit Payload Standard (Phase: post Module-1)
- Define a consistent audit payload schema (required keys per action).

## Auth Logout (Optional) (Phase: Module-2)
- Decide whether to implement `POST /auth/logout` (token blacklist or no-op).

## Migrations Metadata (Phase: post Module-1)
- Document Alembic `alembic_version` (schema migrations) table in docs.

## Configuration Hardening (Phase: post Module-1)
- Document required env vars for production (e.g., `RMS_JWT_SECRET`).
