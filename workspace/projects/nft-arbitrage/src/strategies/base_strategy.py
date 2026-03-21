"""
Abstract base class for all arbitrage strategies.
"""

from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """Every strategy must implement name() and scan()."""

    def __init__(self, cost_engine, redis_cache=None):
        self.cost_engine = cost_engine
        self.redis_cache = redis_cache

    @abstractmethod
    def name(self) -> str:
        """Human-readable strategy name."""
        ...

    @abstractmethod
    def scan(self, collection_id: str, collection_data: dict) -> list[dict]:
        """
        Scan a collection for arbitrage opportunities.

        Parameters
        ----------
        collection_id : str
            Database ID of the collection.
        collection_data : dict
            Normalized data including listings, bids, floor_price, etc.

        Returns
        -------
        list[dict]
            Each dict represents a raw opportunity ready for QC evaluation.
        """
        ...
