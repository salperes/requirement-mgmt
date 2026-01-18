# Traceability Data Model (Module-3)

## Link Entity
- id uuid pk
- source_type enum (Requirement, Test, Design, Standard)
- source_id text
- target_type enum (Requirement, Test, Design, Standard)
- target_id text
- link_type enum:
  - DERIVES
  - SATISFIES
  - VERIFIES
  - REFERENCES
- created_by_user_id
- created_at
- deleted_at (soft delete)

## Rules
- Links are directional.
- Circular DERIVES links are forbidden.
- Soft delete only.
