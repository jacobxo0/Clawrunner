"""
Strategy Selector -- Thompson Sampling
----------------------------------------
Maintains a Beta distribution (alpha, beta) per strategy.
Selects the strategy with the highest sampled probability of success.
"""

import logging
import random
from collections import defaultdict

logger = logging.getLogger(__name__)


class StrategySelector:

    def __init__(self, strategy_names: list[str] | None = None):
        # Beta prior: alpha=1, beta=1 (uniform)
        self._alpha: dict[str, float] = defaultdict(lambda: 1.0)
        self._beta: dict[str, float] = defaultdict(lambda: 1.0)

        if strategy_names:
            for name in strategy_names:
                # Touch the keys so they exist
                _ = self._alpha[name]
                _ = self._beta[name]

    def select(self) -> str:
        """
        Sample from each strategy's Beta distribution and return the
        strategy name with the highest sampled value.
        """
        if not self._alpha:
            raise ValueError("No strategies registered in the selector.")

        best_name = None
        best_sample = -1.0

        for name in self._alpha:
            sample = random.betavariate(self._alpha[name], self._beta[name])
            if sample > best_sample:
                best_sample = sample
                best_name = name

        logger.debug("Thompson sampling selected strategy '%s' (sample=%.4f)", best_name, best_sample)
        return best_name

    def update(self, strategy_name: str, success: bool) -> None:
        """
        Update the posterior for a strategy after observing a trade outcome.

        Parameters
        ----------
        strategy_name : str
        success : bool
            True if the trade was profitable, False otherwise.
        """
        if success:
            self._alpha[strategy_name] += 1.0
        else:
            self._beta[strategy_name] += 1.0

        logger.info(
            "Updated %s: alpha=%.1f beta=%.1f (success=%s)",
            strategy_name, self._alpha[strategy_name],
            self._beta[strategy_name], success,
        )

    def get_stats(self) -> dict[str, dict]:
        """Return current alpha/beta and expected success rate per strategy."""
        stats = {}
        for name in self._alpha:
            a, b = self._alpha[name], self._beta[name]
            stats[name] = {
                "alpha": a,
                "beta": b,
                "expected_success_rate": round(a / (a + b), 4),
            }
        return stats
