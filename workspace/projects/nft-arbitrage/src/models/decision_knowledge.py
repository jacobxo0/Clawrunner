"""
DecisionKnowledge — viden om beslutninger og udfald (for forecast-gate).

Når vi overvejer en opportunity gemmer vi kontekst (strategy, spread, bid_depth, roi, ...).
Når vi har et udfald (fyldt / ikke fyldt, PnL) opdaterer vi rækken.
Så kan vi spørge: "I lignende situationer, hvad var vores hit rate?"
Kun handle hvor vi kan forecast mindst lige så godt som succesfulde aktører.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Boolean

from src.database import Base


class DecisionKnowledge(Base):
    """
    Én beslutningskontekst + udfald.
    opportunity_id linker til opportunities-tabel; outcome_* udfyldes når vi kender resultatet.
    """
    __tablename__ = "decision_knowledge"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id = Column(
        String(36), ForeignKey("opportunities.id"), nullable=True, index=True
    )
    collection_id = Column(
        String(36), ForeignKey("collections.id"), nullable=False, index=True
    )
    strategy = Column(String(100), nullable=False, index=True)
    observed_at = Column(DateTime, nullable=False, index=True)

    # Kontekst da vi besluttede
    spread_pct = Column(Numeric(12, 6), nullable=True)
    bid_depth = Column(Numeric(12, 2), nullable=True)
    roi_pct = Column(Numeric(12, 4), nullable=True)
    fill_prob_predicted = Column(Numeric(6, 4), nullable=True)  # 0–1
    buy_price_eth = Column(Numeric(28, 18), nullable=True)

    # Udfald (udfyldes når trade er afsluttet eller opportunity udløber)
    outcome_filled = Column(Boolean, nullable=True)  # True = executed successfully
    outcome_pnl = Column(Numeric(28, 18), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
