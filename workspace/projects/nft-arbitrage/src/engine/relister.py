"""
Dynamic Relister — Dutch auction-style price decay for held inventory.

When the bot buys an NFT and the immediate sell fails or no bid exists,
the NFT sits in inventory. Over time, its expected exit price should
decrease to ensure we don't hold losing positions indefinitely.

Price curve: acquisition * (1 + markup - decay_per_hour * hours_held)
  - Starts above acquisition price (initial markup)
  - Decays linearly toward floor
  - Never lists below 98% of current floor (safety floor)
"""

import logging
from datetime import datetime, timezone

from src.config import get_settings

logger = logging.getLogger(__name__)


class DynamicRelister:
    """
    Manages dynamic relisting with Dutch auction decay.
    Periodically called by the scheduler to adjust relist prices.
    """

    def __init__(self):
        cfg = get_settings().yaml_settings.get("relisting", {})
        self.initial_markup_pct = cfg.get("initial_markup_pct", 15.0) / 100.0
        self.decay_rate_per_hour = cfg.get("decay_rate_per_hour", 1.0) / 100.0
        self.min_price_floor_pct = cfg.get("min_price_floor_pct", -5.0) / 100.0
        self.max_hold_hours = cfg.get("max_hold_hours", 48)

    def calculate_relist_price(
        self,
        acquisition_price: float,
        hours_held: float,
        floor_price: float,
    ) -> float:
        """
        Calculate the current relist price based on how long we've held the NFT.

        Parameters
        ----------
        acquisition_price : float
            What we paid for the NFT (ETH).
        hours_held : float
            How many hours since acquisition.
        floor_price : float
            Current collection floor price (ETH).

        Returns
        -------
        float
            Recommended relist price in ETH.
        """
        markup = self.initial_markup_pct - (self.decay_rate_per_hour * hours_held)
        relist_price = acquisition_price * (1.0 + markup)

        min_acceptable = acquisition_price * (1.0 + self.min_price_floor_pct)
        relist_price = max(relist_price, min_acceptable)

        safety_floor = floor_price * 0.98 if floor_price > 0 else 0
        if safety_floor > 0:
            relist_price = max(relist_price, safety_floor)

        return round(relist_price, 6)

    async def run(self):
        """
        Check all held inventory and update relist prices.
        Called periodically by the scheduler.
        """
        from sqlalchemy import select
        from src.database import async_session
        from src.models.inventory import Inventory
        from src.models.collection import Collection

        try:
            async with async_session() as session:
                result = await session.execute(
                    select(Inventory).where(Inventory.status == "held")
                )
                positions = result.scalars().all()

                if not positions:
                    return

                updated = 0
                now = datetime.now(timezone.utc)

                for pos in positions:
                    acquired_at = pos.acquired_at
                    if acquired_at is None:
                        continue

                    if acquired_at.tzinfo is None:
                        acquired_at = acquired_at.replace(tzinfo=timezone.utc)

                    hours_held = (now - acquired_at).total_seconds() / 3600.0

                    col_result = await session.execute(
                        select(Collection).where(Collection.id == pos.collection_id)
                    )
                    collection = col_result.scalar_one_or_none()
                    floor_price = float(collection.floor_price or 0) if collection else 0

                    new_price = self.calculate_relist_price(
                        acquisition_price=float(pos.acquisition_price or 0),
                        hours_held=hours_held,
                        floor_price=floor_price,
                    )

                    if abs(new_price - float(pos.relist_price or 0)) > 0.0001:
                        pos.relist_price = new_price
                        pos.relist_updated_at = now
                        updated += 1

                    if hours_held > self.max_hold_hours:
                        pos.status = "liquidating"
                        logger.warning(
                            "inventory_max_hold_exceeded",
                            token_id=pos.token_id,
                            hours=round(hours_held, 1),
                        )

                await session.commit()

                if updated:
                    logger.info(
                        "relister_updated",
                        positions=len(positions),
                        price_changes=updated,
                    )

        except Exception as e:
            logger.error("relister_error", exc_info=True)
