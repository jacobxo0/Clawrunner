"""Shared test fixtures for NFT Arbitrage OS test suite."""

import os
import sys
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock

import pytest

os.environ.setdefault("OPENSEA_API_KEY", "test-key")
os.environ.setdefault("ETH_RPC_URL", "https://eth.example.com")
os.environ.setdefault("ETH_PRIVATE_KEY", "0x" + "ab" * 32)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def mock_settings(monkeypatch):
    """Provide mock settings that don't require real config files."""
    from src.config import Settings, get_settings

    get_settings.cache_clear()
    settings = get_settings()
    return settings


@pytest.fixture
def cost_engine():
    from src.engine.cost_engine import CostEngine
    return CostEngine(redis_cache=None)


@pytest.fixture
def sample_listings():
    return [
        {"price": 0.05, "token_id": "1", "venue": "opensea", "order_hash": "0xabc1"},
        {"price": 0.06, "token_id": "2", "venue": "opensea", "order_hash": "0xabc2"},
        {"price": 0.04, "token_id": "3", "venue": "opensea", "order_hash": "0xabc3"},
    ]


@pytest.fixture
def sample_bids():
    return [
        {"price": 0.055, "venue": "opensea", "order_hash": "0xbid1", "quantity": 3},
        {"price": 0.048, "venue": "opensea", "order_hash": "0xbid2", "quantity": 5},
    ]


@pytest.fixture
def sample_blur_listings():
    return [
        {"price": 0.045, "token_id": "10", "venue": "blur", "order_hash": "0xblur1"},
        {"price": 0.052, "token_id": "11", "venue": "blur", "order_hash": "0xblur2"},
    ]


@pytest.fixture
def sample_blur_bids():
    return [
        {"price": 0.06, "venue": "blur", "order_hash": "0xbb1", "quantity": 10},
        {"price": 0.058, "venue": "blur", "order_hash": "0xbb2", "quantity": 5},
    ]


@pytest.fixture
def sample_collection_data(sample_listings, sample_bids, sample_blur_listings, sample_blur_bids):
    return {
        "slug": "test-collection",
        "listings": sample_listings,
        "bids": sample_bids,
        "sales_7d": [
            {"price": 0.05, "token_id": "100"},
            {"price": 0.052, "token_id": "101"},
            {"price": 0.048, "token_id": "102"},
            {"price": 0.055, "token_id": "103"},
        ],
        "sales_24h": [
            {"price": 0.05, "token_id": "100", "to_address": "0xbuyer1"},
        ],
        "blur_listings": sample_blur_listings,
        "blur_bids": sample_blur_bids,
        "blur_best_bid": 0.06,
        "blur_floor": 0.045,
        "floor_price": 0.04,
        "num_owners": 500,
        "volume_7d": 10.5,
        "royalty_bps": 500,
        "marketplace_fee_bps": 250,
    }
