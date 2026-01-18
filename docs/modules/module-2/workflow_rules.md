# Workflow Rules (Module-2)

## State Machine
States:
- Draft
- Review
- Approved
- Rejected

## Allowed Transitions (Recommended)
| From | To | Who |
|---|---|---|
| Draft | Review | RequirementOwner, Reviewer, Admin |
| Review | Draft | RequirementOwner, Reviewer, Admin |
| Review | Approved | Approver, Admin |
| Review | Rejected | Approver, Admin |
| Approved | Review | Admin (exception) |
| Rejected | Review | RequirementOwner, Admin |

## Transition Requirements
- Transition request may include `reason`.
- Any transition writes an AuditLog event:
  - action: `REQ_STATUS_CHANGED`
  - payload: from_status, to_status, reason, requirement_id, req_code

## Editing Rules by Status (MVP recommendation)
- Draft: editable by Owner/Admin
- Review: editable by Owner/Admin, but should be audited and versioned
- Approved: editable by Admin only OR forces status back to Review (choose via ADR)
- Rejected: editable by Owner/Admin
