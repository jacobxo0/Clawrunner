"""
Observation Loop Motor — kører konstante observationer og lagrer dem som viden.

Data bruges til at matche nuværende situation mod historik og til forecast-gate:
kun handle hvor vi kan forudsige mindst lige så godt som andre der har succes.
"""

import asyncio
from datetime import datetime
from decimal import Decimal

import structlog
from sqlalchemy import select

from src.config import get_settings
from src.database import async_session
from src.models.collection import Collection
from src.models.market_observation import MarketObservation
from src.ingestion.opensea import OpenSeaClient
from src.ingestion.normalizer import EventNormalizer

logger = structlog.get_logger()


def _parse_listing_price(raw: dict) -> float:
    """Extract ETH price from OpenSea listing."""
    price_obj = raw.get("price", {})
    if isinstance(price_obj, dict):
        current = price_obj.get("current", {})
        if current and isinstance(current, dict):
            try:
                return int(current.get("value", 0)) / 10 ** int(current.get("decimals", 18))
            except (ValueError, TypeError):
                pass
    if raw.get("current_price"):
        try:
            return int(raw["current_price"]) / 1e18
        except (ValueError, TypeError):
            pass
    return 0.0


def _parse_offer_price(raw: dict) -> float:
    """Extract ETH price from OpenSea offer."""
    price_obj = raw.get("price", {}) if isinstance(raw.get("price"), dict) else {}
    try:
        return int(price_obj.get("value", 0)) / 10 ** int(price_obj.get("decimals", 18))
    except (ValueError, TypeError):
        return 0.0


class ObservationLoopWorker:
    """
    Kontinuerlig observation: henter markedsstate per collection og gemmer som viden.
    Kør med kort interval (fx 30–60 s) så vi altid har frisk kontekst før handler.
    """

    def __init__(self):
        self.opensea = OpenSeaClient()
        self.normalizer = EventNormalizer()
        settings = get_settings()
        self.interval_seconds = settings.scheduling.get("observation_loop_seconds", 45)
        obs_cfg = settings.observation_loop
        self.max_collections_per_cycle = obs_cfg.get("max_collections_per_cycle", 30)

    async def run(self):
        """Hent state for aktive collections og gem MarketObservation."""
        observed_at = datetime.utcnow()
        try:
            async with async_session() as session:
                result = await session.execute(
                    select(Collection).where(Collection.is_active == True).limit(self.max_collections_per_cycle)
                )
                collections = result.scalars().all()
        except Exception as e:
            logger.error("observation_loop_fetch_collections_error", error=str(e))
            return

        for col in collections:
            try:
                obs = await self._observe_collection(col.id, col.slug, observed_at)
                if obs:
                    async with async_session() as session:
                        session.add(obs)
                        await session.commit()
                    logger.debug(
                        "observation_stored",
                        slug=col.slug,
                        spread_pct=float(obs.spread_pct) if obs.spread_pct else None,
                        bid_depth=float(obs.bid_depth) if obs.bid_depth else None,
                    )
            except Exception as e:
                logger.warning("observation_loop_collection_error", slug=col.slug, error=str(e)[:80])

        logger.info("observation_loop_cycle_done", collections=len(collections), observed_at=observed_at.isoformat())

    async def _observe_collection(self, collection_id: str, slug: str, observed_at: datetime) -> MarketObservation | None:
        """Hent listings + offers + stats for én collection og byg én observation."""
        try:
            listings_task = self.opensea.get_collection_listings(slug, limit=25)
            offers_task = self.opensea.get_collection_offers(slug, limit=25)
            stats_task = self.opensea.get_collection_stats(slug)
            listings_data, offers_data, stats_data = await asyncio.gather(
                listings_task, offers_task, stats_task, return_exceptions=True
            )
        except Exception as e:
            logger.debug("observation_fetch_error", slug=slug, error=str(e)[:60])
            return None

        if isinstance(listings_data, Exception):
            listings_data = {}
        if isinstance(offers_data, Exception):
            offers_data = {}
        if isinstance(stats_data, Exception):
            stats_data = {}

        listings = listings_data.get("listings", [])
        offers = offers_data.get("offers", [])

        listing_prices = [_parse_listing_price(l) for l in listings if _parse_listing_price(l) > 0]
        offer_prices = [_parse_offer_price(o) for o in offers if _parse_offer_price(o) > 0]

        floor_eth = min(listing_prices) if listing_prices else None
        best_bid_eth = max(offer_prices) if offer_prices else None

        if floor_eth is None and stats_data:
            tot = stats_data.get("total", {})
            fp = tot.get("floor_price")
            if fp is not None:
                try:
                    floor_eth = float(fp)
                except (ValueError, TypeError):
                    pass

        spread_pct = None
        if floor_eth and floor_eth > 0 and best_bid_eth and best_bid_eth > 0:
            spread_pct = (best_bid_eth - floor_eth) / floor_eth * 100

        volume_24h_eth = None
        if stats_data:
            tot = stats_data.get("total", {})
            v = tot.get("volume", {}).get("1d") or tot.get("volume_1d")
            if v is not None:
                try:
                    volume_24h_eth = float(v)
                except (ValueError, TypeError):
                    pass

        return MarketObservation(
            collection_id=collection_id,
            observed_at=observed_at,
            spread_pct=Decimal(str(spread_pct)) if spread_pct is not None else None,
            bid_depth=Decimal(len(offers)) if offers else None,
            floor_eth=Decimal(str(floor_eth)) if floor_eth is not None else None,
            best_bid_eth=Decimal(str(best_bid_eth)) if best_bid_eth is not None else None,
            num_listings=Decimal(len(listings)) if listings else None,
            num_bids=Decimal(len(offers)) if offers else None,
            volume_24h_eth=Decimal(str(volume_24h_eth)) if volume_24h_eth is not None else None,
        )
