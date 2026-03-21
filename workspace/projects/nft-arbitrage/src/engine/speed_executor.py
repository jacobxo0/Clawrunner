"""
Speed Executor — ultra-low-latency execution pipeline.

The current system's bottleneck chain:
  Stream event → check bid cache → OpenSea fulfillment API → sign → submit
                                         ↑ 500-2000ms (THIS IS WHERE WE LOSE)

This module eliminates the bottleneck by:
  1. PRE-FETCHING fulfillment data for active opportunities
  2. PRE-CACHING nonces and gas prices (avoid RPC at execution time)
  3. PARALLEL execution prep (fetch + sign happen simultaneously)
  4. COMPETITOR AWARENESS (skip orders someone else is already buying)
  5. INSTANT SUBMISSION (everything pre-built, just broadcast)

New execution chain:
  Stream event → check bid cache → check pre-fetched data → SUBMIT
                                                              ↑ ~50ms

The difference: we do the slow work BEFORE the opportunity arrives,
not after. When the moment comes, we just fire.
"""

import asyncio
import time
from collections import OrderedDict
from decimal import Decimal
from typing import Any

import structlog
from web3 import Web3
from eth_account import Account

from src.config import get_settings
from src.engine.mempool_sniper import MempoolSniper

logger = structlog.get_logger()


class NonceManager:
    """
    Pre-cached nonce management.
    Avoids an RPC call at execution time by tracking nonces locally.
    """

    def __init__(self, w3: Web3, address: str):
        self._w3 = w3
        self._address = address
        self._current_nonce: int | None = None
        self._last_sync: float = 0
        self._lock = asyncio.Lock()

    async def get_nonce(self) -> int:
        """Get next nonce, using cache when fresh enough."""
        async with self._lock:
            now = time.time()
            if self._current_nonce is None or (now - self._last_sync) > 12:
                self._current_nonce = self._w3.eth.get_transaction_count(
                    self._address, "pending"
                )
                self._last_sync = now

            nonce = self._current_nonce
            self._current_nonce += 1
            return nonce

    def invalidate(self):
        """Force re-sync on next call (after tx failure)."""
        self._current_nonce = None


class GasCache:
    """
    Pre-cached gas price that updates in the background.
    At execution time, we just read the cached value — zero latency.
    """

    def __init__(self, w3: Web3):
        self._w3 = w3
        self.gas_price: int = 0
        self.base_fee: int = 0
        self.priority_fee: int = 0
        self.max_fee: int = 0
        self._last_update: float = 0

    async def refresh(self):
        """Update cached gas prices from the chain."""
        try:
            block = self._w3.eth.get_block("latest")
            self.base_fee = block.get("baseFeePerGas", 0)
            try:
                self.priority_fee = self._w3.eth.max_priority_fee
            except Exception:
                self.priority_fee = Web3.to_wei(1.5, "gwei")

            # maxFeePerGas = 2 * baseFee + priorityFee (generous, ensures inclusion)
            self.max_fee = (self.base_fee * 2) + self.priority_fee
            self.gas_price = self._w3.eth.gas_price
            self._last_update = time.time()
        except Exception as e:
            logger.debug("gas_cache_refresh_error", error=str(e)[:80])

    @property
    def is_fresh(self) -> bool:
        return (time.time() - self._last_update) < 15

    @property
    def gwei(self) -> float:
        return float(Web3.from_wei(self.gas_price, "gwei")) if self.gas_price else 20.0


