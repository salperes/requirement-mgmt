# API Contract — Module-2

## Requirements: Workflow
- POST /requirements/{id}/status
  - body: { "to_status": "Review|Draft|Approved|Rejected", "reason": "..." }
  - RBAC: req:status:change
  - Server validates transition rules (workflow_rules.md)

## Approvals
- POST /requirements/{id}/approve
  - body: { "decision": "APPROVE|REJECT", "reason": "...", "reauth_password": "..."? }
  - RBAC: req:approve
  - Creates ApprovalRecord + AuditLog
  - If REJECT: reason required
- GET /requirements/{id}/approvals
  - RBAC: req:read
  - Returns ApprovalRecord list (latest first)

## Comments
- GET /requirements/{id}/comments
- POST /requirements/{id}/comments
  - body: { "text": "..." }
  - Parses mentions and creates notifications
- PATCH /comments/{comment_id}
- DELETE /comments/{comment_id} (soft delete)

## Notifications (In-app)
- GET /notifications?page=&page_size=&unread_only=
- POST /notifications/{id}/read
