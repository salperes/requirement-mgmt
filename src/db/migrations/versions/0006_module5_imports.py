"""0006_module5_imports

Revision ID: 0006_module5_imports
Revises: 0005_module4_verification
Create Date: 2026-01-18
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_module5_imports"
down_revision = "0005_module4_verification"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_sessions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("file_type", sa.String(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"]),
    )

    op.create_table(
        "imported_clauses",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("import_session_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("raw_text", sa.String(), nullable=False),
        sa.Column("location_ref", sa.String(), nullable=True),
        sa.Column("clause_index", sa.Integer(), nullable=False),
        sa.Column("parsed_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["import_session_id"], ["import_sessions.id"]),
    )
    op.create_index("ix_imported_clauses_import_session_id", "imported_clauses", ["import_session_id"])
    op.create_index("ix_imported_clauses_clause_index", "imported_clauses", ["clause_index"])

    op.create_table(
        "source_references",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("requirement_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("import_session_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("imported_clause_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"]),
        sa.ForeignKeyConstraint(["import_session_id"], ["import_sessions.id"]),
        sa.ForeignKeyConstraint(["imported_clause_id"], ["imported_clauses.id"]),
    )
    op.create_index("ix_source_references_requirement_id", "source_references", ["requirement_id"])
    op.create_index("ix_source_references_import_session_id", "source_references", ["import_session_id"])
    op.create_index("ix_source_references_imported_clause_id", "source_references", ["imported_clause_id"])


def downgrade() -> None:
    op.drop_index("ix_source_references_imported_clause_id", table_name="source_references")
    op.drop_index("ix_source_references_import_session_id", table_name="source_references")
    op.drop_index("ix_source_references_requirement_id", table_name="source_references")
    op.drop_table("source_references")

    op.drop_index("ix_imported_clauses_clause_index", table_name="imported_clauses")
    op.drop_index("ix_imported_clauses_import_session_id", table_name="imported_clauses")
    op.drop_table("imported_clauses")

    op.drop_table("import_sessions")