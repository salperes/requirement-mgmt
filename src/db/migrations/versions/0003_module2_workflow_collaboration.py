"""0003_module2_workflow_collaboration

Revision ID: 0003_module2_workflow_collaboration
Revises: 0002_requirements_core
Create Date: 2026-01-18
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_module2_workflow_collaboration"
down_revision = "0002_requirements_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "comments",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("requirement_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("author_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"]),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"]),
    )
    op.create_index("ix_comments_requirement_id", "comments", ["requirement_id"])
    op.create_index("ix_comments_author_user_id", "comments", ["author_user_id"])
    op.create_index("ix_comments_created_at", "comments", ["created_at"])

    op.create_table(
        "comment_mentions",
        sa.Column("comment_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("mentioned_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["comment_id"], ["comments.id"]),
        sa.ForeignKeyConstraint(["mentioned_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("comment_id", "mentioned_user_id"),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=True),
        sa.Column("entity_type", sa.String(), nullable=True),
        sa.Column("entity_id", sa.String(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index(
        "ix_notifications_user_id_is_read_created_at",
        "notifications",
        ["user_id", "is_read", "created_at"],
    )

    op.create_table(
        "approval_records",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("requirement_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("approver_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("signature_provider", sa.String(), nullable=False, server_default=sa.text("'placeholder'")),
        sa.Column("signature_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"]),
        sa.ForeignKeyConstraint(["approver_user_id"], ["users.id"]),
    )
    op.create_index("ix_approval_records_requirement_id", "approval_records", ["requirement_id"])
    op.create_index("ix_approval_records_approver_user_id", "approval_records", ["approver_user_id"])
    op.create_index("ix_approval_records_signed_at", "approval_records", ["signed_at"])


def downgrade() -> None:
    op.drop_index("ix_approval_records_signed_at", table_name="approval_records")
    op.drop_index("ix_approval_records_approver_user_id", table_name="approval_records")
    op.drop_index("ix_approval_records_requirement_id", table_name="approval_records")
    op.drop_table("approval_records")

    op.drop_index("ix_notifications_user_id_is_read_created_at", table_name="notifications")
    op.drop_table("notifications")

    op.drop_table("comment_mentions")

    op.drop_index("ix_comments_created_at", table_name="comments")
    op.drop_index("ix_comments_author_user_id", table_name="comments")
    op.drop_index("ix_comments_requirement_id", table_name="comments")
    op.drop_table("comments")
