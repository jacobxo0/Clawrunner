"""Tests for the orderbook reconstruction and microstructure analytics."""

from src.engine.orderbook import OrderbookBuilder, OrderbookSnapshot, OrderLevel


def test_build_basic_orderbook():
    builder = OrderbookBuilder()
    listings = [
        {"price": 0.1, "token_id": "1", "venue": "opensea", "order_hash": "0x1"},
        {"price": 0.12, "token_id": "2", "venue": "opensea", "order_hash": "0x2"},
    ]
    bids = [
        {"price": 0.09, "venue": "opensea", "order_hash": "0xb1", "quantity": 3},
        {"price": 0.085, "venue": "opensea", "order_hash": "0xb2", "quantity": 5},
    ]
    snapshot = builder.build("test-slug", listings, bids)

    assert snapshot.slug == "test-slug"
    assert snapshot.best_ask == 0.1
    assert snapshot.best_bid == 0.09
    assert snapshot.spread == pytest.approx(0.01, abs=1e-9)
    assert snapshot.spread_pct > 0
    assert len(snapshot.asks) == 2
    assert len(snapshot.bids) == 2


def test_asks_sorted_ascending():
    builder = OrderbookBuilder()
    listings = [
        {"price": 0.15, "token_id": "1"},
        {"price": 0.10, "token_id": "2"},
        {"price": 0.12, "token_id": "3"},
    ]
    snapshot = builder.build("test", listings, [])
    assert snapshot.asks[0].price == 0.10
    assert snapshot.asks[-1].price == 0.15


def test_bids_sorted_descending():
    builder = OrderbookBuilder()
    bids = [
        {"price": 0.08, "venue": "opensea", "quantity": 1},
        {"price": 0.10, "venue": "opensea", "quantity": 1},
        {"price": 0.09, "venue": "opensea", "quantity": 1},
    ]
    snapshot = builder.build("test", [], bids)
    assert snapshot.bids[0].price == 0.10
    assert snapshot.bids[-1].price == 0.08


def test_multi_marketplace_merge():
    builder = OrderbookBuilder()
    os_listings = [{"price": 0.10, "token_id": "1", "venue": "opensea"}]
    blur_listings = [{"price": 0.095, "token_id": "2"}]
    snapshot = builder.build("test", os_listings, [], blur_listings=blur_listings)
    assert len(snapshot.asks) == 2
    assert snapshot.best_ask == 0.095


def test_imbalance_positive_bid_heavy():
    snapshot = OrderbookSnapshot(
        slug="test",
        bids=[OrderLevel(price=0.1, quantity=10, venue="opensea")],
        asks=[OrderLevel(price=0.11, quantity=1, venue="opensea")],
    )
    assert snapshot.imbalance > 0


def test_imbalance_negative_ask_heavy():
    snapshot = OrderbookSnapshot(
        slug="test",
        bids=[OrderLevel(price=0.1, quantity=1, venue="opensea")],
        asks=[OrderLevel(price=0.11, quantity=10, venue="opensea")],
    )
    assert snapshot.imbalance < 0


def test_estimate_toxicity_empty():
    builder = OrderbookBuilder()
    snapshot = OrderbookSnapshot(slug="test", bids=[], asks=[])
    toxicity = builder.estimate_toxicity(snapshot)
    assert toxicity == 0.5


def test_estimate_toxicity_range():
    builder = OrderbookBuilder()
    snapshot = OrderbookSnapshot(
        slug="test",
        bids=[OrderLevel(price=0.1, quantity=5, venue="opensea")],
        asks=[OrderLevel(price=0.11, quantity=5, venue="opensea")],
    )
    toxicity = builder.estimate_toxicity(snapshot)
    assert 0.0 <= toxicity <= 1.0


def test_cached_snapshot():
    builder = OrderbookBuilder()
    builder.build("cached-slug", [{"price": 0.1, "token_id": "1"}], [])
    cached = builder.get("cached-slug")
    assert cached is not None
    assert cached.slug == "cached-slug"
    assert builder.get("nonexistent") is None


import pytest
