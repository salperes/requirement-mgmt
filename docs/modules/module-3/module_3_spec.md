# Module-3 Spec — Traceability + Impact Analysis

## Objective
Provide deterministic, auditable traceability across system artifacts and enable controlled impact analysis when requirements change.

## In Scope
1. **Link Model**
   - Requirement ↔ Requirement (DERIVES)
   - Requirement ↔ Test (VERIFIES)
   - Requirement ↔ Design Artifact (SATISFIES)
   - Requirement ↔ Standard Clause (REFERENCES)
2. **RTM View**
   - Table-based RTM
   - Exportable (CSV/MD)
3. **Impact Analysis**
   - Detect upstream/downstream dependencies
   - Mark impacted objects as *Suspect*
4. **Coverage Metrics**
   - Missing links
   - Unverified requirements
   - Orphan tests (no VERIFIES link)
5. **RBAC Enforcement**
   - Only authorized roles can create/delete links

## Out of Scope
- Graph visualization (nice-to-have later)
- Automatic link creation (AI-assisted in later modules)