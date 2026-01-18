# Migrations Plan

## 0001_init
Creates:
- users, roles, user_roles, audit_log
Adds:
- basic indexes

## 0002_requirements_core
Creates:
- requirements, requirement_versions, baselines, baseline_items
Adds:
- sequence or counter mechanism for `req_code` generation (REQ-000001)

## `req_code` generation options
Preferred (Postgres):
- A DB sequence `req_seq` and computed format `REQ-` + lpad(nextval, 6, '0') in application layer.

Alternative:
- A dedicated table `counters` with row lock for concurrency.

## Idempotency
- Each migration recorded in `schema_migrations` table (tool-dependent).
