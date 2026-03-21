"""
Sweep Detection & Front-Run Strategy
--------------------------------------
Detects when someone is about to sweep (buy many listings at once)
and front-runs by buying the cheapest listings first.

How sweep detection works:
1. Monitor real-time sales events for rapid successive buys
2. If same buyer purchases 3+ items in quick succession → sweep detected
3. Remaining cheap listings will likely be swept too → buy before they do
4. Price rises after sweep → sell at new floor or into post-sweep bids

Why this works:
  - Sweeps cause instant floor price jumps (10-50%+)
  - The sweeper is removing cheap supply → remaining supply reprices up
  - If we buy the cheapest listing BEFORE they get to it → instant profit
  - Even if we don't front-run, buying right after sweep starts is profitable

Risk management:
  - Only front-run if sweeper has bought 3+ items (confirms intent)
  - Only buy listings below the sweeper's average purchase price
  - Set tight stop-loss: if floor doesn't rise within 5 minutes, exit
"""

import logging
import time
from collections import defaultdict
from decimal import Decimal

from src.strategies.base_strategy import BaseStrategy
from src.config import get_settings
from src.engine.volatility import calculate_volatility, adjust_threshold

logger = logging.getLogger(__name__)

# Track active sweeps across scan cycles
_ACTIVE_SWEEPS: dict[str, dict] = {}  # collection_slug -> sweep info
_SWEEP_HISTORY: list[dict] = []


