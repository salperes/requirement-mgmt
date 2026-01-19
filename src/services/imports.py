from __future__ import annotations

import re
import io
import zipfile
from typing import Any, Dict, List, Tuple
from xml.etree import ElementTree

from pypdf import PdfReader

NUMBERED_CLAUSE = re.compile(r"^\s*\d+(?:\.\d+)*[\).]?\s+")
BULLET_CLAUSE = re.compile(r"^\s*[-\u2022]\s+")


def segment_clauses(text: str, file_type: str) -> List[Dict[str, Any]]:
    lines = text.splitlines(keepends=True)
    clauses: List[Dict[str, Any]] = []
    current_lines: List[str] = []
    current_start: int | None = None
    current_kind: str | None = None
    is_xlsx = file_type == "XLSX"

    def flush(end_line: int) -> None:
        nonlocal current_lines, current_start, current_kind
        if not current_lines or current_start is None:
            return
        raw_text = "".join(current_lines).rstrip("\n")
        location_label = "row" if is_xlsx else "line"
        parsed_metadata = {
            "detected_as": current_kind or "text",
            "line_start": current_start,
            "line_end": end_line,
        }
        if is_xlsx:
            parsed_metadata["sheet_name"] = "Sheet1"
        else:
            parsed_metadata["page_number"] = None
        clauses.append(
            {
                "raw_text": raw_text,
                "location_ref": f"{location_label}:{current_start}",
                "parsed_metadata": parsed_metadata,
            }
        )
        current_lines = []
        current_start = None
        current_kind = None

    if is_xlsx:
        row_index = 0
        for line in lines:
            if not line.strip():
                continue
            row_index += 1
            current_lines = [line]
            current_start = row_index
            current_kind = "row"
            flush(row_index)
        for idx, clause in enumerate(clauses, start=1):
            clause["clause_index"] = idx
        return clauses

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


def extract_text(raw_bytes: bytes, file_type: str) -> str:
    if file_type == "PDF":
        reader = PdfReader(io.BytesIO(raw_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)
    if file_type == "DOCX":
        return _extract_docx_text(raw_bytes)
    if file_type == "XLSX":
        return _extract_xlsx_text(raw_bytes)
    raise ValueError("Unsupported file type")


def _extract_docx_text(raw_bytes: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as archive:
        xml_data = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml_data)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: List[str] = []
    for para in root.findall(".//w:p", ns):
        runs = [node.text or "" for node in para.findall(".//w:t", ns)]
        if runs:
            paragraphs.append("".join(runs))
    return "\n".join(paragraphs)


def _extract_xlsx_text(raw_bytes: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as archive:
        shared_strings = _load_shared_strings(archive)
        sheet_names = sorted(
            [name for name in archive.namelist() if name.startswith("xl/worksheets/sheet")]
        )
        if not sheet_names:
            return ""
        sheet_xml = archive.read(sheet_names[0])

    root = ElementTree.fromstring(sheet_xml)
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rows: List[Tuple[int, str]] = []
    for row in root.findall(".//x:row", ns):
        cells = []
        for cell in row.findall("x:c", ns):
            value = ""
            cell_type = cell.get("t")
            v = cell.find("x:v", ns)
            if v is not None and v.text is not None:
                if cell_type == "s":
                    try:
                        value = shared_strings[int(v.text)]
                    except (ValueError, IndexError):
                        value = v.text
                else:
                    value = v.text
            cells.append(value)
        row_index = int(row.get("r", "0") or "0")
        rows.append((row_index, "\t".join(cells)))

    rows.sort(key=lambda item: item[0])
    return "\n".join([row_text for _, row_text in rows if row_text.strip()])


def _load_shared_strings(archive: zipfile.ZipFile) -> List[str]:
    try:
        xml_data = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ElementTree.fromstring(xml_data)
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    values: List[str] = []
    for si in root.findall(".//x:si", ns):
        parts = [node.text or "" for node in si.findall(".//x:t", ns)]
        values.append("".join(parts))
    return values
