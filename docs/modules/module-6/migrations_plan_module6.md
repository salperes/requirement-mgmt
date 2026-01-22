# Migrations Plan — Module-6

## 0007_compliance_core
Creates:
- standards
- standard_clauses
- compliance_mappings

## 0008_projects
Creates:
- projects table with:
  - id (uuid, pk)
  - name (text, not null)
  - description (text, nullable)
  - enforce_regulatory_mapping (boolean, default false)
  - created_by_user_id (uuid, fk to users)
  - created_at (timestamptz)
  - updated_at (timestamptz)
