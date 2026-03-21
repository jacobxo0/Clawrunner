"""
Pydantic schemas for Opportunity API requests and responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class OpportunityBase(BaseModel):
    strategy: str
    collection_id: str
    token_id: Optional[str] = None
    buy_venue: str
    sell_venue: str
    buy_price: float
    expected_exit: float


class OpportunityCreate(OpportunityBase):
    marketplace_fee: Optional[float] = 0
    royalty_fee: Optional[float] = 0
    gas_estimate: Optional[float] = 0
    risk_buffer: Optional[float] = 0
    net_profit: Optional[float] = None
    roi: Optional[float] = None
    confidence: Optional[float] = None
    risk_flags: Optional[Dict[str, Any]] = None
    listing_order_hash: Optional[str] = None
    bid_order_hash: Optional[str] = None


class OpportunityUpdate(BaseModel):
    status: Optional[str] = None
    qc_result: Optional[Dict[str, Any]] = None
    qc_verdict: Optional[str] = None
    confidence: Optional[float] = None
    risk_flags: Optional[Dict[str, Any]] = None
    net_profit: Optional[float] = None
    roi: Optional[float] = None


class OpportunityResponse(BaseModel):
    id: str
    strategy: str
    collection_id: str
    token_id: Optional[str] = None
    buy_venue: str
    sell_venue: str
    buy_price: float
    expected_exit: float
    marketplace_fee: Optional[float] = None
    royalty_fee: Optional[float] = None
    gas_estimate: Optional[float] = None
    risk_buffer: Optional[float] = None
    net_profit: Optional[float] = None
    roi: Optional[float] = None
    confidence: Optional[float] = None
    risk_flags: Optional[Dict[str, Any]] = None
    status: str
    qc_result: Optional[Dict[str, Any]] = None
    qc_verdict: Optional[str] = None
    listing_order_hash: Optional[str] = None
    bid_order_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OpportunitySummary(BaseModel):
    id: str
    strategy: str
    collection_id: str
    token_id: Optional[str] = None
    buy_price: float
    expected_exit: float = 0
    net_profit: Optional[float] = None
    roi: Optional[float] = None
    confidence: Optional[float] = None
    qc_verdict: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
