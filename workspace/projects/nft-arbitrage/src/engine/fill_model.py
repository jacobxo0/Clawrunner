"""
Fill Probability Model — predicts the likelihood an arbitrage opportunity
will actually execute successfully (both buy and sell).

Uses a lightweight scikit-learn GradientBoostingClassifier trained on
historical opportunity data from the DB. Falls back to a heuristic
model when no trained model is available.

Features:
  - spread_pct: bid-ask spread as percentage
  - bid_depth: number of bids at or above exit price
  - collection_volatility: recent price volatility
  - hour_of_day / day_of_week: temporal patterns
  - historical_fill_rate: collection's historical fill rate
  - roi_pct: expected return on investment
  - buy_price_eth: absolute price level
"""

import os
import pickle
from datetime import datetime
from pathlib import Path

import numpy as np
import structlog

logger = structlog.get_logger()

FEATURE_NAMES = [
    "spread_pct",
    "bid_depth",
    "collection_volatility",
    "hour_of_day",
    "day_of_week",
    "historical_fill_rate",
    "roi_pct",
    "buy_price_eth",
]

MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "models"
MODEL_PATH = MODEL_DIR / "fill_model.pkl"


class FillProbabilityModel:
    """
    Predicts fill probability (0.0–1.0) for arbitrage opportunities.
    Uses GradientBoostingClassifier when trained, heuristic fallback otherwise.
    """

    def __init__(self):
        self._model = None
        self._is_trained = False

    def predict(self, features: dict) -> float:
        """
        Predict fill probability for a single opportunity.

        Parameters
        ----------
        features : dict
            Keys matching FEATURE_NAMES. Missing keys default to 0.

        Returns
        -------
        float
            Probability between 0.0 and 1.0.
        """
        if self._is_trained and self._model is not None:
            return self._ml_predict(features)
        return self._heuristic_predict(features)

    def _ml_predict(self, features: dict) -> float:
        """Use trained ML model for prediction."""
        try:
            X = np.array([[features.get(f, 0) for f in FEATURE_NAMES]])
            proba = self._model.predict_proba(X)
            return float(proba[0][1]) if proba.shape[1] > 1 else float(proba[0][0])
        except Exception as e:
            logger.warning("fill_model_predict_error", error=str(e)[:80])
            return self._heuristic_predict(features)

    @staticmethod
    def _heuristic_predict(features: dict) -> float:
        """
        Rule-based fallback when no ML model is available.
        Combines spread, depth, and ROI into a probability estimate.
        """
        score = 0.5

        spread = features.get("spread_pct", 0)
        if spread > 0:
            score += min(spread / 20.0, 0.2)
        else:
            score -= 0.1

        depth = features.get("bid_depth", 0)
        if depth >= 5:
            score += 0.15
        elif depth >= 2:
            score += 0.05
        elif depth == 0:
            score -= 0.2

        roi = features.get("roi_pct", 0)
        if roi >= 5:
            score += 0.1
        elif roi < 1:
            score -= 0.1

        vol = features.get("collection_volatility", 1.0)
        if vol > 2.0:
            score -= 0.1
        elif vol < 0.5:
            score += 0.05

        fill_rate = features.get("historical_fill_rate", 0.5)
        score += (fill_rate - 0.5) * 0.2

        return max(0.05, min(0.95, score))

    async def train(self, lookback_days: int = 30):
        """
        Train the model on historical opportunity data from the DB.
        Opportunities with status 'executed' = positive, 'expired'/'failed' = negative.
        """
        from sklearn.ensemble import GradientBoostingClassifier
        from sqlalchemy import select
        from src.database import async_session
        from src.models.opportunity import Opportunity

        try:
            async with async_session() as session:
                from datetime import timedelta
                cutoff = datetime.utcnow() - timedelta(days=lookback_days)
                result = await session.execute(
                    select(Opportunity).where(Opportunity.created_at >= cutoff)
                )
                opportunities = result.scalars().all()

            if len(opportunities) < 20:
                logger.info("fill_model_insufficient_data", count=len(opportunities))
                return

            X_data = []
            y_data = []

            for opp in opportunities:
                features = [
                    float(opp.roi or 0),
                    0,
                    1.0,
                    opp.created_at.hour if opp.created_at else 12,
                    opp.created_at.weekday() if opp.created_at else 0,
                    0.5,
                    float(opp.roi or 0),
                    float(opp.buy_price or 0),
                ]
                X_data.append(features)
                y_data.append(1 if opp.status == "executed" else 0)

            X = np.array(X_data)
            y = np.array(y_data)

            if len(set(y)) < 2:
                logger.info("fill_model_single_class", label=int(y[0]))
                return

            model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                random_state=42,
            )
            model.fit(X, y)
            self._model = model
            self._is_trained = True
            self.save()

            logger.info(
                "fill_model_trained",
                samples=len(X),
                positive=int(y.sum()),
                negative=int(len(y) - y.sum()),
            )

        except Exception as e:
            logger.error("fill_model_train_error", error=str(e)[:120])

    def load(self):
        """Load a previously trained model from disk."""
        if MODEL_PATH.exists():
            try:
                with open(MODEL_PATH, "rb") as f:
                    self._model = pickle.load(f)
                self._is_trained = True
                logger.info("fill_model_loaded", path=str(MODEL_PATH))
            except Exception as e:
                logger.warning("fill_model_load_error", error=str(e)[:80])
                self._is_trained = False

    def save(self):
        """Persist trained model to disk."""
        if self._model is None:
            return
        try:
            MODEL_DIR.mkdir(parents=True, exist_ok=True)
            with open(MODEL_PATH, "wb") as f:
                pickle.dump(self._model, f)
            logger.info("fill_model_saved", path=str(MODEL_PATH))
        except Exception as e:
            logger.warning("fill_model_save_error", error=str(e)[:80])

    @property
    def is_trained(self) -> bool:
        return self._is_trained
