from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Iterable, List, Optional, Sequence, Tuple

from sqlalchemy.orm import Session

from src.db.models import Link, Requirement, Suspect

ALLOWED_ENTITY_TYPES = {"Requirement", "Test", "Design", "Standard"}
ALLOWED_LINK_TYPES = {"DERIVES", "SATISFIES", "VERIFIES", "REFERENCES"}
SUSPECT_PROPAGATION_LINKS = {"DERIVES", "SATISFIES", "VERIFIES"}


def validate_link_payload(
    source_type: str,
    source_id: str,
    target_type: str,
    target_id: str,
    link_type: str,
) -> Optional[str]:
    if source_type not in ALLOWED_ENTITY_TYPES or target_type not in ALLOWED_ENTITY_TYPES:
        return "Invalid entity type."
    if link_type not in ALLOWED_LINK_TYPES:
        return "Invalid link type."
    if link_type == "DERIVES":
        if source_type != "Requirement" or target_type != "Requirement":
            return "DERIVES links must connect Requirement to Requirement."
        if source_id == target_id:
            return "DERIVES links cannot reference the same requirement."
    if link_type == "SATISFIES" and target_type != "Design":
        return "SATISFIES links must target Design artifacts."
    if link_type == "VERIFIES" and target_type != "Test":
        return "VERIFIES links must target Test artifacts."
    if link_type == "REFERENCES" and target_type != "Standard":
        return "REFERENCES links must target Standard clauses."
    if link_type in {"SATISFIES", "VERIFIES", "REFERENCES"} and source_type != "Requirement":
        return "Requirement must be the source for this link type."
    return None


def detect_derives_cycle(session: Session, source_id: str, target_id: str) -> bool:
    links = (
        session.query(Link)
        .filter(Link.deleted_at.is_(None))
        .filter(Link.link_type == "DERIVES")
        .all()
    )
    adjacency: dict[str, list[str]] = {}
    for link in links:
        if link.source_type == "Requirement" and link.target_type == "Requirement":
            adjacency.setdefault(link.source_id, []).append(link.target_id)

    queue = deque([target_id])
    visited: set[str] = set()
    while queue:
        current = queue.popleft()
        if current == source_id:
            return True
        if current in visited:
            continue
        visited.add(current)
        for neighbor in adjacency.get(current, []):
            if neighbor not in visited:
                queue.append(neighbor)
    return False


def ensure_requirement_exists(session: Session, requirement_id: str) -> bool:
    return (
        session.query(Requirement)
        .filter(Requirement.id == requirement_id)
        .filter(Requirement.deleted_at.is_(None))
        .count()
        > 0
    )


def find_links(
    session: Session,
    source_type: Optional[str] = None,
    source_id: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    link_type: Optional[str] = None,
) -> List[Link]:
    q = session.query(Link).filter(Link.deleted_at.is_(None))
    if source_type:
        q = q.filter(Link.source_type == source_type)
    if source_id:
        q = q.filter(Link.source_id == source_id)
    if target_type:
        q = q.filter(Link.target_type == target_type)
    if target_id:
        q = q.filter(Link.target_id == target_id)
    if link_type:
        q = q.filter(Link.link_type == link_type)
    return q.order_by(Link.created_at.desc()).all()


def _node_key(entity_type: str, entity_id: str) -> str:
    return f"{entity_type}:{entity_id}"


def build_downstream_paths(session: Session, requirement_id: str) -> List[Tuple[str, str, List[str]]]:
    links = session.query(Link).filter(Link.deleted_at.is_(None)).all()
    adjacency: dict[str, List[Tuple[str, str, str]]] = {}
    for link in links:
        if link.link_type not in SUSPECT_PROPAGATION_LINKS:
            continue
        source_key = _node_key(link.source_type, link.source_id)
        adjacency.setdefault(source_key, []).append((link.link_type, link.target_type, link.target_id))

    start_key = _node_key("Requirement", requirement_id)
    queue = deque([(start_key, [start_key])])
    visited: set[str] = set()
    impacts: List[Tuple[str, str, List[str]]] = []

    while queue:
        current, path = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        for link_type, target_type, target_id in adjacency.get(current, []):
            next_key = _node_key(target_type, target_id)
            next_path = path + [f"link:{link_type}", next_key]
            impacts.append((target_type, target_id, next_path))
            if next_key not in visited:
                queue.append((next_key, next_path))
    return impacts


