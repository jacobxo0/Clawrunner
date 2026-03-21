"""
Trade endpoints — read-only listing of executed trades.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from src.database import async_session
from src.models.trade import Trade
from src.schemas.trade import TradeResponse, TradeSummary

router = APIRouter(prefix="/api", tags=["trades"])


@router.get("/trades", response_model=list[TradeSummary])
async def list_trades(
    status: Optional[str] = Query(None, description="Filter by status"),
    side: Optional[str] = Query(None, description="Filter by side (buy/sell)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List trades with optional filters."""
    async with async_session() as session:
        query = select(Trade).order_by(Trade.created_at.desc())

        if status:
            query = query.where(Trade.status == status)
        if side:
            query = query.where(Trade.side == side)

        query = query.offset(offset).limit(limit)
        result = await session.execute(query)
        trades = result.scalars().all()
        return [TradeSummary.model_validate(t) for t in trades]


@router.get("/trades/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: str):
    """Get a single trade by ID."""
    async with async_session() as session:
        result = await session.execute(
            select(Trade).where(Trade.id == trade_id)
        )
        trade = result.scalar_one_or_none()
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        return TradeResponse.model_validate(trade)
