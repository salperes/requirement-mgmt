# Database Schema (MVP)

> Target DB: PostgreSQL recommended (jsonb, sequences).

## Tables

### users
- id uuid pk
- email text unique not null
- password_hash text not null
- display_name text not null
- is_active bool not null default true
- created_at timestamptz not null
- updated_at timestamptz not null

### roles
- id uuid pk
- name text unique not null

### user_roles
- user_id uuid fk users(id)
- role_id uuid fk roles(id)
- pk (user_id, role_id)

### audit_log
- id uuid pk
- request_id text not null
- actor_user_id uuid null fk users(id)
- action text not null
- entity_type text null
- entity_id text null
- payload_json jsonb not null default '{}'
- created_at timestamptz not null
Indexes: (created_at), (action), (actor_user_id)

### requirements
- id uuid pk
- req_code text unique not null
- title text null
- text text not null
- discipline text not null
- req_type_primary text not null
- req_type_secondary jsonb null
- is_explanation bool not null default false
- status text not null default 'Draft'
- owner_user_id uuid fk users(id)
- source text not null default 'manual'
- created_at timestamptz not null
- updated_at timestamptz not null
- deleted_at timestamptz null
Indexes: (req_code), (discipline), (req_type_primary), (status), (deleted_at)

### requirement_versions
- id uuid pk
- requirement_id uuid fk requirements(id)
- version_no int not null
- snapshot_json jsonb not null
- changed_by_user_id uuid fk users(id)
- change_reason text null
- created_at timestamptz not null
Unique: (requirement_id, version_no)

### baselines
- id uuid pk
- baseline_tag text unique not null
- name text not null
- description text null
- created_by_user_id uuid fk users(id)
- created_at timestamptz not null

### baseline_items
- baseline_id uuid fk baselines(id)
- requirement_id uuid fk requirements(id)
- requirement_version_id uuid fk requirement_versions(id)
- pk (baseline_id, requirement_id)
Indexes: (baseline_id)
