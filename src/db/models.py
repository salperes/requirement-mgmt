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
    comments = relationship("Comment", back_populates="requirement")


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


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(Uuid(as_uuid=True), ForeignKey("requirements.id"), nullable=False)
    author_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    text = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    edited_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    requirement = relationship("Requirement", back_populates="comments")
    author = relationship("User")
    mentions = relationship("CommentMention", back_populates="comment", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_comments_requirement_id", "requirement_id"),
        Index("ix_comments_author_user_id", "author_user_id"),
        Index("ix_comments_created_at", "created_at"),
    )


class CommentMention(Base):
    __tablename__ = "comment_mentions"

    comment_id = Column(Uuid(as_uuid=True), ForeignKey("comments.id"), primary_key=True)
    mentioned_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), primary_key=True)

    comment = relationship("Comment", back_populates="mentions")
    mentioned_user = relationship("User")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    body = Column(String, nullable=True)
    entity_type = Column(String, nullable=True)
    entity_id = Column(String, nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    user = relationship("User")

    __table_args__ = (Index("ix_notifications_user_id_is_read_created_at", "user_id", "is_read", "created_at"),)


class ApprovalRecord(Base):
    __tablename__ = "approval_records"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(Uuid(as_uuid=True), ForeignKey("requirements.id"), nullable=False)
    approver_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    decision = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    signature_provider = Column(String, nullable=False, default="placeholder")
    signature_metadata = Column(JSON, nullable=False, default=dict)
    signed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    requirement = relationship("Requirement")
    approver = relationship("User")

    __table_args__ = (
        Index("ix_approval_records_requirement_id", "requirement_id"),
        Index("ix_approval_records_approver_user_id", "approver_user_id"),
        Index("ix_approval_records_signed_at", "signed_at"),
    )


class Link(Base):
    __tablename__ = "links"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type = Column(String, nullable=False)
    source_id = Column(String, nullable=False)
    target_type = Column(String, nullable=False)
    target_id = Column(String, nullable=False)
    link_type = Column(String, nullable=False)
    created_by_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    created_by = relationship("User")

    __table_args__ = (
        Index("ix_links_source_type_source_id", "source_type", "source_id"),
        Index("ix_links_target_type_target_id", "target_type", "target_id"),
        Index("ix_links_link_type", "link_type"),
        Index("ix_links_deleted_at", "deleted_at"),
    )


class Suspect(Base):
    __tablename__ = "suspects"

    entity_type = Column(String, primary_key=True)
    entity_id = Column(String, primary_key=True)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (Index("ix_suspects_entity_type_entity_id", "entity_type", "entity_id"),)


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_code = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    verification_method = Column(String, nullable=False)
    owner_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    owner = relationship("User")


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_case_id = Column(Uuid(as_uuid=True), ForeignKey("test_cases.id"), nullable=False)
    requirement_id = Column(Uuid(as_uuid=True), ForeignKey("requirements.id"), nullable=False)
    baseline_id = Column(Uuid(as_uuid=True), ForeignKey("baselines.id"), nullable=True)
    status = Column(String, nullable=False)
    executed_by_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    executed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    comment = Column(String, nullable=True)

    test_case = relationship("TestCase")
    requirement = relationship("Requirement")
    baseline = relationship("Baseline")
    executed_by = relationship("User")

    __table_args__ = (
        Index("ix_verification_results_test_case_id", "test_case_id"),
        Index("ix_verification_results_requirement_id", "requirement_id"),
        Index("ix_verification_results_baseline_id", "baseline_id"),
        Index("ix_verification_results_status", "status"),
    )


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    related_type = Column(String, nullable=False)
    related_id = Column(Uuid(as_uuid=True), nullable=False)
    evidence_type = Column(String, nullable=False)
    uri_or_text = Column(String, nullable=False)
    checksum = Column(String, nullable=True)
    uploaded_by_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    uploaded_by = relationship("User")

    __table_args__ = (
        Index("ix_evidence_related_type_related_id", "related_type", "related_id"),
        Index("ix_evidence_uploaded_by_user_id", "uploaded_by_user_id"),
    )


class ImportSession(Base):
    __tablename__ = "import_sessions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    uploaded_by_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    status = Column(String, nullable=False, default="IN_PROGRESS")

    uploaded_by = relationship("User")
    clauses = relationship("ImportedClause", back_populates="import_session", cascade="all, delete-orphan")
    source_references = relationship("SourceReference", back_populates="import_session")


class ImportedClause(Base):
    __tablename__ = "imported_clauses"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_session_id = Column(Uuid(as_uuid=True), ForeignKey("import_sessions.id"), nullable=False)
    raw_text = Column(String, nullable=False)
    location_ref = Column(String, nullable=True)
    clause_index = Column(Integer, nullable=False)
    parsed_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    import_session = relationship("ImportSession", back_populates="clauses")
    source_references = relationship("SourceReference", back_populates="imported_clause")

    __table_args__ = (
        Index("ix_imported_clauses_import_session_id", "import_session_id"),
        Index("ix_imported_clauses_clause_index", "clause_index"),
    )


class SourceReference(Base):
    __tablename__ = "source_references"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(Uuid(as_uuid=True), ForeignKey("requirements.id"), nullable=False)
    import_session_id = Column(Uuid(as_uuid=True), ForeignKey("import_sessions.id"), nullable=False)
    imported_clause_id = Column(Uuid(as_uuid=True), ForeignKey("imported_clauses.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    requirement = relationship("Requirement")
    import_session = relationship("ImportSession", back_populates="source_references")
    imported_clause = relationship("ImportedClause", back_populates="source_references")

    __table_args__ = (
        Index("ix_source_references_requirement_id", "requirement_id"),
        Index("ix_source_references_import_session_id", "import_session_id"),
        Index("ix_source_references_imported_clause_id", "imported_clause_id"),
    )
