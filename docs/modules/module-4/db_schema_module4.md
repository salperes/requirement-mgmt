# Database Schema Additions — Module-4

## test_cases
- id uuid pk
- test_code text unique
- title text
- description text
- verification_method text
- owner_user_id uuid
- created_at timestamptz
- updated_at timestamptz
- deleted_at timestamptz

## verification_results
- id uuid pk
- test_case_id uuid
- requirement_id uuid
- baseline_id uuid null
- status text
- executed_by_user_id uuid
- executed_at timestamptz
- comment text

## evidence
- id uuid pk
- related_type text
- related_id uuid
- evidence_type text
- uri_or_text text
- checksum text
- uploaded_by_user_id uuid
- created_at timestamptz
