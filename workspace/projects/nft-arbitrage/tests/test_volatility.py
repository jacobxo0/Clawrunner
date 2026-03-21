"""Tests for the volatility calculator and threshold adjuster."""

from src.engine.volatility import calculate_volatility, adjust_threshold


def test_insufficient_data_returns_neutral():
    assert calculate_volatility([]) == 1.0
    assert calculate_volatility([0.5]) == 1.0
    assert calculate_volatility([0.5, 0.6]) == 1.0


def test_stable_prices_low_volatility():
    prices = [1.0, 1.01, 1.0, 1.01, 1.0, 1.01, 1.0]
    vol = calculate_volatility(prices)
    assert vol < 1.0


def test_volatile_prices_high_volatility():
    prices = [1.0, 2.0, 0.5, 3.0, 0.3, 4.0]
    vol = calculate_volatility(prices)
    assert vol > 1.0


def test_volatility_clamped():
    prices = [0.001, 100.0, 0.001, 100.0]
    vol = calculate_volatility(prices)
    assert vol <= 5.0
    assert vol >= 0.3


def test_adjust_threshold_scales():
    base = 0.005
    low_vol = adjust_threshold(base, 0.5)
    high_vol = adjust_threshold(base, 2.0)
    assert high_vol > base
    assert low_vol < base


def test_adjust_threshold_neutral():
    base = 0.01
    result = adjust_threshold(base, 1.0)
    assert result == base


def test_zero_prices_filtered():
    prices = [0, 0.5, 0, 0.6, 0, 0.55, 0.58]
    vol = calculate_volatility(prices)
    assert vol > 0
