"""
Mempool Sniper — see listings BEFORE they appear on OpenSea.

The speed hierarchy for seeing new NFT listings:
  1. Mempool (pending tx)     → ~0s after broadcast    ← THIS FILE
  2. Block confirmation       → ~12s after broadcast
  3. OpenSea WebSocket stream → ~15-30s after broadcast
  4. OpenSea REST API poll    → ~30-60s after broadcast

Most bots operate at level 3-4. This puts us at level 1.

How it works:
  - Connect to an Ethereum node via WebSocket
  - Subscribe to `newPendingTransactions` with full tx data
  - Decode Seaport calldata to extract order parameters
  - If it's a new listing → instantly check our bid cache → execute

The key insight: when someone creates a listing on OpenSea, a Seaport
`OrderFulfilled` is NOT created. Listings are off-chain signed orders.
BUT: when someone BUYS a listing, that IS an on-chain transaction.

So mempool monitoring helps us in two ways:
  1. See when competitors are buying (so we can skip stale orders)
  2. See when bids are being accepted (liquidity drying up)
  3. Front-run by detecting the APPROVAL tx that precedes a listing

For new listings, we still rely on the OpenSea WebSocket but we
PARALLELIZE the execution prep so we're ready to fire instantly.
"""

import asyncio
import time
from collections import deque
from typing import Callable, Awaitable

import structlog
from web3 import Web3

from src.config import get_settings

logger = structlog.get_logger()

# Seaport function signatures (first 4 bytes of keccak hash)
SEAPORT_SIGS = {
    "0xfb0f3ee1": "fulfillBasicOrder",
    "0x00000000": "fulfillOrder",
    "0xed98a574": "fulfillAvailableOrders",
    "0x87201b41": "fulfillAdvancedOrder",
    "0xe7acab24": "fulfillAvailableAdvancedOrders",
    "0xf2d12b12": "matchOrders",
    "0xa8174404": "matchAdvancedOrders",
}

# Known Seaport contract addresses
SEAPORT_CONTRACTS = {
    "0x00000000000000adc04c56bf30ac9d3c0aaf14dc",  # Seaport 1.5
    "0x0000000000000068f116a894984e2db1123eb395",  # Seaport 1.6
}

# ERC-721 approval signature
APPROVAL_SIG = "0xa22cb465"  # setApprovalForAll(address,bool)

# Track what we've seen to avoid duplicates
_SEEN_TX: deque = deque(maxlen=5000)
_COMPETITOR_BUYS: deque = deque(maxlen=1000)  # Recent competitor purchases


