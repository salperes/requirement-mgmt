# Permissions Matrix (RBAC)

## Roles
- Admin
- RequirementOwner
- Reviewer
- Approver
- Viewer

## Permission Names
- auth:login, auth:me
- admin:users:read, admin:users:write, admin:roles:write
- audit:read
- req:create, req:read, req:update, req:delete
- req:versions:read
- baseline:create, baseline:read, baseline:export

## Matrix
| Permission | Admin | Owner | Reviewer | Approver | Viewer |
|---|---:|---:|---:|---:|---:|
| auth:login | ✅ | ✅ | ✅ | ✅ | ✅ |
| auth:me | ✅ | ✅ | ✅ | ✅ | ✅ |
| admin:users:read | ✅ | ❌ | ❌ | ❌ | ❌ |
| admin:users:write | ✅ | ❌ | ❌ | ❌ | ❌ |
| admin:roles:write | ✅ | ❌ | ❌ | ❌ | ❌ |
| audit:read | ✅ | ❌ | ❌ | ❌ | ❌ |
| req:create | ✅ | ✅ | ❌ | ❌ | ❌ |
| req:read | ✅ | ✅ | ✅ | ✅ | ✅ |
| req:update | ✅ | ✅ | ❌ | ❌ | ❌ |
| req:delete | ✅ | ✅ | ❌ | ❌ | ❌ |
| req:versions:read | ✅ | ✅ | ✅ | ✅ | ✅ |
| baseline:create | ✅ | ✅ | ❌ | ❌ | ❌ |
| baseline:read | ✅ | ✅ | ✅ | ✅ | ✅ |
| baseline:export | ✅ | ✅ | ✅ | ✅ | ✅ |
