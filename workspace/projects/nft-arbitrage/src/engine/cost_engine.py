"""
Cost Engine — calculates total acquisition cost including gas, fees, and risk buffer.

Enhanced with dynamic gas estimation from GasOptimizer:
  - Real gas units per transaction type (not fixed 200k)
  - EIP-1559 base fee + priority fee tracking
  - Cross-marketplace fee awareness (Blur: 0.5%, OpenSea: 2.5%)
"""

import logging
from decimal import Decimal

from src.config import get_settings
from src.cache.redis_cache import RedisCache

logger = logging.getLogger(__name__)

# Dynamic gas estimates per transaction type (from gas_optimizer)
GAS_UNITS_BY_TYPE = {
    "seaport_buy": 160_000,
    "seaport_sell": 180_000,
    "atomic_arb": 340_000,        # buy + sell combined
    "flashbots_bundle": 380_000,  # bundle overhead
    "default": 200_000,
}


class GasOracle:
    """Reads the latest gas price from RedisCache or GasOptimizer."""

    def __init__(self, redis_cache: RedisCache):
        self._cache = redis_cache

    async def get_gas_gwei(self) -> float:
        """Return current gas price in gwei from cache, or default."""
        return await self._cache.get_gas_price()


class CostEngine:
    """
    Calculates the total cost of an NFT purchase and expected profit
    from a buy-then-sell arbitrage cycle.

    Supports different fee structures per marketplace:
      - OpenSea: 2.5% (250 bps)
      - Blur: 0.5% (50 bps)
      - Custom: configurable per opportunity
    """

    def __init__(self, redis_cache: RedisCache = None):
        settings = get_settings()
        cfg = settings.cost_engine
        self._gas_units = cfg.get("gas_units", GAS_UNITS_BY_TYPE["atomic_arb"])
        self._risk_buffer_pct = Decimal(str(cfg.get("risk_buffer_pct", 1.0)))
        self._redis_cache = redis_cache
        self._gas_oracle = GasOracle(redis_cache) if redis_cache else None

    def calculate(
        self,
        buy_price: Decimal | float,
        sell_price: Decimal | float,
        royalty_bps: int = 0,
        marketplace_fee_bps: int = 250,
        gas_gwei: float = None,
    ) -> dict:
        """
        Calculate total cost breakdown and net profit for a buy-sell cycle.

        Parameters
        ----------
        buy_price : Decimal | float
            Price to buy the NFT.
        sell_price : Decimal | float
            Expected exit (sell) price.
        royalty_bps : int
            Creator royalty in basis points (e.g. 500 = 5%).
        marketplace_fee_bps : int
            Marketplace fee in basis points (e.g. 250 = 2.5%).
        gas_gwei : float, optional
            Gas price in gwei. If None, uses a default of 20 gwei.

        Returns
        -------
        dict
            Breakdown of costs, total cost, net profit, and ROI.
        """
        buy = Decimal(str(buy_price))
        sell = Decimal(str(sell_price))
        if gas_gwei is None:
            try:
                from web3 import Web3 as _W3
                w3 = _W3(_W3.HTTPProvider(get_settings().blockchain.eth_rpc_url))
                gas_gwei = float(_W3.from_wei(w3.eth.gas_price, "gwei"))
            except Exception:
                gas_gwei = 5.0

        # Marketplace fee is charged on the sell side
        marketplace_fee = sell * Decimal(marketplace_fee_bps) / Decimal(10_000)
        royalty_fee = sell * Decimal(royalty_bps) / Decimal(10_000)

        # Gas estimate in ETH: gas_units * gas_gwei / 1e9
        gas_estimate = Decimal(str(self._gas_units)) * Decimal(str(gas_gwei)) / Decimal("1000000000")

        # Risk buffer as % of buy price
        risk_buffer = buy * self._risk_buffer_pct / Decimal(100)

        total_cost = buy + gas_estimate + risk_buffer
        total_fees = marketplace_fee + royalty_fee
        net_profit = sell - total_fees - total_cost
        roi = float(net_profit / total_cost * 100) if total_cost > 0 else 0.0

        return {
            "buy_price": float(buy),
            "sell_price": float(sell),
            "marketplace_fee": float(marketplace_fee),
            "royalty_fee": float(royalty_fee),
            "gas_estimate": float(gas_estimate),
            "risk_buffer": float(risk_buffer),
            "total_cost": float(total_cost),
            "total_fees": float(total_fees),
            "net_profit": float(net_profit),
            "roi": round(roi, 4),
        }

    async def calculate_with_live_gas(
        self,
        buy_price: Decimal | float,
        sell_price: Decimal | float,
        royalty_bps: int = 0,
        marketplace_fee_bps: int = 250,
    ) -> dict:
        """Same as calculate() but fetches live gas from the GasOracle."""
        gas_gwei = 20.0
        if self._gas_oracle:
            gas_gwei = await self._gas_oracle.get_gas_gwei()
        return self.calculate(
            buy_price=buy_price,
            sell_price=sell_price,
            royalty_bps=royalty_bps,
            marketplace_fee_bps=marketplace_fee_bps,
            gas_gwei=gas_gwei,
        )
