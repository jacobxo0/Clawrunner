"""
Dashboard endpoint — aggregate statistics.
Returns flat field names for direct consumption by the frontend.
"""

from fastapi import APIRouter
from sqlalchemy import select, func

from src.database import async_session
from src.models.collection import Collection
from src.models.opportunity import Opportunity
from src.models.trade import Trade

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard/stats")
async def dashboard_stats():
    """Return aggregate statistics across all collections, opportunities, and trades."""
    async with async_session() as session:
        # Collections
        total_collections = (await session.execute(
            select(func.count(Collection.id))
        )).scalar() or 0

        active_collections = (await session.execute(
            select(func.count(Collection.id)).where(Collection.is_active == True)
        )).scalar() or 0

        # Opportunities
        total_opportunities = (await session.execute(
            select(func.count(Opportunity.id))
        )).scalar() or 0

        pending_opportunities = (await session.execute(
            select(func.count(Opportunity.id)).where(Opportunity.status == "pending")
        )).scalar() or 0

        approved_opportunities = (await session.execute(
            select(func.count(Opportunity.id)).where(Opportunity.status == "approved")
        )).scalar() or 0

        # Trades
        total_trades = (await session.execute(
            select(func.count(Trade.id))
        )).scalar() or 0

        executed_trades = (await session.execute(
            select(func.count(Trade.id)).where(Trade.status == "executed")
        )).scalar() or 0

        # Total profit
        profit_result = await session.execute(
            select(func.sum(Opportunity.net_profit)).where(
                Opportunity.status == "executed"
            )
        )
        total_profit = float(profit_result.scalar() or 0)

        # Return flat fields that match frontend expectations
        return {
            "total_collections": total_collections,
            "active_collections": active_collections,
            "total_opportunities": total_opportunities,
            "pending_opportunities": pending_opportunities,
            "approved_opportunities": approved_opportunities,
            "total_trades": total_trades,
            "executed_trades": executed_trades,
            "total_profit_eth": round(total_profit, 6),
        }
