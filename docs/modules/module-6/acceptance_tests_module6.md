# Acceptance Tests — Module-6

## Project Management
- Admin can create project with enforce_regulatory_mapping=true
- Admin can update project settings
- Non-admin cannot create/update projects
- All users can read project details

## Standards & Clauses
- Admin can create standards and clauses
- Owner can map requirement to clause
- Viewer cannot modify mappings

## Compliance Validation
- When enforce_regulatory_mapping=true:
  - Validation endpoint returns unmapped regulatory requirements
  - Baseline creation fails if regulatory requirements are unmapped
- When enforce_regulatory_mapping=false:
  - Validation returns valid=true (warnings only in gap analysis)
  - Baseline creation succeeds regardless of mapping status

## Export
- Export includes baseline and compliance status
- Export includes unmapped items when present
