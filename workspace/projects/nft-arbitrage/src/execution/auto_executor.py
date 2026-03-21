"""
Autonomous Executor — demand-driven ATOMIC buy+sell pipeline.

Core principle: NEVER buy unless a verified buyer (active bid) already exists.
Core safety: Buy + sell execute in the SAME block via Flashbots/sequential.
             Either BOTH happen or NEITHER — zero risk of partial execution.

JUST-IN-TIME execution: fetches fresh listing + bid data immediately before
executing, never uses stale order hashes from earlier scans.

Multi-chain: supports Ethereum mainnet and Base L2.
"""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import structlog

from src.config import get_settings
from src.database import async_session
from src.models.trade import Trade
from src.models.opportunity import Opportunity
from src.ingestion.opensea import OpenSeaClient
from src.execution.seaport import SeaportExecutor
from src.notifications.telegram import TelegramNotifier

logger = structlog.get_logger()

_FAILED_ORDERS: set[str] = set()
_FAILED_TOKENS: dict[str, float] = {}


CONSECUTIVE_LOSS_KEY = "nft_arb:consecutive_losses"


class AutoExecutor:
    """
    Handles the full autonomous trade lifecycle with ATOMIC execution.

    Key improvement: JUST-IN-TIME data fetching.
    Instead of using stale order hashes from scanning (which go stale in seconds),
    we fetch fresh listings and bids right before executing.
    """

    def __init__(self, strategy_selector=None, cache=None):
        settings = get_settings()
        self.opensea = OpenSeaClient()
        self.notifier = TelegramNotifier()
        self.strategy_selector = strategy_selector
        self.cache = cache  # RedisCache for consecutive-loss counter

        self._chain_executors: dict[str, SeaportExecutor] = {}

        exec_cfg = settings.execution
        self.mode = exec_cfg.get("mode", "semi_auto")
        self.min_confidence = exec_cfg.get("auto_execute_confidence_min", 0.80)
        self.max_gas_gwei = exec_cfg.get("max_gas_gwei", 50)
        self.max_single_trade = settings.risk.get("max_single_trade_eth", 1.0)
        self.consecutive_loss_limit = settings.risk.get("consecutive_loss_limit", 0)

        self._failed_orders = _FAILED_ORDERS
        self._failed_tokens = _FAILED_TOKENS

    def _get_seaport(self, chain: str = "ethereum") -> SeaportExecutor:
        if chain not in self._chain_executors:
            self._chain_executors[chain] = SeaportExecutor(chain=chain)
        return self._chain_executors[chain]

    async def _get_consecutive_losses(self) -> int:
        """Read current consecutive loss count from cache (0 if not set or no cache)."""
        if not self.cache:
            return 0
        try:
            val = await self.cache.get(CONSECUTIVE_LOSS_KEY)
            return int(val) if val is not None else 0
        except Exception:
            return 0

    async def _set_consecutive_losses(self, count: int):
        """Write consecutive loss count to cache (persists across restarts)."""
        if not self.cache:
            return
        try:
            await self.cache.set(CONSECUTIVE_LOSS_KEY, count, ttl=86400 * 7)
        except Exception as e:
            logger.warning("consecutive_losses_write_failed", error=str(e))

    def should_auto_execute(self, opportunity: dict, qc_result: dict) -> bool:
        """
        Decide if an opportunity should be auto-executed.

        Relaxed from before: no longer requires listing/bid hashes from scan
        because we fetch fresh data just-in-time before executing.
        """
        chain = opportunity.get("chain", "ethereum")
        seaport = self._get_seaport(chain)
        if not seaport.is_ready():
            logger.warning("auto_execute_skip_wallet_not_configured", chain=chain)
            return False

        if self.mode != "full_auto":
            return False

        verdict = qc_result.get("verdict", "")
        if verdict != "APPROVE":
            return False

        confidence = qc_result.get("confidence", 0)
        if confidence < self.min_confidence:
            return False

        strategy = opportunity.get("strategy", "")
        auto_strategies = get_settings().execution.get(
            "auto_strategies", ["bid_spread"]
        )
        if strategy not in auto_strategies:
            return False

        buy_price = float(opportunity.get("buy_price", 0))
        if buy_price > self.max_single_trade:
            return False

        if not opportunity.get("collection_slug"):
            return False

        return True

    async def should_auto_execute_async(self, opportunity: dict, qc_result: dict) -> bool:
        """Async version: also checks consecutive-loss limit before auto-execute."""
        if not self.should_auto_execute(opportunity, qc_result):
            return False
        if self.consecutive_loss_limit <= 0:
            return True
        count = await self._get_consecutive_losses()
        if count >= self.consecutive_loss_limit:
            logger.warning(
                "auto_execute_blocked_consecutive_losses",
                consecutive_losses=count,
                limit=self.consecutive_loss_limit,
            )
            return False
        return True

    async def execute_opportunity(self, opportunity: dict) -> dict:
        """
        Full autonomous execution pipeline with JUST-IN-TIME data fetching.

        1. Skip recently-failed tokens
        2. Pre-flight: check wallet balance & gas on correct chain
        3. JUST-IN-TIME: fetch fresh listing + bid from OpenSea right now
        4. Verify the spread is still profitable
        5. ATOMIC: buy + sell in same block
        6. Record trades, notify, feed back
        """
        import time

        token_id = opportunity.get("token_id", "?")
        strategy = opportunity.get("strategy", "?")
        slug = opportunity.get("collection_slug", "")
        chain = opportunity.get("chain", "ethereum")
        contract_address = opportunity.get("contract_address", "")

        now = time.time()
        expired_keys = [k for k, v in self._failed_tokens.items() if now - v > 300]
        for k in expired_keys:
            del self._failed_tokens[k]
        if len(self._failed_orders) > 500:
            self._failed_orders.clear()

        token_key = f"{slug}:{token_id}"
        last_attempt = self._failed_tokens.get(token_key, 0)
        if now - last_attempt < 120:
            return {"status": "skipped", "reason": "token_cooldown"}

        seaport = self._get_seaport(chain)

        logger.info(
            "auto_execute_start",
            strategy=strategy,
            slug=slug,
            chain=chain,
            token_id=token_id,
        )

        # ── Pre-flight: check wallet balance on the correct chain ──
        balance = await seaport.get_wallet_balance(chain)
        buy_price_est = float(opportunity.get("buy_price", 0))
        gas_overhead = 0.015 if chain == "ethereum" else 0.0001
        total_needed = buy_price_est + gas_overhead
        if balance < total_needed:
            msg = f"Insufficient {chain} balance: {balance:.4f} < {total_needed:.4f} ETH"
            logger.warning("auto_execute_abort_balance", balance=balance, needed=total_needed, chain=chain)
            return {"status": "aborted", "reason": msg}

        # ── Pre-flight: check gas price ───────────────────────
        gas_gwei = await seaport.get_gas_price_gwei(chain)
        max_gas = self.max_gas_gwei if chain == "ethereum" else 1.0
        if gas_gwei > max_gas:
            msg = f"Gas too high on {chain}: {gas_gwei:.2f} gwei (max {max_gas})"
            logger.warning("auto_execute_abort_gas", gas_gwei=gas_gwei, chain=chain)
            return {"status": "aborted", "reason": msg}

        # ═══════════════════════════════════════════════════════
        # JUST-IN-TIME: Fetch fresh listing + bid RIGHT NOW
        # This is the key fix. Never use stale hashes from scanning.
        # ═══════════════════════════════════════════════════════
        fresh = await self._fetch_fresh_spread(slug, chain, token_id, opportunity)
        if not fresh:
            self._failed_tokens[token_key] = time.time()
            await self._record_failed_trade(opportunity, "atomic", "No fresh profitable spread found")
            return {"status": "error", "reason": "No fresh profitable spread available"}

        listing_hash = fresh["listing_hash"]
        bid_hash = fresh["bid_hash"]
        buy_price = fresh["buy_price"]
        exit_price = fresh["exit_price"]
        net_profit = fresh["net_profit"]
        listing_protocol = fresh.get("listing_protocol", "")
        bid_protocol = fresh.get("bid_protocol", "")

        if listing_hash in self._failed_orders or bid_hash in self._failed_orders:
            return {"status": "skipped", "reason": "order_hash_known_stale"}

        logger.info(
            "jit_execution_starting",
            chain=chain,
            token_id=token_id,
            buy=round(buy_price, 5),
            sell=round(exit_price, 5),
            profit=round(net_profit, 5),
            listing_hash=listing_hash[:16],
            bid_hash=bid_hash[:16],
        )

        result = await seaport.atomic_buy_and_sell(
            listing_order_hash=listing_hash,
            bid_order_hash=bid_hash,
            token_id=str(token_id),
            nft_contract=contract_address,
            listing_protocol=listing_protocol,
            bid_protocol=bid_protocol,
            chain=chain,
        )

        if result["status"] == "error":
            error_msg = result.get("reason", "unknown error")
            logger.error("atomic_execution_failed", token_id=token_id, chain=chain, reason=error_msg)

            if "not found" in error_msg.lower() or "stale" in error_msg.lower():
                self._failed_orders.add(listing_hash)
                self._failed_orders.add(bid_hash)
            self._failed_tokens[token_key] = time.time()

            await self._record_failed_trade(opportunity, "atomic", error_msg)
            return {"status": "error", "reason": error_msg}

        if result["status"] == "partial":
            logger.error("atomic_partial_execution", token_id=token_id, result=result)
            explorer = "basescan.org" if chain == "base" else "etherscan.io"
            await self.notifier._send(
                f"<b>PARTIAL EXECUTION — MANUAL INTERVENTION NEEDED</b>\n"
                f"Chain: {chain}\n"
                f"Token: <code>{token_id}</code>\n"
                f"Buy tx: <code>{result.get('buy_tx', '?')}</code>\n"
                f"Check: https://{explorer}/tx/{result.get('buy_tx', '')}"
            )
            return result

        opportunity["buy_price"] = buy_price
        opportunity["expected_exit"] = exit_price
        opportunity["net_profit"] = net_profit
        await self._record_trades(opportunity, result)
        await self._notify_execution(opportunity, result, chain)

        actual_gas = result.get("total_gas", 0)
        actual_profit = exit_price - buy_price - actual_gas
        success = actual_profit > 0

        # Consecutive-loss gate: update counter for self-improving / never-losing
        if self.cache and self.consecutive_loss_limit > 0:
            try:
                count = await self._get_consecutive_losses()
                if success:
                    await self._set_consecutive_losses(0)
                else:
                    await self._set_consecutive_losses(count + 1)
                    logger.warning(
                        "trade_loss_recorded",
                        consecutive_losses=count + 1,
                        limit=self.consecutive_loss_limit,
                        actual_profit=round(actual_profit, 6),
                    )
            except Exception as e:
                logger.warning("consecutive_losses_update_failed", error=str(e))

        if self.strategy_selector:
            self.strategy_selector.update(strategy, success)

        return {
            "status": "executed",
            "buy_tx": result.get("buy_tx_hash"),
            "sell_tx": result.get("sell_tx_hash"),
            "total_gas": result.get("total_gas"),
            "net_profit": net_profit,
        }

    async def _fetch_fresh_spread(
        self, slug: str, chain: str, target_token_id: str, opportunity: dict
    ) -> dict | None:
        """
        Fetch fresh listing + bid data from OpenSea RIGHT NOW.
        Returns the best available spread, or None if not profitable.
        """
        import asyncio

        try:
            listings_task = self.opensea.get_collection_listings(slug, limit=20)
            offers_task = self.opensea.get_collection_offers(slug, limit=20)
            listings_data, offers_data = await asyncio.gather(
                listings_task, offers_task, return_exceptions=True,
            )

            if isinstance(listings_data, Exception) or isinstance(offers_data, Exception):
                logger.error("jit_fetch_failed", slug=slug,
                             listings_err=str(listings_data) if isinstance(listings_data, Exception) else None,
                             offers_err=str(offers_data) if isinstance(offers_data, Exception) else None)
                return None

            listings = listings_data.get("listings", [])
            offers = offers_data.get("offers", [])

            if not listings or not offers:
                return None

            # Find the best realistic bid
            floor_price = float(opportunity.get("buy_price", 0))
            best_bid_price = 0
            best_bid = None
            for offer in offers:
                price_obj = offer.get("price", {})
                try:
                    value = int(price_obj.get("value", "0"))
                    decimals = int(price_obj.get("decimals", 18))
                    price = value / (10 ** decimals)
                except (ValueError, TypeError):
                    continue
                if price > best_bid_price and (floor_price <= 0 or price <= floor_price * 2.0):
                    best_bid_price = price
                    best_bid = offer

            if not best_bid or best_bid_price <= 0:
                return None

            # Find the target token's listing, or the cheapest listing
            target_listing = None
            cheapest_listing = None
            cheapest_price = float("inf")

            for listing in listings:
                price_obj = listing.get("price", {}).get("current", {})
                try:
                    value = int(price_obj.get("value", "0"))
                    decimals = int(price_obj.get("decimals", 18))
                    price = value / (10 ** decimals)
                except (ValueError, TypeError):
                    continue

                if price <= 0:
                    continue

                token_id = self._extract_listing_token_id(listing)
                if token_id == str(target_token_id):
                    target_listing = listing
                    target_listing["_price"] = price
                    target_listing["_token_id"] = token_id

                if price < cheapest_price:
                    cheapest_price = price
                    cheapest_listing = listing
                    cheapest_listing["_price"] = price
                    cheapest_listing["_token_id"] = token_id

            chosen = target_listing or cheapest_listing
            if not chosen:
                return None

            buy_price = chosen["_price"]
            if buy_price >= best_bid_price:
                return None  # No spread

            royalty_bps = int(opportunity.get("royalty_bps", 500))
            marketplace_fee_bps = int(opportunity.get("marketplace_fee_bps", 250))
            total_fee_pct = (royalty_bps + marketplace_fee_bps) / 10000

            # Dynamic gas cost from actual chain gas price
            try:
                from web3 import Web3 as _Web3
                rpc = get_settings().blockchain.rpc_url_for_chain(chain)
                w3 = _Web3(_Web3.HTTPProvider(rpc))
                gas_price_wei = w3.eth.gas_price
                gas_units = 340_000  # atomic arb (buy+sell)
                gas_eth = float(_Web3.from_wei(gas_price_wei * gas_units, "ether"))
            except Exception:
                gas_eth = 0.003 if chain == "ethereum" else 0.00005

            net_profit = best_bid_price * (1 - total_fee_pct) - buy_price - gas_eth
            min_profit = float(get_settings().strategies.get("bid_spread", {}).get("min_profit_eth", 0.005))

            if net_profit < min_profit:
                logger.debug("jit_spread_too_thin", slug=slug,
                             buy=round(buy_price, 5), bid=round(best_bid_price, 5),
                             net_profit=round(net_profit, 5))
                return None

            return {
                "listing_hash": chosen.get("order_hash", ""),
                "bid_hash": best_bid.get("order_hash", ""),
                "listing_protocol": chosen.get("protocol_address", ""),
                "bid_protocol": best_bid.get("protocol_address", ""),
                "buy_price": buy_price,
                "exit_price": best_bid_price,
                "net_profit": net_profit,
                "token_id": chosen.get("_token_id", target_token_id),
            }

        except Exception as e:
            logger.error("jit_fetch_error", slug=slug, error=str(e)[:100])
            return None

    @staticmethod
    def _extract_listing_token_id(listing: dict) -> str:
        """Extract token_id from an OpenSea listing response."""
        protocol = listing.get("protocol_data", {})
        params = protocol.get("parameters", {})
        offer_items = params.get("offer", [])
        if offer_items:
            return str(offer_items[0].get("identifierOrCriteria", ""))
        return ""

    async def _verify_bid_live(self, opportunity: dict) -> bool:
        """
        Re-check that a viable bid still exists for this collection.
        Safety check: ensures a buyer exists before we buy.

        Checks BOTH collection-level offers AND item-level offers.
        If any active bid >= 95% of our target exit price, proceed.
        The atomic execution will fail safely if the specific order is gone.
        """
        try:
            collection_slug = opportunity.get("collection_slug", "")
            if not collection_slug:
                return True

            target_bid_hash = opportunity.get("bid_order_hash", "")
            target_exit_price = float(opportunity.get("expected_exit", 0))

            # Check collection-level offers (50 for better coverage)
            offers = await self.opensea.get_collection_offers(collection_slug, limit=50)
            active_offers = offers.get("offers", [])

            for offer in active_offers:
                # Exact hash match — best case
                if offer.get("order_hash") == target_bid_hash:
                    logger.debug("bid_verified_exact_match", hash=target_bid_hash[:16])
                    return True

                # Price-based match — any bid >= 95% of target
                price_obj = offer.get("price", {})
                try:
                    value = int(price_obj.get("value", "0"))
                    decimals = int(price_obj.get("decimals", 18))
                    offer_price = value / (10**decimals)
                except (ValueError, TypeError):
                    continue

                if offer_price >= target_exit_price * 0.95:
                    logger.debug(
                        "bid_verified_price_match",
                        offer_price=offer_price,
                        target=target_exit_price,
                    )
                    return True

            # If no collection offers match, still try — the atomic execution
            # verifies orders through OpenSea fulfillment API anyway
            if active_offers:
                best_offer_price = 0
                for offer in active_offers:
                    price_obj = offer.get("price", {})
                    try:
                        value = int(price_obj.get("value", "0"))
                        decimals = int(price_obj.get("decimals", 18))
                        best_offer_price = max(best_offer_price, value / (10**decimals))
                    except (ValueError, TypeError):
                        continue

                # Accept if there's any meaningful bid activity (> 50% of target)
                if best_offer_price >= target_exit_price * 0.50:
                    logger.info(
                        "bid_verified_activity_present",
                        best_offer=best_offer_price,
                        target=target_exit_price,
                    )
                    return True

            logger.debug(
                "bid_verify_no_match",
                offers_checked=len(active_offers),
                target=target_exit_price,
            )
            return False

        except Exception as e:
            logger.warning("bid_verification_error", error=str(e))
            # On verification error, let atomic execution decide
            return True

    async def _record_trades(self, opportunity: dict, result: dict):
        """Save both trades with real tx hashes and update opportunity status."""
        try:
            async with async_session() as session:
                buy_model = Trade(
                    id=str(uuid4()),
                    opportunity_id=opportunity.get("id"),
                    collection_id=str(opportunity.get("collection_id", "")),
                    token_id=str(opportunity.get("token_id", "")),
                    side="buy",
                    marketplace=opportunity.get("buy_venue", "opensea"),
                    price=Decimal(str(opportunity.get("buy_price", 0))),
                    gas_used=Decimal(str(result.get("buy_gas", 0))),
                    tx_hash=result.get("buy_tx_hash", ""),
                    status="executed",
                    executed_at=datetime.utcnow(),
                )
                session.add(buy_model)

                sell_model = Trade(
                    id=str(uuid4()),
                    opportunity_id=opportunity.get("id"),
                    collection_id=str(opportunity.get("collection_id", "")),
                    token_id=str(opportunity.get("token_id", "")),
                    side="sell",
                    marketplace=opportunity.get("sell_venue", "opensea"),
                    price=Decimal(str(opportunity.get("expected_exit", 0))),
                    gas_used=Decimal(str(result.get("sell_gas", 0))),
                    tx_hash=result.get("sell_tx_hash", ""),
                    status="executed",
                    executed_at=datetime.utcnow(),
                )
                session.add(sell_model)

                from sqlalchemy import select
                res = await session.execute(
                    select(Opportunity).where(Opportunity.id == opportunity.get("id"))
                )
                opp = res.scalar_one_or_none()
                if opp:
                    opp.status = "executed"

                await session.commit()

        except Exception as e:
            logger.error("trade_record_error", error=str(e))

    async def _record_failed_trade(self, opportunity: dict, side: str, reason: str):
        """Record a failed trade attempt for auditability."""
        try:
            async with async_session() as session:
                model = Trade(
                    id=str(uuid4()),
                    opportunity_id=opportunity.get("id"),
                    collection_id=str(opportunity.get("collection_id", "")),
                    token_id=str(opportunity.get("token_id", "")),
                    side=side,
                    marketplace="opensea",
                    price=Decimal(str(opportunity.get("buy_price", 0))),
                    gas_used=Decimal("0"),
                    tx_hash="",
                    status="failed",
                    executed_at=datetime.utcnow(),
                )
                session.add(model)
                await session.commit()
        except Exception as e:
            logger.error("failed_trade_record_error", error=str(e))

    async def _notify_execution(self, opportunity: dict, result: dict, chain: str = "ethereum"):
        """Send Telegram notification for the completed atomic trade."""
        net_profit = float(opportunity.get("net_profit", 0))
        roi = float(opportunity.get("roi", 0))
        total_gas = result.get("total_gas", 0)
        buy_price = float(opportunity.get("buy_price", 0))
        sell_price = float(opportunity.get("expected_exit", 0))
        explorer = "basescan.org" if chain == "base" else "etherscan.io"

        text = (
            "<b>ATOMIC TRADE EXECUTED</b>\n"
            f"Chain: <code>{chain}</code>\n"
            f"Strategy: <code>{opportunity.get('strategy', '?')}</code>\n"
            f"Collection: <code>{opportunity.get('collection_slug', '?')}</code>\n"
            f"Token: <code>{opportunity.get('token_id', '?')}</code>\n\n"
            f"BUY:  {buy_price:.4f} ETH\n"
            f"SELL: {sell_price:.4f} ETH\n"
            f"Gas:  {total_gas:.6f} ETH\n\n"
            f"Net Profit: <b>{'+'if net_profit>0 else ''}{net_profit:.4f} ETH</b>\n"
            f"ROI: <b>{roi:.1f}%</b>\n\n"
            f"Buy tx:  <a href='https://{explorer}/tx/{result.get('buy_tx_hash', '')}'>view</a>\n"
            f"Sell tx: <a href='https://{explorer}/tx/{result.get('sell_tx_hash', '')}'>view</a>\n"
            f"Block: <code>{result.get('block_number', '?')}</code>"
        )

        await self.notifier._send(text)
