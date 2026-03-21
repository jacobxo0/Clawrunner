"""
Risk Worker — updates risk scores for all active collections
using Moralis analytics data (trades, transfers, ownership).
"""

import structlog
from sqlalchemy import select

from src.database import async_session
from src.models.collection import Collection
from src.ingestion.moralis import MoralisClient
from src.ingestion.normalizer import EventNormalizer
from src.engine.wash_detector import WashDetector
from src.engine.liquidity_scorer import LiquidityScorer

logger = structlog.get_logger()


class RiskWorker:
    """Periodic worker that updates risk scores for collections."""

    def __init__(self):
        self.moralis = MoralisClient()
        self.normalizer = EventNormalizer()
        self.wash_detector = WashDetector()
        self.liquidity_scorer = LiquidityScorer()

    async def run(self):
        """Update risk scores for all active collections."""
        async with async_session() as session:
            result = await session.execute(
                select(Collection).where(Collection.is_active == True)
            )
            collections = result.scalars().all()

            for collection in collections:
                try:
                    await self._update_risk(session, collection)
                except Exception as e:
                    logger.error("risk_update_error", collection=collection.slug, error=str(e))

            await session.commit()

        logger.info("risk_update_complete", collections=len(collections))

    async def _update_risk(self, session, collection: Collection):
        """Fetch analytics and update risk scores for a collection."""
        if not collection.contract_address:
            return

        analytics = await self.moralis.fetch_collection_analytics(collection.contract_address)

        # Normalize transfers for wash detection
        transfers = [
            self.normalizer.normalize_moralis_transfer(t)
            for t in analytics.get("transfers_7d", [])
        ]

        wash_result = self.wash_detector.score(transfers)
        wash_score = wash_result.get("wash_score", 0)

        liquidity_result = self.liquidity_scorer.score(
            bid_count=0,
            bid_depth_eth=0,
            volume_7d=len(analytics.get("trades_7d", [])),
            volume_24h=len(analytics.get("trades_24h", [])),
            num_owners=len(analytics.get("owners", [])),
        )
        liquidity_score = liquidity_result.get("score", 0)

        # Persist scores to database
        collection.wash_score = wash_score
        collection.liquidity_score = liquidity_score
        session.add(collection)

        logger.info(
            "risk_scores_updated",
            collection=collection.slug,
            wash_score=wash_score,
            liquidity_score=liquidity_score,
        )
