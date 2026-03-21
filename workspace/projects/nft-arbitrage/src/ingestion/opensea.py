"""
OpenSea API Client — primary marketplace data source.
Replaces Reservoir (sunset Oct 2025).
Provides listings, bids/offers, collection stats, and sales data.
Free tier: 3 API keys per account.

Endpoints used:
  - GET /api/v2/orders/{chain}/seaport/listings   (item listings)
  - GET /api/v2/listings/collection/{slug}/all     (all collection listings)
  - GET /api/v2/offers/collection/{slug}           (collection offers/bids)
  - GET /api/v2/collections/{slug}/stats           (floor price, volume, etc.)
  - GET /api/v2/events/collection/{slug}           (sales activity)
  - GET /api/v2/collection/{slug}                  (collection metadata)
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import get_settings

logger = structlog.get_logger()

WEI_PER_ETH = 10**18


class OpenSeaClient:
    """
    Async client for OpenSea API v2.
    Handles rate limiting, retries, and pagination.
    """

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.marketplace.opensea_api_key
        self.base_url = "https://api.opensea.io"
        self.chain = "ethereum"

        self.headers = {
            "accept": "application/json",
            "x-api-key": self.api_key,
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=30.0,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _get(self, endpoint: str, params: dict = None) -> dict:
        """Make a GET request with retry logic."""
        async with self._client() as client:
            response = await client.get(endpoint, params=params or {})
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 5))
                logger.warning("opensea_rate_limit", retry_after=retry_after)
                await asyncio.sleep(retry_after)
                response = await client.get(endpoint, params=params or {})
            response.raise_for_status()
            return response.json()

    # ── Listings ──────────────────────────────────────────────

    async def get_collection_listings(
        self,
        collection_slug: str,
        limit: int = 50,
        cursor: str = None,
    ) -> dict:
        """
        Get all active listings for a collection.
        Returns listing orders sorted by price ascending.
        """
        params = {"limit": min(limit, 200)}
        if cursor:
            params["next"] = cursor

        result = await self._get(
            f"/api/v2/listings/collection/{collection_slug}/all",
            params,
        )

        logger.debug(
            "opensea_listings",
            collection=collection_slug,
            count=len(result.get("listings", [])),
        )

        return result

    async def get_item_listings(
        self,
        contract_address: str,
        token_ids: list[str] = None,
        order_by: str = "price",
        order_direction: str = "asc",
        limit: int = 50,
        cursor: str = None,
    ) -> dict:
        """
        Get listings for specific items via the orders endpoint.
        """
        params = {
            "asset_contract_address": contract_address,
            "order_by": order_by,
            "order_direction": order_direction,
            "limit": min(limit, 200),
        }
        if token_ids:
            params["token_ids"] = token_ids
        if cursor:
            params["cursor"] = cursor

        result = await self._get(
            f"/api/v2/orders/{self.chain}/seaport/listings",
            params,
        )

        logger.debug(
            "opensea_item_listings",
            contract=contract_address,
            count=len(result.get("orders", [])),
        )

        return result

    # ── Offers / Bids ─────────────────────────────────────────

    async def get_collection_offers(
        self,
        collection_slug: str,
        limit: int = 50,
        cursor: str = None,
    ) -> dict:
        """
        Get collection-level offers (bids).
        Returns offers sorted by price descending (best bids first).
        """
        params = {"limit": min(limit, 200)}
        if cursor:
            params["next"] = cursor

        result = await self._get(
            f"/api/v2/offers/collection/{collection_slug}",
            params,
        )

        logger.debug(
            "opensea_offers",
            collection=collection_slug,
            count=len(result.get("offers", [])),
        )

        return result

    async def get_item_offers(
        self,
        contract_address: str,
        token_ids: list[str] = None,
        order_by: str = "price",
        order_direction: str = "desc",
        limit: int = 50,
        cursor: str = None,
    ) -> dict:
        """
        Get offers for specific items.
        """
        params = {
            "asset_contract_address": contract_address,
            "order_by": order_by,
            "order_direction": order_direction,
            "limit": min(limit, 200),
        }
        if token_ids:
            params["token_ids"] = token_ids
        if cursor:
            params["cursor"] = cursor

        result = await self._get(
            f"/api/v2/orders/{self.chain}/seaport/offers",
            params,
        )

        return result

    # ── Collection Stats ──────────────────────────────────────

    async def get_collection_stats(self, collection_slug: str) -> dict:
        """
        Get collection statistics: floor price, volume, sales, etc.
        """
        result = await self._get(
            f"/api/v2/collections/{collection_slug}/stats",
        )

        logger.debug(
            "opensea_stats",
            collection=collection_slug,
            floor=result.get("total", {}).get("floor_price"),
        )

        return result

    # ── Collection Metadata ───────────────────────────────────

    async def get_collection(self, collection_slug: str) -> dict:
        """Get collection metadata (name, description, contracts)."""
        result = await self._get(
            f"/api/v2/collections/{collection_slug}",
        )
        return result

    # ── Events / Sales ────────────────────────────────────────

    async def get_collection_events(
        self,
        collection_slug: str,
        event_type: str = "sale",
        limit: int = 50,
        cursor: str = None,
        after: str = None,
        before: str = None,
    ) -> dict:
        """
        Get collection events (sales, transfers, etc.).
        event_type: sale, transfer, cancel, redemption
        """
        params = {
            "event_type": event_type,
            "limit": min(limit, 200),
        }
        if cursor:
            params["next"] = cursor
        if after:
            params["after"] = after
        if before:
            params["before"] = before

        result = await self._get(
            f"/api/v2/events/collection/{collection_slug}",
            params,
        )

        return result

    # ── Batch Fetch ────────────────────────────────────────────

    async def fetch_all_collection_data(
        self,
        collection_slug: str,
        contract_address: str = None,
    ) -> dict:
        """
        Fetch all data needed for opportunity scanning in one batch.
        Returns listings, bids, sales, and collection stats.
        """
        now = datetime.utcnow()
        seven_days_ago = (now - timedelta(days=7)).isoformat() + "Z"
        one_day_ago = (now - timedelta(days=1)).isoformat() + "Z"

        # Fetch everything concurrently
        results = await asyncio.gather(
            self.get_collection_listings(collection_slug, limit=50),
            self.get_collection_offers(collection_slug, limit=50),
            self.get_collection_stats(collection_slug),
            self.get_collection_events(collection_slug, event_type="sale", limit=50, after=seven_days_ago),
            self.get_collection_events(collection_slug, event_type="sale", limit=50, after=one_day_ago),
            return_exceptions=True,
        )

        def safe_result(r, key):
            if isinstance(r, Exception):
                logger.error("opensea_fetch_error", error=str(r))
                return [] if key != "stats" else {}
            if key == "stats":
                return r if isinstance(r, dict) else {}
            return r.get(key, []) if isinstance(r, dict) else []

        data = {
            "listings": safe_result(results[0], "listings"),
            "bids": safe_result(results[1], "offers"),
            "stats": safe_result(results[2], "stats"),
            "sales_7d": safe_result(results[3], "asset_events"),
            "sales_24h": safe_result(results[4], "asset_events"),
        }

        logger.info(
            "opensea_collection_data_fetched",
            collection=collection_slug,
            listings=len(data["listings"]),
            bids=len(data["bids"]),
            sales_7d=len(data["sales_7d"]),
        )

        return data

    # ── Price Helpers ──────────────────────────────────────────

    @staticmethod
    def wei_to_eth(wei_str: str) -> float:
        """Convert a wei string to ETH float."""
        try:
            return int(wei_str) / WEI_PER_ETH
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def parse_offer_price(price_obj: dict) -> float:
        """
        Parse an OpenSea offer price object.
        Format: {"currency": "WETH", "decimals": 18, "value": "1000000000000000000"}
        """
        try:
            value = int(price_obj.get("value", "0"))
            decimals = int(price_obj.get("decimals", 18))
            return value / (10**decimals)
        except (ValueError, TypeError):
            return 0.0
