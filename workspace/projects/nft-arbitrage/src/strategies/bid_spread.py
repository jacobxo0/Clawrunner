"""
Bid-Spread Strategy
--------------------
Finds opportunities where a listing price is lower than the best REALISTIC bid
minus all fees and costs, allowing an instant buy-then-accept-bid arbitrage.

Key insight: we use the best floor-level bid (not trait bids which can be 
much higher but are for specific tokens only). A realistic bid is one that's
within 2x of the floor price — anything higher is likely a trait-specific offer.
"""

import logging
from decimal import Decimal

from src.strategies.base_strategy import BaseStrategy
from src.config import get_settings
from src.engine.volatility import calculate_volatility, adjust_threshold

logger = logging.getLogger(__name__)


class BidSpreadStrategy(BaseStrategy):

    def __init__(self, cost_engine, redis_cache=None):
        super().__init__(cost_engine, redis_cache)
        cfg = get_settings().strategies.get("bid_spread", {})
        self.min_profit_eth = Decimal(str(cfg.get("min_profit_eth", "0.005")))
        self.min_roi_pct = cfg.get("min_roi_pct", 2.0)
        self.max_bid_floor_ratio = cfg.get("max_bid_floor_ratio", 2.0)

    def name(self) -> str:
        return "bid_spread"

    def scan(self, collection_id: str, collection_data: dict) -> list[dict]:
        opportunities: list[dict] = []
        listings = collection_data.get("listings", [])
        bids = collection_data.get("bids", [])
        floor_price = float(collection_data.get("floor_price", 0))

        if not listings or not bids:
            return opportunities

        sale_prices = [float(s.get("price", 0)) for s in collection_data.get("sales_7d", []) if float(s.get("price", 0)) > 0]
        vol = calculate_volatility(sale_prices) if sale_prices else 1.0
        min_profit = Decimal(str(adjust_threshold(float(self.min_profit_eth), vol)))
        min_roi = adjust_threshold(self.min_roi_pct, vol)

        # Filter to realistic bids only: bids within 2x of floor price.
        # Bids way above floor are trait-specific and can't be filled
        # with any random token — they target specific rare tokens.
        if floor_price > 0:
            realistic_bids = [
                b for b in bids
                if float(b.get("price", 0)) <= floor_price * self.max_bid_floor_ratio
                and float(b.get("price", 0)) > 0
            ]
        else:
            realistic_bids = [b for b in bids if float(b.get("price", 0)) > 0]

        if not realistic_bids:
            logger.debug(
                "No realistic bids for %s (all %d bids above %.1fx floor)",
                collection_id, len(bids), self.max_bid_floor_ratio,
            )
            return opportunities

        # Best realistic bid = our exit price
        best_bid = max(realistic_bids, key=lambda b: float(b.get("price", 0)))
        best_bid_price = Decimal(str(best_bid["price"]))

        royalty_bps = collection_data.get("royalty_bps", 0)
        marketplace_fee_bps = collection_data.get("marketplace_fee_bps", 250)

        for listing in listings:
            listing_price = Decimal(str(listing.get("price", 0)))
            if listing_price <= 0:
                continue

            # Listing must be BELOW the best bid for a spread to exist
            if listing_price >= best_bid_price:
                continue

            costs = self.cost_engine.calculate(
                buy_price=listing_price,
                sell_price=best_bid_price,
                royalty_bps=royalty_bps,
                marketplace_fee_bps=marketplace_fee_bps,
            )

            net_profit = costs["net_profit"]
            roi = costs["roi"]

            if net_profit >= min_profit and roi >= min_roi:
                opportunities.append({
                    "strategy": self.name(),
                    "collection_id": collection_id,
                    "token_id": listing.get("token_id"),
                    "buy_venue": listing.get("venue", "opensea"),
                    "sell_venue": best_bid.get("venue", "opensea"),
                    "buy_price": float(listing_price),
                    "expected_exit": float(best_bid_price),
                    "marketplace_fee": float(costs.get("marketplace_fee", 0)),
                    "royalty_fee": float(costs.get("royalty_fee", 0)),
                    "gas_estimate": float(costs.get("gas_estimate", 0)),
                    "net_profit": float(net_profit),
                    "roi": roi,
                    "listing_order_hash": listing.get("order_hash"),
                    "listing_protocol_address": listing.get("protocol_address", ""),
                    "bid_order_hash": best_bid.get("order_hash"),
                    "bid_protocol_address": best_bid.get("protocol_address", ""),
                    "risk_flags": [],
                })

        logger.info(
            "BidSpread: %d opportunities for %s (best bid: %.4f ETH, floor: %.4f ETH, "
            "filtered %d/%d bids as realistic)",
            len(opportunities), collection_id,
            float(best_bid_price), floor_price,
            len(realistic_bids), len(bids),
        )
        return opportunities
