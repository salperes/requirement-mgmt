# Database Schema Additions — Module-6

## projects
- id uuid pk
- name text not null
- description text
- enforce_regulatory_mapping boolean default false
- created_by_user_id uuid fk(users.id)
- created_at timestamptz
- updated_at timestamptz

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
- standard_id uuid fk(standards.id)
- clause_code text
- title text
- text text
- created_at timestamptz

## compliance_mappings
- id uuid pk
- requirement_id uuid fk(requirements.id)
- standard_clause_id uuid fk(standard_clauses.id)
- compliance_status text
- justification text
- created_by_user_id uuid fk(users.id)
- created_at timestamptz
