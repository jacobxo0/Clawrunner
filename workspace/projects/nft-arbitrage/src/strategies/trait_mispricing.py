"""
Trait-Mispricing Strategy
--------------------------
Finds NFTs listed at or below collection floor price that have rare/valuable
traits worth significantly more.

This is PURE ALPHA:
  - Most sellers don't know what their traits are worth
  - They list at or near floor, not knowing a specific trait is in high demand
  - We buy at floor, sell via trait-specific bid or list at trait floor

How trait floors work:
  - A collection might have a floor of 0.05 ETH
  - But "Gold Background" tokens trade at 0.15 ETH (trait floor)
  - If someone lists a "Gold Background" token at 0.06 ETH → instant profit

Data sources:
  - OpenSea offers/bids API includes trait criteria (trait-specific bids)
  - OpenSea listings include token traits
  - Historical sales can be filtered by trait to establish trait floors

Strategy:
  1. Build trait floor map from recent sales + active trait bids
  2. Scan listings for items with traits worth more than listing price
  3. Calculate profit after fees
  4. Priority: items with ACTIVE trait-specific bids (guaranteed exit)
"""

import logging
from collections import defaultdict
from decimal import Decimal

from src.strategies.base_strategy import BaseStrategy
from src.config import get_settings
from src.engine.volatility import calculate_volatility, adjust_threshold

logger = logging.getLogger(__name__)


