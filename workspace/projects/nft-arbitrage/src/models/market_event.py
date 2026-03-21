"""
MarketEvent model -- raw market events (sales, listings, bids, transfers)
ingested from marketplace APIs and websocket feeds.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Numeric, JSON,
)

from src.database import Base


class MarketEvent(Base):
    __tablename__ = "market_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(50), nullable=False, index=True)  # sale, listing, bid, transfer, cancel
    collection_id = Column(
        String(36), ForeignKey("collections.id"), nullable=True, index=True
    )
    token_id = Column(String(255), nullable=True)
    marketplace = Column(String(100), nullable=True)
    from_address = Column(String(255), nullable=True)
    to_address = Column(String(255), nullable=True)
    price = Column(Numeric(precision=28, scale=18), nullable=True)
    currency = Column(String(20), nullable=True)
    tx_hash = Column(String(255), nullable=True, index=True)
    block_number = Column(String(50), nullable=True)
    raw_data = Column(JSON, nullable=True)
    event_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return (
            f"<MarketEvent type={self.event_type!r} "
            f"token={self.token_id} price={self.price}>"
        )
