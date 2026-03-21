"""
OpenSea Stream API — real-time WebSocket feed for instant event detection.

Instead of polling every 30 seconds, this connects via WebSocket and reacts
to new listings and bids within ~200ms of them appearing on OpenSea.

This is the SPEED ADVANTAGE: while other bots poll, we listen.

Protocol: Phoenix channels over WebSocket
Endpoint: wss://stream.openseabeta.com/socket/websocket?token={api_key}
"""

import asyncio
import json
import time
from typing import Callable, Awaitable

import structlog

logger = structlog.get_logger()


class OpenSeaStream:
    """
    Real-time WebSocket connection to OpenSea Stream API.
    Receives listing and bid events as they happen — not minutes later.
    """

    WS_URL = "wss://stream.openseabeta.com/socket/websocket"
    HEARTBEAT_INTERVAL = 30  # seconds

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._ws = None
        self._ref = 0
        self._running = False
        self._subscriptions: dict[str, int] = {}  # slug -> ref
        self._on_listing: Callable | None = None
        self._on_bid: Callable | None = None
        self._on_sale: Callable | None = None
        self._reconnect_delay = 1
        self._last_event_time = 0
        self._event_count = 0

    def on_listing(self, callback: Callable[[dict], Awaitable[None]]):
        """Register callback for new listings (someone lists an NFT for sale)."""
        self._on_listing = callback

    def on_bid(self, callback: Callable[[dict], Awaitable[None]]):
        """Register callback for new bids (someone places an offer)."""
        self._on_bid = callback

    def on_sale(self, callback: Callable[[dict], Awaitable[None]]):
        """Register callback for sales (listing was bought)."""
        self._on_sale = callback

    async def connect(self, slugs: list[str]):
        """Connect to WebSocket and subscribe to collections."""
        self._running = True
        while self._running:
            try:
                await self._connect_and_listen(slugs)
            except Exception as e:
                if not self._running:
                    break
                logger.warning(
                    "stream_reconnecting",
                    error=str(e)[:100],
                    delay=self._reconnect_delay,
                )
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._reconnect_delay * 2, 60)

    async def _connect_and_listen(self, slugs: list[str]):
        """Single connection lifecycle."""
        try:
            import websockets
        except ImportError:
            logger.error("websockets_not_installed", hint="pip install websockets")
            raise

        url = f"{self.WS_URL}?token={self.api_key}"
        logger.info("stream_connecting", collections=len(slugs))

        async with websockets.connect(
            url,
            ping_interval=None,  # We handle heartbeats manually
            close_timeout=5,
        ) as ws:
            self._ws = ws
            self._reconnect_delay = 1  # Reset on successful connect
            logger.info("stream_connected")

            # Subscribe to all collections
            for slug in slugs:
                await self._subscribe(ws, slug)

            # Run heartbeat and listener concurrently
            await asyncio.gather(
                self._heartbeat_loop(ws),
                self._listen_loop(ws),
            )

    async def _subscribe(self, ws, slug: str):
        """Subscribe to a collection's events."""
        self._ref += 1
        ref = self._ref
        self._subscriptions[slug] = ref

        msg = {
            "topic": f"collection:{slug}",
            "event": "phx_join",
            "payload": {},
            "ref": ref,
        }
        await ws.send(json.dumps(msg))
        logger.info("stream_subscribed", collection=slug, ref=ref)

    async def _heartbeat_loop(self, ws):
        """Send heartbeat every 30 seconds to keep connection alive."""
        while self._running:
            try:
                self._ref += 1
                msg = {
                    "topic": "phoenix",
                    "event": "heartbeat",
                    "payload": {},
                    "ref": self._ref,
                }
                await ws.send(json.dumps(msg))
                await asyncio.sleep(self.HEARTBEAT_INTERVAL)
            except Exception:
                break

    async def _listen_loop(self, ws):
        """Listen for incoming events and dispatch to callbacks."""
        async for raw_msg in ws:
            try:
                msg = json.loads(raw_msg)
                await self._handle_message(msg)
            except json.JSONDecodeError:
                continue
            except Exception as e:
                logger.error("stream_event_error", error=str(e)[:100])

    async def _handle_message(self, msg: dict):
        """Route incoming messages to the right callback."""
        event = msg.get("event", "")
        topic = msg.get("topic", "")
        payload = msg.get("payload", {})

        # Skip system messages
        if event in ("phx_reply", "phx_close", "heartbeat"):
            return
        if topic == "phoenix":
            return

        # Extract collection slug from topic "collection:slug"
        slug = topic.replace("collection:", "") if ":" in topic else ""

        # Extract the actual event payload
        event_payload = payload.get("payload", payload)
        event_type = event_payload.get("event_type", event)

        self._event_count += 1
        self._last_event_time = time.time()

        # Parse based on event type
        if event_type == "item_listed" and self._on_listing:
            parsed = self._parse_listing_event(event_payload, slug)
            if parsed:
                logger.info(
                    "stream_listing",
                    collection=slug,
                    token_id=parsed.get("token_id"),
                    price=parsed.get("price"),
                )
                try:
                    await self._on_listing(parsed)
                except Exception as e:
                    logger.error("stream_listing_callback_error", error=str(e)[:100])

        elif event_type == "item_received_bid" and self._on_bid:
            parsed = self._parse_bid_event(event_payload, slug)
            if parsed:
                # Only log at debug to reduce noise
                logger.debug(
                    "stream_bid",
                    collection=slug,
                    price=parsed.get("price"),
                )
                try:
                    await self._on_bid(parsed)
                except Exception as e:
                    logger.error("stream_bid_callback_error", error=str(e)[:100])

        elif event_type == "item_sold" and self._on_sale:
            parsed = self._parse_sale_event(event_payload, slug)
            if parsed:
                logger.debug("stream_sale", collection=slug, price=parsed.get("price"))
                try:
                    await self._on_sale(parsed)
                except Exception as e:
                    logger.error("stream_sale_callback_error", error=str(e)[:100])

    def _parse_listing_event(self, payload: dict, slug: str) -> dict | None:
        """Parse a listing event into our standard format."""
        try:
            item = payload.get("item", {})
            nft_id = item.get("nft_id", "")
            # nft_id format: "ethereum/<contract>/<token_id>"
            parts = nft_id.split("/")
            token_id = parts[-1] if len(parts) >= 3 else ""
            contract = parts[-2] if len(parts) >= 3 else ""

            price_data = payload.get("base_price", "0")
            # base_price is in wei (string)
            price_wei = int(price_data) if price_data else 0
            price_eth = price_wei / 1e18

            return {
                "type": "listing",
                "collection_slug": slug,
                "token_id": token_id,
                "contract_address": contract,
                "price": price_eth,
                "order_hash": payload.get("order_hash", ""),
                "protocol_address": payload.get("protocol_address", ""),
                "maker": payload.get("maker", {}).get("address", ""),
                "event_timestamp": payload.get("event_timestamp", ""),
                "received_at": time.time(),
            }
        except Exception as e:
            logger.debug("stream_parse_listing_error", error=str(e))
            return None

    def _parse_bid_event(self, payload: dict, slug: str) -> dict | None:
        """Parse a bid/offer event into our standard format."""
        try:
            item = payload.get("item", {})
            nft_id = item.get("nft_id", "")
            parts = nft_id.split("/")
            token_id = parts[-1] if len(parts) >= 3 else ""
            contract = parts[-2] if len(parts) >= 3 else ""

            price_data = payload.get("base_price", "0")
            price_wei = int(price_data) if price_data else 0
            price_eth = price_wei / 1e18

            return {
                "type": "bid",
                "collection_slug": slug,
                "token_id": token_id,
                "contract_address": contract,
                "price": price_eth,
                "order_hash": payload.get("order_hash", ""),
                "protocol_address": payload.get("protocol_address", ""),
                "maker": payload.get("maker", {}).get("address", ""),
                "event_timestamp": payload.get("event_timestamp", ""),
                "collection_offer": not bool(token_id),
                "received_at": time.time(),
            }
        except Exception as e:
            logger.debug("stream_parse_bid_error", error=str(e))
            return None

    def _parse_sale_event(self, payload: dict, slug: str) -> dict | None:
        """Parse a sale event."""
        try:
            item = payload.get("item", {})
            nft_id = item.get("nft_id", "")
            parts = nft_id.split("/")
            token_id = parts[-1] if len(parts) >= 3 else ""

            price_data = payload.get("sale_price", "0")
            price_wei = int(price_data) if price_data else 0
            price_eth = price_wei / 1e18

            return {
                "type": "sale",
                "collection_slug": slug,
                "token_id": token_id,
                "price": price_eth,
                "received_at": time.time(),
            }
        except Exception as e:
            logger.debug("stream_parse_sale_error", error=str(e))
            return None

    async def disconnect(self):
        """Gracefully disconnect."""
        self._running = False
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass

    @property
    def stats(self) -> dict:
        """Connection stats."""
        return {
            "connected": self._ws is not None and self._running,
            "subscriptions": list(self._subscriptions.keys()),
            "events_received": self._event_count,
            "last_event_age_seconds": (
                round(time.time() - self._last_event_time, 1)
                if self._last_event_time > 0
                else None
            ),
        }
