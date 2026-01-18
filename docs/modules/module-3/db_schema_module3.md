# Database Schema Additions — Module-3

## links
- id uuid pk
- source_type text
- source_id text
- target_type text
- target_id text
- link_type text
- created_by_user_id uuid
- created_at timestamptz
- deleted_at timestamptz

## suspects
- entity_type text
- entity_id text
- reason text
- created_at timestamptz
Primary key: (entity_type, entity_id)
