"""
Collection model -- tracks NFT collections being monitored for arbitrage.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, Numeric,
)

from src.database import Base


class Collection(Base):
    __tablename__ = "collections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    chain = Column(String(50), nullable=False, default="ethereum")
    contract_address = Column(String(255), nullable=True, index=True)
    total_supply = Column(Integer, nullable=True)
    royalty_bps = Column(Integer, nullable=True, default=0)
    marketplace_fee_bps = Column(Integer, nullable=True, default=250)
    floor_price = Column(Numeric(precision=28, scale=18), nullable=True)
    best_bid = Column(Numeric(precision=28, scale=18), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    wash_score = Column(Float, nullable=True, default=0.0)
    liquidity_score = Column(Float, nullable=True, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<Collection slug={self.slug!r} chain={self.chain!r}>"
