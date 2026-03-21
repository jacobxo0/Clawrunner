"""Tests for the AlphaEngine scoring (whale activity + price momentum)."""

from src.discovery.alpha_engine import AlphaEngine
from src.discovery import whale_tracker


def test_alpha_score_with_whale_data():
    engine = AlphaEngine()
    whale_tracker._WHALE_COLLECTIONS["test-slug"] = {
        "unique_whale_count": 3,
        "buy_count": 5,
    }

    collection = {
        "slug": "test-slug",
        "mint_count": 50,
        "unique_minters": 20,
        "volume_24h": 5.0,
        "volume_7d": 10.0,
        "floor_price": 0.02,
    }

    score = engine._calculate_alpha_score(collection)
    assert score > 0

    whale_tracker._WHALE_COLLECTIONS.pop("test-slug", None)


def test_alpha_score_no_whale_data():
    engine = AlphaEngine()
    collection = {
        "slug": "no-whale-slug",
        "mint_count": 0,
        "unique_minters": 0,
        "volume_24h": 0,
        "volume_7d": 0,
        "floor_price": 0,
    }
    score = engine._calculate_alpha_score(collection)
    assert score >= 0


def test_price_momentum_high():
    engine = AlphaEngine()
    collection = {
        "slug": "momentum-test",
        "volume_24h": 10.0,
        "volume_7d": 7.0,
        "floor_price": 0.05,
    }
    score = engine._calculate_alpha_score(collection)
    assert score > 0


def test_price_momentum_zero_volume():
    engine = AlphaEngine()
    collection = {
        "slug": "no-vol",
        "volume_24h": 0,
        "volume_7d": 0,
    }
    score = engine._calculate_alpha_score(collection)
    assert score >= 0


def test_whale_activity_levels():
    engine = AlphaEngine()

    whale_tracker._WHALE_COLLECTIONS["lvl3"] = {"unique_whale_count": 3}
    whale_tracker._WHALE_COLLECTIONS["lvl2"] = {"unique_whale_count": 2}
    whale_tracker._WHALE_COLLECTIONS["lvl1"] = {"unique_whale_count": 1}

    s3 = engine._calculate_alpha_score({"slug": "lvl3", "volume_24h": 1, "volume_7d": 1, "floor_price": 0.01})
    s2 = engine._calculate_alpha_score({"slug": "lvl2", "volume_24h": 1, "volume_7d": 1, "floor_price": 0.01})
    s1 = engine._calculate_alpha_score({"slug": "lvl1", "volume_24h": 1, "volume_7d": 1, "floor_price": 0.01})

    assert s3 > s2 > s1

    for k in ["lvl3", "lvl2", "lvl1"]:
        whale_tracker._WHALE_COLLECTIONS.pop(k, None)
