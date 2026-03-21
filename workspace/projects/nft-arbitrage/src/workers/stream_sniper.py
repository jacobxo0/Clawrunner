"""
Stream Sniper — ultra-fast arbitrage reactor.

Instead of polling OpenSea every 30 seconds, this listens via WebSocket
and reacts to new listings/bids within milliseconds.

Flow:
1. WebSocket receives "item_listed" event → new cheap listing appeared
2. Instantly check: is there an active bid ABOVE this listing price?
3. Pre-flight: verify wallet has enough balance on the correct chain
4. If yes → ATOMIC buy+sell in same block → profit

This is ~100x faster than polling. While other bots poll every 10-30 seconds,
we see the listing the MOMENT it goes live.
"""

import asyncio
import time
from decimal import Decimal

import structlog

from src.config import get_settings
from src.ingestion.opensea_stream import OpenSeaStream
from src.ingestion.opensea import OpenSeaClient
from src.execution.seaport import SeaportExecutor
from src.engine.cost_engine import CostEngine
from src.notifications.telegram import TelegramNotifier

logger = structlog.get_logger()

_RECENT_ATTEMPTS: dict[str, float] = {}  # order_hash -> timestamp
_KNOWN_BIDS: dict[str, dict] = {}  # collection_slug -> {price, order_hash, ...}
_TOKEN_COOLDOWN: dict[str, float] = {}  # "slug:token_id" -> last_attempt_ts
_EXECUTING_NOW: set[str] = set()  # slugs currently in execution (prevent parallel)

COOLDOWN_AFTER_FAIL_S = 120
COOLDOWN_AFTER_SUCCESS_S = 300


