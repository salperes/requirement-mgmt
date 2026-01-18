# Repository Structure

## Target layout
```
/docs
  /adr
  domain_model.md
  business_rules.md
  api_contract.md
  permissions_matrix.md
  error_handling.md
  db_schema.md
  migrations_plan.md
  ui_mvp_screens.md
  acceptance_tests.md
  qa_checklist.md
  seed_data.md
  agent_prompts.md

/src
  /app
  /api
  /domain
  /services
  /db
    /migrations
  /shared
  /tests
/scripts
/docker
README.md
```

## Conventions
- Docs are **Markdown**, UTF-8, short paragraphs.
- Keep IDs stable (REQ-000001 etc.).
- Every breaking decision gets an ADR in `docs/adr/`.
