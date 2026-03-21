"""Tests for the dynamic relister (Dutch auction price decay)."""

from src.engine.relister import DynamicRelister


def test_initial_price_above_acquisition():
    relister = DynamicRelister()
    price = relister.calculate_relist_price(
        acquisition_price=1.0,
        hours_held=0,
        floor_price=0.8,
    )
    assert price > 1.0


def test_price_decays_over_time():
    relister = DynamicRelister()
    price_0h = relister.calculate_relist_price(1.0, 0, 0.8)
    price_10h = relister.calculate_relist_price(1.0, 10, 0.8)
    price_20h = relister.calculate_relist_price(1.0, 20, 0.8)
    assert price_0h > price_10h > price_20h


def test_price_never_below_floor():
    relister = DynamicRelister()
    price = relister.calculate_relist_price(
        acquisition_price=1.0,
        hours_held=100,
        floor_price=0.9,
    )
    assert price >= 0.9 * 0.98


def test_price_clamp_to_min_acceptable():
    relister = DynamicRelister()
    price = relister.calculate_relist_price(
        acquisition_price=1.0,
        hours_held=100,
        floor_price=0.0,
    )
    min_acceptable = 1.0 * (1.0 + relister.min_price_floor_pct)
    assert price >= min_acceptable


def test_zero_floor_price():
    relister = DynamicRelister()
    price = relister.calculate_relist_price(
        acquisition_price=0.5,
        hours_held=5,
        floor_price=0,
    )
    assert price > 0
