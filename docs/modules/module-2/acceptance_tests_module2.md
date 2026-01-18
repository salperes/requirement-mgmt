# Acceptance Tests — Module-2 (BDD)

## Workflow Transitions
- Given Owner and requirement in Draft, when status->Review, then status becomes Review and audit REQ_STATUS_CHANGED exists.
- Given Viewer, when status->Review, then 403 and audit RBAC_DENY exists.
- Given Approver and requirement in Review, when approve, then status becomes Approved and approval_record exists.

## Approvals
- Given Approver, when reject without reason, then 400 validation error.
- Given Approver, when reject with reason, then status becomes Rejected and approval_record decision=REJECT exists.

## Comments & Mentions
- Given Owner, when create comment with @viewer@example.com, then MENTION notification is created for viewer.
- Given mentioned user, when mark notification read, then is_read=true.

## Auditing
- Comment create/edit/delete produce audit events with requirement_id and comment_id.
- Approve/reject writes audit events with approver_user_id and decision.
