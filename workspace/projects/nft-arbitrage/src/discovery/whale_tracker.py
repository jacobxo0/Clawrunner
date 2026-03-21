"""
Whale Tracker — follow what smart money wallets are buying.

If a wallet that historically picks winners buys into a new collection,
that's a strong alpha signal. We track known whale/smart-money wallets
and monitor their NFT purchases in real-time.

Sources:
- OpenSea events API (transfers/sales to known wallets)
- Moralis API (wallet NFT transfers)
"""

import asyncio
import time
from datetime import datetime, timedelta

import httpx
import structlog

from src.config import get_settings

logger = structlog.get_logger()

# Known NFT whale/smart-money wallets (curated list)
# These are wallets known for early collection picks
WHALE_WALLETS = [
    "0xd387a6e4e84a6c86bd90c158c6028a58cc8ac459",  # Pranksy
    "0xff0bd4aa3496739d5667adc10e2b2b4a1da79366",  # Dingaling
    "0xc6b0562605d35ee710138402b878ffe6f2e23807",  # 6529
    "0x2ce780d7c743a57791b835a9d6f998b15bbba5a4",  # DCinvestor
    "0xf476cd75be8fdd197ae0b466a2ec2ae44da41897",  # Seedphrase
    "0xc5f59709974262c4afacc5386287820bdbc7eb3a",  # Farokh
    "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Vitalik
    "0xa679c6154b8d4619af9f83f0bf9a13a680e01ecf",  # Punk6529
    "0x1da5331994e781ab0e2af9f85bfce2037a514571",  # Wilcox
]

# Track what whales buy — persist across calls
_WHALE_BUYS: list[dict] = []
_WHALE_COLLECTIONS: dict[str, dict] = {}  # collection -> {buy_count, whales, ...}


class WhaleTracker:
    """
    Monitors whale wallets for NFT purchases.
    When whales buy into small/new collections, it's a strong signal.
    """

    def __init__(self):
        settings = get_settings()
        self.opensea_key = settings.marketplace.opensea_api_key
        self.moralis_key = settings.marketplace.moralis_api_key

    async def scan_whale_activity(self, hours: int = 24) -> list[dict]:
        """
        Scan recent whale purchases across all tracked wallets.
        Returns collections that whales are buying into.
        """
        logger.info("whale_scan_starting", wallets=len(WHALE_WALLETS), hours=hours)

        all_purchases = []

        for wallet in WHALE_WALLETS:
            try:
                purchases = await self._get_wallet_purchases(wallet, hours)
                all_purchases.extend(purchases)
                await asyncio.sleep(0.3)  # Rate limit
            except Exception as e:
                logger.debug("whale_scan_wallet_error", wallet=wallet[:10], error=str(e)[:80])

        # Aggregate by collection
        collection_buys: dict[str, dict] = {}
        for purchase in all_purchases:
            col = purchase.get("collection", "unknown")
            if col not in collection_buys:
                collection_buys[col] = {
                    "collection": col,
                    "contract": purchase.get("contract", ""),
                    "buy_count": 0,
                    "unique_whales": set(),
                    "total_spent": 0.0,
                    "avg_price": 0.0,
                    "purchases": [],
                }
            entry = collection_buys[col]
            entry["buy_count"] += 1
            entry["unique_whales"].add(purchase.get("wallet", ""))
            entry["total_spent"] += purchase.get("price", 0)
            entry["purchases"].append(purchase)

        # Convert sets to counts for JSON serialization
        results = []
        for col, data in collection_buys.items():
            data["unique_whale_count"] = len(data["unique_whales"])
            data["unique_whales"] = list(data["unique_whales"])
            data["avg_price"] = data["total_spent"] / max(data["buy_count"], 1)
            results.append(data)

        # Sort by unique whale count (more whales = stronger signal)
        results.sort(key=lambda x: (x["unique_whale_count"], x["buy_count"]), reverse=True)

        # Update global tracking
        for entry in results:
            _WHALE_COLLECTIONS[entry["collection"]] = {
                **entry,
                "last_scanned": datetime.utcnow().isoformat(),
            }
        _WHALE_BUYS.extend(all_purchases)

        # Keep only recent data
        cutoff = time.time() - (48 * 3600)
        _WHALE_BUYS[:] = [b for b in _WHALE_BUYS if b.get("timestamp", 0) > cutoff]

        logger.info(
            "whale_scan_complete",
            total_purchases=len(all_purchases),
            collections_found=len(results),
            top_collection=results[0]["collection"] if results else "none",
        )

        return results

    async def _get_wallet_purchases(self, wallet: str, hours: int) -> list[dict]:
        """Get recent NFT purchases for a wallet via OpenSea events."""
        purchases = []
        after = datetime.utcnow() - timedelta(hours=hours)
        after_ts = int(after.timestamp())

        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(
                    f"https://api.opensea.io/api/v2/events/accounts/{wallet}",
                    params={
                        "event_type": "sale",
                        "after": after_ts,
                        "limit": 50,
                    },
                    headers={
                        "accept": "application/json",
                        "x-api-key": self.opensea_key,
                    },
                )

                if resp.status_code == 200:
                    data = resp.json()
                    events = data.get("asset_events", [])

                    for event in events:
                        # Only track purchases (where whale is the buyer)
                        buyer = event.get("buyer", "")
                        if isinstance(buyer, dict):
                            buyer = buyer.get("address", "")

                        if buyer.lower() != wallet.lower():
                            continue

                        nft = event.get("nft", {})
                        payment = event.get("payment", {})

                        price_val = 0
                        try:
                            price_val = int(payment.get("quantity", "0")) / 1e18
                        except (ValueError, TypeError):
                            pass

                        purchases.append({
                            "wallet": wallet,
                            "collection": nft.get("collection", ""),
                            "contract": nft.get("contract", ""),
                            "token_id": nft.get("identifier", ""),
                            "price": price_val,
                            "timestamp": time.time(),
                            "event_time": event.get("event_timestamp", ""),
                        })

            except Exception as e:
                logger.debug("whale_opensea_error", wallet=wallet[:10], error=str(e)[:80])

        return purchases

    async def get_hot_collections(self, min_whales: int = 2) -> list[dict]:
        """
        Get collections where multiple whales are buying.
        2+ unique whales buying the same collection = strong signal.
        """
        all_activity = await self.scan_whale_activity(hours=48)
        return [
            col for col in all_activity
            if col.get("unique_whale_count", 0) >= min_whales
        ]

    @staticmethod
    def get_whale_data() -> dict:
        """Get current whale tracking data for API/dashboard."""
        return {
            "tracked_wallets": len(WHALE_WALLETS),
            "recent_buys": len(_WHALE_BUYS),
            "collections_with_whale_activity": len(_WHALE_COLLECTIONS),
            "top_collections": sorted(
                _WHALE_COLLECTIONS.values(),
                key=lambda x: x.get("unique_whale_count", 0),
                reverse=True,
            )[:10],
        }
