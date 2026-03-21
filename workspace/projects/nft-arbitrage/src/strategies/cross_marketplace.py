"""
Cross-Marketplace Arbitrage Strategy
--------------------------------------
THE #1 competitive edge for small players.

Finds price discrepancies between OpenSea and Blur:
  - Buy cheap listing on OpenSea → sell into Blur bid pool (or vice versa)
  - Buy cheap listing on Blur → accept higher OpenSea collection offer

Key advantages:
  - Doesn't require large capital — just speed and smarts
  - Exploits the fact that different marketplaces have different user bases
  - Blur traders are more aggressive (higher bids, lower asks)
  - OpenSea has more retail sellers (sometimes mispriced listings)

Cross-marketplace spreads exist because:
  1. Marketplace fees differ (Blur: 0.5%, OpenSea: 2.5%)
  2. User bases differ (Blur: traders, OpenSea: collectors)
  3. Bid pools are separate — arbitrage keeps them in sync, but gaps appear
  4. Listings are not shared — a cheap listing on one may not exist on the other
"""

import logging
from decimal import Decimal

from src.strategies.base_strategy import BaseStrategy
from src.config import get_settings
from src.engine.volatility import calculate_volatility, adjust_threshold

logger = logging.getLogger(__name__)


class CrossMarketplaceStrategy(BaseStrategy):
    """
    Scans for cross-marketplace price discrepancies.

    Two main patterns:
    A) OpenSea listing < Blur best bid → buy on OpenSea, sell into Blur bid
    B) Blur listing < OpenSea best bid → buy on Blur, sell into OpenSea bid

    Both patterns are demand-driven: we only buy when exit liquidity exists.
    """

    def __init__(self, cost_engine, redis_cache=None):
        super().__init__(cost_engine, redis_cache)
        cfg = get_settings().strategies.get("cross_marketplace", {})
        self.min_profit_eth = Decimal(str(cfg.get("min_profit_eth", "0.003")))
        self.min_roi_pct = cfg.get("min_roi_pct", 1.5)
        self.blur_fee_bps = cfg.get("blur_fee_bps", 50)  # Blur: 0.5%
        self.opensea_fee_bps = 250  # OpenSea: 2.5%

    def name(self) -> str:
        return "cross_marketplace"

    def scan(self, collection_id: str, collection_data: dict) -> list[dict]:
        """
        Scan for cross-marketplace arbitrage between OpenSea and Blur.

        Expects collection_data to contain:
          - listings: list of OpenSea listings
          - bids: list of OpenSea bids
          - blur_listings: list of Blur listings
          - blur_bids: list of Blur bid levels
          - royalty_bps: creator royalty
        """
        opportunities = []
        royalty_bps = collection_data.get("royalty_bps", 0)

        sale_prices = [float(s.get("price", 0)) for s in collection_data.get("sales_7d", []) if float(s.get("price", 0)) > 0]
        self._vol = calculate_volatility(sale_prices) if sale_prices else 1.0

        # Pattern A: OpenSea listing → Blur bid
        os_to_blur = self._scan_opensea_to_blur(
            collection_id, collection_data, royalty_bps
        )
        opportunities.extend(os_to_blur)

        # Pattern B: Blur listing → OpenSea bid
        blur_to_os = self._scan_blur_to_opensea(
            collection_id, collection_data, royalty_bps
        )
        opportunities.extend(blur_to_os)

        logger.info(
            "CrossMarketplace: %d opportunities for %s "
            "(OS→Blur: %d, Blur→OS: %d)",
            len(opportunities), collection_id,
            len(os_to_blur), len(blur_to_os),
        )
        return opportunities

    def _scan_opensea_to_blur(
        self, collection_id: str, data: dict, royalty_bps: int,
    ) -> list[dict]:
        """
        Pattern A: Buy cheap on OpenSea, sell into Blur bid pool.

        OpenSea has retail sellers who sometimes misprice.
        Blur has deep bid pools from professional traders.
        """
        opps = []
        os_listings = data.get("listings", [])
        blur_bids = data.get("blur_bids", [])

        if not os_listings or not blur_bids:
            return opps

        # Best Blur bid = our exit price
        best_blur_bid = max(
            (b for b in blur_bids if float(b.get("price", 0)) > 0),
            key=lambda b: float(b.get("price", 0)),
            default=None,
        )
        if not best_blur_bid:
            return opps

        blur_bid_price = Decimal(str(best_blur_bid["price"]))
        blur_bid_depth = int(best_blur_bid.get("quantity", 1))

        vol = getattr(self, "_vol", 1.0)
        adj_min_profit = Decimal(str(adjust_threshold(float(self.min_profit_eth), vol)))
        adj_min_roi = adjust_threshold(self.min_roi_pct, vol)

        for listing in os_listings:
            listing_price = Decimal(str(listing.get("price", 0)))
            if listing_price <= 0 or listing_price >= blur_bid_price:
                continue

            # Selling on Blur: 0.5% marketplace fee + royalty
            costs = self.cost_engine.calculate(
                buy_price=listing_price,
                sell_price=blur_bid_price,
                royalty_bps=royalty_bps,
                marketplace_fee_bps=self.blur_fee_bps,
            )

            net_profit = costs["net_profit"]
            roi = costs["roi"]

            if net_profit >= adj_min_profit and roi >= adj_min_roi:
                opps.append({
                    "strategy": self.name(),
                    "sub_type": "opensea_to_blur",
                    "collection_id": collection_id,
                    "token_id": listing.get("token_id"),
                    "buy_venue": "opensea",
                    "sell_venue": "blur",
                    "buy_price": float(listing_price),
                    "expected_exit": float(blur_bid_price),
                    "marketplace_fee": costs["marketplace_fee"],
                    "royalty_fee": costs["royalty_fee"],
                    "gas_estimate": costs["gas_estimate"],
                    "net_profit": float(net_profit),
                    "roi": roi,
                    "listing_order_hash": listing.get("order_hash"),
                    "listing_protocol_address": listing.get("protocol_address", ""),
                    "bid_depth": blur_bid_depth,
                    "risk_flags": [],
                    "edge_type": "cross_marketplace_spread",
                })

        return opps

    def _scan_blur_to_opensea(
        self, collection_id: str, data: dict, royalty_bps: int,
    ) -> list[dict]:
        """
        Pattern B: Buy cheap on Blur, sell into OpenSea bid.

        Blur has more competitive (lower) listings.
        OpenSea has retail collectors who place generous bids.
        """
        opps = []
        blur_listings = data.get("blur_listings", [])
        os_bids = data.get("bids", [])
        floor_price = float(data.get("floor_price", 0))

        if not blur_listings or not os_bids:
            return opps

        # Filter OS bids to realistic ones (within 2x floor)
        if floor_price > 0:
            realistic_bids = [
                b for b in os_bids
                if 0 < float(b.get("price", 0)) <= floor_price * 2.0
            ]
        else:
            realistic_bids = [b for b in os_bids if float(b.get("price", 0)) > 0]

        if not realistic_bids:
            return opps

        best_os_bid = max(realistic_bids, key=lambda b: float(b.get("price", 0)))
        os_bid_price = Decimal(str(best_os_bid["price"]))

        vol = getattr(self, "_vol", 1.0)
        adj_min_profit = Decimal(str(adjust_threshold(float(self.min_profit_eth), vol)))
        adj_min_roi = adjust_threshold(self.min_roi_pct, vol)

        for listing in blur_listings:
            listing_price = Decimal(str(listing.get("price", 0)))
            if listing_price <= 0 or listing_price >= os_bid_price:
                continue

            # Selling on OpenSea: 2.5% marketplace fee + royalty
            costs = self.cost_engine.calculate(
                buy_price=listing_price,
                sell_price=os_bid_price,
                royalty_bps=royalty_bps,
                marketplace_fee_bps=self.opensea_fee_bps,
            )

            net_profit = costs["net_profit"]
            roi = costs["roi"]

            if net_profit >= adj_min_profit and roi >= adj_min_roi:
                opps.append({
                    "strategy": self.name(),
                    "sub_type": "blur_to_opensea",
                    "collection_id": collection_id,
                    "token_id": listing.get("token_id"),
                    "buy_venue": "blur",
                    "sell_venue": "opensea",
                    "buy_price": float(listing_price),
                    "expected_exit": float(os_bid_price),
                    "marketplace_fee": costs["marketplace_fee"],
                    "royalty_fee": costs["royalty_fee"],
                    "gas_estimate": costs["gas_estimate"],
                    "net_profit": float(net_profit),
                    "roi": roi,
                    "listing_order_hash": listing.get("order_hash", ""),
                    "bid_order_hash": best_os_bid.get("order_hash", ""),
                    "bid_protocol_address": best_os_bid.get("protocol_address", ""),
                    "risk_flags": [],
                    "edge_type": "cross_marketplace_spread",
                })

        return opps
