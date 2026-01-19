# Database Schema Additions — Module-6

## standards
- id uuid pk
- code text
- title text
- version text
- publication_year int
- publisher text
- created_at timestamptz

## standard_clauses
- id uuid pk
- standard_id uuid
- clause_code text
- title text
- text text
- created_at timestamptz

## compliance_mappings
- id uuid pk
- requirement_id uuid
- standard_clause_id uuid
- compliance_status text
- justification text
- created_by_user_id uuid
- created_at timestamptz
