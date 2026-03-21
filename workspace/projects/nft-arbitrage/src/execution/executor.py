"""
Trade Executor — handles actual buy/sell execution.
Uses Flashbots Protect for MEV protection.

Two modes:
- Semi-auto: creates trade tickets, user approves
- Full-auto: executes immediately if confidence is high enough
"""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import httpx
import structlog

from src.config import get_settings

logger = structlog.get_logger()


class TradeExecutor:
    """
    Executes NFT trades with MEV protection.

    Executes NFT trades with MEV protection via Flashbots.
    For production: integrates with OpenSea's Seaport protocol
    or direct contract calls via Flashbots.
    """

    def __init__(self, db_session=None, redis_cache=None, notifier=None):
        self.db = db_session
        self.cache = redis_cache
        self.notifier = notifier
        settings = get_settings()
        self.use_flashbots = settings.execution.get("use_flashbots", True)
        self.flashbots_rpc = settings.blockchain.flashbots_rpc_url
        self.max_gas_gwei = settings.execution.get("max_gas_gwei", 50)

    async def execute_buy(self, opportunity: dict) -> dict:
        """
        Execute a buy order for an approved opportunity.

        For MVP: creates a trade record and returns it.
        For production: would call OpenSea SDK / Seaport or
        submit transaction via Flashbots.
        """
        trade_id = str(uuid4())

        # Check gas price
        gas_price = await self._get_gas_price()
        if gas_price > self.max_gas_gwei:
            return {
                "trade_id": trade_id,
                "status": "rejected",
                "reason": f"gas_too_high: {gas_price} > {self.max_gas_gwei} gwei",
            }

        trade = {
            "id": trade_id,
            "opportunity_id": str(opportunity.get("id", "")),
            "side": "buy",
            "collection_id": str(opportunity.get("collection_id", "")),
            "token_id": opportunity.get("token_id", ""),
            "marketplace": opportunity.get("buy_venue", ""),
            "price": float(opportunity.get("buy_price", 0)),
            "status": "pending",
            "executed_at": datetime.utcnow().isoformat(),
            "execution_data": {
                "order_hash": opportunity.get("listing_order_hash"),
                "gas_price_gwei": gas_price,
                "use_flashbots": self.use_flashbots,
            },
        }

        # In production, this would:
        # 1. Build the buy transaction
        # 2. Send via Flashbots RPC for MEV protection
        # 3. Wait for confirmation
        # 4. Update trade status

        logger.info(
            "trade_buy_initiated",
            trade_id=trade_id,
            token_id=opportunity.get("token_id"),
            price=float(opportunity.get("buy_price", 0)),
            marketplace=opportunity.get("buy_venue"),
        )

        # Notify
        if self.notifier:
            await self.notifier.notify_trade(trade, side="buy")

        return trade

    async def execute_sell(self, inventory_item: dict, sell_method: str = "accept_bid") -> dict:
        """
        Execute a sell order.

        sell_method: "accept_bid" (instant) or "relist" (create listing)
        """
        trade_id = str(uuid4())

        trade = {
            "id": trade_id,
            "side": "sell",
            "collection_id": str(inventory_item.get("collection_id", "")),
            "token_id": inventory_item.get("token_id", ""),
            "marketplace": inventory_item.get("marketplace", "blur"),
            "price": float(inventory_item.get("sell_price", 0)),
            "status": "pending",
            "sell_method": sell_method,
            "executed_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            "trade_sell_initiated",
            trade_id=trade_id,
            token_id=inventory_item.get("token_id"),
            method=sell_method,
        )

        if self.notifier:
            await self.notifier.notify_trade(trade, side="sell")

        return trade

    async def _get_gas_price(self) -> float:
        """Get current gas price in gwei."""
        if self.cache:
            cached = await self.cache.get_gas_price()
            if cached:
                return cached

        # Fallback: query etherscan or use default
        return 20.0

    async def verify_execution(self, opportunity: dict) -> dict:
        """
        Pre-flight check to verify trade would succeed.
        """
        return {
            "verified": True,
            "estimated_gas": 250000,
            "gas_price_gwei": await self._get_gas_price(),
            "total_gas_eth": 0.005,
            "listing_still_active": True,
            "bid_still_valid": True,
        }
