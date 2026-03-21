"""
Alpha Discovery Engine — find emerging NFT collections before they blow up.

Signals that predict a collection will gain value:
1. Sudden spike in minting activity (new collection gaining traction)
2. Whale wallets buying in (smart money signal)
3. Volume spike without price increase yet (accumulation phase)
4. High bid-to-floor ratio (strong demand relative to supply)
5. Social momentum (tracked via on-chain proxy: unique buyers increasing)

Data sources:
- Reservoir API: trending mints, collection activity
- OpenSea API: collection stats, floor prices, volume
- On-chain: whale wallet tracking, transfer patterns
"""

import asyncio
import time
from datetime import datetime, timedelta
from decimal import Decimal

import httpx
import structlog

from src.config import get_settings
from src.discovery.whale_tracker import _WHALE_COLLECTIONS

logger = structlog.get_logger()

# Tracked alpha signals — persist across calls
_ALPHA_SIGNALS: dict[str, dict] = {}  # slug -> signal data
_WHALE_WALLETS: set[str] = set()


class AlphaEngine:
    """
    Autonomous alpha-finding engine.
    Scans multiple data sources to find NFT collections showing early signs
    of becoming popular — before the crowd notices.
    """

    RESERVOIR_BASE = "https://api.reservoir.tools"
    OPENSEA_BASE = "https://api.opensea.io"

    def __init__(self):
        settings = get_settings()
        self.opensea_key = settings.marketplace.opensea_api_key

        # Scoring weights for alpha signals
        self.weights = {
            "mint_velocity": 0.25,       # How fast is it minting?
            "unique_buyers": 0.20,       # Many different buyers = organic
            "volume_spike": 0.20,        # Volume increasing = accumulation
            "whale_activity": 0.15,      # Smart money buying in
            "bid_floor_ratio": 0.10,     # Strong demand vs supply
            "price_momentum": 0.10,      # Price trending up
        }

    async def discover(self) -> list[dict]:
        """
        Run full discovery pipeline. Returns scored collections.
        """
        logger.info("alpha_discovery_starting")

        # Gather signals from multiple sources in parallel
        trending_mints, opensea_trending = await asyncio.gather(
            self._fetch_trending_mints(),
            self._fetch_opensea_activity(),
            return_exceptions=True,
        )

        if isinstance(trending_mints, Exception):
            logger.warning("alpha_trending_mints_error", error=str(trending_mints)[:100])
            trending_mints = []

        if isinstance(opensea_trending, Exception):
            logger.warning("alpha_opensea_activity_error", error=str(opensea_trending)[:100])
            opensea_trending = []

        # Score and rank collections
        scored = []
        seen_slugs = set()

        for collection in trending_mints + opensea_trending:
            slug = collection.get("slug", "")
            if not slug or slug in seen_slugs:
                continue
            seen_slugs.add(slug)

            score = self._calculate_alpha_score(collection)
            collection["alpha_score"] = score
            scored.append(collection)

        # Sort by alpha score
        scored.sort(key=lambda x: x.get("alpha_score", 0), reverse=True)

        # Update global signals
        for col in scored[:20]:
            slug = col.get("slug", "")
            _ALPHA_SIGNALS[slug] = {
                **col,
                "discovered_at": datetime.utcnow().isoformat(),
            }

        logger.info(
            "alpha_discovery_complete",
            total_found=len(scored),
            top_score=scored[0]["alpha_score"] if scored else 0,
            top_collection=scored[0].get("slug", "?") if scored else "none",
        )

        return scored[:20]  # Top 20 alpha picks

    async def _fetch_trending_mints(self) -> list[dict]:
        """
        Fetch trending mints from Reservoir — new collections gaining traction.
        These are collections people are actively minting right now.
        """
        collections = []

        async with httpx.AsyncClient(timeout=15) as client:
            # Ethereum trending mints
            for chain in ["ethereum", "base", "polygon"]:
                try:
                    base = self.RESERVOIR_BASE
                    if chain == "base":
                        base = "https://api-base.reservoir.tools"
                    elif chain == "polygon":
                        base = "https://api-polygon.reservoir.tools"

                    resp = await client.get(
                        f"{base}/collections/trending-mints/v2",
                        params={
                            "period": "24h",
                            "limit": 20,
                        },
                        headers={"accept": "application/json"},
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        mints = data.get("mints", [])

                        for mint in mints:
                            col = mint.get("collection", {})
                            collections.append({
                                "slug": col.get("id", ""),
                                "name": col.get("name", ""),
                                "chain": chain,
                                "contract": col.get("id", ""),
                                "image": col.get("image", ""),
                                "floor_price": float(col.get("floorAsk", {}).get("price", {}).get("amount", {}).get("decimal", 0) or 0),
                                "mint_count": int(mint.get("mintCount", 0)),
                                "mint_volume": float(mint.get("mintVolume", 0)),
                                "unique_minters": int(mint.get("uniqueMintersCount", 0)),
                                "source": "reservoir_trending_mints",
                                "signal_type": "mint_velocity",
                            })

                        logger.info(
                            "alpha_trending_mints_fetched",
                            chain=chain,
                            count=len(mints),
                        )
                except Exception as e:
                    logger.debug("alpha_reservoir_error", chain=chain, error=str(e)[:80])

        return collections

    async def _fetch_opensea_activity(self) -> list[dict]:
        """
        Scan OpenSea for collections with unusual activity patterns.
        Look for volume spikes, rising floors, and high bid activity.
        """
        collections = []

        # Search for collections with specific traits that signal alpha
        search_terms = [
            "art", "generative", "pixel", "abstract", "ai",
            "photography", "3d", "anime", "music", "onchain",
        ]

        async with httpx.AsyncClient(timeout=15) as client:
            for term in search_terms[:5]:  # Limit to avoid rate limits
                try:
                    resp = await client.get(
                        f"{self.OPENSEA_BASE}/api/v2/collections",
                        params={
                            "chain": "ethereum",
                            "limit": 10,
                            "order_by": "market_cap",
                        },
                        headers={
                            "accept": "application/json",
                            "x-api-key": self.opensea_key,
                        },
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        for col in data.get("collections", []):
                            stats = col.get("stats", {})
                            collections.append({
                                "slug": col.get("collection", ""),
                                "name": col.get("name", ""),
                                "chain": "ethereum",
                                "contract": col.get("contracts", [{}])[0].get("address", "") if col.get("contracts") else "",
                                "image": col.get("image_url", ""),
                                "floor_price": float(stats.get("floor_price", 0) or 0),
                                "volume_24h": float(stats.get("one_day_volume", 0) or 0),
                                "volume_7d": float(stats.get("seven_day_volume", 0) or 0),
                                "sales_24h": int(stats.get("one_day_sales", 0) or 0),
                                "owners": int(stats.get("num_owners", 0) or 0),
                                "total_supply": int(stats.get("total_supply", 0) or 0),
                                "source": "opensea_collections",
                                "signal_type": "volume_activity",
                            })

                    await asyncio.sleep(0.5)  # Rate limit respect
                except Exception as e:
                    logger.debug("alpha_opensea_search_error", error=str(e)[:80])

        return collections

    def _calculate_alpha_score(self, collection: dict) -> float:
        """
        Calculate a 0-100 alpha score for a collection.
        Higher = more likely to gain value.
        """
        scores = {}

        # 1. Mint velocity (trending mints data)
        mint_count = collection.get("mint_count", 0)
        unique_minters = collection.get("unique_minters", 0)
        if mint_count > 0:
            scores["mint_velocity"] = min(mint_count / 100, 1.0) * 100
        else:
            scores["mint_velocity"] = 0

        # 2. Unique buyers (organic demand indicator)
        if unique_minters > 0:
            scores["unique_buyers"] = min(unique_minters / 50, 1.0) * 100
        elif collection.get("owners", 0) > 0:
            supply = max(collection.get("total_supply", 1), 1)
            owner_ratio = collection.get("owners", 0) / supply
            scores["unique_buyers"] = min(owner_ratio * 2, 1.0) * 100
        else:
            scores["unique_buyers"] = 0

        # 3. Volume spike
        vol_24h = collection.get("volume_24h", 0)
        vol_7d = collection.get("volume_7d", 0)
        if vol_7d > 0 and vol_24h > 0:
            daily_avg = vol_7d / 7
            if daily_avg > 0:
                spike = vol_24h / daily_avg
                scores["volume_spike"] = min(spike / 3, 1.0) * 100
            else:
                scores["volume_spike"] = 50 if vol_24h > 0 else 0
        else:
            scores["volume_spike"] = collection.get("mint_volume", 0) * 10
            scores["volume_spike"] = min(scores["volume_spike"], 100)

        # 4. Whale activity — look up from WhaleTracker data
        slug = collection.get("slug", "")
        contract = collection.get("contract", "")
        whale_data = _WHALE_COLLECTIONS.get(slug) or _WHALE_COLLECTIONS.get(contract) or {}
        unique_whales = whale_data.get("unique_whale_count", 0)
        if unique_whales >= 3:
            scores["whale_activity"] = 100
        elif unique_whales == 2:
            scores["whale_activity"] = 70
        elif unique_whales == 1:
            scores["whale_activity"] = 40
        else:
            scores["whale_activity"] = 0

        # 5. Bid-to-floor ratio
        floor = collection.get("floor_price", 0)
        if floor > 0 and floor < 0.1:  # Sweet spot: cheap but has a floor
            scores["bid_floor_ratio"] = 80
        elif floor > 0 and floor < 0.5:
            scores["bid_floor_ratio"] = 50
        elif floor > 0:
            scores["bid_floor_ratio"] = 20
        else:
            scores["bid_floor_ratio"] = 0

        # 6. Price momentum — derived from volume ratios
        vol_24h_m = collection.get("volume_24h", 0)
        vol_7d_m = collection.get("volume_7d", 0)
        if vol_7d_m > 0 and vol_24h_m > 0:
            daily_avg_m = vol_7d_m / 7
            if daily_avg_m > 0:
                momentum_ratio = vol_24h_m / daily_avg_m
                if momentum_ratio >= 3.0:
                    scores["price_momentum"] = 100
                elif momentum_ratio >= 2.0:
                    scores["price_momentum"] = 70
                elif momentum_ratio >= 1.5:
                    scores["price_momentum"] = 40
                else:
                    scores["price_momentum"] = max(0, (momentum_ratio - 0.5) * 40)
            else:
                scores["price_momentum"] = 30 if vol_24h_m > 0 else 0
        else:
            scores["price_momentum"] = 0

        # Weighted score
        total = sum(
            scores.get(key, 0) * weight
            for key, weight in self.weights.items()
        )

        return round(total, 1)

    async def find_undervalued(self, min_score: float = 30) -> list[dict]:
        """
        Find collections that score above threshold but have low floor prices.
        These are the "hidden gems" — activity says they're gaining traction
        but price hasn't caught up yet.
        """
        all_collections = await self.discover()

        undervalued = [
            col for col in all_collections
            if col.get("alpha_score", 0) >= min_score
            and 0 < col.get("floor_price", 0) < 0.05  # Affordable
        ]

        logger.info(
            "alpha_undervalued_found",
            total_scanned=len(all_collections),
            undervalued=len(undervalued),
        )

        return undervalued

    @staticmethod
    def get_signals() -> dict:
        """Get current alpha signals for API/dashboard."""
        return {
            "signals": list(_ALPHA_SIGNALS.values()),
            "total_tracked": len(_ALPHA_SIGNALS),
            "last_updated": datetime.utcnow().isoformat(),
        }
