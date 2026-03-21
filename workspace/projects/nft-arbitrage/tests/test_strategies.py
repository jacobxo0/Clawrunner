"""Tests for arbitrage strategies — bid_spread, cross_marketplace."""

from decimal import Decimal
from src.engine.cost_engine import CostEngine


def test_bid_spread_finds_opportunity(sample_collection_data):
    from src.strategies.bid_spread import BidSpreadStrategy
    engine = CostEngine(redis_cache=None)
    strategy = BidSpreadStrategy(engine)

    data = dict(sample_collection_data)
    data["listings"] = [{"price": 0.03, "token_id": "1", "venue": "opensea", "order_hash": "0x1"}]
    data["bids"] = [{"price": 0.055, "venue": "opensea", "order_hash": "0xb1"}]
    data["floor_price"] = 0.04

    opps = strategy.scan("test-id", data)
    assert len(opps) >= 1
    assert opps[0]["strategy"] == "bid_spread"
    assert opps[0]["buy_price"] == 0.03
    assert opps[0]["net_profit"] > 0


def test_bid_spread_rejects_no_spread(sample_collection_data):
    from src.strategies.bid_spread import BidSpreadStrategy
    engine = CostEngine(redis_cache=None)
    strategy = BidSpreadStrategy(engine)

    data = dict(sample_collection_data)
    data["listings"] = [{"price": 0.06, "token_id": "1", "venue": "opensea"}]
    data["bids"] = [{"price": 0.04, "venue": "opensea"}]
    data["floor_price"] = 0.05

    opps = strategy.scan("test-id", data)
    assert len(opps) == 0


def test_bid_spread_filters_unrealistic_bids(sample_collection_data):
    from src.strategies.bid_spread import BidSpreadStrategy
    engine = CostEngine(redis_cache=None)
    strategy = BidSpreadStrategy(engine)

    data = dict(sample_collection_data)
    data["listings"] = [{"price": 0.05, "token_id": "1", "venue": "opensea"}]
    data["bids"] = [{"price": 10.0, "venue": "opensea"}]
    data["floor_price"] = 0.05

    opps = strategy.scan("test-id", data)
    assert len(opps) == 0


def test_cross_marketplace_opensea_to_blur(sample_collection_data):
    from src.strategies.cross_marketplace import CrossMarketplaceStrategy
    engine = CostEngine(redis_cache=None)
    strategy = CrossMarketplaceStrategy(engine)

    data = dict(sample_collection_data)
    data["listings"] = [{"price": 0.03, "token_id": "1", "venue": "opensea", "order_hash": "0x1"}]
    data["blur_bids"] = [{"price": 0.06, "venue": "blur", "order_hash": "0xbb", "quantity": 5}]

    opps = strategy.scan("test-id", data)
    os_to_blur = [o for o in opps if o.get("sub_type") == "opensea_to_blur"]
    assert len(os_to_blur) >= 1


def test_cross_marketplace_no_bids_no_opps(sample_collection_data):
    from src.strategies.cross_marketplace import CrossMarketplaceStrategy
    engine = CostEngine(redis_cache=None)
    strategy = CrossMarketplaceStrategy(engine)

    data = dict(sample_collection_data)
    data["blur_bids"] = []
    data["bids"] = []

    opps = strategy.scan("test-id", data)
    assert len(opps) == 0
