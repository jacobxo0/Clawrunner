"""
Stale-Listing Strategy
-----------------------
Detects listings that have been sitting for a long time while the
collection floor has risen, indicating a forgotten under-priced listing.
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from src.strategies.base_strategy import BaseStrategy
from src.config import get_settings
from src.engine.volatility import calculate_volatility, adjust_threshold

logger = logging.getLogger(__name__)


class StaleListingStrategy(BaseStrategy):

    def __init__(self, cost_engine, redis_cache=None):
        super().__init__(cost_engine, redis_cache)
        cfg = get_settings().strategies.get("stale_listing", {})
        self.min_stale_hours = cfg.get("min_stale_hours", 48)
        self.min_discount_pct = cfg.get("min_discount_pct", 15.0)
        self.min_profit_eth = Decimal(str(cfg.get("min_profit_eth", "0.005")))

    def name(self) -> str:
        return "stale_listing"

    def scan(self, collection_id: str, collection_data: dict) -> list[dict]:
        opportunities: list[dict] = []
        listings = collection_data.get("listings", [])
        floor_price = collection_data.get("floor_price")

        if not listings or not floor_price:
            return opportunities

        floor_price = Decimal(str(floor_price))
        now = datetime.now(timezone.utc)
        stale_cutoff = now - timedelta(hours=self.min_stale_hours)

        sale_prices = [float(s.get("price", 0)) for s in collection_data.get("sales_7d", []) if float(s.get("price", 0)) > 0]
        vol = calculate_volatility(sale_prices) if sale_prices else 1.0
        min_profit = Decimal(str(adjust_threshold(float(self.min_profit_eth), vol)))

        royalty_bps = collection_data.get("royalty_bps", 0)
        marketplace_fee_bps = collection_data.get("marketplace_fee_bps", 250)

        for listing in listings:
            listing_price = Decimal(str(listing.get("price", 0)))
            if listing_price <= 0 or listing_price >= floor_price:
                continue

            # Check staleness
            listed_at = listing.get("listed_at")
            if listed_at is None:
                continue
            if isinstance(listed_at, str):
                listed_at = datetime.fromisoformat(listed_at.replace("Z", "+00:00"))
            if listed_at > stale_cutoff:
                continue

            discount_pct = float((floor_price - listing_price) / floor_price * 100)
            if discount_pct < self.min_discount_pct:
                continue

            costs = self.cost_engine.calculate(
                buy_price=listing_price,
                sell_price=floor_price,
                royalty_bps=royalty_bps,
                marketplace_fee_bps=marketplace_fee_bps,
            )

            net_profit = costs["net_profit"]
            if net_profit < min_profit:
                continue

            opportunities.append({
                "strategy": self.name(),
                "collection_id": collection_id,
                "token_id": listing.get("token_id"),
                "buy_venue": listing.get("venue", "opensea"),
                "sell_venue": "opensea",
                "buy_price": float(listing_price),
                "expected_exit": float(floor_price),
                "marketplace_fee": float(costs.get("marketplace_fee", 0)),
                "royalty_fee": float(costs.get("royalty_fee", 0)),
                "gas_estimate": float(costs.get("gas_estimate", 0)),
                "net_profit": float(net_profit),
                "roi": costs["roi"],
                "listing_order_hash": listing.get("order_hash"),
                "stale_hours": (now - listed_at).total_seconds() / 3600,
                "discount_pct": discount_pct,
                "risk_flags": [],
            })

        logger.info(
            "StaleListing found %d opportunities for collection %s",
            len(opportunities), collection_id,
        )
        return opportunities
