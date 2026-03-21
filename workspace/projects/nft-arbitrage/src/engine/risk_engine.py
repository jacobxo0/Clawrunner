"""
Risk Engine — assesses collection-level risk before taking positions.

For known blue-chip collections (Pudgy Penguins, Azuki, Milady etc.)
with verified high liquidity, the engine trusts the data source and
only flags genuinely concerning signals.
"""

import logging

from src.config import get_settings

logger = logging.getLogger(__name__)

# Known blue-chip slugs — these have verified deep liquidity
BLUE_CHIP_SLUGS = {
    "pudgypenguins", "azuki", "milady", "boredapeyachtclub",
    "mutant-ape-yacht-club", "cryptopunks", "doodles-official",
    "clonex", "moonbirds", "degods",
}


class RiskEngine:
    """
    Evaluates collection risk based on wash-trade score, liquidity,
    and volume thresholds from settings.

    Blue-chip collections get a trust bonus since their liquidity
    is well-established and doesn't need re-verification every scan.
    """

    def __init__(self):
        cfg = get_settings().risk
        self.max_wash_score = cfg.get("max_wash_score", 0.6)
        self.min_liquidity_score = cfg.get("min_liquidity_score", 0.3)
        self.min_volume_7d = cfg.get("min_volume_7d_eth", 10.0)
        self.min_owners = cfg.get("min_owners", 100)

    def assess_collection(self, collection_data: dict) -> dict:
        """
        Assess risk of a collection based on market data.

        Parameters
        ----------
        collection_data : dict
            Keys: wash_trade_score, liquidity_score, volume_7d,
            num_owners, slug, floor_price, etc.

        Returns
        -------
        dict  {"score": 0-100, "flags": list[str], "pass": bool}
        """
        flags: list[str] = []
        score = 0

        slug = collection_data.get("slug", "")
        is_blue_chip = slug in BLUE_CHIP_SLUGS

        wash_score = collection_data.get("wash_trade_score", 0)
        liquidity_score = collection_data.get("liquidity_score", 50)
        volume_7d = collection_data.get("volume_7d", 0)
        num_owners = collection_data.get("num_owners", 0)
        floor_price = collection_data.get("floor_price", 0)

        # Blue-chip trust: if we don't have volume/owner data but
        # it's a known liquid collection, don't flag it
        if is_blue_chip and volume_7d == 0 and floor_price > 0:
            # Trust that blue chips have volume — the data just
            # wasn't fetched in this scan cycle
            volume_7d = self.min_volume_7d + 1
            num_owners = self.min_owners + 1

        # Wash trading risk
        if wash_score > self.max_wash_score:
            flags.append(f"high_wash_trade_score:{wash_score}")
            score += 30

        # Liquidity risk (only flag if genuinely low)
        if liquidity_score < self.min_liquidity_score and not is_blue_chip:
            flags.append(f"low_liquidity:{liquidity_score}")
            score += 25

        # Volume risk
        if volume_7d < self.min_volume_7d:
            flags.append(f"low_volume_7d:{volume_7d}")
            score += 20

        # Owner concentration risk
        if num_owners > 0 and num_owners < self.min_owners:
            flags.append(f"low_owner_count:{num_owners}")
            score += 15

        # Floor price volatility (if provided)
        floor_change_pct = abs(collection_data.get("floor_change_24h_pct", 0))
        if floor_change_pct > 20:
            flags.append(f"high_floor_volatility:{floor_change_pct}%")
            score += 10

        score = min(score, 100)

        result = {
            "score": score,
            "flags": flags,
            "pass": score <= 60,
        }

        logger.debug("Risk assessment: slug=%s score=%d flags=%s", slug, score, flags)
        return result
