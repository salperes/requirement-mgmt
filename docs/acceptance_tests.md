# Acceptance Tests (BDD)

## Module-0 (Skeleton + Auth + RBAC + Audit)
### Auth
- Given valid user, when login, then token is returned and `/auth/me` returns user + roles.
- Given invalid password, when login, then 401 and an audit event `AUTH_LOGIN_FAIL` is recorded.

### RBAC
- Given Viewer, when calling `GET /admin/users`, then 403 and `RBAC_DENY` is audited.
- Given Admin, when assigning roles, then 200 and `RBAC_ROLE_ASSIGNED` is audited.

### Audit
- All critical actions include `request_id` and `actor_user_id` (unless system).

### Migrations
- Fresh DB can be migrated to latest successfully.

## Module-1 (Requirements + Versions + Baselines)
### Requirement Create
- Given Owner, when POST /requirements, then req_code is generated and version 1 exists.

### Requirement Update
- Given existing requirement, when PATCH, then a new version is created and the previous snapshot remains unchanged.

### Requirement Delete (Soft)
- Given requirement, when DELETE, then deleted_at is set and default list hides it.

### Baseline Create
- Given multiple requirements, when baseline is created, then baseline freezes the latest versions.

### Baseline Export
- Export includes baseline_tag and requirement rows with core fields.
