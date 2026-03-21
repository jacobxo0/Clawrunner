"""Add market_observations and decision_knowledge tables.

Revision ID: 002
Revises: 001
Create Date: 2026-02-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "market_observations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("collection_id", sa.String(36), sa.ForeignKey("collections.id"), nullable=False, index=True),
        sa.Column("observed_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("spread_pct", sa.Numeric(12, 6), nullable=True),
        sa.Column("bid_depth", sa.Numeric(12, 2), nullable=True),
        sa.Column("floor_eth", sa.Numeric(28, 18), nullable=True),
        sa.Column("best_bid_eth", sa.Numeric(28, 18), nullable=True),
        sa.Column("num_listings", sa.Numeric(12, 0), nullable=True),
        sa.Column("num_bids", sa.Numeric(12, 0), nullable=True),
        sa.Column("volume_24h_eth", sa.Numeric(28, 18), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "decision_knowledge",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=True, index=True),
        sa.Column("collection_id", sa.String(36), sa.ForeignKey("collections.id"), nullable=False, index=True),
        sa.Column("strategy", sa.String(100), nullable=False, index=True),
        sa.Column("observed_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("spread_pct", sa.Numeric(12, 6), nullable=True),
        sa.Column("bid_depth", sa.Numeric(12, 2), nullable=True),
        sa.Column("roi_pct", sa.Numeric(12, 4), nullable=True),
        sa.Column("fill_prob_predicted", sa.Numeric(6, 4), nullable=True),
        sa.Column("buy_price_eth", sa.Numeric(28, 18), nullable=True),
        sa.Column("outcome_filled", sa.Boolean(), nullable=True),
        sa.Column("outcome_pnl", sa.Numeric(28, 18), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("decision_knowledge")
    op.drop_table("market_observations")
