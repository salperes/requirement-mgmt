# Gap Analysis (Docs vs Implementation)

Last updated: 2026-01-22
Scope: All `docs/**/*.md` modules (0-6).

---

## Summary

| Module | Backend API | Services | DB Schema | Tests | UI | Status |
|--------|-------------|----------|-----------|-------|-----|--------|
| 0 - Auth/RBAC/Audit | ✅ | ✅ | ✅ | ✅ | ❌ | Backend Complete |
| 1 - Requirements/Baselines | ✅ | ✅ | ✅ | ✅ | ❌ | Backend Complete |
| 2 - Workflow/Comments | ✅ | ✅ | ✅ | ✅ | ❌ | Backend Complete* |
| 3 - Traceability/RTM | ✅ | ✅ | ✅ | ✅ | ❌ | Backend Complete* |
| 4 - Verification/Evidence | ✅ | ✅ | ✅ | ✅ | ❌ | Backend Complete |
| 5 - Import/Parsing | ✅ | ✅ | ✅ | ✅ | ❌ | Backend Complete* |
| 6 - Compliance Matrix | ✅ | ✅ | ✅ | ✅ | ❌ | Backend Complete |

**Legend**: ✅ Implemented | ❌ Not Implemented | * Minor gaps noted below

---

## Remaining Gaps

### 1. UI Layer (All Modules) - NOT IMPLEMENTED

No frontend implementation exists. All UI screens documented remain unimplemented:

- **Module-0**: Login, user profile, admin console (`docs/ui_mvp_screens.md`)
- **Module-1**: Requirements list, detail, baseline management (`docs/ui_mvp_screens.md`)
- **Module-2**: Workflow transitions, comments panel (`docs/modules/module-2/ui_mvp_screens_module2.md`)
- **Module-3**: RTM matrix view, impact analysis (`docs/modules/module-3/ui_mvp_screens_module3.md`)
- **Module-4**: Test case management, verification results (`docs/modules/module-4/ui_mvp_screens_module4.md`)
- **Module-5**: Import wizard, document preview (`docs/modules/module-5/ui_mvp_screens_module5.md`)
- **Module-6**: Standards library, compliance matrix (`docs/modules/module-6/ui_mvp_screens_module6.md`)

### 2. Module-2: Status-Based Edit Restrictions (NOT ENFORCED)

Requirement updates are not restricted by workflow status as specified.

- **Expected**: Edits blocked when status is `APPROVED` or `IN_REVIEW` (unless user has override permission)
- **Current**: Any user with `requirement:update` can edit regardless of status
- **Reference**: `docs/modules/module-2/workflow_rules.md`

### 3. Module-3: Orphan and Coverage Reports (PARTIAL)

- Orphans endpoint (`/traceability/orphans`) only reports unlinked test cases
- Design document and standard clause orphan detection returns empty lists
- No dedicated coverage percentage or missing-links summary report
- **Reference**: `docs/modules/module-3/module_3_spec.md`

### 4. Module-5: Import Immutability (NOT ENFORCED)

- Imported clauses and source references should be immutable after import completion
- Currently no DB-level constraint prevents modification
- **Expected**: `UPDATE` trigger or application-level block on `imported_clauses`, `source_references`
- **Reference**: `docs/modules/module-5/migrations_plan_module5.md`, `docs/modules/module-5/qa_checklist_module5.md`

---

## Closed Gaps (Previously Identified)

### ✅ Module-6: Compliance Matrix - RESOLVED (2026-01-22)

All previously missing items have been implemented:

- DB schema: `Standard`, `StandardClause`, `ComplianceMapping` tables (`src/db/migrations/versions/0007_module6_compliance.py`)
- API endpoints in `src/api/routes/compliance.py`:
  - `POST /standards`, `GET /standards`, `GET /standards/{id}`
  - `POST /standards/{id}/clauses`, `GET /standards/{id}/clauses`
  - `POST /compliance-mappings`
  - `GET /compliance?baseline_id=&standard_id=`
  - `GET /compliance/export?format=csv|md|xlsx`
- Services: `src/services/compliance.py` (gap analysis, compliance matrix, export)
- RBAC permissions: `standard:manage`, `compliance:map`, `compliance:read`, `compliance:export`
- Tests: `src/tests/test_module6_compliance.py`

### ✅ Module-6: Regulatory Mapping Enforcement - RESOLVED (2026-01-22)

Optional enforcement for regulatory requirements mapping:

- DB schema: `Project` table with `enforce_regulatory_mapping` flag (`src/db/migrations/versions/0008_projects.py`)
- API endpoints in `src/api/routes/projects.py`:
  - `POST /projects`, `GET /projects`, `GET /projects/{id}`, `PATCH /projects/{id}`
- Validation endpoint in `src/api/routes/compliance.py`:
  - `GET /compliance/validate?project_id=&baseline_id=`
- Services: `src/services/compliance.py` (`validate_regulatory_mapping` function)
- RBAC permissions: `project:create`, `project:update`, `project:read`
- Tests: `src/tests/test_projects_compliance_validation.py`
- Documentation: `docs/modules/module-6/compliance_rules.md`, `docs/modules/module-6/api_contract_module6.md`

---

## Statistics

| Category | Count |
|----------|-------|
| Documentation files | 67 |
| Python source files | 67 |
| Database models | 28 tables |
| API route files | 19 |
| Service files | 14 |
| Test files | 12 |

---

## Next Steps (Recommended Priority)

1. **High**: Implement status-based edit restrictions (Module-2)
2. **Medium**: Add import immutability enforcement (Module-5)
3. **Medium**: Complete orphan detection for design docs and standards (Module-3)
4. **Low**: Build frontend UI layer (all modules)