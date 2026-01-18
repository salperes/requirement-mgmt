# Database Schema Additions — Module-2

## comments
- id uuid pk
- requirement_id uuid fk requirements(id)
- author_user_id uuid fk users(id)
- text text not null
- created_at timestamptz not null
- edited_at timestamptz null
- deleted_at timestamptz null
Indexes: (requirement_id), (author_user_id), (created_at)

## comment_mentions
- comment_id uuid fk comments(id)
- mentioned_user_id uuid fk users(id)
- pk (comment_id, mentioned_user_id)

## notifications
- id uuid pk
- user_id uuid fk users(id)
- type text not null (MENTION/WORKFLOW/APPROVAL)
- title text not null
- body text null
- entity_type text null
- entity_id text null
- is_read bool not null default false
- created_at timestamptz not null
Indexes: (user_id, is_read, created_at)

## approval_records (immutable)
- id uuid pk
- requirement_id uuid fk requirements(id)
- approver_user_id uuid fk users(id)
- decision text not null (APPROVE/REJECT)
- reason text null (required for REJECT)
- signature_provider text not null default 'placeholder'
- signature_metadata jsonb not null default '{}'
- signed_at timestamptz not null
Indexes: (requirement_id), (approver_user_id), (signed_at)
