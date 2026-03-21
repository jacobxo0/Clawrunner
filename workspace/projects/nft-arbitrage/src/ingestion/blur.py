"""
Blur API Client — second major marketplace data source.

Blur dominates ~60-70% of NFT trading volume. Without Blur data,
we're blind to the majority of the market.

Key insight for arbitrage:
  - Blur bids are often HIGHER than OpenSea bids (Blur bidders are more aggressive)
  - Blur listings are often LOWER than OpenSea listings (Blur is a trader marketplace)
  - This creates cross-marketplace spreads: buy cheap on Blur, sell high on OpenSea (or vice versa)

Endpoints:
  - GET /v1/collections/{slug}                 (collection info + floor)
  - GET /v1/collections/{slug}/prices          (price levels)
  - GET /v1/collections/{slug}/executable-bids (active bid pool)
  - POST /v1/auth/challenge + /v1/auth/login   (wallet-signed auth)

Auth: Blur requires wallet signature for full API access.
Fallback: Public price endpoints work without auth for basic data.
"""

import asyncio
import time
from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import get_settings

logger = structlog.get_logger()


class BlurClient:
    """
    Async client for Blur marketplace API.
    Provides bid pool data, listings, and floor prices.

    Blur's bid pool is the #1 source of exit liquidity for NFT arbitrage.
    Their bid pools are aggregated and often deeper than OpenSea's.
    """

    BASE_URL = "https://core-api.prod.blur.io"

    def __init__(self):
        settings = get_settings()
        self.private_key = settings.blockchain.eth_private_key
        self._auth_token: str | None = None
        self._auth_expires: float = 0
        self._headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0",
        }

    def _client(self) -> httpx.AsyncClient:
        headers = {**self._headers}
        if self._auth_token:
            headers["authToken"] = self._auth_token
        return httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=headers,
            timeout=20.0,
        )

    # ── Authentication ─────────────────────────────────────────

    async def authenticate(self) -> bool:
        """
        Authenticate with Blur via wallet signature.
        Required for executable-bids and order submission.
        """
        if self._auth_token and time.time() < self._auth_expires:
            return True

        if not self.private_key:
            logger.warning("blur_auth_skipped_no_private_key")
            return False

        try:
            from eth_account import Account
            from eth_account.messages import encode_defunct

            account = Account.from_key(self.private_key)
            wallet = account.address

            async with httpx.AsyncClient(timeout=15) as client:
                # Step 1: Get challenge
                resp = await client.post(
                    f"{self.BASE_URL}/auth/challenge",
                    json={"walletAddress": wallet},
                )
                if resp.status_code != 200:
                    logger.warning("blur_challenge_failed", status=resp.status_code)
                    return False

                data = resp.json()
                message = data.get("message", "")
                if not message:
                    logger.warning("blur_challenge_no_message")
                    return False

                # Step 2: Sign the challenge
                signable = encode_defunct(text=message)
                signed = account.sign_message(signable)

                # Step 3: Login with signature
                resp = await client.post(
                    f"{self.BASE_URL}/auth/login",
                    json={
                        "message": message,
                        "walletAddress": wallet,
                        "expiresOn": data.get("expiresOn", ""),
                        "hmac": data.get("hmac", ""),
                        "signature": signed.signature.hex(),
                    },
                )

                if resp.status_code == 200:
                    login_data = resp.json()
                    self._auth_token = login_data.get("accessToken", "")
                    self._auth_expires = time.time() + 3500  # ~1 hour
                    logger.info("blur_authenticated", wallet=wallet[:10])
                    return True
                else:
                    logger.warning("blur_login_failed", status=resp.status_code)
                    return False

        except Exception as e:
            logger.error("blur_auth_error", error=str(e))
            return False

    # ── Collection Data ────────────────────────────────────────

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5))
    async def get_collection(self, slug: str) -> dict:
        """Get collection info including floor price from Blur."""
        async with self._client() as client:
            resp = await client.get(f"/v1/collections/{slug}")
            if resp.status_code == 200:
                data = resp.json()
                collection = data.get("collection", {})
                return {
                    "slug": slug,
                    "name": collection.get("name", ""),
                    "contract_address": collection.get("contractAddress", ""),
                    "floor_price": self._parse_price(
                        collection.get("floorPrice", {})
                    ),
                    "best_bid": self._parse_price(
                        collection.get("bestBid", {})
                    ),
                    "total_supply": int(collection.get("totalSupply", 0) or 0),
                    "num_owners": int(collection.get("numberOwners", 0) or 0),
                    "volume_total": float(collection.get("totalVolume", 0) or 0),
                }
            logger.debug("blur_collection_error", slug=slug, status=resp.status_code)
            return {}

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5))
    async def get_collection_prices(self, slug: str) -> dict:
        """
        Get price levels for a collection from Blur.
        Returns floor asks and top bids with depth at each level.
        """
        async with self._client() as client:
            resp = await client.get(f"/v1/collections/{slug}/prices")
            if resp.status_code == 200:
                return resp.json()
            return {}

    # ── Executable Bids (requires auth) ────────────────────────

    async def get_executable_bids(self, slug: str) -> list[dict]:
        """
        Get the executable bid pool for a collection.
        These are real, fillable bids — not just indicative.

        This is THE key data source for cross-marketplace arbitrage:
        if Blur's best bid > OpenSea listing price, we have a spread.
        """
        await self.authenticate()

        try:
            async with self._client() as client:
                resp = await client.get(
                    f"/v1/collections/{slug}/executable-bids",
                )
                if resp.status_code == 200:
                    data = resp.json()
                    bids = data.get("priceLevels", [])

                    parsed = []
                    for level in bids:
                        price = float(level.get("price", 0))
                        quantity = int(level.get("executableSize", 0))
                        if price > 0 and quantity > 0:
                            parsed.append({
                                "price": price,
                                "quantity": quantity,
                                "marketplace": "blur",
                                "venue": "blur",
                            })

                    logger.debug(
                        "blur_bids_fetched",
                        collection=slug,
                        levels=len(parsed),
                        best_bid=parsed[0]["price"] if parsed else 0,
                    )
                    return parsed

                elif resp.status_code == 401:
                    self._auth_token = None
                    logger.warning("blur_bids_auth_expired", slug=slug)
                    return []
                else:
                    logger.debug(
                        "blur_bids_error",
                        slug=slug,
                        status=resp.status_code,
                    )
                    return []

        except Exception as e:
            logger.error("blur_bids_exception", slug=slug, error=str(e)[:100])
            return []

    # ── Listings ───────────────────────────────────────────────

    async def get_listings(self, slug: str, limit: int = 50) -> list[dict]:
        """
        Get active listings from Blur for a collection.
        Blur listings are often cheaper than OpenSea.
        """
        try:
            async with self._client() as client:
                resp = await client.get(
                    f"/v1/collections/{slug}/tokens",
                    params={
                        "filters": '{"traits":[],"hasAsks":true}',
                        "sort": "price",
                        "order": "asc",
                        "limit": limit,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    tokens = data.get("tokens", [])

                    listings = []
                    for token in tokens:
                        ask = token.get("price", {})
                        price = self._parse_price(ask) if isinstance(ask, dict) else float(ask or 0)
                        if price > 0:
                            listings.append({
                                "token_id": str(token.get("tokenId", "")),
                                "price": price,
                                "marketplace": "blur",
                                "venue": "blur",
                                "seller": token.get("owner", {}).get("address", ""),
                                "order_hash": token.get("orderId", ""),
                                "traits": token.get("traits", []),
                            })

                    logger.debug(
                        "blur_listings_fetched",
                        collection=slug,
                        count=len(listings),
                    )
                    return listings
                return []

        except Exception as e:
            logger.error("blur_listings_exception", slug=slug, error=str(e)[:100])
            return []

    # ── Batch Fetch ────────────────────────────────────────────

    async def fetch_collection_data(self, slug: str) -> dict:
        """
        Fetch all relevant Blur data for a collection in one batch.
        Used by the cross-marketplace strategy to compare with OpenSea.
        """
        collection_info, bids, listings = await asyncio.gather(
            self.get_collection(slug),
            self.get_executable_bids(slug),
            self.get_listings(slug, limit=30),
            return_exceptions=True,
        )

        if isinstance(collection_info, Exception):
            collection_info = {}
        if isinstance(bids, Exception):
            bids = []
        if isinstance(listings, Exception):
            listings = []

        # Best bid from bid pool
        best_bid = 0.0
        if bids:
            best_bid = max(b["price"] for b in bids)

        return {
            "collection": collection_info,
            "bids": bids,
            "listings": listings,
            "best_bid": best_bid,
            "floor_price": collection_info.get("floor_price", 0),
            "marketplace": "blur",
        }

    # ── Helpers ────────────────────────────────────────────────

    @staticmethod
    def _parse_price(price_obj: dict | str | float | None) -> float:
        """Parse Blur price objects (can be dict with 'amount' or string)."""
        if price_obj is None:
            return 0.0
        if isinstance(price_obj, (int, float)):
            return float(price_obj)
        if isinstance(price_obj, str):
            try:
                return float(price_obj)
            except ValueError:
                return 0.0
        if isinstance(price_obj, dict):
            amount = price_obj.get("amount")
            if amount is not None:
                try:
                    return float(amount)
                except (ValueError, TypeError):
                    return 0.0
            unit = price_obj.get("unit")
            if unit is not None:
                try:
                    return float(unit)
                except (ValueError, TypeError):
                    return 0.0
        return 0.0
