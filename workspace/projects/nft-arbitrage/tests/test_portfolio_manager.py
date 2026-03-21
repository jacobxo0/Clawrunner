"""Tests for the Portfolio Manager with inventory intelligence."""

import time
from src.engine.portfolio_manager import PortfolioManager


def test_can_take_position_within_limits():
    pm = PortfolioManager()
    assert pm.can_take_position(0.1)


def test_cannot_exceed_total_exposure():
    pm = PortfolioManager()
    pm.add_position("col1", pm.max_total_exposure - 0.01)
    assert not pm.can_take_position(0.02)


def test_cannot_exceed_collection_limit():
    pm = PortfolioManager()
    pm.add_position("col1", pm.max_per_collection)
    assert not pm.can_take_position(0.01, collection_id="col1")


def test_cannot_exceed_max_positions():
    pm = PortfolioManager()
    for i in range(pm.max_positions):
        pm.add_position(f"col{i}", 0.01)
    assert not pm.can_take_position(0.01)


def test_add_remove_position():
    pm = PortfolioManager()
    pm.add_position("col1", 0.5)
    assert pm.get_total_exposure() == 0.5
    assert pm.get_collection_exposure("col1") == 0.5

    pm.remove_position("col1", 0.3)
    assert abs(pm.get_collection_exposure("col1") - 0.2) < 1e-9

    pm.remove_position("col1", 0.2)
    assert pm.get_collection_exposure("col1") == 0.0


def test_check_stale_positions():
    pm = PortfolioManager()
    pm.add_position("col1", 0.1)
    # Backdate the timestamp to simulate staleness
    pm._position_timestamps["col1"] = time.time() - (pm.max_hold_hours * 3600 + 60)
    stale = pm.check_stale_positions()
    assert len(stale) == 1
    assert stale[0]["collection_id"] == "col1"


def test_check_collection_cap():
    pm = PortfolioManager()
    assert pm.check_collection_cap("col1", 0.5)
    pm.add_position("col1", pm.max_per_collection)
    assert not pm.check_collection_cap("col1", 0.01)


def test_should_auto_deleverage():
    pm = PortfolioManager()
    assert not pm.should_auto_deleverage()
    pm.add_position("col1", pm.max_total_exposure * 0.9)
    assert pm.should_auto_deleverage()


def test_get_deleverage_candidates():
    pm = PortfolioManager()
    pm.add_position("col1", 0.1)
    time.sleep(0.01)
    pm.add_position("col2", 0.1)
    candidates = pm.get_deleverage_candidates()
    assert candidates[0] == "col1"
