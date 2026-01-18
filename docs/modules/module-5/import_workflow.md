# Import Workflow (Module-5)

1. User uploads document
2. System creates ImportSession
3. Text is extracted
4. Clauses are segmented
5. Draft Requirements created (status=Draft, source=import)
6. User reviews each draft:
   - Accept → becomes normal Requirement
   - Edit → versioned Requirement
   - Reject → remains only in import log

All steps are auditable.