class StreamSniper:
    """
    Reacts to real-time OpenSea events for instant arbitrage execution.

    Speed advantage:
    - Normal bot: poll → find opportunity → verify → execute (~30-60 seconds)
    - Stream sniper: event arrives → check bid cache → execute (~1-3 seconds)
    """

    def __init__(self):
        settings = get_settings()
        self.opensea = OpenSeaClient()
        self.cost_engine = CostEngine()
        self.notifier = TelegramNotifier()

        api_key = settings.marketplace.opensea_api_key
        self.stream = OpenSeaStream(api_key)

        exec_cfg = settings.execution
        self.max_gas_gwei = exec_cfg.get("max_gas_gwei", 50)
        self.max_single_trade = settings.risk.get("max_single_trade_eth", 1.0)
        self.min_profit_eth = Decimal(
            str(settings.strategies.get("bid_spread", {}).get("min_profit_eth", "0.005"))
        )

        self._chain_executors: dict[str, SeaportExecutor] = {}
        self._collection_fees: dict[str, dict] = {}
        for col in settings.collections:
            if col.get("active", True):
                self._collection_fees[col["slug"]] = {
                    "royalty_bps": col.get("royalty_bps", 500),
                    "marketplace_fee_bps": col.get("marketplace_fee_bps", 250),
                    "contract": col.get("contract", ""),
                    "chain": col.get("chain", "ethereum"),
                }

        # Cached wallet balances per chain, refreshed periodically
        self._chain_balances: dict[str, float] = {}
        self._balance_ts: float = 0.0

    def _get_seaport(self, chain: str = "ethereum") -> SeaportExecutor:
        if chain not in self._chain_executors:
            self._chain_executors[chain] = SeaportExecutor(chain=chain)
        return self._chain_executors[chain]

    async def _refresh_balances(self):
        """Refresh cached wallet balances (max once per 15s)."""
        now = time.time()
        if now - self._balance_ts < 15:
            return
        chains_needed = {v["chain"] for v in self._collection_fees.values()}
        for chain in chains_needed:
            try:
                seaport = self._get_seaport(chain)
                self._chain_balances[chain] = await seaport.get_wallet_balance(chain)
            except Exception:
                pass
        self._balance_ts = now

    async def start(self, slugs: list[str]):
        """Start the stream sniper for given collections."""
        logger.info("stream_sniper_starting", collections=slugs)

        # Pre-load wallet balances and best bids
        await self._refresh_balances()
        await self._refresh_bids(slugs)

        # Register callbacks
        self.stream.on_listing(self._on_new_listing)
        self.stream.on_bid(self._on_new_bid)
        self.stream.on_sale(self._on_sale)

        # Start bid refresh task + WebSocket listener
        await asyncio.gather(
            self.stream.connect(slugs),
            self._bid_refresh_loop(slugs),
        )

    async def _on_new_listing(self, event: dict):
        """
        CRITICAL PATH — a new listing just appeared on OpenSea.
        This is where speed matters. React in milliseconds.
        """
        slug = event.get("collection_slug", "")
        token_id = event.get("token_id", "")
        listing_price = event.get("price", 0)
        listing_hash = event.get("order_hash", "")
        listing_protocol = event.get("protocol_address", "")
        contract = event.get("contract_address", "")

        if not slug or not token_id or listing_price <= 0:
            return

        # ── Cooldown: skip if this exact order was recently attempted ──
        if listing_hash in _RECENT_ATTEMPTS:
            if time.time() - _RECENT_ATTEMPTS[listing_hash] < COOLDOWN_AFTER_FAIL_S:
                return

        # ── Cooldown: skip if this collection+token was recently attempted ──
        token_key = f"{slug}:{token_id}"
        last_attempt = _TOKEN_COOLDOWN.get(token_key, 0)
        if time.time() - last_attempt < COOLDOWN_AFTER_FAIL_S:
            return

        # ── Skip if this collection is already mid-execution ──
        if slug in _EXECUTING_NOW:
            return

        # Get cached best bid for this collection
        best_bid = _KNOWN_BIDS.get(slug)
        if not best_bid:
            return

        bid_price = best_bid.get("price", 0)
        bid_hash = best_bid.get("order_hash", "")
        bid_protocol = best_bid.get("protocol_address", "")

        if bid_price <= listing_price:
            return  # No spread

        # Calculate profit
        fees = self._collection_fees.get(slug, {})
        chain = fees.get("chain", "ethereum")
        costs = self.cost_engine.calculate(
            buy_price=Decimal(str(listing_price)),
            sell_price=Decimal(str(bid_price)),
            royalty_bps=fees.get("royalty_bps", 500),
            marketplace_fee_bps=fees.get("marketplace_fee_bps", 250),
        )

        net_profit = costs["net_profit"]
        roi = costs["roi"]

        if net_profit < self.min_profit_eth:
            return  # Not profitable enough

        # ── Pre-flight: check cached balance BEFORE executing ──
        await self._refresh_balances()
        balance = self._chain_balances.get(chain, 0.0)
        gas_overhead = 0.015 if chain == "ethereum" else 0.0002
        needed = listing_price + gas_overhead
        if balance < needed:
            logger.debug(
                "sniper_skip_insufficient_balance",
                collection=slug,
                chain=chain,
                balance=round(balance, 4),
                needed=round(needed, 4),
            )
            return

        # ── Pre-flight: check buy price within single-trade limit ──
        if listing_price > self.max_single_trade:
            return

        latency_ms = round((time.time() - event.get("received_at", time.time())) * 1000)

        logger.info(
            "sniper_opportunity",
            collection=slug,
            token_id=token_id,
            buy=listing_price,
            sell=bid_price,
            profit=float(net_profit),
            roi=f"{roi:.1f}%",
            latency_ms=latency_ms,
        )

        # Mark as attempted
        _RECENT_ATTEMPTS[listing_hash] = time.time()
        _TOKEN_COOLDOWN[token_key] = time.time()

        # Execute immediately — no verify step, no delay
        await self._execute_snipe(
            slug=slug,
            token_id=token_id,
            listing_price=listing_price,
            bid_price=bid_price,
            net_profit=float(net_profit),
            roi=roi,
            listing_hash=listing_hash,
            bid_hash=bid_hash,
            contract=contract or fees.get("contract", ""),
            listing_protocol=listing_protocol,
            bid_protocol=bid_protocol,
        )

    async def _on_new_bid(self, event: dict):
        """A new bid appeared — update bid cache only if it's collection-wide."""
        slug = event.get("collection_slug", "")
        price = event.get("price", 0)

        if not slug or price <= 0:
            return

        # Only cache collection-wide bids (not trait-specific)
        criteria = event.get("criteria", {})
        is_collection_wide = (
            criteria.get("trait") is None
            and not criteria.get("traits")
        )
        if not is_collection_wide:
            return

        current = _KNOWN_BIDS.get(slug)
        if not current or price > current.get("price", 0):
            _KNOWN_BIDS[slug] = {
                "price": price,
                "order_hash": event.get("order_hash", ""),
                "protocol_address": event.get("protocol_address", ""),
                "collection_wide": True,
                "updated_at": time.time(),
            }
            logger.debug("sniper_bid_updated", collection=slug, price=price)

    async def _on_sale(self, event: dict):
        """A sale happened — the best bid might be gone, refresh."""
        slug = event.get("collection_slug", "")
        if slug and slug in _KNOWN_BIDS:
            # Invalidate cached bid — force refresh
            _KNOWN_BIDS.pop(slug, None)
            logger.debug("sniper_bid_invalidated_after_sale", collection=slug)

    async def _execute_snipe(self, **kwargs):
        """Execute an atomic buy+sell using the chain-aware SeaportExecutor."""
        token_id = kwargs["token_id"]
        slug = kwargs["slug"]
        fees = self._collection_fees.get(slug, {})
        chain = fees.get("chain", "ethereum")
        seaport = self._get_seaport(chain)
        token_key = f"{slug}:{token_id}"

        _EXECUTING_NOW.add(slug)
        try:
            logger.info(
                "sniper_executing",
                collection=slug,
                chain=chain,
                token_id=token_id,
                buy=kwargs["listing_price"],
                sell=kwargs["bid_price"],
            )

            result = await seaport.atomic_buy_and_sell(
                listing_order_hash=kwargs["listing_hash"],
                bid_order_hash=kwargs["bid_hash"],
                token_id=str(token_id),
                nft_contract=kwargs["contract"],
                listing_protocol=kwargs.get("listing_protocol"),
                bid_protocol=kwargs.get("bid_protocol"),
                chain=chain,
            )

            explorer = "basescan.org" if chain == "base" else "etherscan.io"

            if result["status"] == "executed":
                profit = kwargs["net_profit"]
                logger.info(
                    "sniper_success",
                    collection=slug,
                    chain=chain,
                    token_id=token_id,
                    profit=profit,
                    buy_tx=result.get("buy_tx_hash", "")[:16],
                    sell_tx=result.get("sell_tx_hash", "")[:16],
                )
                # Longer cooldown after success (avoid double-trading)
                _TOKEN_COOLDOWN[token_key] = time.time() + COOLDOWN_AFTER_SUCCESS_S
                # Refresh balance immediately after spending ETH
                self._balance_ts = 0.0
                await self._refresh_balances()

                await self.notifier._send(
                    f"<b>SNIPE SUCCESS</b>\n"
                    f"Chain: {chain}\n"
                    f"Collection: {slug}\n"
                    f"Token: <code>{token_id}</code>\n"
                    f"Buy: {kwargs['listing_price']:.4f} ETH\n"
                    f"Sell: {kwargs['bid_price']:.4f} ETH\n"
                    f"Profit: <b>{profit:.4f} ETH</b>\n"
                    f"ROI: {kwargs['roi']:.1f}%\n"
                    f"Buy TX: <a href='https://{explorer}/tx/{result.get('buy_tx_hash','')}'>view</a>\n"
                    f"Sell TX: <a href='https://{explorer}/tx/{result.get('sell_tx_hash','')}'>view</a>"
                )
            elif result["status"] == "error":
                reason = result.get("reason", "unknown")
                logger.warning(
                    "sniper_failed",
                    collection=slug,
                    chain=chain,
                    token_id=token_id,
                    reason=reason[:100],
                )
                _TOKEN_COOLDOWN[token_key] = time.time()
                if "not found" in reason.lower() or "stale" in reason.lower():
                    _RECENT_ATTEMPTS[kwargs["listing_hash"]] = time.time()
                    _RECENT_ATTEMPTS[kwargs["bid_hash"]] = time.time()
                    if slug in _KNOWN_BIDS:
                        stale_hash = _KNOWN_BIDS[slug].get("order_hash", "")
                        if stale_hash == kwargs["bid_hash"]:
                            _KNOWN_BIDS.pop(slug, None)
                            logger.info("sniper_bid_invalidated_stale", collection=slug)
                if "insufficient" in reason.lower() or "balance" in reason.lower():
                    self._balance_ts = 0.0

        except Exception as e:
            logger.error(
                "sniper_execution_error",
                collection=slug,
                token_id=token_id,
                error=str(e)[:100],
            )
            _TOKEN_COOLDOWN[token_key] = time.time()
        finally:
            _EXECUTING_NOW.discard(slug)

    async def _refresh_bids(self, slugs: list[str]):
        """Load best REALISTIC bids from OpenSea API (filters out trait-specific high bids)."""
        for slug in slugs:
            try:
                offers = await self.opensea.get_collection_offers(slug, limit=50)
                active = offers.get("offers", [])
                if not active:
                    continue

                # Get floor price for realistic bid filtering
                fees = self._collection_fees.get(slug, {})
                chain = fees.get("chain", "ethereum")

                # Parse all bid prices
                parsed = []
                for offer in active:
                    price_obj = offer.get("price", {})
                    try:
                        value = int(price_obj.get("value", "0"))
                        decimals = int(price_obj.get("decimals", 18))
                        price = value / (10 ** decimals)
                    except (ValueError, TypeError):
                        continue
                    if price > 0:
                        criteria = offer.get("criteria", {})
                        is_collection_wide = (
                            criteria.get("trait") is None
                            and not criteria.get("traits")
                            and criteria.get("encoded_token_ids") == "*"
                        )
                        parsed.append({
                            "price": price,
                            "offer": offer,
                            "collection_wide": is_collection_wide,
                        })

                if not parsed:
                    continue

                # Prefer collection-wide bids (fillable by any token)
                collection_bids = [p for p in parsed if p["collection_wide"]]
                candidates = collection_bids if collection_bids else parsed

                best = max(candidates, key=lambda p: p["price"])
                best_price = best["price"]
                best_offer = best["offer"]

                _KNOWN_BIDS[slug] = {
                    "price": best_price,
                    "order_hash": best_offer.get("order_hash", ""),
                    "protocol_address": best_offer.get("protocol_address", ""),
                    "collection_wide": best.get("collection_wide", False),
                    "updated_at": time.time(),
                }
                logger.info(
                    "sniper_bid_loaded",
                    collection=slug,
                    best_bid=round(best_price, 5),
                    collection_wide=best.get("collection_wide"),
                )
            except Exception as e:
                logger.warning("sniper_bid_load_error", collection=slug, error=str(e)[:80])

    async def _bid_refresh_loop(self, slugs: list[str]):
        """Periodically refresh bids, balances, and clean up cooldowns."""
        while True:
            await asyncio.sleep(15)
            try:
                now = time.time()
                # Clean up expired cooldowns
                expired = [k for k, v in _RECENT_ATTEMPTS.items() if now - v > 300]
                for k in expired:
                    del _RECENT_ATTEMPTS[k]
                expired_tokens = [k for k, v in _TOKEN_COOLDOWN.items() if now - v > COOLDOWN_AFTER_SUCCESS_S]
                for k in expired_tokens:
                    del _TOKEN_COOLDOWN[k]

                await self._refresh_balances()
                await self._refresh_bids(slugs)
            except Exception as e:
                logger.debug("sniper_refresh_error", error=str(e)[:80])

    async def stop(self):
        """Stop the stream sniper."""
        await self.stream.disconnect()
        logger.info("stream_sniper_stopped")
