"""
Scan Worker — autonomous opportunity scanner and executor.

Runs every 30 seconds:
1. Fetches fresh data from OpenSea AND Blur for each collection
2. Runs ALL enabled strategies:
   - bid_spread: listing below best bid on same marketplace
   - cross_marketplace: buy on one marketplace, sell on another
   - trait_mispricing: rare NFTs listed at floor price
   - stale_listing: forgotten cheap listings
   - sweep_front_run: ride ongoing sweep momentum
3. QC-checks each opportunity
4. AUTO-EXECUTES if demand-driven and confidence is high
5. Stores all opportunities for dashboard visibility
6. Feeds results back to Thompson Sampling for learning
"""

import traceback
from datetime import datetime
from decimal import Decimal

import structlog
from sqlalchemy import select

from src.config import get_settings
from src.database import async_session
from src.models.collection import Collection
from src.models.opportunity import Opportunity as OpportunityModel
from src.ingestion.opensea import OpenSeaClient
from src.ingestion.blur import BlurClient
from src.ingestion.normalizer import EventNormalizer
from src.engine.cost_engine import CostEngine
from src.engine.opportunity_engine import OpportunityEngine
from src.engine.risk_engine import RiskEngine
from src.engine.portfolio_manager import PortfolioManager
from src.engine.forecast_gate import ForecastGate
from src.engine.knowledge_store import record_decision, record_outcome
from src.strategies.bid_spread import BidSpreadStrategy
from src.strategies.stale_listing import StaleListingStrategy
from src.strategies.cross_marketplace import CrossMarketplaceStrategy
from src.strategies.trait_mispricing import TraitMispricingStrategy
from src.strategies.sweep_front_run import SweepFrontRunStrategy
from src.agents.qc_agent import QCAgent
from src.agents.strategy_selector import StrategySelector
from src.execution.auto_executor import AutoExecutor
from src.notifications.telegram import TelegramNotifier
from src.cache.redis_cache import RedisCache
from src.engine.orderbook import OrderbookBuilder
from src.engine.fill_model import FillProbabilityModel

logger = structlog.get_logger()


