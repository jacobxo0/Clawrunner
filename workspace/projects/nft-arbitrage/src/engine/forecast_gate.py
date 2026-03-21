"""
Forecast Gate — kun tillad trade hvor vi kan forecast mindst lige så godt som
andre der har succes med disse ting.

Bruger DecisionKnowledge: i lignende situationer (strategy + collection + spread/bid_depth)
hvad var vores hit rate? Kun hvis hit_rate >= min_benchmark_hit_rate (fx 0.55) og
vi har nok datapunkter, godkendes handlen.
"""

from datetime import datetime, timedelta
from decimal import Decimal

import structlog
from sqlalchemy import select, func, and_, case

from src.config import get_settings
from src.database import async_session
from src.models.decision_knowledge import DecisionKnowledge

logger = structlog.get_logger()


class ForecastGate:
    """
    Tjek at vi kun handler i segmenter hvor vores historiske forecast-kvalitet
    er mindst lige så god som benchmark (succesfulde aktørers niveau).
    """

    def __init__(self):
        settings = get_settings()
        fg = settings.forecast_gate
        self.min_benchmark_hit_rate = float(fg.get("min_benchmark_hit_rate", 0.55))
        self.min_sample_size = int(fg.get("min_sample_size", 5))
        self.allow_if_insufficient_data = fg.get("allow_if_insufficient_data", True)
        self.lookback_days = int(fg.get("lookback_days", 90))
        self.spread_tolerance_pct = float(fg.get("spread_tolerance_pct", 1.0))
        self.bid_depth_tolerance = int(fg.get("bid_depth_tolerance", 2))

    async def allowed(self, opportunity: dict, collection_data: dict) -> tuple[bool, str]:
        """
        Return (True, "") hvis vi må handle; (False, reason) ellers.
        Ligner situationen (strategy, collection, spread, bid_depth) sammenlignes med
        historiske beslutninger; kun hvis hit rate >= benchmark og nok data.
        """
        strategy = opportunity.get("strategy", "")
        collection_id = str(opportunity.get("collection_id", ""))
        spread_pct = opportunity.get("spread_pct") or collection_data.get("orderbook_spread_pct")
        bid_depth = opportunity.get("bid_depth") or collection_data.get("bid_depth", 0)
        if spread_pct is None:
            spread_pct = 0.0
        if bid_depth is None:
            bid_depth = 0
        try:
            spread_pct = float(spread_pct)
            bid_depth = int(bid_depth)
        except (TypeError, ValueError):
            spread_pct = 0.0
            bid_depth = 0

        since = datetime.utcnow() - timedelta(days=self.lookback_days)
        spread_lo = spread_pct - self.spread_tolerance_pct
        spread_hi = spread_pct + self.spread_tolerance_pct
        depth_lo = max(0, bid_depth - self.bid_depth_tolerance)

        async with async_session() as session:
            # Kun rækker hvor vi har outcome; tæl hvor outcome_filled er True
            q = select(
                func.count(DecisionKnowledge.id).label("n"),
                func.sum(case((DecisionKnowledge.outcome_filled == True, 1), else_=0)).label("filled"),
            ).where(
                and_(
                    DecisionKnowledge.collection_id == collection_id,
                    DecisionKnowledge.strategy == strategy,
                    DecisionKnowledge.observed_at >= since,
                    DecisionKnowledge.outcome_filled.isnot(None),
                )
            )
            if spread_pct is not None and spread_lo is not None:
                q = q.where(
                    and_(
                        DecisionKnowledge.spread_pct >= Decimal(str(spread_lo)),
                        DecisionKnowledge.spread_pct <= Decimal(str(spread_hi)),
                    )
                )
            if bid_depth is not None and depth_lo is not None:
                q = q.where(DecisionKnowledge.bid_depth >= depth_lo)

            result = await session.execute(q)
            row = result.one_or_none()
            if not row or row.n is None or row.n == 0:
                if self.allow_if_insufficient_data:
                    return True, ""
                return False, "forecast_gate: no historical data in similar situations"

            n = int(row.n)
            filled = int(row.filled or 0)
            hit_rate = filled / n if n else 0.0

            if n < self.min_sample_size:
                if self.allow_if_insufficient_data:
                    return True, ""
                return False, f"forecast_gate: only {n} similar decisions (need {self.min_sample_size})"

            if hit_rate < self.min_benchmark_hit_rate:
                logger.warning(
                    "forecast_gate_blocked",
                    strategy=strategy,
                    collection_id=collection_id,
                    hit_rate=round(hit_rate, 3),
                    benchmark=self.min_benchmark_hit_rate,
                    n=n,
                )
                return False, (
                    f"forecast_gate: hit rate {hit_rate:.2%} in similar situations "
                    f"< benchmark {self.min_benchmark_hit_rate:.0%}"
                )
            return True, ""
</think>
Retter import i forecast_gate og tilføjer Integer til cast.
<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>
StrReplace