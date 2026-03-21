"""Tests for the liquidity scorer."""

from src.engine.liquidity_scorer import LiquidityScorer


def test_liquidity_scorer_exists():
    scorer = LiquidityScorer()
    assert scorer is not None


def test_score_with_data():
    scorer = LiquidityScorer()
    result = scorer.score(
        bid_count=10,
        bid_depth_eth=2.0,
        volume_24h=1.5,
        volume_7d=10.0,
        num_owners=500,
        total_supply=1000,
    )
    assert isinstance(result, dict)
    assert "score" in result
    assert 0 <= result["score"] <= 100


def test_score_empty_data():
    scorer = LiquidityScorer()
    result = scorer.score()
    assert result["score"] >= 0


def test_score_high_liquidity():
    scorer = LiquidityScorer()
    result = scorer.score(
        bid_count=50,
        bid_depth_eth=20.0,
        volume_24h=10.0,
        volume_7d=100.0,
        num_owners=5000,
        total_supply=10000,
    )
    assert result["score"] > 50
