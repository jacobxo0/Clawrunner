"""
Wash Trade Detector — identifies likely wash trading from transfer patterns.
"""

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class WashDetector:
    """
    Analyzes on-chain sales/transfer data to compute a wash trade score (0-100).
    Higher score = more likely wash trading is occurring.
    """

    def __init__(self):
        from src.config import get_settings
        cfg = get_settings().wash_detection
        self.self_trade_weight = cfg.get("self_trade_weight", 0.40)
        self.ping_pong_weight = cfg.get("ping_pong_weight", 0.35)
        self.cluster_weight = cfg.get("cluster_weight", 0.25)
        self.min_trades_for_detection = cfg.get("min_trades", 10)

    def score(self, sales: list[dict]) -> dict:
        """
        Analyze a list of sales events for wash trading patterns.

        Parameters
        ----------
        sales : list[dict]
            Each dict should have: from_address, to_address, price, token_id,
            and optionally tx_hash.

        Returns
        -------
        dict
            {
                "wash_score": float (0-100),
                "self_trades": int,
                "ping_pong_pairs": int,
                "suspicious_clusters": int,
                "total_trades": int,
                "flagged_addresses": list[str],
            }
        """
        total = len(sales)

        if total < self.min_trades_for_detection:
            return {
                "wash_score": 0,
                "self_trades": 0,
                "ping_pong_pairs": 0,
                "suspicious_clusters": 0,
                "total_trades": total,
                "flagged_addresses": [],
            }

        self_trades = 0
        pair_counts: dict[tuple, int] = defaultdict(int)
        address_trade_count: dict[str, int] = defaultdict(int)
        flagged: set[str] = set()

        for sale in sales:
            from_addr = (sale.get("from_address") or "").lower()
            to_addr = (sale.get("to_address") or "").lower()

            if not from_addr or not to_addr:
                continue

            address_trade_count[from_addr] += 1
            address_trade_count[to_addr] += 1

            # Self-trade detection: same sender and receiver
            if from_addr == to_addr:
                self_trades += 1
                flagged.add(from_addr)
                continue

            # Track A->B and B->A pairs for ping-pong detection
            pair = tuple(sorted([from_addr, to_addr]))
            pair_counts[pair] += 1

        # Ping-pong: same pair trading back and forth
        ping_pong_pairs = sum(1 for count in pair_counts.values() if count >= 3)
        for pair, count in pair_counts.items():
            if count >= 3:
                flagged.add(pair[0])
                flagged.add(pair[1])

        # Cluster detection: addresses involved in too many trades
        avg_trades = total * 2 / max(len(address_trade_count), 1)
        suspicious_clusters = 0
        for addr, count in address_trade_count.items():
            if count > avg_trades * 3 and count >= 5:
                suspicious_clusters += 1
                flagged.add(addr)

        # Compute weighted wash score
        self_trade_ratio = self_trades / total if total > 0 else 0
        ping_pong_ratio = ping_pong_pairs / max(len(pair_counts), 1)
        cluster_ratio = suspicious_clusters / max(len(address_trade_count), 1)

        wash_score = (
            self_trade_ratio * 100 * self.self_trade_weight
            + ping_pong_ratio * 100 * self.ping_pong_weight
            + cluster_ratio * 100 * self.cluster_weight
        )
        wash_score = min(100, wash_score)

        result = {
            "wash_score": round(wash_score, 2),
            "self_trades": self_trades,
            "ping_pong_pairs": ping_pong_pairs,
            "suspicious_clusters": suspicious_clusters,
            "total_trades": total,
            "flagged_addresses": sorted(flagged),
        }

        logger.debug("Wash detection result: score=%.2f flags=%d", wash_score, len(flagged))
        return result
