# Verification Model (Module-4)

## Verification Method (Enum)
- TEST
- ANALYSIS
- INSPECTION
- DEMONSTRATION

## Verification Status (Enum)
- NOT_RUN
- PASS
- FAIL
- BLOCKED

## Test Case
- id uuid
- test_code (TC-000001)
- title
- description
- verification_method
- owner_user_id
- created_at
- updated_at
- deleted_at (soft)

## Verification Result
- id uuid
- test_case_id
- requirement_id
- baseline_id (nullable)
- status
- executed_by_user_id
- executed_at
- comment
