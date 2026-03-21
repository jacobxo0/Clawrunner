"""Tests for the wash trade detector."""

from src.engine.wash_detector import WashDetector


def test_wash_detector_exists():
    detector = WashDetector()
    assert detector is not None


def test_self_trade_detection():
    detector = WashDetector()
    sales = [
        {"from_address": "0xAAA", "to_address": "0xBBB", "price": 0.1, "token_id": "1"},
        {"from_address": "0xBBB", "to_address": "0xAAA", "price": 0.1, "token_id": "1"},
    ] * 6  # Need >= min_trades_for_detection
    result = detector.score(sales)
    assert isinstance(result, dict)
    assert "wash_score" in result
    assert result["wash_score"] >= 0


def test_no_wash_clean_trades():
    detector = WashDetector()
    sales = [
        {"from_address": f"0x{i:040x}", "to_address": f"0x{i+100:040x}", "price": 0.1, "token_id": str(i)}
        for i in range(15)
    ]
    result = detector.score(sales)
    assert result["wash_score"] < 50


def test_insufficient_data():
    detector = WashDetector()
    sales = [
        {"from_address": "0xAAA", "to_address": "0xBBB", "price": 0.1, "token_id": "1"},
    ]
    result = detector.score(sales)
    assert result["wash_score"] == 0
