from __future__ import annotations

import re
from typing import Any, Dict, List

NUMBERED_CLAUSE = re.compile(r"^\s*\d+(?:\.\d+)*[\).]?\s+")
BULLET_CLAUSE = re.compile(r"^\s*[-\u2022]\s+")


def segment_clauses(text: str, file_type: str) -> List[Dict[str, Any]]:
    lines = text.splitlines()
    clauses: List[Dict[str, Any]] = []
    current_lines: List[str] = []
    current_start: int | None = None
    current_kind: str | None = None

    def flush(end_line: int) -> None:
        nonlocal current_lines, current_start, current_kind
        if not current_lines or current_start is None:
            return
        raw_text = "\n".join(current_lines)
        location_label = "row" if file_type == "XLSX" else "line"
        clauses.append(
            {
                "raw_text": raw_text,
                "location_ref": f"{location_label}:{current_start}",
                "parsed_metadata": {
                    "detected_as": current_kind or "text",
                    "line_start": current_start,
                    "line_end": end_line,
                },
            }
        )
        current_lines = []
        current_start = None
        current_kind = None

    for idx, line in enumerate(lines, start=1):
        if not line.strip():
            if current_lines:
                flush(idx - 1)
            continue

        kind = None
        if NUMBERED_CLAUSE.match(line):
            kind = "numbered"
        elif BULLET_CLAUSE.match(line):
            kind = "bullet"

        if kind or not current_lines:
            if current_lines:
                flush(idx - 1)
            current_lines = [line]
            current_start = idx
            current_kind = kind or "text"
        else:
            current_lines.append(line)

    if current_lines:
        flush(len(lines))

    for idx, clause in enumerate(clauses, start=1):
        clause["clause_index"] = idx
    return clauses


def infer_file_type(filename: str) -> str | None:
    lower = (filename or "").lower()
    if lower.endswith(".pdf"):
        return "PDF"
    if lower.endswith(".docx"):
        return "DOCX"
    if lower.endswith(".xlsx"):
        return "XLSX"
    return None