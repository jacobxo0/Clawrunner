"""
Trade model -- records executed buy/sell transactions.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Numeric,
)

from src.database import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id = Column(
        String(36), ForeignKey("opportunities.id"), nullable=True, index=True
    )
    collection_id = Column(
        String(36), ForeignKey("collections.id"), nullable=False, index=True
    )
    token_id = Column(String(255), nullable=True)
    side = Column(String(10), nullable=False)  # "buy" or "sell"
    marketplace = Column(String(100), nullable=False)
    price = Column(Numeric(precision=28, scale=18), nullable=False)
    gas_used = Column(Numeric(precision=28, scale=18), nullable=True)
    tx_hash = Column(String(255), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    executed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return (
            f"<Trade id={self.id[:8]}... side={self.side!r} "
            f"price={self.price} status={self.status!r}>"
        )
