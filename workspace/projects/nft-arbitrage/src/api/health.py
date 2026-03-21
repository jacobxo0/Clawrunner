"""
Health check endpoint with wallet status.
"""

import time
from fastapi import APIRouter

from src.execution.seaport import SeaportExecutor

router = APIRouter(tags=["health"])

_start_time = time.time()
_VERSION = "0.2.0"


@router.get("/health")
@router.get("/api/health")
async def health_check():
    """Return service health status, uptime, version, and wallet info."""
    uptime_seconds = round(time.time() - _start_time, 2)
    uptime_hours = round(uptime_seconds / 3600, 2)

    # Wallet status
    seaport = SeaportExecutor()
    wallet_ready = seaport.is_ready()
    wallet_address = seaport.wallet_address or "not configured"
    balance = 0.0
    if wallet_ready:
        try:
            balance = await seaport.get_wallet_balance()
        except Exception:
            balance = -1.0  # indicates error

    # Stream sniper status
    stream_info = {"connected": False}
    try:
        from fastapi import Request
        from starlette.requests import HTTPConnection
        # Try to get sniper from app state
        from src.main import app as _app
        if hasattr(_app.state, "stream_sniper"):
            stream_info = _app.state.stream_sniper.stream.stats
    except Exception:
        pass

    return {
        "status": "healthy",
        "uptime_seconds": uptime_seconds,
        "uptime_hours": uptime_hours,
        "version": _VERSION,
        "wallet": {
            "ready": wallet_ready,
            "address": wallet_address,
            "balance_eth": round(balance, 6),
        },
        "stream": stream_info,
    }
