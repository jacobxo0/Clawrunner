"""
Moralis API Client — supplementary data source for NFT trades,
collection stats, floor price history, and cross-chain data.
Free tier: 40,000 Compute Units (CUs) per day.

Uses direct HTTP calls (no SDK dependency) for async compatibility.

Endpoints used:
  - GET /nft/{address}/trades          (NFT trades by contract)
  - GET /nft/{address}/stats           (collection stats)
  - GET /nft/{address}/lowestprice     (lowest price / floor)
  - GET /nft/{address}/owners          (ownership data)
  - GET /nft/{address}                 (NFTs in collection)
  - GET /nft/{address}/transfers       (transfer history)
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import get_settings

logger = structlog.get_logger()


class MoralisClient:
    """
    Async client for Moralis Web3 Data API.
    Supplements OpenSea with historical trades, floor data, and analytics.
    """

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.marketplace.moralis_api_key
        self.base_url = "https://deep-index.moralis.io/api/v2.2"
        self.chain = "eth"

        self.headers = {
            "accept": "application/json",
            "X-API-Key": self.api_key,
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
                logger.warning("moralis_rate_limit")
                await asyncio.sleep(2)
                response = await client.get(endpoint, params=params or {})
            response.raise_for_status()
            return response.json()

    # ── NFT Trades ────────────────────────────────────────────

    async def get_nft_trades(
        self,
        contract_address: str,
        from_date: str = None,
        to_date: str = None,
        marketplace: str = None,
        limit: int = 100,
        cursor: str = None,
    ) -> dict:
        """
        Get NFT trades for a contract.
        Supports filtering by marketplace (opensea, blur, looksrare, etc.).
        """
        params = {
            "chain": self.chain,
            "limit": min(limit, 100),
        }
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        if marketplace:
            params["marketplace"] = marketplace
        if cursor:
            params["cursor"] = cursor

        result = await self._get(f"/nft/{contract_address}/trades", params)

        logger.debug(
            "moralis_trades",
            contract=contract_address,
            count=len(result.get("result", [])),
        )

        return result

    # ── Collection Stats ──────────────────────────────────────

    async def get_collection_stats(self, contract_address: str) -> dict:
        """
        Get collection-level stats: total tokens, owners, transfers.
        """
        params = {"chain": self.chain}
        result = await self._get(f"/nft/{contract_address}/stats", params)
        return result

    # ── Floor Price ───────────────────────────────────────────

    async def get_lowest_price(
        self,
        contract_address: str,
        marketplace: str = None,
        days: int = None,
    ) -> dict:
        """Get the lowest trade price for a collection."""
        params = {"chain": self.chain}
        if marketplace:
            params["marketplace"] = marketplace
        if days:
            params["days"] = days

        result = await self._get(f"/nft/{contract_address}/lowestprice", params)
        return result

    # ── Owners ────────────────────────────────────────────────

    async def get_nft_owners(
        self,
        contract_address: str,
        limit: int = 100,
        cursor: str = None,
    ) -> dict:
        """Get NFT owners for a contract. Useful for ownership concentration analysis."""
        params = {
            "chain": self.chain,
            "limit": min(limit, 100),
        }
        if cursor:
            params["cursor"] = cursor

        result = await self._get(f"/nft/{contract_address}/owners", params)
        return result

    # ── Transfers ─────────────────────────────────────────────

    async def get_nft_transfers(
        self,
        contract_address: str,
        from_date: str = None,
        to_date: str = None,
        limit: int = 100,
        cursor: str = None,
    ) -> dict:
        """Get transfer history. Useful for wash trading detection."""
        params = {
            "chain": self.chain,
            "limit": min(limit, 100),
        }
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        if cursor:
            params["cursor"] = cursor

        result = await self._get(f"/nft/{contract_address}/transfers", params)
        return result

    # ── NFT Collection Items ──────────────────────────────────

    async def get_collection_nfts(
        self,
        contract_address: str,
        limit: int = 100,
        cursor: str = None,
        normalize_metadata: bool = True,
    ) -> dict:
        """Get NFTs in a collection with metadata."""
        params = {
            "chain": self.chain,
            "limit": min(limit, 100),
            "normalizeMetadata": normalize_metadata,
        }
        if cursor:
            params["cursor"] = cursor

        result = await self._get(f"/nft/{contract_address}", params)
        return result

    # ── Batch Fetch for Analytics ─────────────────────────────

    async def fetch_collection_analytics(
        self,
        contract_address: str,
    ) -> dict:
        """
        Fetch analytics data for a collection: trades, ownership, transfers.
        Used by the risk worker for wash detection and trend analysis.
        """
        now = datetime.utcnow()
        seven_days_ago = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        one_day_ago = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

        results = await asyncio.gather(
            self.get_nft_trades(contract_address, from_date=seven_days_ago, limit=100),
            self.get_nft_trades(contract_address, from_date=one_day_ago, limit=100),
            self.get_collection_stats(contract_address),
            self.get_nft_owners(contract_address, limit=100),
            self.get_nft_transfers(contract_address, from_date=seven_days_ago, limit=100),
            return_exceptions=True,
        )

        def safe(r, key="result"):
            if isinstance(r, Exception):
                logger.error("moralis_fetch_error", error=str(r))
                return [] if key == "result" else {}
            if key == "result":
                return r.get("result", []) if isinstance(r, dict) else []
            return r if isinstance(r, dict) else {}

        data = {
            "trades_7d": safe(results[0], "result"),
            "trades_24h": safe(results[1], "result"),
            "collection_stats": safe(results[2], "full"),
            "owners": safe(results[3], "result"),
            "transfers_7d": safe(results[4], "result"),
        }

        logger.info(
            "moralis_analytics_fetched",
            contract=contract_address,
            trades_7d=len(data["trades_7d"]),
            trades_24h=len(data["trades_24h"]),
            owners=len(data["owners"]),
        )

        return data
