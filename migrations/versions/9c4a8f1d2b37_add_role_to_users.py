"""Add role to users.

Revision ID: 9c4a8f1d2b37
Revises: 5e775ba7535a
Create Date: 2026-11-08

"""
from alembic import op
import sqlalchemy as sa


revision = "9c4a8f1d2b37"
down_revision = "5e775ba7535a"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column("role", sa.String(length=30), server_default="user", nullable=False)
        )


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("role")