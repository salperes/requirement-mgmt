"""0004_module3_traceability

Revision ID: 0004_module3_traceability
Revises: 0003_module2_workflow_collaboration
Create Date: 2026-01-18
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_module3_traceability"
down_revision = "0003_module2_workflow_collaboration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "links",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("target_id", sa.String(), nullable=False),
        sa.Column("link_type", sa.String(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
    )
    op.create_index("ix_links_source_type_source_id", "links", ["source_type", "source_id"])
    op.create_index("ix_links_target_type_target_id", "links", ["target_type", "target_id"])
    op.create_index("ix_links_link_type", "links", ["link_type"])
    op.create_index("ix_links_deleted_at", "links", ["deleted_at"])

    op.create_table(
        "suspects",
        sa.Column("entity_type", sa.String(), primary_key=True),
        sa.Column("entity_id", sa.String(), primary_key=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_suspects_entity_type_entity_id", "suspects", ["entity_type", "entity_id"])


def downgrade() -> None:
    op.drop_index("ix_suspects_entity_type_entity_id", table_name="suspects")
    op.drop_table("suspects")

    op.drop_index("ix_links_deleted_at", table_name="links")
    op.drop_index("ix_links_link_type", table_name="links")
    op.drop_index("ix_links_target_type_target_id", table_name="links")
    op.drop_index("ix_links_source_type_source_id", table_name="links")
    op.drop_table("links")
