"""
Bid model -- tracks active bids / offers on NFT collections and tokens.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Numeric, Boolean, JSON,
)

from src.database import Base


class Bid(Base):
    __tablename__ = "bids"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    collection_id = Column(
        String(36), ForeignKey("collections.id"), nullable=False, index=True
    )
    token_id = Column(String(255), nullable=True, index=True)  # NULL = collection bid
    marketplace = Column(String(100), nullable=False, index=True)
    bidder = Column(String(255), nullable=True)
    price = Column(Numeric(precision=28, scale=18), nullable=False)
    currency = Column(String(20), nullable=True, default="WETH")
    order_hash = Column(String(255), nullable=True, unique=True)
    is_active = Column(Boolean, default=True, nullable=False)
    raw_data = Column(JSON, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return (
            f"<Bid collection={self.collection_id[:8]}... "
            f"marketplace={self.marketplace!r} price={self.price}>"
        )
