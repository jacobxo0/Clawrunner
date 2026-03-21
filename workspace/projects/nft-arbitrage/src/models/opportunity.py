"""
Opportunity model -- a detected arbitrage opportunity.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, DateTime, ForeignKey, Numeric, JSON,
)

from src.database import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy = Column(String(100), nullable=False, index=True)
    collection_id = Column(
        String(36), ForeignKey("collections.id"), nullable=False, index=True
    )
    slug = Column(String(255), nullable=True, index=True)
    chain = Column(String(50), nullable=True, default="ethereum")
    token_id = Column(String(255), nullable=True)

    # Venue info
    buy_venue = Column(String(100), nullable=False)
    sell_venue = Column(String(100), nullable=False)

    # Financials (high-precision decimals for ETH amounts)
    buy_price = Column(Numeric(precision=28, scale=18), nullable=False)
    expected_exit = Column(Numeric(precision=28, scale=18), nullable=False)
    marketplace_fee = Column(Numeric(precision=28, scale=18), nullable=True, default=0)
    royalty_fee = Column(Numeric(precision=28, scale=18), nullable=True, default=0)
    gas_estimate = Column(Numeric(precision=28, scale=18), nullable=True, default=0)
    risk_buffer = Column(Numeric(precision=28, scale=18), nullable=True, default=0)
    net_profit = Column(Numeric(precision=28, scale=18), nullable=True)
    roi = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)

    # Risk & QC
    risk_flags = Column(JSON, nullable=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    qc_result = Column(JSON, nullable=True)
    qc_verdict = Column(String(50), nullable=True)

    # Order hashes for on-chain execution
    listing_order_hash = Column(String(255), nullable=True)
    bid_order_hash = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return (
            f"<Opportunity id={self.id[:8]}... strategy={self.strategy!r} "
            f"roi={self.roi} status={self.status!r}>"
        )
