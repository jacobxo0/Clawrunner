"""
Pydantic schemas for Trade API requests and responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TradeBase(BaseModel):
    opportunity_id: Optional[str] = None
    collection_id: str
    token_id: Optional[str] = None
    side: str  # "buy" or "sell"
    marketplace: str
    price: float


class TradeCreate(TradeBase):
    gas_used: Optional[float] = None
    tx_hash: Optional[str] = None
    status: str = "pending"
    executed_at: Optional[datetime] = None


class TradeUpdate(BaseModel):
    status: Optional[str] = None
    tx_hash: Optional[str] = None
    gas_used: Optional[float] = None
    executed_at: Optional[datetime] = None


class TradeResponse(BaseModel):
    id: str
    opportunity_id: Optional[str] = None
    collection_id: str
    token_id: Optional[str] = None
    side: str
    marketplace: str
    price: float
    gas_used: Optional[float] = None
    tx_hash: Optional[str] = None
    status: str
    executed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TradeSummary(BaseModel):
    id: str
    token_id: Optional[str] = None
    side: str
    marketplace: str
    price: float
    gas_used: Optional[float] = None
    tx_hash: Optional[str] = None
    status: str
    executed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
