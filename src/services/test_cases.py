from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from src.db.models import TestCase


def generate_test_code(session: Session) -> str:
    if session.bind and session.bind.dialect.name == "postgresql":
        next_val = session.execute(select(text("nextval('tc_code_seq')"))).scalar_one()
        return f"TC-{int(next_val):06d}"

    max_code = session.execute(select(TestCase.test_code).order_by(TestCase.test_code.desc())).scalar()
    if not max_code:
        return "TC-000001"
    try:
        numeric = int(max_code.split("-")[-1])
    except (ValueError, AttributeError):
        numeric = 0
    return f"TC-{numeric + 1:06d}"


def apply_test_case_updates(test_case: TestCase, updates: dict) -> bool:
    changed = False
    for field, value in updates.items():
        if hasattr(test_case, field) and value is not None:
            if getattr(test_case, field) != value:
                setattr(test_case, field, value)
                changed = True
    if changed:
        test_case.updated_at = datetime.utcnow()
    return changed
