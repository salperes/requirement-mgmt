from __future__ import annotations

from typing import Iterable


ALLOWED_TRANSITIONS: dict[tuple[str, str], set[str]] = {
    ("Draft", "Review"): {"RequirementOwner", "Reviewer", "Admin"},
    ("Review", "Draft"): {"RequirementOwner", "Reviewer", "Admin"},
    ("Review", "Approved"): {"Approver", "Admin"},
    ("Review", "Rejected"): {"Approver", "Admin"},
    ("Approved", "Review"): {"Admin"},
    ("Rejected", "Review"): {"RequirementOwner", "Admin"},
}


def resolve_allowed_transition(current_status: str, to_status: str, role_names: Iterable[str]) -> bool:
    allowed_roles = ALLOWED_TRANSITIONS.get((current_status, to_status), set())
    if not allowed_roles:
        return False
    return bool(set(role_names) & allowed_roles)
