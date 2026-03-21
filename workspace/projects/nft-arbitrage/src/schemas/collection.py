"""
Pydantic schemas for Collection API requests and responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CollectionBase(BaseModel):
    slug: str
    name: str
    chain: str = "ethereum"
    contract_address: Optional[str] = None
    total_supply: Optional[int] = None
    royalty_bps: Optional[int] = 0
    marketplace_fee_bps: Optional[int] = 250


class CollectionCreate(CollectionBase):
    pass


class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    chain: Optional[str] = None
    contract_address: Optional[str] = None
    total_supply: Optional[int] = None
    royalty_bps: Optional[int] = None
    marketplace_fee_bps: Optional[int] = None
    floor_price: Optional[float] = None
    best_bid: Optional[float] = None
    is_active: Optional[bool] = None


class CollectionResponse(CollectionBase):
    id: str
    floor_price: Optional[float] = None
    best_bid: Optional[float] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CollectionSummary(BaseModel):
    id: str
    slug: str
    name: str
    chain: str
    contract_address: Optional[str] = None
    floor_price: Optional[float] = None
    best_bid: Optional[float] = None
    royalty_bps: Optional[int] = 0
    marketplace_fee_bps: Optional[int] = 250
    is_active: bool

    class Config:
        from_attributes = True
