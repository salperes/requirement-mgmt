"""0008_projects

Revision ID: 0008_projects
Revises: 0007_module6_compliance
Create Date: 2026-01-22
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_projects"
down_revision = "0007_module6_compliance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("enforce_regulatory_mapping", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_by_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
    )
    op.create_index("ix_projects_name", "projects", ["name"])


def downgrade() -> None:
    op.drop_index("ix_projects_name", table_name="projects")
    op.drop_table("projects")
