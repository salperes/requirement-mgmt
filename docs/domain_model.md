# Domain Model (RMS)

## Core Entities

### User
- id (uuid)
- email (unique)
- display_name
- password_hash
- is_active
- created_at, updated_at

### Role
- id
- name: Admin, RequirementOwner, Reviewer, Approver, Viewer

### UserRole
- user_id
- role_id

### AuditLog (Append-only, Immutable)
- id (uuid)
- request_id
- actor_user_id (nullable for system)
- action (string, e.g. AUTH_LOGIN_SUCCESS)
- entity_type (string)
- entity_id (string/uuid)
- payload_json (json/jsonb)
- created_at

### Requirement
- id (uuid)
- req_code (unique, immutable; format REQ-000001)
- title (optional)
- text (string; MVP markdown/plain)
- discipline (enum)
- req_type_primary (enum)
- req_type_secondary (optional array)
- is_explanation (bool)
- status (enum: Draft, Review, Approved, Rejected)
- owner_user_id
- source (enum: manual, import) [import later]
- created_at, updated_at
- deleted_at (nullable; soft delete)

### RequirementVersion
- id
- requirement_id
- version_no (int)
- snapshot_json (json/jsonb)
- changed_by_user_id
- change_reason (optional)
- created_at

### Baseline
- id
- baseline_tag (unique, e.g. BL-2026-01-18-01)
- name
- description (optional)
- created_by_user_id
- created_at

### BaselineItem
- baseline_id
- requirement_id
- requirement_version_id
