"""0007_module6_compliance

Revision ID: 0007_module6_compliance
Revises: 0006_module5_imports
Create Date: 2026-01-19
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_module6_compliance"
down_revision = "0006_module5_imports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "standards",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=True),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("publisher", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_standards_code", "standards", ["code"])
    op.create_index("ix_standards_code_version", "standards", ["code", "version"])

    op.create_table(
        "standard_clauses",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("standard_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("clause_code", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["standard_id"], ["standards.id"]),
    )
    op.create_index("ix_standard_clauses_standard_id", "standard_clauses", ["standard_id"])
    op.create_index("ix_standard_clauses_clause_code", "standard_clauses", ["clause_code"])

    op.create_table(
        "compliance_mappings",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("requirement_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("standard_clause_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("compliance_status", sa.String(), nullable=False),
        sa.Column("justification", sa.String(), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"]),
        sa.ForeignKeyConstraint(["standard_clause_id"], ["standard_clauses.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
    )
    op.create_index("ix_compliance_mappings_requirement_id", "compliance_mappings", ["requirement_id"])
    op.create_index("ix_compliance_mappings_standard_clause_id", "compliance_mappings", ["standard_clause_id"])
    op.create_index("ix_compliance_mappings_status", "compliance_mappings", ["compliance_status"])


def downgrade() -> None:
    op.drop_index("ix_compliance_mappings_status", table_name="compliance_mappings")
    op.drop_index("ix_compliance_mappings_standard_clause_id", table_name="compliance_mappings")
    op.drop_index("ix_compliance_mappings_requirement_id", table_name="compliance_mappings")
    op.drop_table("compliance_mappings")

    op.drop_index("ix_standard_clauses_clause_code", table_name="standard_clauses")
    op.drop_index("ix_standard_clauses_standard_id", table_name="standard_clauses")
    op.drop_table("standard_clauses")

    op.drop_index("ix_standards_code_version", table_name="standards")
    op.drop_index("ix_standards_code", table_name="standards")
    op.drop_table("standards")