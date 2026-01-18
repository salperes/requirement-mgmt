# Suspect Auto-Clear Rules (Module-4)

## Trigger
- VerificationResult status changes to PASS

## Logic
- If all VERIFIES-linked tests for a requirement are PASS,
  then clear Suspect flag for that requirement.

## Audit
- action: TRACE_SUSPECT_AUTO_CLEARED
- payload: requirement_id, test_case_ids
