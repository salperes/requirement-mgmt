# API Contract (Module-0 + Module-1)

## Common
- All responses are JSON unless exporting (CSV/MD).
- Pagination: `page`, `page_size` with default 1 / 25.
- Errors follow `error_handling.md`.

## Health
- GET /health

## Auth
- POST /auth/login
- POST /auth/logout (optional for stateless JWT)
- GET /auth/me

## Admin (Admin only)
- GET /admin/users
- POST /admin/users
- PATCH /admin/users/{id}
- PUT /admin/users/{id}/roles
- GET /admin/audit

## Requirements
- POST /requirements
- GET /requirements?query=&discipline=&type=&status=&owner=&include_deleted=&page=&page_size=
- GET /requirements/{id}
- PATCH /requirements/{id}
- DELETE /requirements/{id}   (soft delete)

## Requirement Versions
- GET /requirements/{id}/versions
- GET /requirements/{id}/versions/{version_no}

## Baselines
- POST /baselines
- GET /baselines
- GET /baselines/{id}
- GET /baselines/{id}/items
- GET /baselines/{id}/export?format=md|csv
