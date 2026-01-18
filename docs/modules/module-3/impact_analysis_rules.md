# Impact Analysis Rules (Module-3)

## Trigger Events
- Requirement text update
- Requirement status change
- Requirement deletion (soft)
- Link create/delete

## Suspect Logic
- Any change to a Requirement marks downstream entities as Suspect.
- Propagation follows DERIVES → SATISFIES → VERIFIES paths recursively.

## Clearing Suspect
- Cleared when downstream entity is re-verified (Module-4) or manually by Admin.

## Audit
- Each propagation writes TRACE_SUSPECT_SET with full link path.
