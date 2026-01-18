import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String, Table, Uuid
from sqlalchemy.orm import relationship

from src.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    roles = relationship("Role", secondary="user_roles", back_populates="users")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)

    users = relationship("User", secondary="user_roles", back_populates="roles")


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Uuid(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("role_id", Uuid(as_uuid=True), ForeignKey("roles.id"), primary_key=True),
)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(String, nullable=False, index=True)
    actor_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=True)
    entity_id = Column(String, nullable=True)
    payload_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    actor = relationship("User")
