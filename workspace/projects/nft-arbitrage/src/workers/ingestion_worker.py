"""
Ingestion Worker — fetches latest market data from OpenSea + Moralis
for all active collections and updates cache + database.

Data flow:
  OpenSea -> listings, bids, floor price, events
  Moralis  -> trades (historical sales), analytics
"""

from datetime import datetime

import structlog
from sqlalchemy import select

from src.config import get_settings
from src.database import async_session
from src.models.collection import Collection
from src.ingestion.opensea import OpenSeaClient
from src.ingestion.moralis import MoralisClient
from src.ingestion.normalizer import EventNormalizer
from src.cache.redis_cache import RedisCache

logger = structlog.get_logger()


class IngestionWorker:
    """
    Periodic worker that:
    1. Fetches listings, bids, stats from OpenSea API
    2. Fetches trade history from Moralis API
    3. Normalizes data into internal format
    4. Updates cache (floors, best bids, gas)
    5. Stores events in database for backtesting
    """

    def __init__(self):
        self.opensea = OpenSeaClient()
        self.moralis = MoralisClient()
        self.normalizer = EventNormalizer()
        self.cache = RedisCache()

    async def run(self):
        """Run ingestion for all active collections."""
        await self.cache.connect()

        async with async_session() as session:
            result = await session.execute(
                select(Collection).where(Collection.is_active == True)
            )
            collections = result.scalars().all()

        if not collections:
            logger.debug("no_active_collections")
            return

        for collection in collections:
            try:
                await self._ingest_collection(collection)
            except Exception as e:
                logger.error(
                    "ingestion_error",
                    collection=collection.slug,
                    error=str(e),
                )

        # Update gas price cache
        await self._update_gas_price()

        logger.info("ingestion_complete", collections=len(collections))

    async def _ingest_collection(self, collection: Collection):
        """Fetch and cache data for a single collection."""
        slug = collection.slug
        contract = collection.contract_address

        # ── Fetch from OpenSea (listings, bids, stats) ────────
        opensea_data = await self.opensea.fetch_all_collection_data(
            collection_slug=slug,
            contract_address=contract,
        )

        # ── Normalize collection stats ────────────────────────
        stats = opensea_data.get("stats", {})
        normalized_info = self.normalizer.normalize_collection_info(stats)

        # ── Extract best bid from offers ──────────────────────
        bids = opensea_data.get("bids", [])
        best_bid_price = 0.0
        if bids:
            first_offer = bids[0]
            normalized_bid = self.normalizer.normalize_opensea_offer(first_offer, collection.id)
            best_bid_price = float(normalized_bid["price"])
            normalized_info["best_bid"] = best_bid_price

        # ── Cache floor price and best bid ────────────────────
        if normalized_info.get("floor_price", 0) > 0:
            await self.cache.set_floor_price(
                str(collection.id),
                normalized_info["floor_price"],
                ttl=30,
            )

        if best_bid_price > 0:
            await self.cache.set_best_bid(
                str(collection.id),
                {"price": best_bid_price},
                ttl=30,
            )

        # ── Cache individual listings ─────────────────────────
        for raw_listing in opensea_data.get("listings", []):
            normalized = self.normalizer.normalize_opensea_listing(raw_listing, collection.id)
            token_id = normalized.get("token_id", "")
            if token_id:
                await self.cache.set_listing(
                    str(collection.id),
                    token_id,
                    normalized,
                    ttl=60,
                )

        # ── Update collection in database ─────────────────────
        async with async_session() as session:
            result = await session.execute(
                select(Collection).where(Collection.id == collection.id)
            )
            col = result.scalar_one_or_none()
            if col:
                col.floor_price = normalized_info.get("floor_price")
                col.best_bid = normalized_info.get("best_bid")
                col.updated_at = datetime.utcnow()
                await session.commit()

        logger.info(
            "collection_ingested",
            slug=slug,
            floor=normalized_info.get("floor_price"),
            best_bid=normalized_info.get("best_bid"),
            listings=len(opensea_data.get("listings", [])),
            bids=len(bids),
        )

    async def _update_gas_price(self):
        """Update cached gas price (simplified for MVP)."""
        await self.cache.set_gas_price(20.0, ttl=30)
