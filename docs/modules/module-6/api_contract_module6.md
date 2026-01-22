# API Contract — Module-6

## Projects
- POST /projects — Create project (Admin only)
- GET /projects — List all projects
- GET /projects/{id} — Get project details
- PATCH /projects/{id} — Update project settings (Admin only)

### Project Payload
```json
{
  "name": "string (required)",
  "description": "string (optional)",
  "enforce_regulatory_mapping": "boolean (optional, default: false)"
}
```

## Standards
- POST /standards
- GET /standards
- GET /standards/{id}

## Clauses
- POST /standards/{id}/clauses
- GET /standards/{id}/clauses

## Compliance
- POST /compliance-mappings
- GET /compliance?baseline_id=&standard_id=&project_id=
- GET /compliance/export?format=csv|md|xlsx
- GET /compliance/validate?baseline_id= — Validate regulatory mapping (if enforced)

### Validation Response
```json
{
  "valid": false,
  "enforce_regulatory_mapping": true,
  "unmapped_regulatory_requirements": [
    {"id": "uuid", "req_code": "REQ-001", "title": "..."}
  ]
}
```
