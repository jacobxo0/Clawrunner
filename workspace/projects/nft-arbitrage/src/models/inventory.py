"""
Inventory model -- tracks NFTs currently owned by the bot's wallet.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Numeric, Boolean,
)

from src.database import Base


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    collection_id = Column(
        String(36), ForeignKey("collections.id"), nullable=False, index=True
    )
    token_id = Column(String(255), nullable=False)
    wallet_address = Column(String(255), nullable=False, index=True)
    acquisition_price = Column(Numeric(precision=28, scale=18), nullable=True)
    acquisition_tx = Column(String(255), nullable=True)
    trade_id = Column(
        String(36), ForeignKey("trades.id"), nullable=True
    )
    is_held = Column(Boolean, default=True, nullable=False)
    listed_price = Column(Numeric(precision=28, scale=18), nullable=True)
    acquired_at = Column(DateTime, nullable=True)
    disposed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return (
            f"<Inventory token={self.token_id} "
            f"held={self.is_held} price={self.acquisition_price}>"
        )
