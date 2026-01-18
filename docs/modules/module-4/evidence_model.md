# Evidence Model (Module-4)

## Evidence
- id uuid
- related_type (TestCase / VerificationResult)
- related_id
- evidence_type (FILE / LINK / NOTE)
- uri_or_text
- checksum (optional)
- uploaded_by_user_id
- created_at

## Rules
- Evidence is immutable once attached
- Evidence must reference a VerificationResult for PASS
