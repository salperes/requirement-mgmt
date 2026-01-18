import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Table, Uuid, Index
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


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    req_code = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=True)
    text = Column(String, nullable=False)
    discipline = Column(String, nullable=False, index=True)
    req_type_primary = Column(String, nullable=False, index=True)
    req_type_secondary = Column(JSON, nullable=True)
    is_explanation = Column(Boolean, nullable=False, default=False)
    status = Column(String, nullable=False, default="Draft", index=True)
    owner_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    source = Column(String, nullable=False, default="manual")
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    owner = relationship("User")
    versions = relationship("RequirementVersion", back_populates="requirement")


class RequirementVersion(Base):
    __tablename__ = "requirement_versions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(Uuid(as_uuid=True), ForeignKey("requirements.id"), nullable=False)
    version_no = Column(Integer, nullable=False)
    snapshot_json = Column(JSON, nullable=False, default=dict)
    changed_by_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    change_reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    requirement = relationship("Requirement", back_populates="versions")
    changed_by = relationship("User")

    __table_args__ = (
        Index("uq_requirement_versions_req_id_version_no", "requirement_id", "version_no", unique=True),
    )


class Baseline(Base):
    __tablename__ = "baselines"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    baseline_tag = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_by_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    created_by = relationship("User")
    items = relationship("BaselineItem", back_populates="baseline")


class BaselineItem(Base):
    __tablename__ = "baseline_items"

    baseline_id = Column(Uuid(as_uuid=True), ForeignKey("baselines.id"), primary_key=True)
    requirement_id = Column(Uuid(as_uuid=True), ForeignKey("requirements.id"), primary_key=True)
    requirement_version_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("requirement_versions.id"),
        nullable=False,
    )

    baseline = relationship("Baseline", back_populates="items")
    requirement = relationship("Requirement")
    requirement_version = relationship("RequirementVersion")

    __table_args__ = (Index("ix_baseline_items_baseline_id", "baseline_id"),)
