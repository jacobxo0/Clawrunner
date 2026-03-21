"""Tests for the CostEngine — P&L calculation, fee math, gas estimates."""

from decimal import Decimal
from src.engine.cost_engine import CostEngine


def test_basic_profit_calculation():
    engine = CostEngine(redis_cache=None)
    result = engine.calculate(
        buy_price=0.05,
        sell_price=0.07,
        royalty_bps=500,
        marketplace_fee_bps=250,
        gas_gwei=5.0,
    )
    assert result["buy_price"] == 0.05
    assert result["sell_price"] == 0.07
    assert result["marketplace_fee"] > 0
    assert result["royalty_fee"] > 0
    assert result["gas_estimate"] > 0
    assert result["net_profit"] < (0.07 - 0.05)


def test_zero_royalty():
    engine = CostEngine(redis_cache=None)
    result = engine.calculate(
        buy_price=0.1, sell_price=0.15,
        royalty_bps=0, marketplace_fee_bps=250, gas_gwei=5.0,
    )
    assert result["royalty_fee"] == 0.0


def test_negative_profit_when_spread_too_thin():
    engine = CostEngine(redis_cache=None)
    result = engine.calculate(
        buy_price=0.1, sell_price=0.101,
        royalty_bps=500, marketplace_fee_bps=250, gas_gwei=20.0,
    )
    assert result["net_profit"] < 0


def test_roi_calculation():
    engine = CostEngine(redis_cache=None)
    result = engine.calculate(
        buy_price=1.0, sell_price=2.0,
        royalty_bps=0, marketplace_fee_bps=0, gas_gwei=0.0,
    )
    assert result["roi"] > 0


def test_marketplace_fee_bps():
    engine = CostEngine(redis_cache=None)
    result_opensea = engine.calculate(
        buy_price=1.0, sell_price=1.5,
        royalty_bps=0, marketplace_fee_bps=250, gas_gwei=5.0,
    )
    result_blur = engine.calculate(
        buy_price=1.0, sell_price=1.5,
        royalty_bps=0, marketplace_fee_bps=50, gas_gwei=5.0,
    )
    assert result_blur["marketplace_fee"] < result_opensea["marketplace_fee"]
    assert result_blur["net_profit"] > result_opensea["net_profit"]
