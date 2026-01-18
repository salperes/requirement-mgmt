"""0002_requirements_core

Revision ID: 0002_requirements_core
Revises: 0001_init
Create Date: 2026-01-18
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_requirements_core"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE SEQUENCE IF NOT EXISTS req_code_seq START 1")

    op.create_table(
        "requirements",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("req_code", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("discipline", sa.String(), nullable=False),
        sa.Column("req_type_primary", sa.String(), nullable=False),
        sa.Column("req_type_secondary", sa.JSON(), nullable=True),
        sa.Column("is_explanation", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(), nullable=False, server_default=sa.text("'Draft'")),
        sa.Column("owner_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(), nullable=False, server_default=sa.text("'manual'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
    )
    op.create_index("ix_requirements_req_code", "requirements", ["req_code"], unique=True)
    op.create_index("ix_requirements_discipline", "requirements", ["discipline"])
    op.create_index("ix_requirements_req_type_primary", "requirements", ["req_type_primary"])
    op.create_index("ix_requirements_status", "requirements", ["status"])
    op.create_index("ix_requirements_deleted_at", "requirements", ["deleted_at"])
    op.create_index("ix_requirements_owner_user_id", "requirements", ["owner_user_id"])

    op.create_table(
        "requirement_versions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("requirement_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("snapshot_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("changed_by_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("change_reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"]),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["users.id"]),
        sa.UniqueConstraint("requirement_id", "version_no", name="uq_requirement_versions_req_id_version_no"),
    )
    op.create_index("ix_requirement_versions_changed_by_user_id", "requirement_versions", ["changed_by_user_id"])

    op.create_table(
        "baselines",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("baseline_tag", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
    )
    op.create_index("ix_baselines_baseline_tag", "baselines", ["baseline_tag"], unique=True)

    op.create_table(
        "baseline_items",
        sa.Column("baseline_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("requirement_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("requirement_version_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["baseline_id"], ["baselines.id"]),
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"]),
        sa.ForeignKeyConstraint(["requirement_version_id"], ["requirement_versions.id"]),
        sa.PrimaryKeyConstraint("baseline_id", "requirement_id"),
    )
    op.create_index("ix_baseline_items_baseline_id", "baseline_items", ["baseline_id"])


def downgrade() -> None:
    op.drop_index("ix_baseline_items_baseline_id", table_name="baseline_items")
    op.drop_table("baseline_items")

    op.drop_index("ix_baselines_baseline_tag", table_name="baselines")
    op.drop_table("baselines")

    op.drop_index("ix_requirement_versions_changed_by_user_id", table_name="requirement_versions")
    op.drop_table("requirement_versions")

    op.drop_index("ix_requirements_owner_user_id", table_name="requirements")
    op.drop_index("ix_requirements_deleted_at", table_name="requirements")
    op.drop_index("ix_requirements_status", table_name="requirements")
    op.drop_index("ix_requirements_req_type_primary", table_name="requirements")
    op.drop_index("ix_requirements_discipline", table_name="requirements")
    op.drop_index("ix_requirements_req_code", table_name="requirements")
    op.drop_table("requirements")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP SEQUENCE IF EXISTS req_code_seq")
