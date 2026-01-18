# UI Screens — Module-2 (MVP)

## Requirement Detail (enhanced)
- Status badge (Draft/Review/Approved/Rejected)
- Action buttons (RBAC + current status):
  - Request Review (Draft->Review)
  - Send Back to Draft (Review->Draft)
  - Approve / Reject (Review->Approved/Rejected; Approver only)
- Approval panel: last decision + reason + signed_at
  - Source: GET /requirements/{id}/approvals

## Comments Panel
- Comment list
- Add comment box
- Edit/delete own comment (optional)

## Notifications Inbox
- List notifications (unread first)
- Mark as read
- Click opens related entity

## UI Route
- GET /ui/module-2 (MVP interactive screen)