"""
Agent model -- logs agent decisions and actions for auditability.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, DateTime, JSON,
)

from src.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_name = Column(String(100), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    opportunity_id = Column(String(36), nullable=True, index=True)
    decision = Column(String(50), nullable=True)  # approve, reject, escalate
    reasoning = Column(String(2000), nullable=True)
    confidence = Column(Float, nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    duration_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return (
            f"<Agent name={self.agent_name!r} action={self.action!r} "
            f"decision={self.decision!r}>"
        )
