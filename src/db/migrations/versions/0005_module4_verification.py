"""0005_module4_verification

Revision ID: 0005_module4_verification
Revises: 0004_module3_traceability
Create Date: 2026-01-18
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_module4_verification"
down_revision = "0004_module3_traceability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE SEQUENCE IF NOT EXISTS tc_code_seq START 1")

    op.create_table(
        "test_cases",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("test_code", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("verification_method", sa.String(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
    )
    op.create_index("ix_test_cases_test_code", "test_cases", ["test_code"], unique=True)
    op.create_index("ix_test_cases_owner_user_id", "test_cases", ["owner_user_id"])
    op.create_index("ix_test_cases_deleted_at", "test_cases", ["deleted_at"])

    op.create_table(
        "verification_results",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("test_case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("requirement_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("baseline_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("executed_by_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["test_case_id"], ["test_cases.id"]),
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"]),
        sa.ForeignKeyConstraint(["baseline_id"], ["baselines.id"]),
        sa.ForeignKeyConstraint(["executed_by_user_id"], ["users.id"]),
    )
    op.create_index("ix_verification_results_test_case_id", "verification_results", ["test_case_id"])
    op.create_index("ix_verification_results_requirement_id", "verification_results", ["requirement_id"])
    op.create_index("ix_verification_results_baseline_id", "verification_results", ["baseline_id"])
    op.create_index("ix_verification_results_status", "verification_results", ["status"])

    op.create_table(
        "evidence",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("related_type", sa.String(), nullable=False),
        sa.Column("related_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("evidence_type", sa.String(), nullable=False),
        sa.Column("uri_or_text", sa.String(), nullable=False),
        sa.Column("checksum", sa.String(), nullable=True),
        sa.Column("uploaded_by_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"]),
    )
    op.create_index("ix_evidence_related_type_related_id", "evidence", ["related_type", "related_id"])
    op.create_index("ix_evidence_uploaded_by_user_id", "evidence", ["uploaded_by_user_id"])


def downgrade() -> None:
    op.drop_index("ix_evidence_uploaded_by_user_id", table_name="evidence")
    op.drop_index("ix_evidence_related_type_related_id", table_name="evidence")
    op.drop_table("evidence")

    op.drop_index("ix_verification_results_status", table_name="verification_results")
    op.drop_index("ix_verification_results_baseline_id", table_name="verification_results")
    op.drop_index("ix_verification_results_requirement_id", table_name="verification_results")
    op.drop_index("ix_verification_results_test_case_id", table_name="verification_results")
    op.drop_table("verification_results")

    op.drop_index("ix_test_cases_deleted_at", table_name="test_cases")
    op.drop_index("ix_test_cases_owner_user_id", table_name="test_cases")
    op.drop_index("ix_test_cases_test_code", table_name="test_cases")
    op.drop_table("test_cases")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP SEQUENCE IF EXISTS tc_code_seq")
