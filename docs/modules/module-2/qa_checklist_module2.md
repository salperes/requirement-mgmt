# QA Checklist — Module-2

## RBAC
- Only Approver/Admin can approve/reject.
- Viewer cannot comment or change status.
- Own-comment enforcement for edit/delete.

## Workflow
- Transition validation matches workflow_rules.md.
- Status cannot be mutated via generic requirement PATCH without rules.

## Data Integrity
- approval_records immutable.
- notifications created only by server triggers.
