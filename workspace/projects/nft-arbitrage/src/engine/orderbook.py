"""
Orderbook Reconstruction — builds a unified bid/ask book from multi-marketplace data.

NFT markets don't have a central orderbook; OpenSea and Blur each maintain
separate listing and bid pools. This module merges them into a unified view
with microstructure analytics:
  - Bid/ask imbalance (predicts short-term direction)
  - Order flow toxicity (predicts adverse selection risk)
  - Depth metrics (predict fill probability and slippage)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import structlog

logger = structlog.get_logger()


@dataclass
class OrderLevel:
    price: float
    quantity: int
    venue: str
    order_hash: str = ""
    timestamp: Optional[datetime] = None


@dataclass
class OrderbookSnapshot:
    slug: str
    bids: list[OrderLevel] = field(default_factory=list)
    asks: list[OrderLevel] = field(default_factory=list)
    built_at: Optional[datetime] = None

    @property
    def best_bid(self) -> float:
        return self.bids[0].price if self.bids else 0.0

    @property
    def best_ask(self) -> float:
        return self.asks[0].price if self.asks else 0.0

    @property
    def spread(self) -> float:
        if self.best_bid > 0 and self.best_ask > 0:
            return self.best_ask - self.best_bid
        return 0.0

    @property
    def spread_pct(self) -> float:
        if self.best_ask > 0:
            return (self.spread / self.best_ask) * 100
        return 0.0

    @property
    def bid_depth_eth(self) -> float:
        return sum(lvl.price * lvl.quantity for lvl in self.bids)

    @property
    def ask_depth_eth(self) -> float:
        return sum(lvl.price * lvl.quantity for lvl in self.asks)

    @property
    def imbalance(self) -> float:
        """
        Bid/ask imbalance: positive = more bid pressure, negative = more ask pressure.
        Range: -1.0 to +1.0
        """
        total = self.bid_depth_eth + self.ask_depth_eth
        if total == 0:
            return 0.0
        return (self.bid_depth_eth - self.ask_depth_eth) / total


class OrderbookBuilder:
    """
    Merges OpenSea + Blur data into a unified orderbook snapshot
    with microstructure analytics.
    """

    def __init__(self):
        self._cache: dict[str, OrderbookSnapshot] = {}

    def build(
        self,
        slug: str,
        listings: list[dict],
        bids: list[dict],
        blur_listings: list[dict] = None,
        blur_bids: list[dict] = None,
    ) -> OrderbookSnapshot:
        """
        Build a unified orderbook from multi-marketplace data.

        Parameters
        ----------
        slug : str
            Collection slug.
        listings : list[dict]
            OpenSea listings with price, token_id, order_hash.
        bids : list[dict]
            OpenSea bids with price, order_hash.
        blur_listings : list[dict]
            Blur listings (optional).
        blur_bids : list[dict]
            Blur bids (optional).

        Returns
        -------
        OrderbookSnapshot
        """
        ask_levels: list[OrderLevel] = []
        bid_levels: list[OrderLevel] = []

        for listing in (listings or []):
            price = float(listing.get("price", 0))
            if price > 0:
                ask_levels.append(OrderLevel(
                    price=price,
                    quantity=1,
                    venue=listing.get("venue", "opensea"),
                    order_hash=listing.get("order_hash", ""),
                ))

        for listing in (blur_listings or []):
            price = float(listing.get("price", 0))
            if price > 0:
                ask_levels.append(OrderLevel(
                    price=price,
                    quantity=1,
                    venue="blur",
                    order_hash=listing.get("order_hash", ""),
                ))

        for bid in (bids or []):
            price = float(bid.get("price", 0))
            qty = int(bid.get("quantity", 1))
            if price > 0:
                bid_levels.append(OrderLevel(
                    price=price,
                    quantity=qty,
                    venue=bid.get("venue", "opensea"),
                    order_hash=bid.get("order_hash", ""),
                ))

        for bid in (blur_bids or []):
            price = float(bid.get("price", 0))
            qty = int(bid.get("quantity", 1))
            if price > 0:
                bid_levels.append(OrderLevel(
                    price=price,
                    quantity=qty,
                    venue="blur",
                    order_hash=bid.get("order_hash", ""),
                ))

        ask_levels.sort(key=lambda x: x.price)
        bid_levels.sort(key=lambda x: x.price, reverse=True)

        snapshot = OrderbookSnapshot(
            slug=slug,
            bids=bid_levels,
            asks=ask_levels,
            built_at=datetime.now(timezone.utc),
        )

        self._cache[slug] = snapshot
        return snapshot

    def get(self, slug: str) -> Optional[OrderbookSnapshot]:
        """Get cached orderbook snapshot for a collection."""
        return self._cache.get(slug)

    @staticmethod
    def estimate_toxicity(snapshot: OrderbookSnapshot) -> float:
        """
        Estimate order flow toxicity (0.0 = safe, 1.0 = very toxic).

        High toxicity = informed traders dominating the flow.
        Signals: wide spread, heavy imbalance, thin book.
        """
        if not snapshot.bids or not snapshot.asks:
            return 0.5

        spread_score = min(snapshot.spread_pct / 20.0, 1.0)

        imbalance_score = abs(snapshot.imbalance)

        total_depth = snapshot.bid_depth_eth + snapshot.ask_depth_eth
        depth_score = max(0.0, 1.0 - (total_depth / 10.0))

        toxicity = (spread_score * 0.4) + (imbalance_score * 0.35) + (depth_score * 0.25)
        return round(min(toxicity, 1.0), 3)
