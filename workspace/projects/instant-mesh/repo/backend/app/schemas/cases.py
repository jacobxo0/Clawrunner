"""Case/alert object schema for agent handoff.

When a NormalizedEvent is flagged, a Case is created and handed to the
agentic case-bot for investigation and resolution.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CaseStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    ESCALATED = "escalated"
    RESOLVED_TRUE_POSITIVE = "resolved_tp"
    RESOLVED_FALSE_POSITIVE = "resolved_fp"
    CLOSED = "closed"


class CasePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CaseNote(BaseModel):
    """Timestamped note on a case – can come from agent or human."""

    timestamp: datetime
    author: str = Field(description="'agent:<name>' or 'human:<email>'")
    text: str
    action_taken: str | None = None


class Case(BaseModel):
    """Investigation case created from a flagged event."""

    case_id: str
    created_at: datetime
    updated_at: datetime
    status: CaseStatus = CaseStatus.OPEN
    priority: CasePriority = CasePriority.MEDIUM

    # Link to triggering event(s)
    event_ids: list[str] = Field(min_length=1)
    aggregate_risk: float = Field(ge=0.0, le=1.0)

    # Summary for investigator
    summary: str | None = None
    risk_factors: list[str] = Field(default_factory=list)

    # Agent interaction
    assigned_agent: str | None = Field(default=None, description="Agent ID handling this case")
    notes: list[CaseNote] = Field(default_factory=list)

    # Resolution
    resolution: str | None = None
    resolved_by: str | None = None
    resolved_at: datetime | None = None