class TraitMispricingStrategy(BaseStrategy):

    def __init__(self, cost_engine, redis_cache=None):
        super().__init__(cost_engine, redis_cache)
        cfg = get_settings().strategies.get("trait_mispricing", {})
        self.enabled = cfg.get("enabled", False)
        self.min_trait_premium_pct = cfg.get("min_trait_premium_pct", 15.0)
        self.min_sales_for_trait = cfg.get("min_sales_for_trait", 3)
        self.min_profit_eth = Decimal(str(cfg.get("min_profit_eth", "0.005")))
        self.min_roi_pct = cfg.get("min_roi_pct", 5.0)

    def name(self) -> str:
        return "trait_mispricing"

    def scan(self, collection_id: str, collection_data: dict) -> list[dict]:
        if not self.enabled:
            return []

        opportunities = []
        listings = collection_data.get("listings", [])
        bids = collection_data.get("bids", [])
        sales = collection_data.get("sales_7d", [])
        floor_price = float(collection_data.get("floor_price", 0))
        royalty_bps = collection_data.get("royalty_bps", 0)
        marketplace_fee_bps = collection_data.get("marketplace_fee_bps", 250)

        if not listings or floor_price <= 0:
            return opportunities

        sale_prices = [float(s.get("price", 0)) for s in sales if float(s.get("price", 0)) > 0]
        vol = calculate_volatility(sale_prices) if sale_prices else 1.0
        adj_min_profit = Decimal(str(adjust_threshold(float(self.min_profit_eth), vol)))
        adj_min_roi = adjust_threshold(self.min_roi_pct, vol)

        # Step 1: Build trait floor map from bids and sales
        trait_floors = self._build_trait_floors(bids, sales, floor_price)

        if not trait_floors:
            logger.debug(
                "No trait floors computed for %s — need more trait bid/sale data",
                collection_id,
            )
            return opportunities

        # Step 2: Find trait-specific bids (guaranteed exit)
        trait_bids = self._extract_trait_bids(bids)

        # Step 3: Scan listings for mispriced items
        for listing in listings:
            listing_price = Decimal(str(listing.get("price", 0)))
            if listing_price <= 0:
                continue

            token_id = listing.get("token_id", "")
            item_traits = listing.get("traits", {})

            if not item_traits:
                continue

            # Check each trait against known trait floors
            best_trait_value = 0.0
            best_trait_name = ""
            matching_bid = None

            for trait_key, trait_value in self._normalize_traits(item_traits):
                trait_id = f"{trait_key}:{trait_value}"

                # Check for active trait-specific bid (best exit)
                if trait_id in trait_bids:
                    bid_info = trait_bids[trait_id]
                    bid_price = float(bid_info.get("price", 0))
                    if bid_price > best_trait_value:
                        best_trait_value = bid_price
                        best_trait_name = trait_id
                        matching_bid = bid_info

                # Check trait floor from sales history
                if trait_id in trait_floors:
                    tf = trait_floors[trait_id]
                    if tf > best_trait_value:
                        best_trait_value = tf
                        best_trait_name = trait_id
                        if trait_id not in trait_bids:
                            matching_bid = None

            if best_trait_value <= 0 or best_trait_value <= float(listing_price):
                continue

            # Calculate premium
            premium_pct = (
                (best_trait_value - float(listing_price)) / float(listing_price) * 100
            )
            if premium_pct < self.min_trait_premium_pct:
                continue

            # Calculate profit
            exit_price = Decimal(str(best_trait_value))

            # Use Blur fee if selling into Blur bid, otherwise OpenSea
            sell_fee_bps = marketplace_fee_bps
            if matching_bid and matching_bid.get("venue") == "blur":
                sell_fee_bps = 50

            costs = self.cost_engine.calculate(
                buy_price=listing_price,
                sell_price=exit_price,
                royalty_bps=royalty_bps,
                marketplace_fee_bps=sell_fee_bps,
            )

            net_profit = costs["net_profit"]
            roi = costs["roi"]

            if net_profit >= adj_min_profit and roi >= adj_min_roi:
                opp = {
                    "strategy": self.name(),
                    "collection_id": collection_id,
                    "token_id": token_id,
                    "buy_venue": listing.get("venue", "opensea"),
                    "sell_venue": matching_bid.get("venue", "opensea") if matching_bid else "opensea",
                    "buy_price": float(listing_price),
                    "expected_exit": float(exit_price),
                    "marketplace_fee": costs["marketplace_fee"],
                    "royalty_fee": costs["royalty_fee"],
                    "gas_estimate": costs["gas_estimate"],
                    "net_profit": float(net_profit),
                    "roi": roi,
                    "listing_order_hash": listing.get("order_hash"),
                    "bid_order_hash": matching_bid.get("order_hash", "") if matching_bid else "",
                    "trait_key": best_trait_name,
                    "trait_premium_pct": round(premium_pct, 1),
                    "has_guaranteed_exit": matching_bid is not None,
                    "risk_flags": [] if matching_bid else ["no_guaranteed_exit"],
                    "edge_type": "trait_mispricing",
                }
                opportunities.append(opp)

        logger.info(
            "TraitMispricing: %d opportunities for %s "
            "(trait floors: %d, trait bids: %d)",
            len(opportunities), collection_id,
            len(trait_floors), len(trait_bids),
        )
        return opportunities

    def _build_trait_floors(
        self, bids: list[dict], sales: list[dict], collection_floor: float,
    ) -> dict[str, float]:
        """
        Build a map of trait → floor price from:
        1. Active trait-specific bids (strongest signal)
        2. Recent sales of items with specific traits

        Returns {trait_id: floor_price}
        """
        trait_prices: dict[str, list[float]] = defaultdict(list)

        # From trait-specific bids
        for bid in bids:
            bid_type = bid.get("bid_type", "collection")
            if bid_type != "attribute":
                continue

            trait_filter = bid.get("trait_filter", {})
            price = float(bid.get("price", 0))
            if price <= 0:
                continue

            if isinstance(trait_filter, dict):
                key = trait_filter.get("key", "")
                value = trait_filter.get("value", "")
                if key and value:
                    trait_id = f"{key}:{value}"
                    trait_prices[trait_id].append(price)
            elif isinstance(trait_filter, list):
                for tf in trait_filter:
                    key = tf.get("key", "")
                    value = tf.get("value", "")
                    if key and value:
                        trait_id = f"{key}:{value}"
                        trait_prices[trait_id].append(price)

        # From recent sales (use median as trait floor)
        for sale in sales:
            raw_data = sale.get("raw_data", {})
            nft = raw_data.get("nft", {}) if isinstance(raw_data, dict) else {}
            traits = nft.get("traits", [])
            price = float(sale.get("price", 0))

            if price <= 0 or not traits:
                continue

            for trait in traits:
                trait_type = trait.get("trait_type", "")
                trait_value_str = str(trait.get("value", ""))
                if trait_type and trait_value_str:
                    trait_id = f"{trait_type}:{trait_value_str}"
                    trait_prices[trait_id].append(price)

        # Calculate floors (minimum of recent prices, but must be above collection floor)
        trait_floors = {}
        for trait_id, prices in trait_prices.items():
            if len(prices) < 1:  # At least 1 data point from bids or sales
                continue

            # Use the minimum price as the trait floor
            trait_floor = min(prices)

            # Only interesting if significantly above collection floor
            if collection_floor > 0 and trait_floor > collection_floor * 1.1:
                trait_floors[trait_id] = trait_floor

        return trait_floors

    def _extract_trait_bids(self, bids: list[dict]) -> dict[str, dict]:
        """
        Extract active trait-specific bids.
        These are guaranteed exits — someone wants a specific trait.

        Returns {trait_id: {price, order_hash, venue, ...}}
        """
        trait_bids: dict[str, dict] = {}

        for bid in bids:
            bid_type = bid.get("bid_type", "collection")
            if bid_type != "attribute":
                continue

            trait_filter = bid.get("trait_filter", {})
            price = float(bid.get("price", 0))
            if price <= 0:
                continue

            filters = [trait_filter] if isinstance(trait_filter, dict) else trait_filter
            for tf in filters:
                key = tf.get("key", "")
                value = tf.get("value", "")
                if not key or not value:
                    continue

                trait_id = f"{key}:{value}"

                # Keep the best bid for each trait
                if trait_id not in trait_bids or price > trait_bids[trait_id]["price"]:
                    trait_bids[trait_id] = {
                        "price": price,
                        "order_hash": bid.get("order_hash", ""),
                        "protocol_address": bid.get("protocol_address", ""),
                        "venue": bid.get("venue", "opensea"),
                        "bidder": bid.get("bidder_address", ""),
                    }

        return trait_bids

    @staticmethod
    def _normalize_traits(traits) -> list[tuple[str, str]]:
        """
        Normalize different trait formats into a list of (key, value) tuples.
        Handles both dict format {key: value} and list format [{trait_type, value}].
        """
        result = []

        if isinstance(traits, dict):
            for key, value in traits.items():
                if key and value:
                    result.append((str(key), str(value)))

        elif isinstance(traits, list):
            for trait in traits:
                if isinstance(trait, dict):
                    key = trait.get("trait_type", trait.get("key", ""))
                    value = trait.get("value", "")
                    if key and value:
                        result.append((str(key), str(value)))

        return result
