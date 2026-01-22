# Claude Code Session Context

## Project Overview

**Name:** RMS (Requirements Management System)
**Type:** FastAPI backend API for managing requirements, traceability, verification, and compliance
**Language:** Python 3.11
**Framework:** FastAPI + SQLAlchemy + Alembic

## Architecture

```
src/
├── app/main.py          # FastAPI app entry point
├── api/
│   ├── deps.py          # Dependency injection (auth, db)
│   ├── schemas.py       # Pydantic request/response models
│   └── routes/          # API endpoints by domain
├── services/            # Business logic layer
├── db/
│   ├── models.py        # SQLAlchemy ORM models
│   ├── session.py       # Database session management
│   └── migrations/      # Alembic migrations
├── shared/
│   ├── settings.py      # Configuration
│   ├── errors.py        # Custom exceptions
│   └── security.py      # JWT, password hashing
└── tests/               # Pytest test suites
```

## Modules Status

| Module | Description | Status |
|--------|-------------|--------|
| 0 | Auth, RBAC, Audit | ✅ Complete |
| 1 | Requirements, Versioning, Baselines | ✅ Complete |
| 2 | Workflow, Comments, Notifications | ✅ Complete |
| 3 | Traceability, Links, RTM | ✅ Complete |
| 4 | Verification, Test Cases, Evidence | ✅ Complete |
| 5 | Import, Parsing | ✅ Complete |
| 6 | Compliance Matrix, Projects | ✅ Complete |

## Recent Changes (2026-01-22)

- Added `Project` model with `enforce_regulatory_mapping` setting
- Added project CRUD endpoints (`/projects`)
- Added compliance validation endpoint (`/compliance/validate`)
- Added RBAC permissions: `project:create`, `project:update`, `project:read`
- All 34 tests passing

## Remaining Gaps

See `docs/gap_analysis.md` for full details:

1. **UI Layer** - No frontend implementation (all modules)
2. **Module-2** - Status-based edit restrictions not enforced
3. **Module-3** - Orphan detection partial (only test cases)
4. **Module-5** - Import immutability not enforced at DB level

## Key Files

| Purpose | Path |
|---------|------|
| API entry point | `src/app/main.py` |
| All DB models | `src/db/models.py` |
| RBAC permissions | `src/services/rbac.py` |
| Pydantic schemas | `src/api/schemas.py` |
| Gap analysis | `docs/gap_analysis.md` |
| Module-6 specs | `docs/modules/module-6/` |

## Development Commands

```bash
# Run tests in Docker
docker-compose build app
docker-compose run --rm app pytest src/tests/ -v

# Run specific test file
docker-compose run --rm app pytest src/tests/test_projects_compliance_validation.py -v

# Start development server
docker-compose up

# Apply migrations
docker-compose run --rm app alembic upgrade head
```

## Database

- **Dev/Test:** SQLite (in-memory for tests)
- **Production:** PostgreSQL 16

### Key Tables (28 total)

- `users`, `roles`, `user_roles` - Authentication
- `audit_log` - Audit trail
- `requirements`, `requirement_versions` - Module 1
- `baselines`, `baseline_items` - Module 1
- `comments`, `comment_mentions`, `notifications`, `approval_records` - Module 2
- `links`, `suspects` - Module 3
- `test_cases`, `verification_results`, `evidence` - Module 4
- `import_sessions`, `imported_clauses`, `source_references` - Module 5
- `projects`, `standards`, `standard_clauses`, `compliance_mappings` - Module 6

## Git Info

- **Branch:** master
- **Remote:** github.com:salperes/requirement-mgmt.git

## Session Notes

Last session focused on:
1. Analyzing docs vs implementation coverage
2. Adding optional `enforce_regulatory_mapping` project setting
3. Implementing validation for regulatory requirements compliance mapping
4. Fixing RBAC permissions for project endpoints
