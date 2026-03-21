"""Tests for the Seaport ABI encoder — basic orders, match, fulfillAvailable."""

import pytest
from src.execution.seaport_encoder import (
    encode_basic_order,
    encode_match_advanced_orders,
    encode_fulfill_available_advanced_orders,
    encode_fulfillment_tx,
    _coerce_bytes32,
    _coerce_address,
    _coerce_int,
)


def test_coerce_bytes32_from_hex():
    result = _coerce_bytes32("0x" + "ab" * 32)
    assert len(result) == 32


def test_coerce_bytes32_from_int():
    result = _coerce_bytes32(42)
    assert len(result) == 32
    assert result[-1] == 42


def test_coerce_address_zero():
    result = _coerce_address(None)
    assert result == "0x0000000000000000000000000000000000000000"


def test_coerce_address_valid():
    addr = "0xd387a6e4e84a6c86bd90c158c6028a58cc8ac459"
    result = _coerce_address(addr)
    assert result.startswith("0x")
    assert len(result) == 42


def test_coerce_int():
    assert _coerce_int(42) == 42
    assert _coerce_int("100") == 100
    assert _coerce_int(None) == 0


def test_encode_basic_order():
    params = {
        "considerationToken": "0x0000000000000000000000000000000000000000",
        "considerationIdentifier": 0,
        "considerationAmount": "1000000000000000",
        "offerer": "0xd387a6e4e84a6c86bd90c158c6028a58cc8ac459",
        "zone": "0x0000000000000000000000000000000000000000",
        "offerToken": "0x5180db8F5c931aaE63c74266b211F580155ecac8",
        "offerIdentifier": 42,
        "offerAmount": 1,
        "basicOrderType": 0,
        "startTime": 1000000,
        "endTime": 9999999,
        "zoneHash": "0x" + "00" * 32,
        "salt": 12345,
        "offererConduitKey": "0x" + "00" * 32,
        "fulfillerConduitKey": "0x" + "00" * 32,
        "totalOriginalAdditionalRecipients": 0,
        "additionalRecipients": [],
        "signature": "0xdeadbeef",
    }
    result = encode_basic_order(params)
    assert isinstance(result, (bytes, str))
    assert len(result) > 0


def test_encode_match_advanced_orders():
    input_data = {
        "orders": [{
            "parameters": {
                "offerer": "0xd387a6e4e84a6c86bd90c158c6028a58cc8ac459",
                "zone": "0x0000000000000000000000000000000000000000",
                "offer": [],
                "consideration": [],
                "orderType": 0,
                "startTime": 1000,
                "endTime": 9999,
                "zoneHash": "0x" + "00" * 32,
                "salt": 1,
                "conduitKey": "0x" + "00" * 32,
                "totalOriginalConsiderationItems": 0,
            },
            "numerator": 1,
            "denominator": 1,
            "signature": "0xab",
            "extraData": "0x",
        }],
        "criteriaResolvers": [],
        "fulfillments": [],
        "recipient": "0x0000000000000000000000000000000000000000",
    }
    result = encode_match_advanced_orders(input_data)
    assert isinstance(result, (bytes, str))
    assert len(result) > 0


def test_encode_fulfill_available_advanced_orders():
    input_data = {
        "advancedOrders": [{
            "parameters": {
                "offerer": "0xd387a6e4e84a6c86bd90c158c6028a58cc8ac459",
                "zone": "0x0000000000000000000000000000000000000000",
                "offer": [],
                "consideration": [],
                "orderType": 0,
                "startTime": 1000,
                "endTime": 9999,
                "zoneHash": "0x" + "00" * 32,
                "salt": 1,
                "conduitKey": "0x" + "00" * 32,
                "totalOriginalConsiderationItems": 0,
            },
            "numerator": 1,
            "denominator": 1,
            "signature": "0xab",
            "extraData": "0x",
        }],
        "criteriaResolvers": [],
        "offerFulfillments": [[{"orderIndex": 0, "itemIndex": 0}]],
        "considerationFulfillments": [[{"orderIndex": 0, "itemIndex": 0}]],
        "fulfillerConduitKey": "0x" + "00" * 32,
        "recipient": "0x0000000000000000000000000000000000000000",
        "maximumFulfilled": 1,
    }
    result = encode_fulfill_available_advanced_orders(input_data)
    assert isinstance(result, (bytes, str))
    assert len(result) > 0


def test_dispatch_basic_order():
    tx_data = {
        "function": "fulfillBasicOrder_efficient_6GL6yc",
        "input_data": {
            "parameters": {
                "considerationToken": "0x0000000000000000000000000000000000000000",
                "offerer": "0xd387a6e4e84a6c86bd90c158c6028a58cc8ac459",
                "zone": "0x0000000000000000000000000000000000000000",
                "offerToken": "0x5180db8F5c931aaE63c74266b211F580155ecac8",
                "offerIdentifier": 1,
                "offerAmount": 1,
                "basicOrderType": 0,
                "startTime": 1000,
                "endTime": 9999,
                "zoneHash": "0x" + "00" * 32,
                "salt": 1,
                "offererConduitKey": "0x" + "00" * 32,
                "fulfillerConduitKey": "0x" + "00" * 32,
                "additionalRecipients": [],
                "signature": "0xab",
            },
        },
    }
    result = encode_fulfillment_tx(tx_data)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_dispatch_hex_passthrough():
    tx_data = {
        "function": "anything",
        "input_data": "0xdeadbeef",
    }
    result = encode_fulfillment_tx(tx_data)
    assert result == bytes.fromhex("deadbeef")


def test_dispatch_unknown_function():
    tx_data = {
        "function": "unknownMethod",
        "input_data": {"some": "data"},
    }
    result = encode_fulfillment_tx(tx_data)
    assert result == b""
