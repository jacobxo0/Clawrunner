"""Add wash_score and liquidity_score columns to collections

Revision ID: 001
Revises: None
Create Date: 2026-02-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("collections") as batch_op:
        batch_op.add_column(sa.Column("wash_score", sa.Float(), nullable=True, server_default="0.0"))
        batch_op.add_column(sa.Column("liquidity_score", sa.Float(), nullable=True, server_default="0.0"))


def downgrade() -> None:
    with op.batch_alter_table("collections") as batch_op:
        batch_op.drop_column("liquidity_score")
        batch_op.drop_column("wash_score")
