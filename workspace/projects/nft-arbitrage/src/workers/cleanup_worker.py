"""
Cleanup Worker — removes expired listings, bids, and old opportunities.
"""

from datetime import datetime, timedelta

import structlog
from sqlalchemy import select, delete

from src.database import async_session
from src.models.opportunity import Opportunity

logger = structlog.get_logger()


class CleanupWorker:
    """Periodic worker that cleans up stale data."""

    async def run(self):
        """Clean up expired data."""
        cutoff = datetime.utcnow() - timedelta(days=7)

        async with async_session() as session:
            # Remove old rejected opportunities
            result = await session.execute(
                delete(Opportunity).where(
                    Opportunity.status == "rejected",
                    Opportunity.created_at < cutoff,
                )
            )
            deleted = result.rowcount
            await session.commit()

        if deleted:
            logger.info("cleanup_complete", deleted_opportunities=deleted)
        else:
            logger.debug("cleanup_nothing_to_remove")
