# Error Handling & Response Format

## Success Envelope
Return raw JSON objects (no extra envelope) for simplicity in MVP.

## Error Envelope
```
{
  "error": {
    "code": "RBAC_FORBIDDEN",
    "message": "You do not have permission to perform this action.",
    "details": {
      "permission": "req:update",
      "request_id": "...."
    }
  }
}
```

## HTTP Status Codes
- 400: validation error
- 401: unauthenticated
- 403: forbidden (RBAC)
- 404: not found
- 409: conflict (duplicate req_code, duplicate baseline_tag)
- 422: semantic validation errors (optional)
- 500: unexpected

## Validation Rules (minimum)
- discipline must be one of enum
- req_type_primary must be one of enum
- text must be non-empty for requirement create
