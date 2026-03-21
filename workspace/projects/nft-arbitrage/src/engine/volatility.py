"""
Volatility Calculator — computes price volatility and adjusts strategy thresholds.

NFT volatility is computed from log-returns of recent sale prices.
Higher volatility = wider spreads needed for safety (avoid losses),
but also = more opportunities (prices move faster).

Used by strategies to dynamically adjust min_profit and min_roi
thresholds based on current market conditions.
"""

import math
from typing import Sequence


def calculate_volatility(recent_prices: Sequence[float]) -> float:
    """
    Calculate price volatility as a multiplier (1.0 = normal).

    Uses standard deviation of log-returns normalized to a baseline.
    If fewer than 3 prices, returns 1.0 (neutral).

    Parameters
    ----------
    recent_prices : Sequence[float]
        Chronologically ordered sale prices (oldest first).

    Returns
    -------
    float
        Volatility multiplier: <1.0 = calm, 1.0 = normal, >1.0 = volatile.
    """
    prices = [p for p in recent_prices if p > 0]
    if len(prices) < 3:
        return 1.0

    log_returns = []
    for i in range(1, len(prices)):
        if prices[i - 1] > 0:
            log_returns.append(math.log(prices[i] / prices[i - 1]))

    if not log_returns:
        return 1.0

    mean = sum(log_returns) / len(log_returns)
    variance = sum((r - mean) ** 2 for r in log_returns) / len(log_returns)
    stddev = math.sqrt(variance)

    baseline_stddev = 0.10
    multiplier = stddev / baseline_stddev if baseline_stddev > 0 else 1.0

    return max(0.3, min(multiplier, 5.0))


def adjust_threshold(base_threshold: float, volatility: float) -> float:
    """
    Scale a strategy threshold by volatility.

    High volatility → require higher profit margins (safety).
    Low volatility → can accept thinner margins (more trades).

    Parameters
    ----------
    base_threshold : float
        The default threshold (e.g. min_profit_eth = 0.005).
    volatility : float
        Volatility multiplier from calculate_volatility().

    Returns
    -------
    float
        Adjusted threshold.
    """
    scaling = 0.5 + (volatility * 0.5)
    return base_threshold * scaling
