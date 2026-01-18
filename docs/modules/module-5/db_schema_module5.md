# Database Schema Additions — Module-5

## import_sessions
- id uuid pk
- file_name text
- file_type text
- uploaded_by_user_id uuid
- uploaded_at timestamptz
- status text

## imported_clauses
- id uuid pk
- import_session_id uuid
- raw_text text
- location_ref text
- clause_index int
- parsed_metadata jsonb
- created_at timestamptz

## source_references
- id uuid pk
- requirement_id uuid
- import_session_id uuid
- imported_clause_id uuid
- created_at timestamptz
