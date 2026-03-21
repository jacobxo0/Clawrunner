"""Internal normalized event schema for the scoring pipeline.

Every incoming ISO 20022 message is parsed into a NormalizedEvent before
entering the scoring mesh. This is the canonical internal format.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class EventType(str, Enum):
    CREDIT_TRANSFER = "credit_transfer"      # pacs.008
    CANCELLATION = "cancellation"            # camt.056
    IDENTITY_UPDATE = "identity_update"      # acmt.023


class RiskScore(BaseModel):
    """Output of a single scoring stage."""

    scorer: str = Field(description="Name of the scoring module (e.g. 'rules_v1', 'ml_graph_v2')")
    score: float = Field(ge=0.0, le=1.0, description="Risk probability 0-1")
    reasons: list[str] = Field(default_factory=list)
    latency_ms: float | None = None


class NormalizedEvent(BaseModel):
    """Canonical internal event flowing through the scoring pipeline."""

    event_id: str = Field(description="Internal UUID assigned at ingestion")
    event_type: EventType
    ingested_at: datetime
    source_msg_id: str = Field(description="Original ISO 20022 MsgId")
    uetr: str | None = None

    # Parties
    debtor_name: str | None = None
    debtor_iban: str | None = None
    debtor_bic: str | None = None
    debtor_country: str | None = None
    creditor_name: str | None = None
    creditor_iban: str | None = None
    creditor_bic: str | None = None
    creditor_country: str | None = None

    # Amount
    amount: Decimal | None = None
    currency: str = "EUR"

    # Context
    purpose_code: str | None = None
    remittance_info: str | None = None

    # Scoring results (appended by pipeline stages)
    scores: list[RiskScore] = Field(default_factory=list)
    flagged: bool = False
    aggregate_risk: float | None = Field(default=None, ge=0.0, le=1.0)

    # Raw payload reference
    raw_payload_ref: str | None = Field(
        default=None,
        description="S3/blob key or audit-log row ID for the original XML",
    )
