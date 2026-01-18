# QA Checklist (MVP)

## Security
- Password hashing uses a modern algorithm (Argon2/bcrypt/scrypt).
- Tokens expire and cannot be reused indefinitely.
- RBAC enforced on every endpoint.

## Data Integrity
- req_code uniqueness under concurrency.
- requirement_versions uniqueness (requirement_id, version_no).
- baseline_items uses frozen version ids.

## Audit
- Audit events for: login success/fail, req create/update/delete, baseline create, RBAC deny.
- Audit payload includes changed fields and ids.

## Performance (basic)
- Requirements list uses indexes (req_code, status, discipline, type).
- Pagination for list endpoints.