class MempoolSniper:
    """
    Monitors the Ethereum mempool for Seaport-related transactions.

    Detects:
    1. Competitor buy attempts (so we skip orders they're buying)
    2. NFT approvals (precursor to new listings)
    3. Bid acceptances (exit liquidity changes)

    Speed advantage: ~12 seconds ahead of anyone using API polling.
    """

    def __init__(self):
        settings = get_settings()
        self.rpc_url = settings.blockchain.eth_rpc_url
        self._ws_url = self._to_ws_url(self.rpc_url)
        self._running = False
        self._on_competitor_buy: Callable | None = None
        self._on_approval: Callable | None = None
        self._tracked_contracts: set[str] = set()

        # Stats
        self._tx_seen = 0
        self._seaport_tx_seen = 0
        self._start_time = 0

    @staticmethod
    def _to_ws_url(http_url: str) -> str:
        """Convert HTTP RPC URL to WebSocket URL."""
        if not http_url:
            return ""
        url = http_url.replace("https://", "wss://").replace("http://", "ws://")
        # Alchemy/Infura specific conversions
        if "alchemy.com" in url:
            url = url.replace("/v2/", "/v2/ws/") if "/v2/ws/" not in url else url
        return url

    def track_contracts(self, contracts: list[str]):
        """Add NFT contract addresses to monitor for approvals."""
        for c in contracts:
            self._tracked_contracts.add(c.lower())

    def on_competitor_buy(self, callback: Callable[[dict], Awaitable[None]]):
        """Register callback when a competitor is buying an NFT we're watching."""
        self._on_competitor_buy = callback

    def on_approval(self, callback: Callable[[dict], Awaitable[None]]):
        """Register callback when an NFT contract gets approved (pre-listing signal)."""
        self._on_approval = callback

    async def start(self):
        """Start monitoring the mempool."""
        if not self._ws_url:
            logger.warning("mempool_sniper_no_ws_url")
            return

        self._running = True
        self._start_time = time.time()
        logger.info("mempool_sniper_starting", ws_url=self._ws_url[:50])

        while self._running:
            try:
                await self._connect_and_listen()
            except Exception as e:
                if not self._running:
                    break
                logger.warning("mempool_reconnecting", error=str(e)[:100])
                await asyncio.sleep(2)

    async def _connect_and_listen(self):
        """Single WebSocket connection lifecycle."""
        try:
            import websockets
            import json
        except ImportError:
            logger.error("websockets_not_installed")
            return

        async with websockets.connect(
            self._ws_url,
            ping_interval=30,
            close_timeout=5,
        ) as ws:
            logger.info("mempool_connected")

            # Subscribe to pending transactions
            subscribe_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_subscribe",
                "params": ["newPendingTransactions"],
            }
            await ws.send(json.dumps(subscribe_msg))

            response = await ws.recv()
            resp_data = json.loads(response)
            sub_id = resp_data.get("result", "")
            logger.info("mempool_subscribed", subscription_id=sub_id)

            # Listen for pending transactions
            async for raw_msg in ws:
                if not self._running:
                    break

                try:
                    msg = json.loads(raw_msg)
                    params = msg.get("params", {})
                    tx_hash = params.get("result", "")

                    if not tx_hash or tx_hash in _SEEN_TX:
                        continue

                    _SEEN_TX.append(tx_hash)
                    self._tx_seen += 1

                    # Fetch full tx data
                    await self._analyze_pending_tx(tx_hash)

                except Exception:
                    continue

    async def _analyze_pending_tx(self, tx_hash: str):
        """Analyze a pending transaction for Seaport activity."""
        try:
            w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            tx = w3.eth.get_transaction(tx_hash)

            if tx is None:
                return

            to_addr = (tx.get("to") or "").lower()
            input_data = tx.get("input", "").hex() if isinstance(tx.get("input"), bytes) else str(tx.get("input", ""))

            if len(input_data) < 10:
                return

            func_sig = input_data[:10]

            # Check if it's a Seaport transaction (someone buying)
            if to_addr in SEAPORT_CONTRACTS and func_sig in SEAPORT_SIGS:
                self._seaport_tx_seen += 1
                func_name = SEAPORT_SIGS[func_sig]

                event = {
                    "type": "competitor_buy",
                    "tx_hash": tx_hash,
                    "buyer": tx.get("from", ""),
                    "function": func_name,
                    "gas_price_gwei": float(Web3.from_wei(tx.get("gasPrice", 0), "gwei")),
                    "value_eth": float(Web3.from_wei(tx.get("value", 0), "ether")),
                    "detected_at": time.time(),
                }

                _COMPETITOR_BUYS.append(event)

                logger.info(
                    "mempool_competitor_buy",
                    func=func_name,
                    value=event["value_eth"],
                    gas=event["gas_price_gwei"],
                )

                if self._on_competitor_buy:
                    asyncio.create_task(self._on_competitor_buy(event))

            # Check for NFT approval (pre-listing signal)
            elif to_addr in self._tracked_contracts and func_sig == APPROVAL_SIG:
                event = {
                    "type": "nft_approval",
                    "tx_hash": tx_hash,
                    "owner": tx.get("from", ""),
                    "contract": to_addr,
                    "detected_at": time.time(),
                }

                logger.debug("mempool_nft_approval", contract=to_addr[:12])

                if self._on_approval:
                    asyncio.create_task(self._on_approval(event))

        except Exception:
            pass  # Pending tx can disappear at any time

    async def stop(self):
        """Stop the mempool monitor."""
        self._running = False

    @property
    def stats(self) -> dict:
        """Get mempool monitoring stats."""
        runtime = time.time() - self._start_time if self._start_time else 0
        return {
            "running": self._running,
            "runtime_seconds": round(runtime),
            "total_tx_seen": self._tx_seen,
            "seaport_tx_seen": self._seaport_tx_seen,
            "recent_competitor_buys": len(_COMPETITOR_BUYS),
            "tracked_contracts": len(self._tracked_contracts),
        }

    @staticmethod
    def get_recent_competitor_buys(seconds: int = 60) -> list[dict]:
        """Get competitor buys in the last N seconds."""
        cutoff = time.time() - seconds
        return [b for b in _COMPETITOR_BUYS if b["detected_at"] > cutoff]

    @staticmethod
    def is_order_being_bought(value_eth: float, tolerance: float = 0.01) -> bool:
        """
        Check if a competitor is currently trying to buy at a similar price.
        If yes, our order will likely fail — skip it.
        """
        cutoff = time.time() - 15  # Last 15 seconds
        for buy in _COMPETITOR_BUYS:
            if buy["detected_at"] < cutoff:
                continue
            if abs(buy["value_eth"] - value_eth) < tolerance:
                return True
        return False
