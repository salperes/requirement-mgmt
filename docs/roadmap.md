# Roadmap

## Post Module-1
- Audit immutability: add DB-level guardrails on `audit_log` (triggers/permissions).
- Audit payload standard: define required keys per action.
- Migrations metadata: document Alembic `alembic_version` table.
- Configuration hardening: document prod env vars (e.g., `RMS_JWT_SECRET`).

## Module-2
- Auth logout (optional): decide implementation approach (blacklist/no-op).