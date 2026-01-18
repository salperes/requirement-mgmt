from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Sequence

from sqlalchemy.orm import Session

from src.db.models import Baseline, BaselineItem, Requirement, RequirementVersion


def generate_baseline_tag(session: Session, now: Optional[datetime] = None) -> str:
    current = now or datetime.utcnow()
    date_prefix = current.strftime("%Y-%m-%d")
    base = f"BL-{date_prefix}"

    existing = (
        session.query(Baseline.baseline_tag)
        .filter(Baseline.baseline_tag.like(f"{base}%"))
        .all()
    )
    seq = 1
    if existing:
        suffixes = []
        for (tag,) in existing:
            parts = tag.split("-")
            if len(parts) >= 4 and parts[-1].isdigit():
                suffixes.append(int(parts[-1]))
        if suffixes:
            seq = max(suffixes) + 1
    return f"{base}-{seq:02d}"


def get_latest_versions(session: Session, requirement_ids: Sequence) -> dict[str, RequirementVersion]:
    versions: dict[str, RequirementVersion] = {}
    for req_id in requirement_ids:
        version = (
            session.query(RequirementVersion)
            .filter(RequirementVersion.requirement_id == req_id)
            .order_by(RequirementVersion.version_no.desc())
            .first()
        )
        if version:
            versions[str(req_id)] = version
    return versions


def create_baseline_items(
    session: Session,
    baseline: Baseline,
    requirement_ids: List,
    versions: dict[str, RequirementVersion],
) -> List[BaselineItem]:
    items: List[BaselineItem] = []
    for req_id in requirement_ids:
        version = versions.get(str(req_id))
        if not version:
            continue
        item = BaselineItem(
            baseline_id=baseline.id,
            requirement_id=req_id,
            requirement_version_id=version.id,
        )
        session.add(item)
        items.append(item)
    return items


def list_baseline_items(session: Session, baseline_id: str) -> List[BaselineItem]:
    return (
        session.query(BaselineItem)
        .filter(BaselineItem.baseline_id == baseline_id)
        .all()
    )
