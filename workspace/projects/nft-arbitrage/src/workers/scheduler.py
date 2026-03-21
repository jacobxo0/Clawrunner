"""
APScheduler setup — runs all background workers autonomously.

Job schedule:
  - Ingestion:     every 10s  (fetch listings, bids, sales)
  - Scan+Execute:  every 30s  (find and auto-execute opportunities)
  - Risk Update:   every 15m  (wash detection, liquidity scoring)
  - Daily Summary: every day 08:00 UTC
  - Param Tuning:  every day 08:30 UTC
  - Meta Learning: every Monday 09:00 UTC
  - Cleanup:       every 6h
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

import structlog

from src.config import get_settings

logger = structlog.get_logger()


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the APScheduler instance."""
    scheduler = AsyncIOScheduler()
    settings = get_settings()
    sched = settings.scheduling

    # ── Data Ingestion: fetch fresh market data ──────────────
    scheduler.add_job(
        run_ingestion_worker,
        IntervalTrigger(seconds=sched.get("ingestion_interval_seconds", 10)),
        id="ingestion",
        name="Data Ingestion",
        max_instances=1,
    )

    # ── Observation loop: konstant observation lagres som viden ──
    if get_settings().observation_loop.get("enabled", True):
        scheduler.add_job(
            run_observation_loop_worker,
            IntervalTrigger(seconds=sched.get("observation_loop_seconds", 45)),
            id="observation_loop",
            name="Observation Loop (knowledge)",
            max_instances=1,
        )

    # ── Opportunity Scan + Auto-Execute (faster = competitive edge) ──
    scheduler.add_job(
        run_scan_worker,
        IntervalTrigger(seconds=sched.get("opportunity_scan_seconds", 15)),
        id="opportunity_scan",
        name="Opportunity Scanner + Auto-Executor",
        max_instances=1,
    )

    # ── Risk Score Updates ───────────────────────────────────
    scheduler.add_job(
        run_risk_worker,
        IntervalTrigger(minutes=sched.get("risk_update_minutes", 15)),
        id="risk_update",
        name="Risk Score Update",
        max_instances=1,
    )

    # ── Daily Performance Summary ────────────────────────────
    scheduler.add_job(
        run_daily_summary,
        CronTrigger(hour=sched.get("daily_report_hour", 8), minute=0),
        id="daily_summary",
        name="Daily Summary Report",
        max_instances=1,
    )

    # ── Daily Parameter Auto-Tuning ──────────────────────────
    scheduler.add_job(
        run_parameter_tuner,
        CronTrigger(hour=sched.get("daily_report_hour", 8), minute=30),
        id="param_tuning",
        name="Parameter Auto-Tuning",
        max_instances=1,
    )

    # ── Weekly Meta-Learning (AI-driven analysis) ────────────
    scheduler.add_job(
        run_meta_learning,
        CronTrigger(
            day_of_week=sched.get("meta_learning_day", "monday").lower()[:3],
            hour=9,
            minute=0,
        ),
        id="meta_learning",
        name="Weekly Meta-Learning",
        max_instances=1,
    )

    # ── Alpha Discovery (find emerging collections) ─────────
    scheduler.add_job(
        run_alpha_discovery,
        IntervalTrigger(minutes=sched.get("alpha_discovery_minutes", 30)),
        id="alpha_discovery",
        name="Alpha Discovery Engine",
        max_instances=1,
    )

    # ── Whale Tracker (follow smart money) ────────────────
    scheduler.add_job(
        run_whale_tracker,
        IntervalTrigger(minutes=sched.get("whale_tracker_minutes", 60)),
        id="whale_tracker",
        name="Whale Tracker",
        max_instances=1,
    )

    # ── Gas Price Tracker ───────────────────────────────────
    scheduler.add_job(
        run_gas_tracker,
        IntervalTrigger(seconds=sched.get("gas_update_seconds", 30)),
        id="gas_tracker",
        name="Gas Price Tracker",
        max_instances=1,
    )

    # ── Data Cleanup ─────────────────────────────────────────
    scheduler.add_job(
        run_cleanup_worker,
        IntervalTrigger(hours=sched.get("cleanup_hours", 6)),
        id="cleanup",
        name="Data Cleanup",
        max_instances=1,
    )

    # ── Dynamic Relisting (Dutch auction price decay) ──────
    scheduler.add_job(
        run_relister,
        IntervalTrigger(minutes=sched.get("relist_check_minutes", 30)),
        id="relister",
        name="Dynamic Relister",
        max_instances=1,
    )

    # ── Fill Model Training (weekly) ──────────────────────
    scheduler.add_job(
        run_fill_model_training,
        CronTrigger(day_of_week="sun", hour=3, minute=0),
        id="fill_model_training",
        name="Fill Model Training",
        max_instances=1,
    )

    # ── Portfolio Health Check ────────────────────────────
    scheduler.add_job(
        run_portfolio_check,
        IntervalTrigger(minutes=sched.get("portfolio_check_minutes", 60)),
        id="portfolio_check",
        name="Portfolio Health Check",
        max_instances=1,
    )

    logger.info("scheduler_configured", jobs=len(scheduler.get_jobs()))
    return scheduler


