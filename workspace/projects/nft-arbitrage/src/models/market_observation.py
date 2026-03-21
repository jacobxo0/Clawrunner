"""
MarketObservation - continuous loop: stores market state as knowledge.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric

from src.database import Base


class MarketObservation(Base):
    __tablename__ = "market_observations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    collection_id = Column(
        String(36), ForeignKey("collections.id"), nullable=False, index=True
    )
    observed_at = Column(DateTime, nullable=False, index=True)

    spread_pct = Column(Numeric(12, 6), nullable=True)
    bid_depth = Column(Numeric(12, 2), nullable=True)
    floor_eth = Column(Numeric(28, 18), nullable=True)
    best_bid_eth = Column(Numeric(28, 18), nullable=True)
    num_listings = Column(Numeric(12, 0), nullable=True)
    num_bids = Column(Numeric(12, 0), nullable=True)
    volume_24h_eth = Column(Numeric(28, 18), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
