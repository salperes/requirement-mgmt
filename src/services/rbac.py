from typing import Iterable

ROLE_PERMISSIONS = {
    "Admin": {
        "auth:login",
        "auth:me",
        "admin:users:read",
        "admin:users:write",
        "admin:roles:write",
        "audit:read",
        "req:create",
        "req:read",
        "req:update",
        "req:delete",
        "req:versions:read",
        "baseline:create",
        "baseline:read",
        "baseline:export",
    },
    "RequirementOwner": {
        "auth:login",
        "auth:me",
        "req:create",
        "req:read",
        "req:update",
        "req:delete",
        "req:versions:read",
        "baseline:create",
        "baseline:read",
        "baseline:export",
    },
    "Reviewer": {
        "auth:login",
        "auth:me",
        "req:read",
        "req:versions:read",
        "baseline:read",
        "baseline:export",
    },
    "Approver": {
        "auth:login",
        "auth:me",
        "req:read",
        "req:versions:read",
        "baseline:read",
        "baseline:export",
    },
    "Viewer": {
        "auth:login",
        "auth:me",
        "req:read",
        "req:versions:read",
        "baseline:read",
        "baseline:export",
    },
}


def resolve_permissions(role_names: Iterable[str]) -> set[str]:
    permissions: set[str] = set()
    for role in role_names:
        permissions |= ROLE_PERMISSIONS.get(role, set())
    return permissions


def has_permission(role_names: Iterable[str], permission: str) -> bool:
    return permission in resolve_permissions(role_names)