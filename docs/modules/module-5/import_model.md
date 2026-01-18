# Import Data Model (Module-5)

## ImportSession
- id uuid
- file_name
- file_type (PDF/DOCX/XLSX)
- uploaded_by_user_id
- uploaded_at
- status (IN_PROGRESS / COMPLETED / FAILED)

## ImportedClause
- id uuid
- import_session_id
- raw_text
- page_number / sheet_name
- clause_index
- parsed_metadata json
- created_at

## SourceReference
- id uuid
- requirement_id
- import_session_id
- imported_clause_id
- created_at