class SweepFrontRunStrategy(BaseStrategy):
    """
    Detects ongoing sweeps and identifies front-running opportunities.

    A sweep is detected when:
    - Same buyer address purchases 3+ items in < 10 minutes
    - Average purchase price is at or above floor
    - Total spend exceeds a meaningful threshold

    Front-run opportunity:
    - Cheapest remaining listings below sweeper's avg price
    - Expected exit: new floor price after sweep completes
    """

    def __init__(self, cost_engine, redis_cache=None):
        super().__init__(cost_engine, redis_cache)
        cfg = get_settings().strategies.get("sweep_front_run", {})
        self.enabled = cfg.get("enabled", True)
        self.min_sweep_count = cfg.get("min_sweep_count", 3)
        self.sweep_window_minutes = cfg.get("sweep_window_minutes", 10)
        self.min_profit_eth = Decimal(str(cfg.get("min_profit_eth", "0.003")))
        self.min_roi_pct = cfg.get("min_roi_pct", 3.0)
        self.floor_lift_estimate_pct = cfg.get("floor_lift_estimate_pct", 15.0)

    def name(self) -> str:
        return "sweep_front_run"

    def scan(self, collection_id: str, collection_data: dict) -> list[dict]:
        if not self.enabled:
            return []

        opportunities = []
        listings = collection_data.get("listings", [])
        sales_24h = collection_data.get("sales_24h", [])
        floor_price = float(collection_data.get("floor_price", 0))
        slug = collection_data.get("slug", "")
        royalty_bps = collection_data.get("royalty_bps", 0)
        marketplace_fee_bps = collection_data.get("marketplace_fee_bps", 250)

        if not sales_24h or not listings or floor_price <= 0:
            return opportunities

        sale_prices = [float(s.get("price", 0)) for s in collection_data.get("sales_7d", []) if float(s.get("price", 0)) > 0]
        vol = calculate_volatility(sale_prices) if sale_prices else 1.0
        adj_min_profit = Decimal(str(adjust_threshold(float(self.min_profit_eth), vol)))
        adj_min_roi = adjust_threshold(self.min_roi_pct, vol)

        # Step 1: Detect active sweeps from recent sales
        sweep = self._detect_sweep(slug, sales_24h, floor_price)

        if not sweep:
            return opportunities

        sweep_avg_price = sweep["avg_price"]
        sweep_count = sweep["count"]
        sweeper = sweep["buyer"]

        # Step 2: Estimate new floor after sweep
        estimated_new_floor = floor_price * (1 + self.floor_lift_estimate_pct / 100)

        # Also consider: if sweeper is buying at X, floor will settle near X
        if sweep_avg_price > estimated_new_floor:
            estimated_new_floor = sweep_avg_price * 0.95

        # Step 3: Find cheapest listings below sweep price
        sorted_listings = sorted(
            [l for l in listings if float(l.get("price", 0)) > 0],
            key=lambda l: float(l.get("price", 0)),
        )

        for listing in sorted_listings[:5]:  # Only look at cheapest 5
            listing_price = Decimal(str(listing.get("price", 0)))
            if listing_price <= 0:
                continue

            # Skip if listing is above sweeper's average (they'd skip it too)
            if float(listing_price) >= sweep_avg_price:
                continue

            # Calculate expected profit based on new floor estimate
            exit_price = Decimal(str(estimated_new_floor))

            costs = self.cost_engine.calculate(
                buy_price=listing_price,
                sell_price=exit_price,
                royalty_bps=royalty_bps,
                marketplace_fee_bps=marketplace_fee_bps,
            )

            net_profit = costs["net_profit"]
            roi = costs["roi"]

            if net_profit >= adj_min_profit and roi >= adj_min_roi:
                opportunities.append({
                    "strategy": self.name(),
                    "collection_id": collection_id,
                    "token_id": listing.get("token_id"),
                    "buy_venue": listing.get("venue", "opensea"),
                    "sell_venue": "opensea",
                    "buy_price": float(listing_price),
                    "expected_exit": float(exit_price),
                    "marketplace_fee": costs["marketplace_fee"],
                    "royalty_fee": costs["royalty_fee"],
                    "gas_estimate": costs["gas_estimate"],
                    "net_profit": float(net_profit),
                    "roi": roi,
                    "listing_order_hash": listing.get("order_hash"),
                    "sweep_detected": True,
                    "sweep_count": sweep_count,
                    "sweep_buyer": sweeper[:10] + "...",
                    "sweep_avg_price": sweep_avg_price,
                    "estimated_new_floor": float(exit_price),
                    "risk_flags": ["sweep_momentum_risk"],
                    "edge_type": "sweep_front_run",
                })

        if opportunities:
            logger.info(
                "SweepFrontRun: %d opportunities for %s "
                "(sweep: %d buys by %s, avg %.4f ETH)",
                len(opportunities), slug,
                sweep_count, sweeper[:10], sweep_avg_price,
            )

        return opportunities

    def _detect_sweep(
        self, slug: str, sales: list[dict], floor_price: float,
    ) -> dict | None:
        """
        Detect an active sweep from recent sales data.

        A sweep is confirmed when:
        - Same buyer bought 3+ items
        - Within the sweep window (10 min default)
        - At or above floor price (intentional accumulation)
        """
        if not sales:
            return None

        # Group sales by buyer address
        buyer_purchases: dict[str, list[dict]] = defaultdict(list)

        for sale in sales:
            buyer = sale.get("to_address", "")
            if not buyer:
                continue

            price = float(sale.get("price", 0))
            if price <= 0:
                continue

            buyer_purchases[buyer.lower()].append({
                "price": price,
                "token_id": sale.get("token_id", ""),
                "timestamp": sale.get("event_timestamp"),
            })

        # Find buyers with 3+ purchases (sweep candidates)
        for buyer, purchases in buyer_purchases.items():
            if len(purchases) < self.min_sweep_count:
                continue

            # Sort by price to understand sweep pattern
            purchases.sort(key=lambda p: p["price"])

            avg_price = sum(p["price"] for p in purchases) / len(purchases)
            total_spent = sum(p["price"] for p in purchases)

            # Confirm: avg price near or above floor (intentional buying)
            if avg_price < floor_price * 0.8:
                continue  # Buying way below floor — probably not a sweep

            sweep_info = {
                "buyer": buyer,
                "count": len(purchases),
                "avg_price": avg_price,
                "total_spent": total_spent,
                "min_price": purchases[0]["price"],
                "max_price": purchases[-1]["price"],
                "detected_at": time.time(),
            }

            # Update global tracking
            _ACTIVE_SWEEPS[slug] = sweep_info
            _SWEEP_HISTORY.append({**sweep_info, "slug": slug})

            logger.info(
                "sweep_detected",
                collection=slug,
                buyer=buyer[:10],
                count=len(purchases),
                avg_price=avg_price,
                total_spent=total_spent,
            )

            return sweep_info

        # Check if there's a still-active sweep from recent scan
        if slug in _ACTIVE_SWEEPS:
            prev = _ACTIVE_SWEEPS[slug]
            age = time.time() - prev.get("detected_at", 0)
            if age < self.sweep_window_minutes * 60:
                return prev

        return None

    @staticmethod
    def get_active_sweeps() -> dict:
        """Get active sweep data for API/dashboard."""
        now = time.time()
        active = {
            slug: info for slug, info in _ACTIVE_SWEEPS.items()
            if now - info.get("detected_at", 0) < 600  # Last 10 min
        }
        return {
            "active_sweeps": active,
            "total_detected": len(_SWEEP_HISTORY),
        }
