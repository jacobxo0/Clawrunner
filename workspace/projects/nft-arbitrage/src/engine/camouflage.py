"""
Anti-Bot Camouflage Engine — evade detection by varying wallet, RPC, and timing.

Marketplaces and competitors pattern-match on:
  - Same wallet buying repeatedly
  - Rapid-fire transactions from one address
  - Single RPC endpoint usage patterns

Countermeasures:
  - Rotate wallets across a pool of funded addresses
  - Add random timing jitter between actions
  - Rotate RPC endpoints to avoid fingerprinting
"""

import asyncio
import os
import random
import time

import structlog
from eth_account import Account

from src.config import get_settings

logger = structlog.get_logger()


class CamouflageEngine:
    """
    Manages wallet rotation, RPC rotation, and timing jitter
    to avoid bot-detection heuristics on NFT marketplaces.
    """

    def __init__(self):
        settings = get_settings()
        cam_cfg = settings.yaml_settings.get("camouflage", {})

        self.enabled = cam_cfg.get("enabled", False)
        self.min_delay_ms = cam_cfg.get("min_delay_ms", 500)
        self.max_delay_ms = cam_cfg.get("max_delay_ms", 5000)

        self._wallets = self._load_wallets()
        self._rpcs = self._load_rpcs()
        self._wallet_idx = 0
        self._rpc_idx = 0
        self._last_action_time: float = 0.0

    def _load_wallets(self) -> list[dict]:
        """Load wallet pool from WALLET_KEYS_CSV env var, fallback to single key."""
        wallets = []
        csv = os.getenv("WALLET_KEYS_CSV", "")
        if csv:
            for key in csv.split(","):
                key = key.strip()
                if key:
                    try:
                        acct = Account.from_key(key)
                        wallets.append({
                            "private_key": key,
                            "address": acct.address,
                            "account": acct,
                        })
                    except Exception as e:
                        logger.warning("camouflage_bad_wallet_key", error=str(e)[:60])

        if not wallets:
            pk = get_settings().blockchain.eth_private_key
            if pk:
                acct = Account.from_key(pk)
                wallets.append({
                    "private_key": pk,
                    "address": acct.address,
                    "account": acct,
                })

        logger.info("camouflage_wallets_loaded", count=len(wallets))
        return wallets

    def _load_rpcs(self) -> list[str]:
        """Load RPC pool from RPC_URLS_CSV env var, fallback to single URL."""
        rpcs = []
        csv = os.getenv("RPC_URLS_CSV", "")
        if csv:
            rpcs = [u.strip() for u in csv.split(",") if u.strip()]

        if not rpcs:
            rpcs = [get_settings().blockchain.eth_rpc_url]

        logger.info("camouflage_rpcs_loaded", count=len(rpcs))
        return [r for r in rpcs if r]

    def get_next_wallet(self) -> dict:
        """Round-robin wallet rotation. Returns {private_key, address, account}."""
        if not self._wallets:
            return {}
        wallet = self._wallets[self._wallet_idx % len(self._wallets)]
        self._wallet_idx += 1
        return wallet

    def get_next_rpc(self) -> str:
        """Round-robin RPC endpoint rotation."""
        if not self._rpcs:
            return get_settings().blockchain.eth_rpc_url
        rpc = self._rpcs[self._rpc_idx % len(self._rpcs)]
        self._rpc_idx += 1
        return rpc

    async def apply_jitter(self) -> float:
        """
        Async random delay to avoid pattern detection.
        Returns the actual delay in seconds.
        """
        if not self.enabled:
            return 0.0

        delay_ms = random.randint(self.min_delay_ms, self.max_delay_ms)
        delay_s = delay_ms / 1000.0
        await asyncio.sleep(delay_s)
        self._last_action_time = time.time()
        return delay_s

    def time_since_last_action(self) -> float:
        """Seconds since last recorded action."""
        if self._last_action_time == 0.0:
            return float("inf")
        return time.time() - self._last_action_time

    @property
    def wallet_count(self) -> int:
        return len(self._wallets)

    @property
    def rpc_count(self) -> int:
        return len(self._rpcs)
