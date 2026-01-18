# Coding Conventions & Project Standards (RMS)

## General Principles
- Clean Architecture: API, Domain, Infrastructure separation
- Domain logic must not depend on frameworks
- Favor explicitness over magic
- Fail fast with clear error messages

## Naming Conventions
### Files & Folders
- snake_case for folders
- snake_case for backend files
- PascalCase for domain classes
- kebab-case for URLs

### Identifiers
- UUIDs for all primary keys
- Immutable identifiers (req_code, baseline_tag)

## API Conventions
- RESTful endpoints
- Nouns, not verbs
- Use HTTP status codes correctly
- Pagination on all list endpoints

## Error Handling
- Never expose stack traces
- Always return error envelope defined in error_handling.md
- Log errors with request_id

## Database
- Explicit indexes for query fields
- No cascade delete on core entities
- Migrations must be forward-only

## Testing
- Unit tests for domain & services
- API tests for endpoints
- One test file per endpoint/module

## Security
- Hash passwords (Argon2/bcrypt/scrypt)
- Validate all inputs
- Enforce RBAC server-side only

## Documentation
- Update relevant MD when behavior changes
- Add ADR for architectural decisions
