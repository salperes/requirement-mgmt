# Module-2 Spec — Workflow + Collaboration + E-Sign Placeholder

## Objective
Implement a controlled requirement lifecycle with collaboration and approvable records, while keeping complexity low and remaining compatible with later modules.

## In Scope
1. **Workflow State Machine**
   - States: Draft, Review, Approved, Rejected
   - Transitions are **server-enforced**
2. **Comments**
   - Comments on a Requirement (flat list MVP)
   - Create/edit/delete (delete = soft)
3. **Mentions & Notifications (MVP)**
   - Parse `@email` or `@username` in comments
   - Create notification records for mentioned users
   - Workflow notifications on status change (Draft/Review)
4. **Approval Records + E-sign Placeholder**
   - Approver can approve/reject with a reason
   - Store approval record + “signature placeholder” metadata
   - Immutable audit events for transitions and approvals
   - Provide approval history endpoint for UI panels
5. **RBAC updates**
   - Reviewer: can comment, optionally move Draft↔Review
   - Approver: can Approve/Reject (Review→Approved/Rejected)
   - Owner: can request review and comment
6. **UI screens**
   - Workflow actions and status banner
   - Comment panel + mentions
   - Notification inbox (simple list)

## Out of Scope
- Real cryptographic signing, certificate validation, timestamp authority
- External delivery (email/slack); store-only inbox
- Complex comment threading, reactions