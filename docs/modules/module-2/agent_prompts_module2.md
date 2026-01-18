# Agent Prompts — Module-2 (Copy/Paste)

## Global Guardrails
- Apply Module-2 on top of existing Module-0/1 codebase.
- Do NOT implement Module-3+ features.
- Workflow transitions must be server-enforced and audited.

## Architect Agent
Create ADRs:
- 0004-workflow-state-machine
- 0005-comments-mentions-notifications
- 0006-approval-records-esign-placeholder
Update:
- api_contract and permissions matrix in main docs (if you maintain a single docs set)

## Backend Agent
Implement:
- Migration 0003_workflow_collaboration
- Status change endpoint + validation
- Approve/reject endpoint + approval_records + audit
- Comments + mention parsing + notifications
- Notifications inbox endpoints
Tests: cover acceptance_tests_module2.md

## Frontend Agent
Implement:
- Status banner + action buttons
- Comment panel
- Notifications inbox

## QA Agent
Automate:
- workflow transitions
- approvals validation
- mentions -> notification
- RBAC bypass attempts
