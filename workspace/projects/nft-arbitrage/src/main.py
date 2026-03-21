"""
NFT Arbitrage OS — FastAPI Application.
"""

import asyncio
import os
from pathlib import Path
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.config import get_settings
from src.database import init_db, close_db

logger = structlog.get_logger()

# Resolve paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    settings = get_settings()
    logger.info("starting", environment=settings.environment, version="0.1.0")

    # Import all models so tables get created
    import src.models  # noqa: F401

    # Initialize database tables
    await init_db()
    logger.info("database_initialized")

    # Initialize cache (Redis or in-memory fallback)
    from src.cache.redis_cache import RedisCache
    app.state.cache = RedisCache()
    await app.state.cache.connect()

    # Initialize event bus
    from src.agents.event_bus import EventBus
    app.state.event_bus = EventBus()

    # Start background scheduler
    try:
        from src.workers.scheduler import create_scheduler
        app.state.scheduler = create_scheduler()
        app.state.scheduler.start()
        logger.info("scheduler_started")
    except Exception as e:
        logger.warning("scheduler_start_failed", error=str(e))

    # Seed collections from config
    try:
        await _seed_collections_from_config(settings)
    except Exception as e:
        logger.warning("seed_failed", error=str(e))

    # Send Telegram startup notification
    try:
        from src.notifications.telegram import TelegramNotifier
        notifier = TelegramNotifier()
        mode = settings.execution.get("mode", "semi_auto")
        num_collections = len(settings.collections)
        await notifier.notify_startup(mode, num_collections)
    except Exception as e:
        logger.warning("telegram_startup_notify_failed", error=str(e))

    # Auto-unwrap any WETH sitting in wallet → ETH for reinvestment
    try:
        from src.execution.seaport import SeaportExecutor as _SE
        for _chain in ("ethereum", "base"):
            _ex = _SE(chain=_chain)
            if _ex.is_ready():
                _weth = await _ex.get_weth_balance(_chain)
                if _weth > 0.0001:
                    logger.info("startup_unwrap_weth", chain=_chain, amount=round(_weth, 6))
                    await _ex.unwrap_weth(_chain)
    except Exception as e:
        logger.warning("startup_unwrap_failed", error=str(e))

    # Start Stream Sniper (real-time WebSocket listener)
    sniper_task = None
    try:
        from src.workers.stream_sniper import StreamSniper
        from src.execution.seaport import SeaportExecutor

        seaport = SeaportExecutor()
        if seaport.is_ready() and settings.execution.get("mode") == "full_auto":
            sniper = StreamSniper()
            affordable_slugs = [
                col["slug"] for col in settings.collections
                if col.get("active", True)
            ]
            sniper_task = asyncio.create_task(sniper.start(affordable_slugs))
            app.state.stream_sniper = sniper
            logger.info("stream_sniper_started", collections=len(affordable_slugs))
        else:
            logger.info("stream_sniper_skipped", reason="wallet not ready or not full_auto")
    except Exception as e:
        logger.warning("stream_sniper_start_failed", error=str(e))

    logger.info(
        "system_ready",
        mode=settings.execution.get("mode", "semi_auto"),
        dashboard="http://localhost:8000",
    )
    yield

    # Shutdown
    logger.info("shutting_down")

    # Stop stream sniper
    if hasattr(app.state, "stream_sniper"):
        try:
            await app.state.stream_sniper.stop()
        except Exception:
            pass
    if sniper_task:
        sniper_task.cancel()

    if hasattr(app.state, "scheduler"):
        try:
            app.state.scheduler.shutdown(wait=False)
        except Exception:
            pass
    if hasattr(app.state, "cache"):
        await app.state.cache.close()
    await close_db()
    logger.info("shutdown_complete")


# Create FastAPI app
app = FastAPI(
    title="NFT Arbitrage OS",
    description="Autonomous NFT arbitrage system with self-improvement",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
from src.api.health import router as health_router
from src.api.collections import router as collections_router
from src.api.opportunities import router as opportunities_router
from src.api.trades import router as trades_router
from src.api.dashboard import router as dashboard_router
from src.api.discovery import router as discovery_router
from src.api.mobile_status import router as mobile_status_router

app.include_router(health_router)
app.include_router(mobile_status_router)
app.include_router(collections_router)
app.include_router(opportunities_router)
app.include_router(trades_router)
app.include_router(dashboard_router)
app.include_router(discovery_router)

# Mount static files (frontend)
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# Root serves the dashboard
@app.get("/")
async def root():
    """Serve the dashboard HTML."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "NFT Arbitrage OS v0.1.0", "docs": "/docs"}


# Mobile-friendly interface (telefon)
@app.get("/mobile")
async def mobile():
    """Serve mobile-first dashboard for phone."""
    mobile_path = FRONTEND_DIR / "mobile.html"
    if mobile_path.exists():
        return FileResponse(str(mobile_path))
    return {"message": "mobile.html not found", "docs": "/docs"}


async def _seed_collections_from_config(settings):
    """Seed or update collections from YAML config."""
    from sqlalchemy import select
    from src.database import async_session
    from src.models.collection import Collection

    async with async_session() as session:
        for col_config in settings.collections:
            if not col_config.get("active", True):
                continue

            result = await session.execute(
                select(Collection).where(Collection.slug == col_config["slug"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                changed = False
                new_chain = col_config.get("chain", "ethereum")
                new_contract = col_config.get("contract", "")
                if existing.chain != new_chain:
                    existing.chain = new_chain
                    changed = True
                if existing.contract_address != new_contract:
                    existing.contract_address = new_contract
                    changed = True
                if existing.royalty_bps != col_config.get("royalty_bps", 0):
                    existing.royalty_bps = col_config.get("royalty_bps", 0)
                    changed = True
                if changed:
                    logger.info("collection_updated", slug=col_config["slug"],
                                chain=new_chain, contract=new_contract[:16])
            else:
                collection = Collection(
                    slug=col_config["slug"],
                    name=col_config.get("name", col_config["slug"]),
                    chain=col_config.get("chain", "ethereum"),
                    contract_address=col_config.get("contract"),
                    royalty_bps=col_config.get("royalty_bps", 0),
                    marketplace_fee_bps=col_config.get("marketplace_fee_bps", 250),
                )
                session.add(collection)
                logger.info("collection_seeded", slug=col_config["slug"])

        await session.commit()


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
