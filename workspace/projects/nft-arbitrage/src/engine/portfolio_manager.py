"""
Portfolio Manager — tracks exposure and enforces risk limits.

Enhanced with inventory intelligence:
  - Time-based position staleness detection
  - Per-collection exposure caps
  - Auto-deleverage when approaching risk limits
"""

import logging
import time
from collections import defaultdict

from src.config import get_settings

logger = logging.getLogger(__name__)


class PortfolioManager:
    """
    Tracks total ETH exposure and per-collection limits.
    Uses settings.risk for limit configuration.

    Inventory intelligence:
      - Detects positions held beyond max_hold_hours
      - Enforces per-collection ETH caps
      - Signals when auto-deleveraging is needed
    """

    def __init__(self):
        cfg = get_settings().risk
        self.max_total_exposure = cfg.get("max_total_exposure_eth", 5.0)
        self.max_per_collection = cfg.get("max_per_collection_eth", 1.0)
        self.max_positions = cfg.get("max_open_positions", 10)

        relist_cfg = get_settings().yaml_settings.get("relisting", {})
        self.max_hold_hours = relist_cfg.get("max_hold_hours", 48)
        self.auto_deleverage_threshold = cfg.get("auto_deleverage_threshold_pct", 85.0) / 100.0

        self._positions: dict[str, float] = defaultdict(float)
        self._position_count: int = 0
        self._position_timestamps: dict[str, float] = {}

    def get_total_exposure(self) -> float:
        """Return total ETH currently exposed across all positions."""
        return sum(self._positions.values())

    def get_collection_exposure(self, collection_id: str) -> float:
        """Return ETH exposure for a specific collection."""
        return self._positions.get(collection_id, 0.0)

    def can_take_position(self, amount: float, collection_id: str = None) -> bool:
        """
        Check whether a new position of `amount` ETH is allowed.

        Parameters
        ----------
        amount : float
            ETH cost of the proposed position.
        collection_id : str, optional
            If provided, also checks per-collection limit.

        Returns
        -------
        bool
        """
        total = self.get_total_exposure()

        if total + amount > self.max_total_exposure:
            logger.debug(
                "Position rejected: total exposure %.4f + %.4f > %.4f",
                total, amount, self.max_total_exposure,
            )
            return False

        if self._position_count >= self.max_positions:
            logger.debug(
                "Position rejected: max positions %d reached",
                self.max_positions,
            )
            return False

        if collection_id:
            coll_exposure = self.get_collection_exposure(collection_id)
            if coll_exposure + amount > self.max_per_collection:
                logger.debug(
                    "Position rejected: collection %s exposure %.4f + %.4f > %.4f",
                    collection_id, coll_exposure, amount, self.max_per_collection,
                )
                return False

        return True

    def add_position(self, collection_id: str, amount: float):
        """Record a new position."""
        self._positions[collection_id] += amount
        self._position_count += 1
        self._position_timestamps[collection_id] = time.time()
        logger.info(
            "Position added: collection=%s amount=%.4f total_exposure=%.4f",
            collection_id, amount, self.get_total_exposure(),
        )

    def remove_position(self, collection_id: str, amount: float):
        """Remove a position (e.g. after selling)."""
        self._positions[collection_id] = max(
            0, self._positions[collection_id] - amount
        )
        self._position_count = max(0, self._position_count - 1)
        if self._positions[collection_id] == 0:
            del self._positions[collection_id]
            self._position_timestamps.pop(collection_id, None)
        logger.info(
            "Position removed: collection=%s amount=%.4f total_exposure=%.4f",
            collection_id, amount, self.get_total_exposure(),
        )

    def check_stale_positions(self) -> list[dict]:
        """Find positions held longer than max_hold_hours."""
        stale = []
        now = time.time()
        for cid, ts in self._position_timestamps.items():
            hours = (now - ts) / 3600.0
            if hours > self.max_hold_hours:
                stale.append({
                    "collection_id": cid,
                    "hours_held": round(hours, 1),
                    "exposure_eth": self._positions.get(cid, 0),
                })
        return stale

    def check_collection_cap(self, collection_id: str, new_amount: float) -> bool:
        """Check if adding new_amount would exceed per-collection cap."""
        current = self.get_collection_exposure(collection_id)
        return (current + new_amount) <= self.max_per_collection

    def should_auto_deleverage(self) -> bool:
        """True if total exposure exceeds the auto-deleverage threshold."""
        ratio = self.get_total_exposure() / self.max_total_exposure if self.max_total_exposure > 0 else 0
        return ratio >= self.auto_deleverage_threshold

    def get_deleverage_candidates(self) -> list[str]:
        """
        Return collection IDs sorted by staleness (oldest first),
        suitable for auto-deleveraging.
        """
        if not self._position_timestamps:
            return []
        sorted_positions = sorted(
            self._position_timestamps.items(), key=lambda x: x[1]
        )
        return [cid for cid, _ in sorted_positions]
