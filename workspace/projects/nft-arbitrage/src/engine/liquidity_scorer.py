"""
Liquidity Scorer — evaluates how liquid (easy to buy/sell) a collection is.
"""

import logging
import math

logger = logging.getLogger(__name__)


class LiquidityScorer:
    """
    Computes a 0-100 liquidity score based on bid depth,
    trading volume, and owner distribution.
    """

    # Weight allocation (must sum to 1.0)
    W_BID_DEPTH = 0.35
    W_VOLUME = 0.35
    W_OWNERS = 0.30

    def score(
        self,
        bid_count: int = 0,
        bid_depth_eth: float = 0.0,
        volume_24h: float = 0.0,
        volume_7d: float = 0.0,
        num_owners: int = 0,
        total_supply: int = 0,
    ) -> dict:
        """
        Calculate liquidity score.

        Returns
        -------
        dict
            {
                "score": float (0-100),
                "components": {
                    "bid_depth": float,
                    "volume": float,
                    "owner_diversity": float,
                },
            }
        """
        bid_depth_score = self._score_bid_depth(bid_count, bid_depth_eth)
        volume_score = self._score_volume(volume_24h, volume_7d)
        owner_score = self._score_owners(num_owners, total_supply)

        total = (
            bid_depth_score * self.W_BID_DEPTH
            + volume_score * self.W_VOLUME
            + owner_score * self.W_OWNERS
        )

        result = {
            "score": round(total, 2),
            "components": {
                "bid_depth": round(bid_depth_score, 2),
                "volume": round(volume_score, 2),
                "owner_diversity": round(owner_score, 2),
            },
        }

        logger.debug("Liquidity score: %s", result)
        return result

    @staticmethod
    def _score_bid_depth(bid_count: int, bid_depth_eth: float) -> float:
        """Score bid depth: more bids and deeper depth = higher score."""
        # Logarithmic scaling: 10 bids = ~60, 50 bids = ~85, 100+ = ~95
        count_score = min(100, 25 * math.log1p(bid_count))
        # ETH depth: 1 ETH = ~40, 10 ETH = ~75, 50+ ETH = ~95
        depth_score = min(100, 20 * math.log1p(bid_depth_eth))
        return (count_score + depth_score) / 2

    @staticmethod
    def _score_volume(volume_24h: float, volume_7d: float) -> float:
        """Score trading volume. Higher volume = more liquid."""
        # Daily vol: 1 ETH = ~40, 10 ETH = ~75
        daily = min(100, 25 * math.log1p(volume_24h))
        # Weekly vol: 10 ETH = ~60, 100 ETH = ~90
        weekly = min(100, 18 * math.log1p(volume_7d))
        return daily * 0.6 + weekly * 0.4

    @staticmethod
    def _score_owners(num_owners: int, total_supply: int) -> float:
        """Score owner diversity. More unique owners = less concentration risk."""
        if total_supply <= 0:
            return min(100, 15 * math.log1p(num_owners))

        # Owner ratio (unique owners / total supply)
        ratio = num_owners / total_supply
        ratio_score = min(100, ratio * 120)  # 80%+ ownership diversity = ~100

        # Absolute owner count still matters
        count_score = min(100, 15 * math.log1p(num_owners))

        return ratio_score * 0.5 + count_score * 0.5
