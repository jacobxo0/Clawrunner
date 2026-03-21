"""Tests for the anti-bot camouflage engine."""

import os
import pytest
from unittest.mock import patch


def test_camouflage_single_wallet():
    from src.engine.camouflage import CamouflageEngine
    engine = CamouflageEngine()
    assert engine.wallet_count >= 1
    wallet = engine.get_next_wallet()
    assert "address" in wallet
    assert "private_key" in wallet


def test_camouflage_rpc_rotation():
    from src.engine.camouflage import CamouflageEngine
    engine = CamouflageEngine()
    assert engine.rpc_count >= 1
    rpc = engine.get_next_rpc()
    assert isinstance(rpc, str)


def test_camouflage_wallet_round_robin():
    from src.engine.camouflage import CamouflageEngine
    engine = CamouflageEngine()
    if engine.wallet_count > 1:
        w1 = engine.get_next_wallet()
        w2 = engine.get_next_wallet()
        assert w1["address"] != w2["address"] or engine.wallet_count == 1


def test_camouflage_time_since_last_action():
    from src.engine.camouflage import CamouflageEngine
    engine = CamouflageEngine()
    assert engine.time_since_last_action() == float("inf")


@pytest.mark.asyncio
async def test_camouflage_jitter_disabled():
    from src.engine.camouflage import CamouflageEngine
    engine = CamouflageEngine()
    engine.enabled = False
    delay = await engine.apply_jitter()
    assert delay == 0.0


@pytest.mark.asyncio
async def test_camouflage_jitter_enabled():
    from src.engine.camouflage import CamouflageEngine
    engine = CamouflageEngine()
    engine.enabled = True
    engine.min_delay_ms = 1
    engine.max_delay_ms = 10
    delay = await engine.apply_jitter()
    assert 0.0 < delay <= 0.015
    assert engine.time_since_last_action() < 1.0
