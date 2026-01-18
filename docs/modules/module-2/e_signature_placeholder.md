# E-Signature Placeholder (Module-2)

## Goal
Record an approval as a structured, auditable record without integrating a real signing provider.

## Approval Record (immutable)
On approve/reject:
- Create an ApprovalRecord row (immutable)
- Write an AuditLog event
- Optionally create a notification for the requirement owner

## Placeholder Signature Data
Store:
- approver_user_id
- decision: APPROVE / REJECT
- reason (required for REJECT)
- signed_at
- signature_provider: placeholder
- signature_metadata: JSON (ip, user_agent, method, etc.)

## Optional Re-auth
For approval action, optionally require password re-entry to reduce spoofing risk.
