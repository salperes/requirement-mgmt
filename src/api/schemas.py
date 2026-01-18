from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: EmailStr
    display_name: str
    is_active: bool
    roles: List[str]


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str
    roles: List[str] = []


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserRolesUpdate(BaseModel):
    roles: List[str]


class AuditLogOut(BaseModel):
    id: str
    request_id: str
    actor_user_id: Optional[str]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    payload_json: Dict[str, Any]
    created_at: datetime