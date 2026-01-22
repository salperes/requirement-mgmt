# Compliance Rules (Module-6)

## Compliance Status Values

- **COMPLIANT**: Requirement fully satisfies clause
- **PARTIAL**: Requirement partially satisfies clause
- **NON_COMPLIANT**: Requirement does not satisfy clause
- **NA**: Clause not applicable

## Rules

1. **Regulatory Mapping Enforcement** (Optional, per-project setting)
   - When `enforce_regulatory_mapping` is enabled on the project:
     - All requirements with `req_type_primary = "Regulatory"` MUST have at least one compliance mapping
     - Validation is triggered on:
       - Baseline creation/finalization
       - Compliance report generation
       - Requirement status transition to `APPROVED`
     - If validation fails, operation is blocked with error listing unmapped regulatory requirements
   - When disabled: No enforcement, gap analysis report shows unmapped items as warnings only

2. **Compliance evaluated per baseline**
   - Compliance matrix is scoped to a specific baseline
   - Each baseline can have different compliance status for same requirement-clause pair

3. **All mapping changes audited**
   - Every create/update to `compliance_mappings` is logged to `audit_log`
   - Audit includes: user, timestamp, old/new status, justification

## Project Settings

Projects can configure compliance behavior via the `projects` table:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enforce_regulatory_mapping` | boolean | false | When true, regulatory requirements must have at least one compliance mapping |

This setting is configured during project creation and can be updated by Admin users.