# ── Worker runners ─────────────────────────────────────────────

async def run_ingestion_worker():
    """Fetch latest market data for all active collections."""
    from src.workers.ingestion_worker import IngestionWorker
    try:
        worker = IngestionWorker()
        await worker.run()
    except Exception as e:
        logger.error("ingestion_worker_error", error=str(e))
        await _notify_error("IngestionWorker", str(e))


async def run_observation_loop_worker():
    """Konstant observation: lagre markedsstate som viden (til forecast-gate)."""
    from src.workers.observation_loop_worker import ObservationLoopWorker
    try:
        worker = ObservationLoopWorker()
        await worker.run()
    except Exception as e:
        logger.error("observation_loop_worker_error", error=str(e))


async def run_scan_worker():
    """Scan for opportunities and auto-execute if qualified."""
    from src.workers.scan_worker import ScanWorker
    try:
        worker = ScanWorker()
        await worker.run()
    except Exception as e:
        logger.error("scan_worker_error", error=str(e))
        await _notify_error("ScanWorker", str(e))


async def run_risk_worker():
    """Update risk scores for all collections."""
    from src.workers.risk_worker import RiskWorker
    try:
        worker = RiskWorker()
        await worker.run()
    except Exception as e:
        logger.error("risk_worker_error", error=str(e))
        await _notify_error("RiskWorker", str(e))


async def run_daily_summary():
    """Send daily performance report via Telegram."""
    from src.workers.summary_worker import SummaryWorker
    try:
        worker = SummaryWorker()
        await worker.run()
    except Exception as e:
        logger.error("summary_worker_error", error=str(e))


async def run_parameter_tuner():
    """Daily parameter auto-tuning based on trade outcomes."""
    from src.agents.parameter_tuner import ParameterTuner
    try:
        tuner = ParameterTuner()
        await tuner.run()
    except Exception as e:
        logger.error("parameter_tuner_error", error=str(e))
        await _notify_error("ParameterTuner", str(e))


async def run_meta_learning():
    """Weekly AI meta-analysis of system performance."""
    from src.agents.meta_learning import MetaLearningAgent
    try:
        agent = MetaLearningAgent()
        result = await agent.run_weekly_review()
        logger.info(
            "meta_learning_complete",
            status=result.get("status"),
            recommendations=len(result.get("recommendations", [])),
        )
    except Exception as e:
        logger.error("meta_learning_error", error=str(e))
        await _notify_error("MetaLearning", str(e))


async def run_alpha_discovery():
    """Scan for emerging NFT collections showing early growth signals."""
    from src.discovery.alpha_engine import AlphaEngine
    try:
        engine = AlphaEngine()
        results = await engine.discover()
        if results:
            logger.info(
                "alpha_discovery_results",
                top=results[0].get("slug", "?"),
                score=results[0].get("alpha_score", 0),
                total=len(results),
            )
            # Auto-add high-scoring affordable collections to tracked list
            undervalued = await engine.find_undervalued(min_score=40)
            if undervalued:
                await _auto_add_alpha_collections(undervalued)
    except Exception as e:
        logger.error("alpha_discovery_error", error=str(e))
        await _notify_error("AlphaDiscovery", str(e))


async def run_whale_tracker():
    """Scan whale wallets for recent NFT purchases."""
    from src.discovery.whale_tracker import WhaleTracker
    try:
        tracker = WhaleTracker()
        results = await tracker.scan_whale_activity(hours=24)
        hot = [r for r in results if r.get("unique_whale_count", 0) >= 2]
        if hot:
            logger.info(
                "whale_hot_collections",
                count=len(hot),
                top=hot[0].get("collection", "?"),
                whales=hot[0].get("unique_whale_count", 0),
            )
            # Notify via Telegram about whale convergence
            try:
                from src.notifications.telegram import TelegramNotifier
                notifier = TelegramNotifier()
                for col in hot[:3]:
                    msg = (
                        f"\U0001F433 Whale Alert: {col['collection']}\n"
                        f"  {col['unique_whale_count']} whales buying, "
                        f"{col['buy_count']} purchases\n"
                        f"  Total spent: {col['total_spent']:.3f} ETH"
                    )
                    await notifier.send_message(msg)
            except Exception:
                pass
    except Exception as e:
        logger.error("whale_tracker_error", error=str(e))
        await _notify_error("WhaleTracker", str(e))


