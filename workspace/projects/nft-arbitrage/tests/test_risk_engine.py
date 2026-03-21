"""Tests for the risk engine scoring."""

from src.engine.risk_engine import RiskEngine


def test_risk_engine_exists():
    engine = RiskEngine()
    assert engine is not None


def test_assess_clean_collection():
    engine = RiskEngine()
    result = engine.assess_collection({
        "slug": "test-collection",
        "wash_trade_score": 0.1,
        "liquidity_score": 80,
        "volume_7d": 50.0,
        "num_owners": 500,
        "floor_price": 0.05,
    })
    assert result["pass"] is True
    assert result["score"] < 50
    assert isinstance(result["flags"], list)


def test_assess_high_wash_score():
    engine = RiskEngine()
    result = engine.assess_collection({
        "slug": "wash-collection",
        "wash_trade_score": 0.9,
        "liquidity_score": 80,
        "volume_7d": 50.0,
        "num_owners": 500,
    })
    assert "high_wash_trade_score" in str(result["flags"])


def test_blue_chip_trust():
    engine = RiskEngine()
    result = engine.assess_collection({
        "slug": "pudgypenguins",
        "wash_trade_score": 0,
        "liquidity_score": 10,
        "volume_7d": 0,
        "num_owners": 0,
        "floor_price": 5.0,
    })
    assert result["pass"] is True


def test_low_liquidity_flagged():
    engine = RiskEngine()
    result = engine.assess_collection({
        "slug": "illiquid-thing",
        "wash_trade_score": 0,
        "liquidity_score": 0.1,
        "volume_7d": 50.0,
        "num_owners": 500,
    })
    assert "low_liquidity" in str(result["flags"])
