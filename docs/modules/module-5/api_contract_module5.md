# API Contract — Module-5

## Import
- POST /imports
  (multipart upload)
- GET /imports
- GET /imports/{id}
- GET /imports/{id}/clauses

## Draft Acceptance
- POST /imports/{id}/clauses/{clause_id}/accept
- POST /imports/{id}/clauses/{clause_id}/reject

## Source Trace
- GET /requirements/{id}/source