def upsert_suspect(session: Session, entity_type: str, entity_id: str, reason: Optional[str]) -> Suspect:
    existing = (
        session.query(Suspect)
        .filter(Suspect.entity_type == entity_type)
        .filter(Suspect.entity_id == entity_id)
        .one_or_none()
    )
    if existing:
        existing.reason = reason
        existing.created_at = datetime.utcnow()
        session.commit()
        session.refresh(existing)
        return existing
    suspect = Suspect(
        entity_type=entity_type,
        entity_id=entity_id,
        reason=reason,
        created_at=datetime.utcnow(),
    )
    session.add(suspect)
    session.commit()
    session.refresh(suspect)
    return suspect


def list_suspects(session: Session, entity_keys: Sequence[Tuple[str, str]]) -> set[str]:
    if not entity_keys:
        return set()
    conditions = [(Suspect.entity_type == et) & (Suspect.entity_id == eid) for et, eid in entity_keys]
    q = session.query(Suspect)
    if conditions:
        from sqlalchemy import or_

        q = q.filter(or_(*conditions))
    return {_node_key(s.entity_type, s.entity_id) for s in q.all()}


def set_suspects_from_requirement(
    session: Session,
    requirement_id: str,
    reason: Optional[str],
) -> List[Tuple[str, str, List[str]]]:
    impacts = build_downstream_paths(session, requirement_id)
    for entity_type, entity_id, _path in impacts:
        upsert_suspect(session, entity_type, entity_id, reason)
    return impacts


def build_rtm_rows(
    session: Session,
    requirement_ids: Sequence[str],
    requirement_snapshots: dict[str, dict],
) -> List[dict]:
    rows: List[dict] = []
    for requirement_id in requirement_ids:
        snapshot = requirement_snapshots.get(requirement_id, {})
        req_code = snapshot.get("req_code")
        title = snapshot.get("title")
        discipline = snapshot.get("discipline")
        req_type_primary = snapshot.get("req_type_primary")

        links = (
            session.query(Link)
            .filter(Link.deleted_at.is_(None))
            .filter(Link.source_type == "Requirement")
            .filter(Link.source_id == requirement_id)
            .all()
        )
        design_ids = [link.target_id for link in links if link.link_type == "SATISFIES"]
        test_ids = [link.target_id for link in links if link.link_type == "VERIFIES"]
        standard_ids = [link.target_id for link in links if link.link_type == "REFERENCES"]

        suspect_keys = [("Requirement", requirement_id)]
        suspect_keys += [("Design", item) for item in design_ids]
        suspect_keys += [("Test", item) for item in test_ids]
        suspect_keys += [("Standard", item) for item in standard_ids]
        suspects = list_suspects(session, suspect_keys)
        suspect_flag = _node_key("Requirement", requirement_id) in suspects
        if not suspect_flag:
            for entity_type, entity_id in suspect_keys[1:]:
                if _node_key(entity_type, entity_id) in suspects:
                    suspect_flag = True
                    break

        coverage_status = "OK"
        if req_type_primary == "Functional":
            coverage_status = "COVERED" if (design_ids or test_ids) else "MISSING"
        elif req_type_primary == "Regulatory":
            coverage_status = "COVERED" if standard_ids else "MISSING"

        rows.append(
            {
                "req_code": req_code,
                "requirement_title": title,
                "discipline": discipline,
                "req_type_primary": req_type_primary,
                "design_artifact_ids": design_ids,
                "test_case_ids": test_ids,
                "standard_clause_ids": standard_ids,
                "suspect": suspect_flag,
                "coverage_status": coverage_status,
            }
        )
    return rows
