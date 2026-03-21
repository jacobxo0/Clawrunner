"""
Knowledge Store — gem beslutningskontekst og opdater med udfald.

Når vi overvejer en opportunity: insert DecisionKnowledge.
Når vi har udfald (executed / ikke): update outcome_filled og outcome_pnl.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import update

from src.database import async_session
from src.models.decision_knowledge import DecisionKnowledge


async def record_decision(
    opportunity_id: str,
    collection_id: str,
    strategy: str,
    spread_pct: float | None,
    bid_depth: float | None,
    roi_pct: float | None,
    fill_prob_predicted: float | None,
    buy_price_eth: float | None,
) -> str:
    """
    Gem én beslutningskontekst (kald før execution). Returnerer knowledge-id.
    """
    observed_at = datetime.utcnow()
    kid = str(uuid.uuid4())
    row = DecisionKnowledge(
        id=kid,
        opportunity_id=opportunity_id,
        collection_id=collection_id,
        strategy=strategy,
        observed_at=observed_at,
        spread_pct=Decimal(str(spread_pct)) if spread_pct is not None else None,
        bid_depth=Decimal(str(bid_depth)) if bid_depth is not None else None,
        roi_pct=Decimal(str(roi_pct)) if roi_pct is not None else None,
        fill_prob_predicted=Decimal(str(fill_prob_predicted)) if fill_prob_predicted is not None else None,
        buy_price_eth=Decimal(str(buy_price_eth)) if buy_price_eth is not None else None,
    )
    async with async_session() as session:
        session.add(row)
        await session.commit()
    return kid


async def record_outcome(opportunity_id: str, outcome_filled: bool, outcome_pnl: float | None):
    """Opdater DecisionKnowledge med udfald efter trade (eller afvist/udløbet)."""
    async with async_session() as session:
        await session.execute(
            update(DecisionKnowledge)
            .where(DecisionKnowledge.opportunity_id == opportunity_id)
            .values(
                outcome_filled=outcome_filled,
                outcome_pnl=Decimal(str(outcome_pnl)) if outcome_pnl is not None else None,
            )
        )
        await session.commit()
