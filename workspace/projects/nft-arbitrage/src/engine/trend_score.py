"""
Trend Score — calculates momentum/trend indicators for a collection.
Uses weighted signals from settings.trend_scoring configuration.
"""

import logging

from src.config import get_settings

logger = logging.getLogger(__name__)


class TrendScorer:
    """
    Computes a -100 to +100 trend score using configurable weighted signals.
    Positive = bullish momentum, Negative = bearish.
    """

    def __init__(self):
        cfg = get_settings().trend_scoring
        # Default weights if not configured
        self.weights = {
            "floor_change_24h": cfg.get("weight_floor_change_24h", 0.25),
            "floor_change_7d": cfg.get("weight_floor_change_7d", 0.20),
            "volume_change_24h": cfg.get("weight_volume_change_24h", 0.20),
            "sales_velocity": cfg.get("weight_sales_velocity", 0.15),
            "bid_strength": cfg.get("weight_bid_strength", 0.20),
        }

    def score(self, collection_data: dict) -> dict:
        """
        Calculate trend score from collection market data.

        Parameters
        ----------
        collection_data : dict
            Expected keys: floor_change_24h_pct, floor_change_7d_pct,
            volume_change_24h_pct, sales_24h, sales_7d, best_bid,
            floor_price.

        Returns
        -------
        dict
            {
                "score": float (-100 to +100),
                "signals": dict of individual signal scores,
                "trend": str ("bullish", "bearish", "neutral"),
            }
        """
        signals = {}

        # Floor price change (24h) — positive change = bullish
        floor_24h = collection_data.get("floor_change_24h_pct", 0)
        signals["floor_change_24h"] = self._clamp(floor_24h * 2, -100, 100)

        # Floor price change (7d) — longer term trend
        floor_7d = collection_data.get("floor_change_7d_pct", 0)
        signals["floor_change_7d"] = self._clamp(floor_7d * 1.5, -100, 100)

        # Volume change (24h)
        vol_change = collection_data.get("volume_change_24h_pct", 0)
        signals["volume_change_24h"] = self._clamp(vol_change * 1.5, -100, 100)

        # Sales velocity: daily sales rate vs 7d average
        sales_24h = collection_data.get("sales_24h", 0)
        sales_7d = collection_data.get("sales_7d", 0)
        avg_daily = sales_7d / 7 if sales_7d > 0 else 0
        if avg_daily > 0:
            velocity = ((sales_24h - avg_daily) / avg_daily) * 100
        else:
            velocity = 0
        signals["sales_velocity"] = self._clamp(velocity, -100, 100)

        # Bid strength: best bid / floor price ratio
        best_bid = collection_data.get("best_bid", 0)
        floor_price = collection_data.get("floor_price", 0)
        if floor_price > 0 and best_bid > 0:
            bid_ratio = best_bid / floor_price
            # Ratio of 0.95+ is very bullish, 0.7 is neutral, <0.5 is bearish
            bid_signal = (bid_ratio - 0.7) * 333  # 0.7 -> 0, 1.0 -> 100
        else:
            bid_signal = -50
        signals["bid_strength"] = self._clamp(bid_signal, -100, 100)

        # Weighted sum
        total = sum(
            signals[key] * self.weights.get(key, 0)
            for key in signals
        )
        total = self._clamp(total, -100, 100)

        # Classify trend
        if total > 20:
            trend = "bullish"
        elif total < -20:
            trend = "bearish"
        else:
            trend = "neutral"

        result = {
            "score": round(total, 2),
            "signals": {k: round(v, 2) for k, v in signals.items()},
            "trend": trend,
        }

        logger.debug("Trend score: %s", result)
        return result

    @staticmethod
    def _clamp(value: float, min_val: float, max_val: float) -> float:
        return max(min_val, min(max_val, value))