async def _auto_add_alpha_collections(undervalued: list[dict]):
    """Auto-add high-scoring undervalued collections to tracking."""
    from sqlalchemy import select
    from src.database import async_session
    from src.models.collection import Collection

    try:
        async with async_session() as session:
            for col in undervalued[:5]:  # Max 5 at a time
                slug = col.get("slug", "")
                if not slug or len(slug) < 3:
                    continue

                existing = await session.execute(
                    select(Collection).where(Collection.slug == slug)
                )
                if existing.scalar_one_or_none():
                    continue

                new_col = Collection(
                    slug=slug,
                    name=col.get("name", slug),
                    chain=col.get("chain", "ethereum"),
                    contract_address=col.get("contract", ""),
                    floor_price=col.get("floor_price", 0),
                )
                session.add(new_col)
                logger.info(
                    "alpha_auto_added_collection",
                    slug=slug,
                    score=col.get("alpha_score", 0),
                    floor=col.get("floor_price", 0),
                )
            await session.commit()
    except Exception as e:
        logger.warning("alpha_auto_add_failed", error=str(e))


async def run_gas_tracker():
    """Update gas price tracking for optimization."""
    from src.engine.gas_optimizer import GasOptimizer
    from src.cache.redis_cache import RedisCache
    try:
        cache = RedisCache()
        try:
            await cache.connect()
        except Exception:
            pass
        optimizer = GasOptimizer(cache)
        snapshot = await optimizer.get_current_gas()
        logger.debug(
            "gas_updated",
            total_gwei=snapshot.total_gwei,
            base_fee=snapshot.base_fee_gwei,
            favorable=optimizer.is_gas_favorable(snapshot),
        )
    except Exception as e:
        logger.debug("gas_tracker_error", error=str(e)[:80])


async def run_cleanup_worker():
    """Clean up expired listings, bids, and opportunities."""
    from src.workers.cleanup_worker import CleanupWorker
    try:
        worker = CleanupWorker()
        await worker.run()
    except Exception as e:
        logger.error("cleanup_worker_error", error=str(e))


async def run_relister():
    """Update relist prices for held inventory using Dutch auction decay."""
    from src.engine.relister import DynamicRelister
    try:
        relister = DynamicRelister()
        await relister.run()
    except Exception as e:
        logger.error("relister_error", error=str(e))
        await _notify_error("Relister", str(e))


async def run_fill_model_training():
    """Weekly training of the fill probability ML model."""
    from src.engine.fill_model import FillProbabilityModel
    try:
        model = FillProbabilityModel()
        await model.train(lookback_days=30)
        logger.info("fill_model_training_complete")
    except Exception as e:
        logger.error("fill_model_training_error", error=str(e))
        await _notify_error("FillModelTraining", str(e))


async def run_portfolio_check():
    """Check for stale positions and deleverage signals."""
    from src.engine.portfolio_manager import PortfolioManager
    try:
        pm = PortfolioManager()
        stale = pm.check_stale_positions()
        if stale:
            logger.warning("stale_positions_detected", count=len(stale), positions=stale)
            try:
                from src.notifications.telegram import TelegramNotifier
                notifier = TelegramNotifier()
                msg = f"\u26a0\ufe0f Stale positions: {len(stale)} held > {pm.max_hold_hours}h"
                for p in stale[:3]:
                    msg += f"\n  {p['collection_id']}: {p['hours_held']}h, {p['exposure_eth']:.4f} ETH"
                await notifier.send_message(msg)
            except Exception:
                pass
        if pm.should_auto_deleverage():
            candidates = pm.get_deleverage_candidates()
            logger.warning("auto_deleverage_triggered", candidates=candidates[:3])
    except Exception as e:
        logger.error("portfolio_check_error", error=str(e))


async def _notify_error(component: str, error: str):
    """Send error notification via Telegram."""
    try:
        from src.notifications.telegram import TelegramNotifier
        notifier = TelegramNotifier()
        await notifier.notify_error(component, error)
    except Exception:
        pass  # Don't let notification failures cascade
