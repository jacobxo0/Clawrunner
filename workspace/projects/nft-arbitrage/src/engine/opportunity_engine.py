"""
Opportunity Engine — orchestrates strategy scanning, risk filtering,
and portfolio-aware opportunity creation.
"""

import logging
from typing import Any

from src.engine.cost_engine import CostEngine
from src.engine.risk_engine import RiskEngine
from src.engine.portfolio_manager import PortfolioManager
from src.strategies.base_strategy import BaseStrategy
from src.config import get_settings

logger = logging.getLogger(__name__)


def _to_dict(item) -> dict:
    """Convert an object to a dict safely (handles dicts, models, etc)."""
    if isinstance(item, dict):
        return item
    if hasattr(item, "__dict__"):
        return {k: v for k, v in item.__dict__.items() if not k.startswith("_")}
    return dict(item)


class OpportunityEngine:
    """
    Scans collections using registered strategies and filters results
    through risk assessment and portfolio limits.
    """

    def __init__(
        self,
        cost_engine: CostEngine,
        risk_engine: RiskEngine,
        portfolio_manager: PortfolioManager,
        strategies: list[BaseStrategy],
    ):
        self.cost_engine = cost_engine
        self.risk_engine = risk_engine
        self.portfolio_manager = portfolio_manager
        self.strategies = strategies
        self.settings = get_settings()

    async def scan_collection(
        self,
        collection_id: str,
        collection_data: dict,
    ) -> list[dict]:
        """
        Run all enabled strategies against a collection's data.

        Converts normalized items to dicts for strategy consumption,
        runs risk assessment, and applies portfolio limits.
        """
        # Convert normalized items to dicts for strategies
        scan_data = {}
        for key, value in collection_data.items():
            if isinstance(value, list):
                scan_data[key] = [_to_dict(item) for item in value]
            else:
                scan_data[key] = value

        all_opportunities: list[dict] = []

        for strategy in self.strategies:
            strategy_name = strategy.name()

            # Check if strategy is enabled
            strategy_cfg = self.settings.strategies.get(strategy_name, {})
            if not strategy_cfg.get("enabled", True):
                continue

            try:
                raw_opps = strategy.scan(collection_id, scan_data)
                logger.info(
                    "Strategy %s found %d raw opportunities for %s",
                    strategy_name, len(raw_opps), collection_id,
                )

                for opp in raw_opps:
                    # Risk assessment
                    risk = self.risk_engine.assess_collection(scan_data)
                    opp["risk_flags"] = risk.get("flags", [])
                    opp["risk_score"] = risk.get("score", 0)

                    # Portfolio exposure check
                    buy_price = opp.get("buy_price", 0)
                    if not self.portfolio_manager.can_take_position(
                        buy_price, collection_id=collection_id
                    ):
                        logger.info(
                            "Skipping opportunity — portfolio limit (buy=%.4f)",
                            buy_price,
                        )
                        continue

                    # Skip if risk score is too high
                    if risk.get("score", 0) > 80:
                        logger.info(
                            "Skipping opportunity — risk score too high (%d)",
                            risk["score"],
                        )
                        continue

                    opp["status"] = "pending"
                    all_opportunities.append(opp)

            except Exception as e:
                logger.error(
                    "Strategy %s failed for %s: %s",
                    strategy_name, collection_id, str(e),
                    exc_info=True,
                )

        logger.info(
            "OpportunityEngine found %d opportunities for %s",
            len(all_opportunities), collection_id,
        )
        return all_opportunities
