"""
Decision Engine
----------------
Decides whether an approved opportunity should be auto-executed
or queued for human review based on confidence thresholds from settings.
"""

import logging

from src.config import get_settings

logger = logging.getLogger(__name__)


class DecisionEngine:

    def __init__(self):
        settings = get_settings()
        exec_cfg = settings.execution
        self.auto_execute_threshold = exec_cfg.get("auto_execute_confidence", 0.90)
        self.human_review_threshold = exec_cfg.get("human_review_confidence", 0.70)

    def decide(self, qc_result: dict) -> str:
        """
        Given a QC result, return one of:
        - "AUTO_EXECUTE"  -- confidence >= auto threshold and verdict APPROVE
        - "QUEUE_REVIEW"  -- confidence between thresholds
        - "REJECT"        -- verdict is REJECT

        Parameters
        ----------
        qc_result : dict
            Output from QCAgent.evaluate().

        Returns
        -------
        str
        """
        verdict = qc_result.get("verdict", "REJECT")
        confidence = qc_result.get("confidence", 0.0)

        if verdict == "REJECT":
            decision = "REJECT"
        elif verdict == "APPROVE" and confidence >= self.auto_execute_threshold:
            decision = "AUTO_EXECUTE"
        else:
            decision = "QUEUE_REVIEW"

        logger.info(
            "Decision: %s (verdict=%s, confidence=%.3f)",
            decision, verdict, confidence,
        )
        return decision
