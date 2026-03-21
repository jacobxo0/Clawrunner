"""Tests for the fill probability model (heuristic fallback)."""

from src.engine.fill_model import FillProbabilityModel, FEATURE_NAMES


def test_heuristic_predict_returns_valid_range():
    model = FillProbabilityModel()
    features = {
        "spread_pct": 5.0,
        "bid_depth": 3,
        "collection_volatility": 1.0,
        "hour_of_day": 14,
        "day_of_week": 2,
        "historical_fill_rate": 0.5,
        "roi_pct": 5.0,
        "buy_price_eth": 0.05,
    }
    prob = model.predict(features)
    assert 0.0 <= prob <= 1.0


def test_heuristic_high_depth_boosts_probability():
    model = FillProbabilityModel()
    low_depth = model.predict({"bid_depth": 0, "spread_pct": 5, "roi_pct": 5})
    high_depth = model.predict({"bid_depth": 10, "spread_pct": 5, "roi_pct": 5})
    assert high_depth > low_depth


def test_heuristic_zero_depth_penalized():
    model = FillProbabilityModel()
    prob = model.predict({"bid_depth": 0, "spread_pct": 0, "roi_pct": 0})
    assert prob < 0.5


def test_heuristic_high_roi_boosts():
    model = FillProbabilityModel()
    low_roi = model.predict({"roi_pct": 0.5, "bid_depth": 3})
    high_roi = model.predict({"roi_pct": 10.0, "bid_depth": 3})
    assert high_roi > low_roi


def test_model_not_trained_by_default():
    model = FillProbabilityModel()
    assert not model.is_trained


def test_missing_features_default_to_zero():
    model = FillProbabilityModel()
    prob = model.predict({})
    assert 0.0 <= prob <= 1.0


def test_feature_names_constant():
    assert len(FEATURE_NAMES) == 8
    assert "spread_pct" in FEATURE_NAMES
    assert "bid_depth" in FEATURE_NAMES
