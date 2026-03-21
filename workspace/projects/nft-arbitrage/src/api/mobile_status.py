"""
Mobile status API — lightweight payload for phone UI.
"""

import time
from fastapi import APIRouter, Request
from sqlalchemy import select, func

from src.database import async_session
from src.models.trade import Trade
from src.models.opportunity import Opportunity

router = APIRouter(prefix="/api", tags=["mobile"])

_start = time.time()


@router.get("/mobile-status")
async def mobile_status(request: Request):
    """Minimal status for mobile dashboard: wallet, trades, PnL, consecutive losses."""
    uptime = round(time.time() - _start, 0)
    out = {
        "ok": True,
        "uptime_seconds": uptime,
        "wallet_balance_eth": None,
        "total_trades": 0,
        "total_profit_eth": 0.0,
        "consecutive_losses": 0,
    }
    try:
        from src.main import app
        if hasattr(app.state, "cache") and app.state.cache:
            val = await app.state.cache.get("nft_arb:consecutive_losses")
            out["consecutive_losses"] = int(val) if val is not None else 0
    except Exception:
        pass
    try:
        from src.execution.seaport import SeaportExecutor
        seaport = SeaportExecutor()
        if seaport.is_ready():
            out["wallet_balance_eth"] = round(await seaport.get_wallet_balance(), 4)
    except Exception:
        pass
    try:
        async with async_session() as session:
            total_trades = (await session.execute(
                select(func.count(Trade.id)).where(Trade.status == "executed")
            )).scalar() or 0
            out["total_trades"] = int(total_trades)
            profit_row = await session.execute(
                select(func.sum(Opportunity.net_profit)).where(Opportunity.status == "executed")
            )
            total_profit = float(profit_row.scalar() or 0)
            out["total_profit_eth"] = round(total_profit, 4)
    except Exception:
        pass
    return out
