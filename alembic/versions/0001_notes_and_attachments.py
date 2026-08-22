"""create notes and attachments

Revision ID: 0001_notes
Revises:
Create Date: 2026-08-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_notes"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        if_not_exists=True,
    )
    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=512), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=True),
        sa.Column("size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("parent_table", sa.String(length=64), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=False),
        sa.Column("field_name", sa.String(length=64), nullable=False),
        sa.UniqueConstraint("key", name="uq_attachments_key"),
        if_not_exists=True,
    )
    op.create_index(
        "ix_attachments_parent_table",
        "attachments",
        ["parent_table"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_attachments_parent_id",
        "attachments",
        ["parent_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_attachments_field_name",
        "attachments",
        ["field_name"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_attachments_parent_field",
        "attachments",
        ["parent_table", "parent_id", "field_name"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_attachments_parent_field", table_name="attachments")
    op.drop_index("ix_attachments_field_name", table_name="attachments")
    op.drop_index("ix_attachments_parent_id", table_name="attachments")
    op.drop_index("ix_attachments_parent_table", table_name="attachments")
    op.drop_table("attachments")
    op.drop_table("notes")
