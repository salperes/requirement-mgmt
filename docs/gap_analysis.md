# Gap Analysis (Docs vs Implementation)

Last updated: 2026-01-19
Scope: All `docs/**/*.md` except Module-6 exclusions are not applied (note: module-6 is included here per request).

## Module-6 — Compliance Matrix (Missing)
- Missing DB schema + migrations for `standards`, `standard_clauses`, `compliance_mappings`. (docs/modules/module-6/db_schema_module6.md)
- Missing API endpoints:
  - POST/GET /standards
  - GET /standards/{id}
  - POST/GET /standards/{id}/clauses
  - POST /compliance-mappings
  - GET /compliance?baseline_id=&standard_id=
  - GET /compliance/export?format=csv|md|xlsx
  (docs/modules/module-6/api_contract_module6.md)
- Missing services for compliance matrix, gap analysis, and export. (docs/modules/module-6/module_6_spec.md, compliance_rules.md)
- Missing RBAC permissions: `standard:manage`, `compliance:map`, `compliance:read`, `compliance:export`. (docs/modules/module-6/permissions_matrix_module6.md)
- Missing UI screens for standards library, compliance matrix, gap analysis. (docs/modules/module-6/ui_mvp_screens_module6.md)
- Missing acceptance tests for module-6. (docs/modules/module-6/acceptance_tests_module6.md)

## Module-0/Module-1 UI (Missing)
- No UI routes for Module-0 login/me/admin users and Module-1 requirements/baselines screens.
  (docs/ui_mvp_screens.md)

## Module-3 Coverage/Gaps (Partial)
- Orphans endpoint only reports tests; design/standard orphan lists are empty.
  (docs/modules/module-3/module_3_spec.md)
- No dedicated coverage/missing-links or unverified-requirements report beyond RTM view.
  (docs/modules/module-3/module_3_spec.md)

## Module-2 Status-Based Edit Rules (Not enforced)
- Requirement updates are not restricted by status (Draft/Review/Approved/Rejected) as recommended.
  (docs/modules/module-2/workflow_rules.md)

## Module-5 Immutability (Not enforced in DB)
- Imported clauses/source references are intended to be immutable; currently no DB-level enforcement.
  (docs/modules/module-5/migrations_plan_module5.md, qa_checklist_module5.md)