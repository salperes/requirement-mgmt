# Standards Data Model (Module-6)

## Standard
- id uuid
- code (ISO 9001, ANSI N43.17, IEC 62304)
- title
- version
- publication_year
- publisher
- created_at

## StandardClause
- id uuid
- standard_id
- clause_code
- title
- text
- created_at

## ComplianceMapping
- id uuid
- requirement_id
- standard_clause_id
- compliance_status (COMPLIANT / PARTIAL / NON_COMPLIANT / NA)
- justification
- created_by_user_id
- created_at
