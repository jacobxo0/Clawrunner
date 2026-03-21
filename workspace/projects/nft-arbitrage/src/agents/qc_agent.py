"""
Quality-Control Agent
---------------------
Evaluates raw opportunities and returns an APPROVE / REJECT / HUMAN_REVIEW
verdict with reasons and a confidence score.

Smart about blue-chip collections: established collections with verified
liquidity get higher base confidence when the bid-spread is clear.
"""

import logging
from decimal import Decimal

from src.agents.base_agent import BaseAgent
from src.config import get_settings

logger = logging.getLogger(__name__)

# Known blue-chip collections with deep liquidity
BLUE_CHIP_SLUGS = {
    "pudgypenguins", "azuki", "milady", "boredapeyachtclub",
    "mutant-ape-yacht-club", "cryptopunks", "doodles-official",
    "clonex", "moonbirds", "degods",
}


class QCAgent(BaseAgent):

    def __init__(self, cost_engine, portfolio_manager=None, redis_cache=None):
        self.cost_engine = cost_engine
        self.portfolio_manager = portfolio_manager
        self.redis_cache = redis_cache

        settings = get_settings()
        risk_cfg = settings.risk
        self.max_collection_exposure = risk_cfg.get("max_collection_exposure_eth", 2.0)
        self.max_portfolio_exposure = risk_cfg.get("max_portfolio_exposure_eth", 10.0)
        self.min_profit_eth = Decimal(str(risk_cfg.get("min_profit_eth", "0.005")))
        self.min_roi_pct = risk_cfg.get("min_roi_pct", 2.0)
        self.max_single_trade = risk_cfg.get("max_single_trade_eth", 1.0)

    async def evaluate(self, opportunity: dict, collection_data: dict) -> dict:
        """
        Run QC checks on an opportunity.

        Returns dict: verdict, reasons, confidence
        """
        reasons: list[str] = []
        confidence = 1.0

        strategy = opportunity.get("strategy", "")
        slug = collection_data.get("slug", "")
        is_blue_chip = slug in BLUE_CHIP_SLUGS

        # -- Check 1: minimum profit --
        net_profit = Decimal(str(opportunity.get("net_profit", 0)))
        if net_profit < self.min_profit_eth:
            reasons.append(
                f"Net profit {net_profit} ETH below minimum {self.min_profit_eth} ETH"
            )

        roi = opportunity.get("roi", 0.0)
        if roi < self.min_roi_pct:
            reasons.append(f"ROI {roi:.2f}% below minimum {self.min_roi_pct}%")

        # -- Check 2: buy price within single-trade limit --
        buy_price = float(opportunity.get("buy_price", 0))
        if buy_price > self.max_single_trade:
            reasons.append(
                f"Buy price {buy_price:.4f} ETH exceeds max single trade "
                f"{self.max_single_trade} ETH"
            )
            confidence *= 0.4

        # -- Check 3: portfolio exposure --
        if self.portfolio_manager is not None:
            collection_id = opportunity.get("collection_id")
            col_exposure = await self._get_collection_exposure(collection_id)
            if col_exposure + buy_price > self.max_collection_exposure:
                reasons.append(
                    f"Collection exposure {col_exposure + buy_price:.4f} ETH "
                    f"exceeds limit {self.max_collection_exposure} ETH"
                )
                confidence *= 0.5

        # -- Check 4: risk flags (weighted by severity) --
        risk_flags = opportunity.get("risk_flags", [])
        severe_flags = [f for f in risk_flags if "wash" in f or "volatility" in f]
        minor_flags = [f for f in risk_flags if f not in severe_flags]

        if severe_flags:
            reasons.append(f"Severe risk flags: {', '.join(severe_flags)}")
            confidence *= 0.5
        if minor_flags and not is_blue_chip:
            reasons.append(f"Minor risk flags: {', '.join(minor_flags)}")
            confidence *= 0.85

        # -- Check 5: bid validity --
        bid_hash = opportunity.get("bid_order_hash")
        demand_strategies = {"bid_spread", "cross_marketplace"}
        if not bid_hash and strategy in demand_strategies:
            # For demand-driven strategies, we still have bid data even without hash
            # The bid was just scanned from the marketplace, so it's likely active
            if is_blue_chip:
                confidence *= 0.95
            else:
                reasons.append("Missing bid order hash")
                confidence *= 0.7

        # -- Check 5b: cross-marketplace specific checks --
        if strategy == "cross_marketplace":
            # Cross-marketplace has higher confidence when bid depth is deep
            bid_depth = opportunity.get("bid_depth", 0)
            if bid_depth >= 5:
                confidence *= 1.0  # Deep bid pool = reliable exit
            elif bid_depth >= 2:
                confidence *= 0.95
            else:
                confidence *= 0.85
                reasons.append(f"Shallow bid depth: {bid_depth}")

        # -- Check 5c: sweep front-run has inherent momentum risk --
        if strategy == "sweep_front_run":
            sweep_count = opportunity.get("sweep_count", 0)
            if sweep_count >= 5:
                confidence *= 0.95  # Strong sweep signal
            elif sweep_count >= 3:
                confidence *= 0.85  # Moderate sweep signal
            else:
                confidence *= 0.7
                reasons.append(f"Weak sweep signal: {sweep_count} buys")

        # -- Check 5d: trait mispricing with guaranteed exit --
        if strategy == "trait_mispricing":
            has_exit = opportunity.get("has_guaranteed_exit", False)
            if has_exit:
                confidence *= 1.0  # Active trait bid exists
            else:
                confidence *= 0.75
                reasons.append("No guaranteed exit — trait floor based on sales history")

        # -- Check 6: sanity check on spread --
        expected_exit = float(opportunity.get("expected_exit", 0))
        if expected_exit > 0 and buy_price > 0:
            spread_ratio = expected_exit / buy_price
            if spread_ratio > 10:
                # Suspiciously large spread — might be a stale/invalid bid
                reasons.append(
                    f"Suspicious spread ratio {spread_ratio:.1f}x "
                    f"(buy {buy_price:.4f} -> sell {expected_exit:.4f})"
                )
                confidence *= 0.3

        # -- Determine verdict --
        has_blockers = any(
            "below minimum" in r or "exceeds limit" in r or "exceeds max" in r
            for r in reasons
        )

        if has_blockers:
            verdict = "REJECT"
            confidence = min(confidence, 0.3)
        elif confidence < 0.6:
            verdict = "HUMAN_REVIEW"
        else:
            verdict = "APPROVE"

        result = {
            "verdict": verdict,
            "reasons": reasons,
            "confidence": round(confidence, 3),
        }

        logger.info(
            "QC verdict=%s confidence=%.3f strategy=%s token=%s slug=%s",
            verdict, confidence,
            strategy, opportunity.get("token_id"), slug,
        )
        return result

    async def _get_collection_exposure(self, collection_id: str) -> float:
        """Return current ETH exposure in a collection via portfolio manager."""
        try:
            return self.portfolio_manager.get_collection_exposure(collection_id)
        except Exception:
            logger.warning("Could not fetch portfolio exposure, assuming 0")
            return 0.0