class FulfillmentCache:
    """
    Pre-fetched OpenSea fulfillment data for known opportunities.

    When we see an opportunity in the scan worker, we immediately
    fetch the fulfillment data and cache it. When the stream sniper
    sees the same listing, the fulfillment data is already ready.
    """

    def __init__(self, max_size: int = 200):
        self._cache: OrderedDict[str, dict] = OrderedDict()
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def put(self, order_hash: str, fulfillment_data: dict):
        """Cache fulfillment data for an order."""
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)
        self._cache[order_hash] = {
            "data": fulfillment_data,
            "cached_at": time.time(),
        }

    def get(self, order_hash: str, max_age_seconds: int = 60) -> dict | None:
        """Get cached fulfillment data if fresh enough."""
        entry = self._cache.get(order_hash)
        if entry is None:
            self._misses += 1
            return None

        age = time.time() - entry["cached_at"]
        if age > max_age_seconds:
            self._misses += 1
            del self._cache[order_hash]
            return None

        self._hits += 1
        return entry["data"]

    def invalidate(self, order_hash: str):
        """Remove a stale entry."""
        self._cache.pop(order_hash, None)

    @property
    def stats(self) -> dict:
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{self._hits / max(self._hits + self._misses, 1) * 100:.1f}%",
        }


class SpeedExecutor:
    """
    Ultra-fast trade execution with pre-cached everything.

    Usage:
      1. Call `warm_up()` during startup to pre-cache gas & nonces
      2. Call `pre_fetch_fulfillment()` when opportunities are found
      3. Call `instant_execute()` when stream sniper triggers — fires in ~50ms
    """

    def __init__(self):
        settings = get_settings()
        self.rpc_url = settings.blockchain.eth_rpc_url
        self.private_key = settings.blockchain.eth_private_key
        self.api_key = settings.marketplace.opensea_api_key
        self.flashbots_rpc = settings.blockchain.flashbots_rpc_url
        self.chain_id = settings.blockchain.chain_id
        self.max_gas_gwei = settings.execution.get("max_gas_gwei", 50)

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        if self.private_key:
            self.account = Account.from_key(self.private_key)
            self.wallet = self.account.address
        else:
            self.account = None
            self.wallet = None

        self.nonce_mgr = NonceManager(self.w3, self.wallet) if self.wallet else None
        self.gas_cache = GasCache(self.w3)
        self.fulfillment_cache = FulfillmentCache()

        # Track execution timing for optimization
        self._execution_times: list[float] = []

    async def warm_up(self):
        """Pre-cache everything for instant execution."""
        if not self.wallet:
            return

        await self.gas_cache.refresh()
        if self.nonce_mgr:
            await self.nonce_mgr.get_nonce()

        logger.info(
            "speed_executor_warmed_up",
            gas_gwei=self.gas_cache.gwei,
            wallet=self.wallet[:12],
        )

    async def pre_fetch_fulfillment(
        self,
        listing_hash: str,
        bid_hash: str,
        token_id: str,
        nft_contract: str,
        protocol_address: str = None,
        chain: str = "ethereum",
    ):
        """
        Pre-fetch fulfillment data for both buy and sell sides.
        Called when an opportunity is detected (during scan, not execution).
        """
        import httpx

        base_url = "https://api.opensea.io"
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        protocol = protocol_address or "0x0000000000000068F116a894984e2DB1123eB395"

        async with httpx.AsyncClient(timeout=10) as client:
            # Fetch both fulfillments in parallel
            buy_task = client.post(
                f"{base_url}/api/v2/listings/fulfillment_data",
                headers=headers,
                json={
                    "listing": {
                        "hash": listing_hash,
                        "chain": chain,
                        "protocol_address": protocol,
                    },
                    "fulfiller": {"address": self.wallet},
                },
            )

            sell_task = client.post(
                f"{base_url}/api/v2/offers/fulfillment_data",
                headers=headers,
                json={
                    "offer": {
                        "hash": bid_hash,
                        "chain": chain,
                        "protocol_address": protocol,
                    },
                    "fulfiller": {"address": self.wallet},
                    "consideration": {
                        "asset_contract_address": nft_contract,
                        "token_id": str(token_id),
                    },
                },
            )

            buy_resp, sell_resp = await asyncio.gather(
                buy_task, sell_task, return_exceptions=True,
            )

            if not isinstance(buy_resp, Exception) and buy_resp.status_code == 200:
                self.fulfillment_cache.put(
                    f"buy:{listing_hash}", buy_resp.json()
                )

            if not isinstance(sell_resp, Exception) and sell_resp.status_code == 200:
                self.fulfillment_cache.put(
                    f"sell:{bid_hash}:{token_id}", sell_resp.json()
                )

            logger.debug(
                "speed_pre_fetched",
                listing=listing_hash[:12],
                bid=bid_hash[:12],
                buy_ok=not isinstance(buy_resp, Exception) and buy_resp.status_code == 200,
                sell_ok=not isinstance(sell_resp, Exception) and sell_resp.status_code == 200,
            )

    async def instant_execute(
        self,
        listing_hash: str,
        bid_hash: str,
        token_id: str,
        nft_contract: str,
        buy_price_eth: float,
        protocol_address: str = None,
    ) -> dict:
        """
        Execute a trade as fast as possible using pre-cached data.

        Returns within ~50-200ms if fulfillment data was pre-fetched.
        Falls back to live fetch if cache misses (~500-2000ms).
        """
        start = time.time()

        if not self.wallet or not self.account:
            return {"status": "error", "reason": "wallet_not_configured"}

        # Check if a competitor is already buying at this price
        if MempoolSniper.is_order_being_bought(buy_price_eth):
            return {"status": "skipped", "reason": "competitor_buying_same_price"}

        # Gas check (from cache — no RPC call)
        if not self.gas_cache.is_fresh:
            await self.gas_cache.refresh()

        if self.gas_cache.gwei > self.max_gas_gwei:
            return {"status": "skipped", "reason": f"gas_too_high:{self.gas_cache.gwei:.0f}"}

        # Try to get pre-cached fulfillment data
        buy_data = self.fulfillment_cache.get(f"buy:{listing_hash}")
        sell_data = self.fulfillment_cache.get(f"sell:{bid_hash}:{token_id}")

        # If not cached, fetch live (slower path)
        if not buy_data or not sell_data:
            logger.debug("speed_cache_miss_fetching_live")
            await self.pre_fetch_fulfillment(
                listing_hash, bid_hash, token_id, nft_contract,
                protocol_address,
            )
            buy_data = self.fulfillment_cache.get(f"buy:{listing_hash}")
            sell_data = self.fulfillment_cache.get(f"sell:{bid_hash}:{token_id}")

        if not buy_data or not sell_data:
            elapsed = (time.time() - start) * 1000
            return {
                "status": "error",
                "reason": "fulfillment_data_unavailable",
                "elapsed_ms": round(elapsed),
            }

        # Extract transaction data
        buy_tx = buy_data.get("fulfillment_data", {}).get("transaction", {})
        sell_tx = sell_data.get("fulfillment_data", {}).get("transaction", {})

        if not buy_tx or not sell_tx:
            return {"status": "error", "reason": "missing_tx_data_in_fulfillment"}

        # Build and sign both transactions
        nonce = await self.nonce_mgr.get_nonce()

        buy_signed = self._sign_tx(
            to=buy_tx.get("to", ""),
            value=int(buy_tx.get("value", "0")),
            data=self._parse_input(buy_tx),
            nonce=nonce,
            gas_limit=300_000,
        )

        sell_signed = self._sign_tx(
            to=sell_tx.get("to", ""),
            value=int(sell_tx.get("value", "0")),
            data=self._parse_input(sell_tx),
            nonce=nonce + 1,
            gas_limit=300_000,
        )

        if not buy_signed or not sell_signed:
            self.nonce_mgr.invalidate()
            return {"status": "error", "reason": "tx_signing_failed"}

        # Submit as Flashbots bundle
        buy_raw = "0x" + buy_signed.raw_transaction.hex()
        sell_raw = "0x" + sell_signed.raw_transaction.hex()

        elapsed_prep = (time.time() - start) * 1000

        result = await self._submit_bundle(buy_raw, sell_raw)

        elapsed_total = (time.time() - start) * 1000
        self._execution_times.append(elapsed_total)

        if result:
            buy_hash = self.w3.keccak(buy_signed.raw_transaction).hex()
            sell_hash = self.w3.keccak(sell_signed.raw_transaction).hex()

            logger.info(
                "speed_execute_submitted",
                prep_ms=round(elapsed_prep),
                total_ms=round(elapsed_total),
                buy_tx=buy_hash[:16],
            )

            return {
                "status": "submitted",
                "buy_tx_hash": buy_hash,
                "sell_tx_hash": sell_hash,
                "prep_ms": round(elapsed_prep),
                "total_ms": round(elapsed_total),
                "bundle_hash": result.get("bundleHash", ""),
            }
        else:
            # Fallback: sequential submission
            try:
                buy_hash = self.w3.eth.send_raw_transaction(
                    buy_signed.raw_transaction
                ).hex()
                sell_hash = self.w3.eth.send_raw_transaction(
                    sell_signed.raw_transaction
                ).hex()

                elapsed_total = (time.time() - start) * 1000

                logger.info(
                    "speed_execute_sequential",
                    total_ms=round(elapsed_total),
                    buy_tx=buy_hash[:16],
                )

                return {
                    "status": "submitted_sequential",
                    "buy_tx_hash": buy_hash,
                    "sell_tx_hash": sell_hash,
                    "total_ms": round(elapsed_total),
                }
            except Exception as e:
                self.nonce_mgr.invalidate()
                return {"status": "error", "reason": str(e)[:100]}

    def _sign_tx(
        self, to: str, value: int, data: bytes,
        nonce: int, gas_limit: int,
    ):
        """Sign a transaction using cached gas params."""
        try:
            tx = {
                "nonce": nonce,
                "to": Web3.to_checksum_address(to),
                "value": value,
                "gas": gas_limit,
                "maxFeePerGas": self.gas_cache.max_fee or Web3.to_wei(50, "gwei"),
                "maxPriorityFeePerGas": self.gas_cache.priority_fee or Web3.to_wei(1.5, "gwei"),
                "chainId": self.chain_id,
                "data": data,
                "type": 2,  # EIP-1559
            }
            return self.account.sign_transaction(tx)
        except Exception as e:
            logger.error("speed_sign_failed", error=str(e)[:80])
            return None

    def _parse_input(self, tx_data: dict) -> bytes:
        """Parse input data from fulfillment response."""
        input_data = tx_data.get("input_data", {})
        if isinstance(input_data, str) and input_data.startswith("0x"):
            return bytes.fromhex(input_data[2:])
        return b""

    async def _submit_bundle(self, buy_raw: str, sell_raw: str) -> dict | None:
        """Submit Flashbots bundle for atomic execution."""
        import httpx

        try:
            target_block = self.w3.eth.block_number + 1

            async with httpx.AsyncClient(timeout=10) as client:
                for offset in range(3):
                    resp = await client.post(
                        self.flashbots_rpc,
                        json={
                            "jsonrpc": "2.0",
                            "method": "eth_sendBundle",
                            "params": [{
                                "txs": [buy_raw, sell_raw],
                                "blockNumber": hex(target_block + offset),
                            }],
                            "id": 1,
                        },
                    )
                    result = resp.json()
                    if "result" in result and result["result"]:
                        return result["result"]

            return None
        except Exception as e:
            logger.debug("speed_bundle_error", error=str(e)[:80])
            return None

    @property
    def stats(self) -> dict:
        """Execution performance stats."""
        times = self._execution_times[-50:]  # Last 50
        return {
            "cache_stats": self.fulfillment_cache.stats,
            "gas_gwei": self.gas_cache.gwei,
            "gas_fresh": self.gas_cache.is_fresh,
            "avg_execution_ms": (
                round(sum(times) / len(times)) if times else 0
            ),
            "min_execution_ms": round(min(times)) if times else 0,
            "max_execution_ms": round(max(times)) if times else 0,
            "total_executions": len(self._execution_times),
        }