class ScanWorker:
    """
    Autonomous scan-and-execute worker.

    Key principle: DEMAND-DRIVEN execution.
    We only buy when a verified buyer (active bid) already exists.

    Enhanced with:
    - Blur marketplace data (bid pools + listings)
    - Cross-marketplace arbitrage detection
    - Trait mispricing analysis
    - Sweep detection and front-running
    """

    def __init__(self):
        self.opensea = OpenSeaClient()
        self.blur = BlurClient()
        self.normalizer = EventNormalizer()
        self.cache = RedisCache()
        self.cost_engine = CostEngine(self.cache)
        self.risk_engine = RiskEngine()
        self.portfolio = PortfolioManager()
        self.notifier = TelegramNotifier()

        # Strategy selector (Thompson Sampling for adaptive learning)
        all_strategies = [
            "bid_spread", "cross_marketplace", "trait_mispricing",
            "stale_listing", "sweep_front_run",
        ]
        self.strategy_selector = StrategySelector(all_strategies)

        # QC Agent
        self.qc = QCAgent(
            cost_engine=self.cost_engine,
            portfolio_manager=self.portfolio,
            redis_cache=self.cache,
        )

        # Autonomous executor (cache for consecutive-loss gate)
        self.auto_executor = AutoExecutor(
            strategy_selector=self.strategy_selector,
            cache=self.cache,
        )

        # Register ALL strategies
        self.bid_spread = BidSpreadStrategy(self.cost_engine, self.cache)
        self.stale_listing = StaleListingStrategy(self.cost_engine, self.cache)
        self.cross_marketplace = CrossMarketplaceStrategy(self.cost_engine, self.cache)
        self.trait_mispricing = TraitMispricingStrategy(self.cost_engine, self.cache)
        self.sweep_front_run = SweepFrontRunStrategy(self.cost_engine, self.cache)

        self.orderbook_builder = OrderbookBuilder()
        self.fill_model = FillProbabilityModel()
        self.fill_model.load()
        self.forecast_gate = ForecastGate()

        self.opportunity_engine = OpportunityEngine(
            cost_engine=self.cost_engine,
            risk_engine=self.risk_engine,
            portfolio_manager=self.portfolio,
            strategies=[
                self.bid_spread,
                self.cross_marketplace,
                self.trait_mispricing,
                self.stale_listing,
                self.sweep_front_run,
            ],
        )

    async def run(self):
        """Scan all active collections, budget-aware: only trade what we can afford."""
        try:
            await self.cache.connect()
        except BaseException:
            pass

        # Check wallet balance on each chain (reuse cached executors)
        chain_balances: dict[str, float] = {}
        try:
            from src.execution.seaport import SeaportExecutor
            if not hasattr(self, "_chain_executors"):
                self._chain_executors: dict[str, SeaportExecutor] = {}
            for chain in ("ethereum", "base"):
                if chain not in self._chain_executors:
                    self._chain_executors[chain] = SeaportExecutor(chain=chain)
                executor = self._chain_executors[chain]
                if executor.is_ready():
                    chain_balances[chain] = await executor.get_wallet_balance(chain)
            logger.info("wallet_balances", **{f"bal_{k}": round(v, 4) for k, v in chain_balances.items()})
        except Exception as e:
            logger.warning("balance_check_error", error=str(e))

        async with async_session() as session:
            result = await session.execute(
                select(Collection).where(Collection.is_active == True)
            )
            collections = result.scalars().all()

        total_opportunities = 0
        total_executed = 0
        skipped = 0

        for collection in collections:
            chain = collection.chain or "ethereum"
            wallet_balance = chain_balances.get(chain, 0.0)

            floor = float(collection.floor_price or 0)
            if floor > 0 and wallet_balance > 0 and floor > wallet_balance * 0.95:
                logger.debug(
                    "scan_skip_too_expensive",
                    collection=collection.slug,
                    chain=chain,
                    floor=floor,
                    balance=wallet_balance,
                )
                skipped += 1
                continue

            try:
                opps, executed = await self._scan_collection(collection)
                total_opportunities += len(opps)
                total_executed += executed
            except Exception as e:
                logger.error(
                    "scan_error",
                    collection=collection.slug,
                    error=str(e),
                    traceback=traceback.format_exc(),
                )

        logger.info(
            "scan_complete",
            collections=len(collections),
            scanned=len(collections) - skipped,
            skipped_expensive=skipped,
            opportunities=total_opportunities,
            auto_executed=total_executed,
            wallet_balance=round(wallet_balance, 4),
        )

    async def _scan_collection(self, collection: Collection) -> tuple[list, int]:
        """Scan a single collection for opportunities across ALL marketplaces."""

        import asyncio

        # ── Fetch fresh data from BOTH OpenSea AND Blur in parallel ──
        os_data_task = self.opensea.fetch_all_collection_data(
            collection_slug=collection.slug,
            contract_address=collection.contract_address,
        )
        blur_data_task = self.blur.fetch_collection_data(collection.slug)

        raw_data, blur_data = await asyncio.gather(
            os_data_task, blur_data_task, return_exceptions=True,
        )

        if isinstance(raw_data, Exception):
            logger.error("opensea_fetch_error", slug=collection.slug, error=str(raw_data)[:100])
            raw_data = {}
        if isinstance(blur_data, Exception):
            logger.debug("blur_fetch_error", slug=collection.slug, error=str(blur_data)[:100])
            blur_data = {}

        # ── Normalize OpenSea data ────────────────────────────
        listings = []
        for l in raw_data.get("listings", []):
            d = self.normalizer.normalize_opensea_listing(l, collection.id)
            d["price"] = float(d.get("price", 0))
            d["venue"] = d.get("marketplace", "opensea")
            listings.append(d)

        bids = []
        for b in raw_data.get("bids", []):
            d = self.normalizer.normalize_opensea_offer(b, collection.id)
            d["price"] = float(d.get("price", 0))
            d["venue"] = d.get("marketplace", "opensea")
            bids.append(d)

        sales_7d = []
        for s in raw_data.get("sales_7d", []):
            d = self.normalizer.normalize_opensea_sale(s, collection.id)
            d["price"] = float(d.get("price", 0))
            sales_7d.append(d)

        sales_24h = []
        for s in raw_data.get("sales_24h", []):
            d = self.normalizer.normalize_opensea_sale(s, collection.id)
            d["price"] = float(d.get("price", 0))
            sales_24h.append(d)

        # ── Blur data (already normalized by BlurClient) ──────
        blur_listings = blur_data.get("listings", []) if isinstance(blur_data, dict) else []
        blur_bids = blur_data.get("bids", []) if isinstance(blur_data, dict) else []
        blur_best_bid = float(blur_data.get("best_bid", 0)) if isinstance(blur_data, dict) else 0

        # ── Floor price: use the best (lowest) across marketplaces ──
        stats = raw_data.get("stats", {})
        info = self.normalizer.normalize_collection_info(stats)
        os_floor = info.get("floor_price", 0)
        blur_floor = float(blur_data.get("floor_price", 0)) if isinstance(blur_data, dict) else 0

        # True floor = lowest across all marketplaces
        floor_price = os_floor
        if blur_floor > 0 and (blur_floor < floor_price or floor_price == 0):
            floor_price = blur_floor

        # Update floor price in DB so budget-check works next cycle
        if floor_price > 0:
            try:
                async with async_session() as session:
                    from sqlalchemy import update
                    await session.execute(
                        update(Collection)
                        .where(Collection.id == collection.id)
                        .values(
                            floor_price=Decimal(str(floor_price)),
                            best_bid=Decimal(str(max(
                                blur_best_bid,
                                float(bids[0].get("price", 0)) if bids else 0,
                            ))),
                        )
                    )
                    await session.commit()
            except Exception:
                pass

        royalty_bps = int(collection.royalty_bps or 0)
        marketplace_fee_bps = int(collection.marketplace_fee_bps or 250)

        ob_snapshot = self.orderbook_builder.build(
            slug=collection.slug,
            listings=listings,
            bids=bids,
            blur_listings=blur_listings,
            blur_bids=blur_bids,
        )

        collection_data = {
            "slug": collection.slug,
            # OpenSea data
            "listings": listings,
            "bids": bids,
            "sales_7d": sales_7d,
            "sales_24h": sales_24h,
            # Blur data (for cross-marketplace strategy)
            "blur_listings": blur_listings,
            "blur_bids": blur_bids,
            "blur_best_bid": blur_best_bid,
            "blur_floor": blur_floor,
            # Combined
            "floor_price": floor_price,
            "num_owners": info.get("owner_count", 0),
            "volume_7d": info.get("volume_total", 0),
            "royalty_bps": royalty_bps,
            "marketplace_fee_bps": marketplace_fee_bps,
            # Orderbook metrics
            "orderbook_spread_pct": ob_snapshot.spread_pct,
            "orderbook_imbalance": ob_snapshot.imbalance,
            "bid_depth": len(ob_snapshot.bids),
        }

        logger.info(
            "scan_data_fetched",
            collection=collection.slug,
            os_listings=len(listings),
            os_bids=len(bids),
            blur_listings=len(blur_listings),
            blur_bids=len(blur_bids),
            floor=floor_price,
            blur_best_bid=blur_best_bid,
        )

        # ── Run strategies ────────────────────────────────────
        opportunities = await self.opportunity_engine.scan_collection(
            collection_id=str(collection.id),
            collection_data=collection_data,
        )

        # ── QC + Auto-Execute ─────────────────────────────────
        stored = []
        executed_count = 0

        for opp in opportunities:
            opp["collection_slug"] = collection.slug
            opp["contract_address"] = collection.contract_address or ""
            opp["chain"] = collection.chain or "ethereum"
            opp["royalty_bps"] = royalty_bps
            opp["marketplace_fee_bps"] = marketplace_fee_bps

            # QC check
            qc_result = await self.qc.evaluate(opp, collection_data)
            opp["qc_verdict"] = qc_result["verdict"]
            opp["confidence"] = qc_result["confidence"]

            if qc_result["verdict"] == "REJECT":
                continue

            fill_features = {
                "spread_pct": collection_data.get("orderbook_spread_pct", 0),
                "bid_depth": collection_data.get("bid_depth", 0),
                "collection_volatility": 1.0,
                "hour_of_day": datetime.utcnow().hour,
                "day_of_week": datetime.utcnow().weekday(),
                "historical_fill_rate": 0.5,
                "roi_pct": float(opp.get("roi", 0)),
                "buy_price_eth": float(opp.get("buy_price", 0)),
            }
            opp["fill_probability"] = self.fill_model.predict(fill_features)

            # Store without circular qc_result reference
            qc_clean = {
                "verdict": qc_result.get("verdict"),
                "reasons": qc_result.get("reasons", []),
                "confidence": qc_result.get("confidence"),
            }
            opp["qc_result"] = qc_clean
            opp_id = await self._store_opportunity(opp, "pending")
            opp["id"] = opp_id

            # ── Forecast gate: kun handle hvor vi kan forecast lige så godt som succesfulde ──
            opp["spread_pct"] = collection_data.get("orderbook_spread_pct")
            opp["bid_depth"] = collection_data.get("bid_depth", 0)
            forecast_allowed, forecast_reason = await self.forecast_gate.allowed(opp, collection_data)
            if not forecast_allowed:
                logger.info(
                    "forecast_gate_skip",
                    strategy=opp.get("strategy"),
                    slug=collection.slug,
                    reason=forecast_reason[:80] if forecast_reason else "",
                )

            # Gem beslutningskontekst som viden (bruges til fremtidig forecast-gate)
            if forecast_allowed:
                await record_decision(
                    opportunity_id=opp_id,
                    collection_id=str(opp.get("collection_id", "")),
                    strategy=opp.get("strategy", ""),
                    spread_pct=opp.get("spread_pct"),
                    bid_depth=opp.get("bid_depth"),
                    roi_pct=float(opp.get("roi", 0)) if opp.get("roi") is not None else None,
                    fill_prob_predicted=opp.get("fill_probability"),
                    buy_price_eth=float(opp.get("buy_price", 0)) if opp.get("buy_price") is not None else None,
                )

            # ── AUTO-EXECUTE if qualified (incl. consecutive-loss gate) ──
            if forecast_allowed and await self.auto_executor.should_auto_execute_async(opp, qc_result):
                try:
                    result = await self.auto_executor.execute_opportunity(opp)
                    filled = result.get("status") == "executed"
                    pnl = result.get("net_profit") if filled else None
                    await record_outcome(opp_id, filled, pnl)
                    if filled:
                        executed_count += 1
                        logger.info(
                            "auto_executed",
                            collection=collection.slug,
                            token_id=opp.get("token_id"),
                            profit=opp.get("net_profit"),
                        )
                except Exception as e:
                    await record_outcome(opp_id, False, None)
                    logger.error(
                        "auto_execute_error",
                        token_id=opp.get("token_id"),
                        error=str(e),
                    )
            else:
                # Notify high-confidence opportunities for manual review
                if qc_result["verdict"] == "APPROVE" and qc_result["confidence"] >= 0.6:
                    await self.notifier.notify_opportunity(opp)

            stored.append(opp)

        if stored:
            logger.info(
                "opportunities_found",
                collection=collection.slug,
                total=len(stored),
                auto_executed=executed_count,
            )

        return stored, executed_count

    async def _store_opportunity(self, opp: dict, status: str = "pending") -> str:
        """Save opportunity to database and return its ID."""
        import uuid as uuid_mod
        opp_id = str(uuid_mod.uuid4())

        try:
            async with async_session() as session:
                model = OpportunityModel(
                    id=opp_id,
                    strategy=opp.get("strategy", "unknown"),
                    collection_id=str(opp.get("collection_id", "")),
                    slug=opp.get("collection_slug", ""),
                    chain=opp.get("chain", "ethereum"),
                    token_id=str(opp.get("token_id", "")),
                    buy_venue=str(opp.get("buy_venue", "")),
                    sell_venue=str(opp.get("sell_venue", "")),
                    buy_price=Decimal(str(opp.get("buy_price", 0))),
                    expected_exit=Decimal(str(opp.get("expected_exit", 0))),
                    marketplace_fee=Decimal(str(opp.get("marketplace_fee", 0))),
                    royalty_fee=Decimal(str(opp.get("royalty_fee", 0))),
                    gas_estimate=Decimal(str(opp.get("gas_estimate", 0))),
                    risk_buffer=Decimal("0"),
                    net_profit=Decimal(str(opp.get("net_profit", 0))),
                    roi=float(opp.get("roi", 0)),
                    confidence=float(opp.get("confidence", 0)),
                    risk_flags=opp.get("risk_flags", []),
                    status=status,
                    qc_result=opp.get("qc_result"),
                    qc_verdict=str(opp.get("qc_verdict", "")),
                    listing_order_hash=str(opp.get("listing_order_hash", "") or ""),
                    bid_order_hash=str(opp.get("bid_order_hash", "") or ""),
                )
                session.add(model)
                await session.commit()
        except Exception as e:
            logger.error("store_opportunity_error", error=str(e))

        return opp_id
